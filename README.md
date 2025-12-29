# Kombi Master Pro 🔧

Kombi servis takip ve müşteri yönetim sistemi.

## Özellikler

- 👥 Müşteri yönetimi
- 📝 Servis kayıtları
- 💰 Borç ve tahsilat takibi
- 🔔 Bakım hatırlatıcıları
- 📊 Aylık gelir raporları
- 👤 Çoklu kullanıcı desteği
- 📥 Excel import
- 💾 Veritabanı backup

## Kurulum

### Gereksinimler
- Python 3.9+

### Local Çalıştırma

```bash
# Bağımlılıkları kur
pip install -r requirements.txt

# Masaüstü uygulaması olarak çalıştır
python main.py

# Sadece web sunucu olarak çalıştır
python main.py --server
```

### Docker ile Çalıştırma

```bash
# Image oluştur
docker build -t kombi-pro .

# Çalıştır
docker run -d -p 8000:8000 -v kombi-data:/app kombi-pro
```

## Erişim

- **Web:** http://localhost:8000
- **Varsayılan Kullanıcı:** admin / kombi2024

## Proje Yapısı

```
combiDesktop/
├── main.py              # Ana uygulama
├── app/
│   ├── database.py      # Veritabanı işlemleri
│   ├── utils.py         # Yardımcı fonksiyonlar
│   ├── routers/         # API endpoint'leri
│   │   ├── auth.py      # Kimlik doğrulama
│   │   ├── customers.py # Müşteri işlemleri
│   │   ├── finance.py   # Finans raporları
│   │   └── records.py   # Kayıt işlemleri
│   └── ui/              # Frontend
│       ├── index.html   # Ana sayfa
│       └── login.html   # Giriş sayfası
├── Dockerfile
├── requirements.txt
└── .gitignore
```

## Lisans

MIT
