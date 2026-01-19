---
description: Oracle Cloud sunucusuna Kombi Pro deploy etme
---

# Kombi Pro Deploy Workflow

## Sunucu Bilgileri
- **SSH:** `ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228`
- **Uygulama:** `/home/ubuntu/kombi-app`
- **Database:** `/home/ubuntu/kombi-app/kombi_master_v2.db`
- **Servis:** `systemd` (kombi.service)
- **URL:** https://kombi.selimerdinc.cloud

## Deploy Adımları

// turbo-all

### 1. Dosyaları sunucuya yükle
```bash
scp -i ~/Downloads/ssh-key-2025-12-29.key app/ui/index.html ubuntu@141.148.220.228:/home/ubuntu/kombi-app/app/ui/
```

### 2. (Backend değişiklikleri için)
```bash
scp -i ~/Downloads/ssh-key-2025-12-29.key app/routers/*.py ubuntu@141.148.220.228:/home/ubuntu/kombi-app/app/routers/
scp -i ~/Downloads/ssh-key-2025-12-29.key main.py ubuntu@141.148.220.228:/home/ubuntu/kombi-app/
```

### 3. Servisi yeniden başlat
```bash
ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228 "sudo systemctl restart kombi"
```

### 4. Durumu kontrol et
```bash
ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228 "sudo systemctl status kombi --no-pager"
```

## Acil Durum Komutları

### Servis Logları
```bash
ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228 "sudo journalctl -u kombi -n 50 --no-pager"
```

### Database Backup (Manuel)
```bash
ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228 "~/backup.sh"
```

### Son Backup'tan Restore
```bash
ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228 "ls -lt ~/backups/*.db | head -1"
ssh -i ~/Downloads/ssh-key-2025-12-29.key ubuntu@141.148.220.228 "cp ~/backups/kombi_YYYY-MM-DD_HH-MM.db ~/kombi-app/kombi_master_v2.db && sudo systemctl restart kombi"
```

## Önemli Notlar
- ⚠️ **TEK KAYNAK:** Sadece `/home/ubuntu/kombi-app` kullanılıyor
- ⚠️ **Docker kullanılmıyor** - systemd ile yönetiliyor
- ✅ **Otomatik başlatma:** Sunucu restart'ta servis otomatik başlar
- ✅ **Günlük backup:** Her gün 03:00'da cron ile alınıyor
- ✅ **30 gün tutma:** Eski backup'lar otomatik siliniyor

