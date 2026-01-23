import os
import sys
from datetime import datetime

# Proje kök dizinini sys.path'e ekle (app modülünü bulabilmesi için)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.notification_service import send_database_to_telegram
from app.utils import logger

def run_daily_backup():
    # Veritabanı yolu (app/database.py ile aynı mantıkta)
    db_path = os.path.join(BASE_DIR, "data", "kombi_master_v2.db")
    
    if not os.path.exists(db_path):
        logger.error(f"Veritabanı bulunamadı: {db_path}")
        return

    logger.info(f"Otomatik günlük yedekleme başlatıldı: {datetime.now()}")
    
    success, message = send_database_to_telegram(db_path)
    
    if success:
        logger.info(f"Günlük yedekleme başarılı: {message}")
    else:
        logger.error(f"Günlük yedekleme hatası: {message}")

if __name__ == "__main__":
    run_daily_backup()
