# Üretim Yayın Kontrol Listesi (Faz 4)

## Lisans ve Hukuk
- [ ] **Swiss Ephemeris ticari lisansı** — kerykeion/pyswisseph AGPLv3'tür.
      Kapalı kaynak mağaza yayını öncesi Astrodienst AG'den ticari lisans
      alınmalı (~750 CHF, tek seferlik): https://www.astro.com/swisseph/
- [ ] KVKK/GDPR aydınlatma metni ve gizlilik politikası (yüz fotoğrafı işlenip
      **anında silinir** — bu açıkça yazılmalı)
- [ ] Kullanım şartları: yorumların eğlence/içgörü amaçlı olduğu, tıbbi/finansal
      tavsiye olmadığı ibaresi (uygulamada mevcut, sözleşmeye de eklenecek)
- [ ] Apple App Store 5.3.1 / Google Play "fal" kategori kuralları incelemesi

## Güvenlik
- [x] Firebase Auth ID token doğrulaması (backend, `RYTHO_DEV_MODE=0`)
- [x] Firestore güvenlik kuralları (owner-only yazma, katılımcı-only DM)
- [x] Gemini anahtarı Secret Manager'da; API-kısıtlı anahtar kullanılıyor
- [ ] Firebase App Check (Play Integrity / DeviceCheck) etkinleştir
- [ ] Storage kuralları deploy (önce konsoldan Storage "Get Started")
- [ ] Cloud Run min-instance=0 maliyet / cold-start dengesi gözden geçir
- [ ] Rate limiting (Cloud Armor veya uygulama içi kota)

## Moderasyon
- [x] `/api/v1/chat/moderate` ucu mevcut (Gemini tabanlı)
- [ ] Akış gönderilerinde yayın öncesi moderasyon çağrısı zorunlu kıl
- [ ] Kullanıcı şikayet (report) akışı + engelleme

## Kalite
- [ ] Sentry / Crashlytics entegrasyonu
- [ ] Analytics (Firebase Analytics) olay şeması
- [ ] Yük testi: rapor uçları LLM'e bağlı — önbellek isabet oranını izle
- [ ] iOS derlemesi (macOS gerektirir) + TestFlight
- [ ] Android imzalama anahtarı üret, Play Console iç test kanalı

## Monetizasyon (öneri)
- [ ] Ücretsiz: günlük okuma, temel harita, sınırlı sohbet
- [ ] Premium: sınırsız sohbet, derin raporlar (natal/BaZi tam), sinastri,
      yüz okuma; RevenueCat ile abonelik
