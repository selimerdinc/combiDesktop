from fastapi import APIRouter, HTTPException, Request
from app.database import db_mgr
from app.utils import clean_phone
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("")
def list_customers(request: Request, q: str = ""):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    user_id = user['user_id']
    q = q.strip()
    
    with db_mgr.get_connection() as conn:
        if not q:
            rows = conn.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,)).fetchall()
            return [dict(r) for r in rows]

        # 1. Telefon Araması (Sadece rakamları al)
        phone_val = clean_phone(q)
        sql_parts = []
        params = [user_id]
        
        if len(phone_val) >= 3:
            sql_parts.append("phone LIKE ?")
            params.append(f"%{phone_val}%")
        
        # 2. Metin Araması (Kelime bazlı)
        words = q.split()
        if words:
            word_conditions = []
            for w in words:
                w_wild = f"%{w}%"
                cond = "(PY_UPPER(name) LIKE PY_UPPER(?) OR PY_UPPER(district) LIKE PY_UPPER(?) OR PY_UPPER(address) LIKE PY_UPPER(?))"
                word_conditions.append(cond)
                params.extend([w_wild, w_wild, w_wild])
            
            if word_conditions:
                sql_parts.append("(" + " AND ".join(word_conditions) + ")")
        
        if not sql_parts:
             return []

        final_sql = "SELECT * FROM customers WHERE user_id = ? AND (" + " OR ".join(sql_parts) + ")"
        rows = conn.execute(final_sql, params).fetchall()
        return [dict(r) for r in rows]

@router.get("/{id}")
def get_customer(request: Request, id: int):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        row = conn.execute("SELECT * FROM customers WHERE id=? AND user_id=?", (id, user['user_id'])).fetchone()
        return dict(row) if row else {}

@router.put("/{id}")
async def update_customer(request: Request, id: int, data: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    try:
        new_name = data['name'].upper().strip()
        phone_cleaned = clean_phone(data['phone'])
        if len(phone_cleaned) < 10: raise HTTPException(status_code=400, detail="Telefon en az 10 hane olmalı!")

        with db_mgr.get_connection() as conn:
            # Sadece kendi müşterisini güncelleyebilir
            existing = conn.execute("SELECT id FROM customers WHERE name = ? AND id != ? AND user_id = ?", 
                                   (new_name, id, user['user_id'])).fetchone()
            if existing:
                target_id = existing['id']
                conn.execute("UPDATE records SET customer_id = ? WHERE customer_id = ?", (target_id, id))
                conn.execute("UPDATE customers SET phone=?, district=?, address=? WHERE id=?",
                             (phone_cleaned, data['district'], data['address'], target_id))
                conn.execute("DELETE FROM customers WHERE id = ?", (id,))
                conn.commit()
                return {"status": "merged", "new_id": target_id}
            else:
                conn.execute("UPDATE customers SET name=?, phone=?, district=?, address=? WHERE id=? AND user_id=?",
                             (new_name, phone_cleaned, data['district'], data['address'], id, user['user_id']))
                conn.commit()
                return {"status": "ok", "new_id": id}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{id}")
def delete_customer(request: Request, id: int):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        conn.execute("DELETE FROM customers WHERE id=? AND user_id=?", (id, user['user_id']))
        conn.commit()
    return {"status": "ok"}

@router.get("/{id}/history")
def get_history(request: Request, id: int):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        rows = conn.execute("SELECT * FROM records WHERE customer_id=? AND user_id=? ORDER BY date DESC", 
                           (id, user['user_id'])).fetchall()
        return [dict(r) for r in rows]

from datetime import datetime, timedelta
from app.utils import clean_float

@router.post("")
async def add_customer_service(request: Request, data: dict):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    user_id = user['user_id']
    
    try:
        name_val = data['name'].upper().strip()
        phone_cleaned = clean_phone(data['phone'])
        if len(phone_cleaned) < 10: raise HTTPException(status_code=400, detail="Telefon en az 10 hane olmalı!")
        
        with db_mgr.get_connection() as conn:
            # Aynı kullanıcının müşterisi var mı kontrol et
            existing = conn.execute("SELECT id FROM customers WHERE name = ? AND user_id = ?", (name_val, user_id)).fetchone()
            if existing:
                c_id = existing['id']
                conn.execute("UPDATE customers SET phone=?, district=?, address=? WHERE id=?", 
                            (phone_cleaned, data['district'], data['address'], c_id))
            else:
                c_id = conn.execute("INSERT INTO customers (user_id, name, phone, district, address) VALUES (?,?,?,?,?)", 
                                   (user_id, name_val, phone_cleaned, data['district'], data['address'])).lastrowid
            
            total, paid = clean_float(data.get('total_fee', 0)), clean_float(data.get('paid_fee', 0))
            is_paid = 1 if paid >= total and total > 0 else 0
            
            if data.get('date'):
                process_date = datetime.strptime(data['date'], '%Y-%m-%d')
            else:
                process_date = datetime.now()
            
            process_date_str = process_date.strftime('%Y-%m-%d')
            rem_date = (process_date + timedelta(days=365)).strftime('%Y-%m-%d') if data['type'] == 'Bakım' else None
            
            conn.execute('''INSERT INTO records (user_id, customer_id, brand, job, total_fee, paid_fee, is_paid, type, date, reminder_date) VALUES (?,?,?,?,?,?,?,?,?,?)''',
                         (user_id, c_id, data['brand'], data['job'], total, paid, is_paid, data['type'], process_date_str, rem_date))
            conn.commit()
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))
