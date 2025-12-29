from fastapi import APIRouter, Request, HTTPException
from app.database import db_mgr
from app.routers.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/finance", tags=["finance"])

@router.get("/monthly")
def get_monthly_finance(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        rows = conn.execute('''SELECT strftime('%Y-%m', date) as month, COALESCE(SUM(paid_fee), 0) as total 
                               FROM records WHERE user_id = ? GROUP BY month HAVING total > 0 ORDER BY month DESC''', 
                           (user['user_id'],)).fetchall()
        return [dict(r) for r in rows]

@router.get("/unpaid")
def get_unpaid_records(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        rows = conn.execute('''SELECT r.*, c.name, c.phone, (r.total_fee - r.paid_fee) as debt
                               FROM records r JOIN customers c ON r.customer_id = c.id 
                               WHERE r.is_paid = 0 AND debt > 0 AND r.user_id = ? ORDER BY r.date DESC''',
                           (user['user_id'],)).fetchall()
        return [dict(r) for r in rows]

@router.get("/stats")
def get_stats(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Oturum gerekli")
    
    with db_mgr.get_connection() as conn:
        now_str = datetime.now().strftime('%Y-%m')
        ay = conn.execute("SELECT COALESCE(SUM(paid_fee), 0) FROM records WHERE strftime('%Y-%m', date) = ? AND user_id = ?", 
                         (now_str, user['user_id'])).fetchone()[0]
        alinacak = conn.execute("SELECT COALESCE(SUM(r.total_fee - r.paid_fee), 0) FROM records r JOIN customers c ON r.customer_id = c.id WHERE r.is_paid = 0 AND r.user_id = ?",
                               (user['user_id'],)).fetchone()[0]
        return {"aylik": ay, "alinacak": alinacak}
