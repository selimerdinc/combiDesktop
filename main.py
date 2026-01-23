import threading
import uvicorn
import os
import time
import webbrowser
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.routers import customers, finance, records, auth
from app.utils import logger

# FastAPI Uygulaması
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Modülleri Dahil Et
app.include_router(customers.router)
app.include_router(finance.router)
app.include_router(records.router)
app.include_router(auth.router)

# HTML Dosya Yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "app", "ui")
TEMPLATE_PATH = os.path.join(UI_DIR, "index.html")
LOGIN_PATH = os.path.join(UI_DIR, "login.html")

# Static dosyaları servis et (JS, CSS, Resimler için)
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

def get_html(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        # Her sunucu basladiginda yeni bir version ID uret (Cache Busting)
        version = int(time.time())
        return content.replace("{{VERSION}}", str(version))

# Auth Middleware - API dışındaki tüm istekleri kontrol et
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Bu yollar auth gerektirmez
    public_paths = ["/login", "/api/auth/login", "/api/auth/check"]
    
    if any(request.url.path.startswith(p) for p in public_paths):
        return await call_next(request)
    
    # Session kontrolü (veritabanından)
    token = request.cookies.get("session_token")
    if token and auth.get_session(token):
        return await call_next(request)
    
    # API isteği ise 401, değilse login'e yönlendir
    if request.url.path.startswith("/api/"):
        return HTMLResponse(status_code=401, content='{"detail": "Oturum gerekli"}')
    
    return RedirectResponse(url="/login", status_code=302)

# Login sayfası
@app.get("/login", response_class=HTMLResponse)
def serve_login():
    return get_html(LOGIN_PATH)

# Ana sayfa (korumalı)
@app.get("/", response_class=HTMLResponse)
def serve_home():
    return get_html(TEMPLATE_PATH)

# Desktop modu için pywebview desteği (opsiyonel)
def run_desktop():
    try:
        import webview
        
        class JSApi:
            def open_external(self, url):
                webbrowser.open(url)
        
        api = JSApi()
        webview.create_window('Kombi Master Pro v3.0', html=get_html(TEMPLATE_PATH), js_api=api, width=1300, height=850)
        webview.start()
    except ImportError:
        print("pywebview yüklü değil. Sadece web modunda çalışıyor.")
        print("Tarayıcınızda açın: http://127.0.0.1:8000")

if __name__ == "__main__":
    import sys
    
    if "--web" in sys.argv or "--server" in sys.argv:
        # Sunucu modu: Sadece web servisi çalıştır
        logger.info("🌐 Sunucu modu aktif! http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    else:
        # Desktop modu: pywebview ile masaüstü uygulaması
        logger.info("🖥️ Masaüstü modu başlatılıyor...")
        t = threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error"), daemon=True)
        t.start()
        run_desktop()