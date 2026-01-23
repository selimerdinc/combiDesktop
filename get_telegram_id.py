import requests
import os
import time
from dotenv import load_dotenv

def get_chat_id():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token or "your_bot_token" in token:
        token = input("Lütfen Telegram Bot Tokeninizi girin: ").strip()
    
    print(f"\n🔍 Bot kontrol ediliyor... (Token: {token[:10]}...)")
    print("💡 İPUCU: Eğer ID görünmüyorsa, Telegram'dan botunuza bir mesaj (örrn: 'merhaba') gönderin.\n")
    
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        while True:
            response = requests.get(url).json()
            if not response.get("ok"):
                print(f"❌ Hata: {response.get('description', 'Bilinmeyen hata')}")
                return

            results = response.get("result", [])
            if results:
                last_msg = results[-1]
                chat_id = last_msg.get("message", {}).get("chat", {}).get("id")
                user_name = last_msg.get("message", {}).get("from", {}).get("first_name")
                
                print("✅ ID BULDUM!")
                print(f"👤 Kullanıcı: {user_name}")
                print(f"🆔 Chat ID: {chat_id}")
                print("\nBu ID değerini .env dosyasındaki TELEGRAM_CHAT_ID kısmına yapıştırın.")
                break
            else:
                print("⏳ Mesaj bekleniyor... (Botunuza Telegram'dan bir mesaj atın)", end="\r")
                time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nİşlem iptal edildi.")
    except Exception as e:
        print(f"\n❌ Beklenmedik hata: {e}")

if __name__ == "__main__":
    get_chat_id()
