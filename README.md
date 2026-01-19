# Kombi Master Pro 🔧

Kombi servis takip ve müşteri yönetim sistemi.

## Özellikler

- 👥 Müşteri yönetimi (ekleme, düzenleme, silme)
- 📝 Servis kayıtları (marka, iş, ücret bilgileri)
- 💰 Borç ve tahsilat takibi
- 🔔 Yıllık bakım hatırlatıcıları
- 📊 Aylık gelir raporları
- 👤 Çoklu kullanıcı desteği
- 🔐 Kullanıcı yönetimi (kayıt, şifre değiştirme, silme)
- 📥 Excel'den veri aktarımı
- 💾 Veritabanı backup
- 💬 WhatsApp entegrasyonu (bakım hatırlatma, borç talebi)

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
# Image oluştur ve çalıştır
docker-compose up -d

# Logları gör
docker-compose logs -f
```

## Erişim

- **Web:** http://localhost:8000
- **Varsayılan Kullanıcı:** admin / kombi2024

## Proje Yapısı

```
combiDesktop/
├── main.py              # Ana uygulama (FastAPI + pywebview)
├── app/
│   ├── database.py      # Veritabanı işlemleri (SQLite)
│   ├── utils.py         # Yardımcı fonksiyonlar
│   ├── routers/         # API endpoint'leri
│   │   ├── auth.py      # Kimlik doğrulama & kullanıcı yönetimi
│   │   ├── customers.py # Müşteri işlemleri
│   │   ├── finance.py   # Finans raporları
│   │   └── records.py   # Kayıt işlemleri & Excel import
│   └── ui/              # Frontend
│       ├── index.html   # Ana sayfa (SPA)
│       └── login.html   # Giriş sayfası
├── data/                # Veritabanı dosyası (Docker volume)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

## API Endpoints

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/customers` | GET, POST | Müşteri listele/ekle |
| `/api/customers/{id}` | GET, PUT, DELETE | Müşteri detay/güncelle/sil |
| `/api/customers/{id}/history` | GET | Müşteri servis geçmişi |
| `/api/finance/monthly` | GET | Aylık gelir raporu |
| `/api/finance/unpaid` | GET | Ödenmemiş borçlar |
| `/api/finance/stats` | GET | Özet istatistikler |
| `/api/reminders` | GET | Bakım hatırlatıcıları |
| `/api/records/{id}/collect` | POST | Tam ödeme al |
| `/api/records/{id}/partial-payment` | POST | Kısmi ödeme al |
| `/api/auth/login` | POST | Giriş yap |
| `/api/auth/logout` | POST | Çıkış yap |
| `/api/auth/register` | POST | Yeni kullanıcı kayıt |
| `/api/auth/users` | GET | Kullanıcı listesi |
| `/api/auth/change-password` | POST | Şifre değiştir |
| `/api/backup/download` | GET | Veritabanı backup indir |
| `/api/import-excel` | POST | Excel'den veri aktar |

## Lisans

MIT
# Auto-deploy test: Mon Jan 19 06:36:04 +03 2026

