import requests
import os
from dotenv import load_dotenv
from app.utils import logger

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_database_to_telegram(db_path: str):
    """Veritabanı dosyasını Telegram üzerinden gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials missing in environment variables!")
        return False, "Telegram ayarları eksik (.env dosyasını kontrol edin)"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    
    try:
        with open(db_path, 'rb') as db_file:
            files = {'document': db_file}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': f"🤖 Kombi Master Pro Yedek\n📅 Tarih: {os.path.basename(db_path)}"
            }
            response = requests.post(url, data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                logger.info("Database successfully sent to Telegram.")
                return True, "Yedek Telegram'a gönderildi!"
            else:
                error_msg = response.json().get('description', 'Bilinmeyen hata')
                logger.error(f"Telegram API Error: {error_msg}")
                return False, f"Telegram Hatası: {error_msg}"
                
    except Exception as e:
        logger.error(f"Failed to send backup to Telegram: {str(e)}")
        return False, f"Beklenmedik bir hata oluştu: {str(e)}"
