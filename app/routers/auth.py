from fastapi import APIRouter, HTTPException, Response, Request
from app.database import db_mgr, hash_password
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Session yardımcı fonksiyonları (veritabanı tabanlı)
def create_session(user_id: int, username: str, name: str) -> str:
    """Yeni session oluştur ve veritabanına kaydet"""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(days=7)
    
    with db_mgr.get_connection() as conn:
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, user_id, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
    
    return token

def get_session(token: str) -> dict:
    """Token'dan session bilgisi al"""
    if not token:
        return None
    
    with db_mgr.get_connection() as conn:
        row = conn.execute("""
            SELECT s.user_id, u.username, u.name, s.expires_at 
            FROM sessions s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.token = ?
        """, (token,)).fetchone()
        
        if not row:
            return None
        
        # Süre dolmuş mu kontrol et
        expires_at = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires_at:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        
        return {
            "user_id": row['user_id'],
            "username": row['username'],
            "name": row['name']
        }

def delete_session(token: str):
    """Session'ı sil"""
    with db_mgr.get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()

def cleanup_expired_sessions():
    """Süresi dolmuş session'ları temizle"""
    with db_mgr.get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", 
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        conn.commit()

@router.post("/login")
async def login(response: Response, data: dict):
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    
    with db_mgr.get_connection() as conn:
        user = conn.execute(
            "SELECT id, password_hash, name FROM users WHERE LOWER(username) = ?",
            (username,)
        ).fetchone()
        
        if user and user['password_hash'] == hash_password(password):
            # Session token oluştur (veritabanına kaydedilir)
            token = create_session(user['id'], username, user['name'])
            
            # Cookie set et (7 gün geçerli)
            response.set_cookie(
                key="session_token",
                value=token,
                max_age=7 * 24 * 60 * 60,
                httponly=True
            )
            return {"status": "ok", "name": user['name']}
        else:
            raise HTTPException(status_code=401, detail="Kullanıcı adı veya şifre hatalı!")

@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        delete_session(token)
    response.delete_cookie("session_token")
    return {"status": "ok"}

@router.get("/check")
async def check_auth(request: Request):
    token = request.cookies.get("session_token")
    session = get_session(token)
    if session:
        return {"authenticated": True, **session}
    return {"authenticated": False}

@router.post("/register")
async def register(data: dict):
    """Yeni kullanıcı kaydı"""
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    name = data.get("name", "")
    
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Kullanıcı adı en az 3 karakter!")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter!")
    
    with db_mgr.get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış!")
        
        conn.execute(
            "INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
            (username, hash_password(password), name)
        )
        conn.commit()
    
    return {"status": "ok"}

@router.get("/users")
async def list_users(request: Request):
    """Tüm kullanıcıları listele"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        rows = conn.execute("SELECT id, username, name, created_at FROM users ORDER BY id").fetchall()
        return [dict(r) for r in rows]

@router.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: int):
    """Kullanıcı sil"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    if user['user_id'] == user_id:
        raise HTTPException(status_code=400, detail="Kendinizi silemezsiniz!")
    
    with db_mgr.get_connection() as conn:
        # Kullanıcının müşterilerini ve kayıtlarını sil
        conn.execute("DELETE FROM records WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM customers WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    
    return {"status": "ok"}

def get_current_user(request: Request) -> dict:
    """Aktif kullanıcı bilgisini döndür"""
    token = request.cookies.get("session_token")
    return get_session(token)

@router.post("/change-password")
async def change_password(request: Request, data: dict):
    """Kullanıcının kendi şifresini değiştirmesi"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı!")
    
    with db_mgr.get_connection() as conn:
        db_user = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", 
            (user['user_id'],)
        ).fetchone()
        
        if not db_user or db_user['password_hash'] != hash_password(current_password):
            raise HTTPException(status_code=400, detail="Mevcut şifre yanlış!")
        
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user['user_id'])
        )
        conn.commit()
    
    return {"status": "ok"}

# Backward compatibility için active_sessions (main.py middleware için)
# Bu artık veritabanı tabanlı çalışıyor
class SessionProxy:
    def __contains__(self, token):
        return get_session(token) is not None
    
    def __getitem__(self, token):
        return get_session(token)

active_sessions = SessionProxy()
