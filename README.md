# Pega-Python Integration

Bu proje Pega ile Python (FastAPI) arasında iki yönlü entegrasyon sağlayan bir köprü uygulamasıdır.

## 🎯 Proje Amacı

Organizasyonlarda departman değişikliği, çalışan onboarding/offboarding gibi HR süreçlerini Pega'dan alıp Python tarafında işlemek ve gerektiğinde Pega'ya geri bildirim göndermek.

## 🏗️ Mimari

```
Pega Case Management → REST API → Python FastAPI → SQLite Database
                                      ↕️
                               External Systems
                            (Email, Slack, Dashboard)
```

## 🚀 Özellikler

### Pega'dan Python'a (Gelen)
- **Webhook Endpoint**: `/webhook/pega` - Pega'dan JSON event'leri alır
- **Event Processing**: Arka planda asenkron işleme
- **Risk Analizi**: Yüksek riskli departman değişiklikleri için otomatik değerlendirme
- **Sistem Entegrasyonları**: Dış sistemlerle otomatik senkronizasyon

### Python'dan Pega'ya (Giden) 
- **Case Oluşturma**: Yeni Pega case'leri oluşturma
- **Case Güncelleme**: Mevcut case'leri güncelleme
- **Not Ekleme**: Case'lere otomatik not ekleme
- **Aksiyon Çalıştırma**: Pega iş akışında aksiyon tetikleme

### Monitoring & Reporting
- **Dashboard**: Gerçek zamanlı istatistikler
- **Event Listesi**: Gelişmiş filtreleme seçenekleri  
- **Metrikler**: 7 günlük trend analizi
- **Event Detayları**: Her event'in işlem sonuçları

## 🛠️ Kurulum

### 1. Projeyi Klonlayın
```bash
git clone https://github.com/YzrSalih/pega-python-integration.git
cd pega-python-integration
```

### 2. Çevre Değişkenlerini Ayarlayın
```bash
cp .env.example .env
# .env dosyasını Pega bağlantı bilgilerinizle düzenleyin
```

### 3. Sunucuyu Başlatın
```bash
./start.sh
```

Alternatif olarak manuel kurulum:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API Endpoints

### Webhook (Pega → Python)
- `POST /webhook/pega` - Pega'dan event alma
- `GET /events` - Event'leri listeleme (filtreleme ile)
- `GET /events/{id}` - Event detayları
- `POST /events/{id}/reprocess` - Failed event'i yeniden işleme

### Pega Integration (Python → Pega)  
- `POST /pega/case` - Yeni case oluşturma
- `PUT /pega/case/{case_id}` - Case güncelleme
- `POST /pega/case/{case_id}/note` - Case'e not ekleme
- `POST /pega/case/{case_id}/action/{action_id}` - Case aksiyonu çalıştırma

### Monitoring
- `GET /health` - Sağlık kontrolü
- `GET /metrics` - 7 günlük istatistikler  
- `GET /dashboard` - Dashboard özet bilgileri

## 🧪 Test Etme

```bash
# Test script'ini çalıştırın
python test_api.py

# Veya manuel test
curl -X POST "http://localhost:8000/webhook/pega" \
     -H "Content-Type: application/json" \
     -d '{
       "caseId": "HRSR-WORK-12345",
       "event": "department_change", 
       "employeeId": "EMP001",
       "oldDepartment": "IT",
       "newDepartment": "Finance"
     }'
```

## 🔧 Yapılandırma

### Çevre Değişkenleri (.env)
```bash
# Pega Bağlantısı
PEGA_URL=https://yourpega.com/prweb/api/v1
PEGA_USERNAME=your_username
PEGA_PASSWORD=your_password
# Alternatif: PEGA_API_KEY=your_api_key

# Diğer
DB_PATH=events.db
LOG_LEVEL=INFO
```

## 📊 Desteklenen Event Türleri

- `department_change` - Departman değişikliği
- `employee_onboarding` - Yeni çalışan işe alım
- `employee_offboarding` - Çalışan çıkış
- `role_change` - Rol değişikliği  

Her event türü için özel iş mantığı ve entegrasyonlar mevcuttur.

## 🔄 İş Akışı Örneği

1. **Pega**: HR departmanında departman değişikliği case'i oluşturulur
2. **Pega → Python**: REST call ile event gönderilir
3. **Python**: Event kaydedilir ve arka planda işlenir:
   - Risk analizi yapılır
   - Dış sistemler güncellenir (badge, email, etc.)
   - Yüksek risk durumunda Pega'ya uyarı gönderilir
4. **Python → Pega**: Gerekirse otomatik case notu veya aksiyon

## 🚀 Geliştirilecek Özellikler

- [ ] Email/Slack bildirimleri
- [ ] Dashboard web arayüzü
- [ ] Advanced risk scoring algoritması
- [ ] Audit trail ve compliance raporları
- [ ] Multi-tenant support
- [ ] Event replay mekanizması

## 📝 API Dokümantasyonu

Sunucu çalıştıktan sonra:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.