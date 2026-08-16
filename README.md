# RythoAI — Kişisel Kozmik Zeka Platformu

Kadim kaynakların (İlm-i Nücum, Kıyafetname, Mian Xiang, BaZi, I Ching, Batı astrolojisi)
AI tarafından öğrenildiği (RAG bilgi tabanı), gerçek astronomik veriyle (Swiss Ephemeris + NASA JPL)
beslenen, kullanıcıyı zamanla tanıyıp kişiye özel yorum üreten çok platformlu uygulama.

> **v1 kapsamı.** Serbest metinli sosyal katman (gönderi akışı, kanallar, DM)
> ticari v1'de **yoktur**. Sosyal katmanın yerini serbest metin içermeyen
> arkadaş deneyimi alır: seri görünürlüğü, kapalı kümeden hazır tepkiler ve
> günlük ikili dinamik. **Yüz okuma kapsam içindedir** — tamamen cihaz
> üstünde (MediaPipe); görüntü sunucuya gitmez.

## Depo Yapısı

```
astroaiproject/
├── apps/
│   └── mobile/          # Flutter istemci (iOS / Android / Web)
├── backend/             # FastAPI hesaplama + AI motoru (Cloud Run)
│   ├── api/             # REST uçları
│   ├── core/            # config, auth, cache
│   ├── services/        # astroloji, bazi, iching, yüz, RAG, rapor
│   └── data/            # heksagram verileri vb.
├── knowledge/           # AI bilgi tabanı
│   ├── corpus/          # RAG için kadim metin korpusu (markdown)
│   └── rules/           # Kıyafetname / Mian Xiang / Wu Xing kural matrisleri (JSON)
├── infra/               # Deploy betikleri, Firebase kuralları
├── docs/
│   └── design/          # Tasarım sistemi stil rehberi
└── legacy/
    └── android/         # Eski Android-native prototip (referans amaçlı)
```

## Bileşenler

| Bileşen | Teknoloji | Açıklama |
|---|---|---|
| Mobil istemci | Flutter + Riverpod + Dio | Yeni "astronomik enstrüman / gravür" tasarım dili |
| Backend | FastAPI (Python 3.11) | Cloud Run üzerinde; Firebase Auth token doğrulamalı |
| Astroloji | Kerykeion / Swiss Ephemeris | Natal, transit, sinastri; Tropikal + Sidereal (Lahiri) |
| Çin metafiziği | Özel BaZi motoru + 64 heksagram I Ching | Jie Qi güneş terimleri swisseph ile hesaplanır |
| AI yorum | Gemini (gemini-flash-latest) + RAG | knowledge/ korpusundan pasaj çekilir, önbelleklenir |
| Önbellek | Firestore (üretim) / dosya (lokal) | Instance'lar arası paylaşımlı; burç yorumu dönem başına bir kez üretilir |
| Veri | Firebase (Auth, Firestore, Storage, FCM) | Profiller, kullanıcı hafızası, bildirim |
| Yüz analizi | MediaPipe Face Mesh | **v1 içinde, cihaz üstünde** — görüntü telefondan çıkmaz; sunucuya yalnız oranlar gider |

## Geliştirme

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1          # veya: python -m venv .venv
pip install -r requirements.txt      # bulut-uyumlu çekirdek
pip install -r requirements-local.txt  # opsiyonel: DeepFace/TF
copy .env.example .env               # anahtarları doldurun
uvicorn main:app --reload --port 8000
```

API dokümantasyonu: http://localhost:8000/docs

### Mobil (Flutter)

```powershell
cd apps/mobile
flutter pub get
flutter run
```

Backend adresi `--dart-define=RYTHO_API_URL=...` ile geçilir; verilmezse
Cloud Run üretim adresi kullanılır.

### Deploy

```powershell
# Backend -> Cloud Run
cd infra
./deploy-backend.ps1

# Firestore kuralları + indexler
firebase deploy --only firestore,storage
```

## Üretim Ortamı

| Kaynak | Adres |
|---|---|
| Backend (Cloud Run) | https://rytho-backend-770582338651.us-central1.run.app |
| API dokümantasyonu | https://rytho-backend-770582338651.us-central1.run.app/docs |
| Firebase Console | https://console.firebase.google.com/project/rhytoai |
| İmaj deposu | `us-central1-docker.pkg.dev/rhytoai/rytho/backend` |

Gemini anahtarı Secret Manager'da `GEMINI_API_KEY` olarak tutulur; Cloud Run
bunu ortam değişkeni olarak okur. Not: Cloud Run'da `/healthz` yolu Google
Frontend tarafından yakalanabildiğinden canlılık kontrolü için kök `/` ucunu
kullanın.

## Ortam Değişkenleri (backend/.env)

| Değişken | Açıklama |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio anahtarı |
| `GOOGLE_CLOUD_PROJECT` | `rhytoai` |
| `RYTHO_DEV_MODE` | `1` ise auth zorunlu değil (sadece lokal) |
| `KNOWLEDGE_DIR` | Bilgi tabanı dizini (varsayılan: `../knowledge`) |

## Lisans Notu

Swiss Ephemeris (kerykeion/pyswisseph) **AGPL** lisanslıdır. Kapalı kaynak ticari
yayın öncesi Astrodienst ticari lisansı (~750 CHF) satın alınmalıdır.
Bkz. `docs/production-checklist.md`.
