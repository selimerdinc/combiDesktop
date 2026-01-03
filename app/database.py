import sqlite3
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "kombi_master_v2.db")

def hash_password(password: str) -> str:
    """Şifreyi SHA256 ile hash'le"""
    return hashlib.sha256(password.encode()).hexdigest()

class DatabaseManager:
    def __init__(self):
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Gelişmiş Türkçe Normalizasyon
        tr_map = str.maketrans({
            'ç': 'C', 'Ç': 'C',
            'ğ': 'G', 'Ğ': 'G',
            'ı': 'I', 'I': 'I', 'i': 'I', 'İ': 'I',
            'ö': 'O', 'Ö': 'O',
            'ş': 'S', 'Ş': 'S',
            'ü': 'U', 'Ü': 'U'
        })
        
        conn.create_function("PY_UPPER", 1, lambda x: str(x).translate(tr_map).upper() if x else "")
        
        # Foreign Key desteğini her bağlantıda aç
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Users tablosu
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Sessions tablosu (kalıcı oturum için)
            conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )''')
            
            # Customers tablosu (user_id ile)
            conn.execute('''CREATE TABLE IF NOT EXISTS customers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT, phone TEXT, district TEXT, address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')
            
            # Records tablosu (user_id ile)
            conn.execute('''CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                customer_id INTEGER, brand TEXT, job TEXT,
                total_fee REAL, paid_fee REAL DEFAULT 0,
                is_paid INTEGER DEFAULT 0, type TEXT,
                date DATE, reminder_date DATE,
                FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')
            
            # Mevcut tablolara user_id kolonu ekle (varsa)
            try:
                conn.execute("ALTER TABLE customers ADD COLUMN user_id INTEGER")
            except:
                pass
            try:
                conn.execute("ALTER TABLE records ADD COLUMN user_id INTEGER")
            except:
                pass
            
            # Varsayılan admin kullanıcı oluştur
            admin_exists = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
            if not admin_exists:
                conn.execute(
                    "INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                    ("admin", hash_password("kombi2024"), "Yönetici")
                )
                admin_id = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()[0]
                
                # Mevcut verileri admin'e ata
                conn.execute("UPDATE customers SET user_id = ? WHERE user_id IS NULL", (admin_id,))
                conn.execute("UPDATE records SET user_id = ? WHERE user_id IS NULL", (admin_id,))
            
            conn.commit()

db_mgr = DatabaseManager()
