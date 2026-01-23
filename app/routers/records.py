from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from app.database import db_mgr, DB_NAME
from app.utils import clean_phone, clean_float, logger
from app.notification_service import send_database_to_telegram
from app.routers.auth import get_current_user
from datetime import datetime, timedelta
import pandas as pd
import io
import os

router = APIRouter(tags=["records"])

@router.get("/api/backup/download")
def download_backup(request: Request):
    """Veritabanı backup dosyasını indir"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    if not os.path.exists(DB_NAME):
        raise HTTPException(status_code=404, detail="Veritabanı bulunamadı")
    
    backup_filename = f"kombi_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
    return FileResponse(
        path=DB_NAME,
        filename=backup_filename,
        media_type="application/octet-stream"
    )

@router.post("/api/backup/telegram")
def telegram_backup(request: Request):
    """Veritabanını Telegram'a gönder"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    if not os.path.exists(DB_NAME):
        raise HTTPException(status_code=404, detail="Veritabanı bulunamadı")
    
    success, message = send_database_to_telegram(DB_NAME)
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"status": "ok", "message": message}

@router.get("/api/reminders")
def get_reminders(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    min_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
    with db_mgr.get_connection() as conn:
        rows = conn.execute('''SELECT r.*, c.name, c.phone FROM records r JOIN customers c ON r.customer_id = c.id 
                               WHERE r.reminder_date >= ? AND r.type = 'Bakım' AND r.user_id = ? ORDER BY r.reminder_date ASC''', 
                           (min_date, user['user_id'])).fetchall()
        return [dict(r) for r in rows]

@router.post("/api/records/{id}/collect")
def collect_payment(request: Request, id: int):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        conn.execute("UPDATE records SET paid_fee = total_fee, is_paid = 1 WHERE id = ? AND user_id = ?", 
                    (id, user['user_id']))
        conn.commit()
    return {"status": "ok"}

@router.post("/api/import-excel")
async def import_excel(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    logger.info(f"Excel import started by user {user['username']}")
    user_id = user['user_id']
    
    try:
        df = pd.read_excel(io.BytesIO(await file.read()))
        df.columns = [str(c).strip().upper() for c in df.columns]
        success, skip = 0, 0
        
        # Kolon eşleştirme (farklı varyasyonları destekle)
        col_map = {
            'NAME': next((c for c in df.columns if 'AD' in c and 'SOYAD' not in c), None),
            'SURNAME': next((c for c in df.columns if 'SOYAD' in c), None),
            'PHONE': next((c for c in df.columns if 'TEL' in c), None),
            'DISTRICT': next((c for c in df.columns if 'SEMT' in c or 'BÖLGE' in c or 'İLÇE' in c), None),
            'ADDRESS': next((c for c in df.columns if 'ADRES' in c), None),
            'JOB': next((c for c in df.columns if 'İŞ' in c or 'AÇIKLAMA' in c), None),
            'FEE': next((c for c in df.columns if 'ÜCRET' in c or 'TUTAR' in c or 'FİYAT' in c), None),
            'BRAND': next((c for c in df.columns if 'MARKA' in c or 'CİHAZ' in c), None),
            'DATE': next((c for c in df.columns if 'TARİH' in c and 'BAKIM' not in c), None),
            'REMINDER': next((c for c in df.columns if 'BAKIM' in c and 'TARİH' in c), None)
        }

        with db_mgr.get_connection() as conn:
            for _, row in df.iterrows():
                try:
                    # Temel bilgiler
                    name = str(row.get(col_map['NAME'], '')).strip().upper()
                    surname = str(row.get(col_map['SURNAME'], '')).strip().upper()
                    full_name = f"{name} {surname}".strip()
                    
                    phone = clean_phone(str(row.get(col_map['PHONE'], '')))
                    if not full_name or len(phone) < 10:
                        skip += 1
                        continue
                    
                    # Diğer bilgiler
                    district = str(row.get(col_map['DISTRICT'], '')).strip()
                    address = str(row.get(col_map['ADDRESS'], '')).strip()
                    job = str(row.get(col_map['JOB'], '')).strip()
                    brand = str(row.get(col_map['BRAND'], '')).strip()
                    ucret = clean_float(row.get(col_map['FEE'], 0))
                    
                    # Tarihler
                    raw_date = row.get(col_map['DATE'])
                    if pd.isna(raw_date) or not raw_date:
                        islem_tarihi = datetime.now().strftime('%Y-%m-%d')
                    else:
                        islem_tarihi = str(raw_date)[:10]

                    raw_rem = row.get(col_map['REMINDER'])
                    if pd.isna(raw_rem) or not raw_rem:
                        rem_date = (datetime.strptime(islem_tarihi, '%Y-%m-%d') + timedelta(days=365)).strftime('%Y-%m-%d')
                    else:
                        rem_date = str(raw_rem)[:10]
                    
                    existing = conn.execute("SELECT id FROM customers WHERE name = ? AND user_id = ?", (full_name, user_id)).fetchone()
                    if existing:
                        c_id = existing['id']
                        conn.execute("UPDATE customers SET phone=?, district=?, address=? WHERE id=?", (phone, district, address, c_id))
                    else:
                        c_id = conn.execute("INSERT INTO customers (user_id, name, phone, district, address) VALUES (?,?,?,?,?)", 
                                           (user_id, full_name, phone, district, address)).lastrowid

                    conn.execute("INSERT INTO records (user_id, customer_id, brand, job, total_fee, paid_fee, is_paid, type, date, reminder_date) VALUES (?,?,?,?,?,?,1,'Bakım',?,?)",
                                 (user_id, c_id, brand, job, ucret, ucret, islem_tarihi, rem_date))
                    success += 1
                except Exception as e:
                    skip += 1
                    continue
            conn.commit()
        return {"count": success, "skipped": skip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel okuma hatası: {str(e)}")

@router.put("/api/records/{id}")
async def update_record(request: Request, id: int, data: dict):
    """Kayıt güncelle"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        total = clean_float(data.get('total_fee', 0))
        paid = clean_float(data.get('paid_fee', 0))
        is_paid = 1 if paid >= total and total > 0 else 0
        
        conn.execute("""
            UPDATE records SET 
                brand = ?, job = ?, total_fee = ?, paid_fee = ?, is_paid = ?, 
                date = ?, reminder_date = ?
            WHERE id = ? AND user_id = ?
        """, (
            data.get('brand', ''), data.get('job', ''), total, paid, is_paid,
            data.get('date'), data.get('reminder_date'),
            id, user['user_id']
        ))
        conn.commit()
    return {"status": "ok"}

@router.delete("/api/records/{id}")
async def delete_record(request: Request, id: int):
    """Kayıt sil"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        conn.execute("DELETE FROM records WHERE id = ? AND user_id = ?", (id, user['user_id']))
        conn.commit()
    return {"status": "ok"}

@router.post("/api/records/{id}/partial-payment")
async def partial_payment(request: Request, id: int, data: dict):
    """Kısmi ödeme al"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    amount = clean_float(data.get('amount', 0))
    
    with db_mgr.get_connection() as conn:
        record = conn.execute("SELECT total_fee, paid_fee FROM records WHERE id = ? AND user_id = ?", 
                             (id, user['user_id'])).fetchone()
        if not record:
            raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
        
        new_paid = record['paid_fee'] + amount
        is_paid = 1 if new_paid >= record['total_fee'] else 0
        
        conn.execute("UPDATE records SET paid_fee = ?, is_paid = ? WHERE id = ?", 
                    (new_paid, is_paid, id))
        conn.commit()
    return {"status": "ok", "new_paid": new_paid}
