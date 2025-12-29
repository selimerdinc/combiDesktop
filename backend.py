from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List, Optional

app = FastAPI()



# Veritabanı Bağlantısı
def get_db():
    conn = sqlite3.connect('kombi_pro.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı Başlatma (Tablolar)
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS customers 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, district TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS records 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, brand TEXT, 
         job TEXT, fee REAL, is_paid INTEGER DEFAULT 0, date DATE)''')

# Modeller
class Customer(BaseModel):
    name: str
    phone: str
    district: str

# API Rotaları
@app.get("/customers")
async def get_customers():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM customers").fetchall()
        return [dict(row) for row in rows]

@app.post("/customers")
async def add_customer(cust: Customer):
    try:
        with get_db() as conn:
            cursor = conn.execute("INSERT INTO customers (name, phone, district) VALUES (?,?,?)",
                                 (cust.name, cust.phone, cust.district))
            return {"id": cursor.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Müşteri zaten kayıtlı.")


