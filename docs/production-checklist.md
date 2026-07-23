# Üretim Yayın Kontrol Listesi (Faz 4)

## Lisans ve Hukuk
- [ ] **Swiss Ephemeris ticari lisansı** — kerykeion/pyswisseph AGPLv3'tür.
      Kapalı kaynak mağaza yayını öncesi Astrodienst AG'den ticari lisans
      alınmalı (~750 CHF, tek seferlik): https://www.astro.com/swisseph/
      **→ SATIN ALMA, UYGULAMA SAHİBİNİN İŞİDİR; yayından önce zorunlu.**
- [x] KVKK/GDPR aydınlatma metni ve gizlilik politikası
      (docs/legal/gizlilik-politikasi.md — yüz fotoğrafının analiz sonrası
      **anında silindiği** açıkça yazılı; uygulama içinden Sicil → Hakkında
      bölümünde okunabilir)
- [x] Kullanım şartları (docs/legal/kullanim-sartlari.md — eğlence/içgörü
      ibaresi, topluluk kuralları; uygulama içinde Sicil → Hakkında)
- [x] Apple 5.3.1 / Google Play "fal" kategori kuralları incelemesi
      (notlar: docs/store-launch.md §4)
- [ ] Hukuki metinleri bir web adresinde yayınla (mağaza formları URL ister;
      Firebase Hosting önerilir)

## Güvenlik
- [x] Firebase Auth ID token doğrulaması (backend, `RYTHO_DEV_MODE=0`;
      üretimde 401 doğrulandı)
- [x] Firestore güvenlik kuralları (owner-only yazma, katılımcı-only DM,
      reports create-only, blocked owner-only) — deploy edildi
- [x] Gemini anahtarı Secret Manager'da; API-kısıtlı anahtar kullanılıyor
- [ ] Firebase App Check (Play Integrity) — **konsol tarafı uygulama
      sahibinde**; SDK entegrasyonu bilinçli olarak eklenmedi, adımlar:
      docs/store-launch.md §3
- [x] Storage kuralları deploy edildi (`firebase deploy --only storage`)
- [ ] Cloud Run min-instance=0 maliyet / cold-start dengesi gözden geçir
- [x] Rate limiting: uygulama içi kayan pencere kotası
      (backend/core/ratelimit.py — LLM uçları 10/dk, diğerleri 60/dk, 429 +
      Türkçe mesaj; Cloud Run'da yayında)
- [x] Global exception handler (stack trace sızdırmayan Türkçe 500) +
      güvenlik başlıkları (nosniff, X-Frame-Options, HSTS) — yayında

## Moderasyon
- [x] `/api/v1/chat/moderate` ucu mevcut (Gemini tabanlı)
- [x] Akış gönderilerinde yayın öncesi moderasyon çağrısı (composer;
      uygunsuz içerikte nazik uyarı, ağ hatasında fail-open + log)
- [x] Kullanıcı şikayet akışı (gönderi kartı ⋯ menüsü + profil sayfası →
      `reports` koleksiyonu) + engelleme (users/{uid}/blocked; akış ve
      mesajlarda istemci tarafı filtre)

## Kalite
- [x] Crashlytics entegrasyonu (firebase_crashlytics; FlutterError +
      PlatformDispatcher.onError bağlı, debug/web'de devre dışı)
- [x] Analytics olay şeması (lib/core/analytics.dart: report_generated,
      post_published, user_followed, channel_subscribed, iching_cast,
      face_analyzed)
- [ ] Yük testi: rapor uçları LLM'e bağlı — önbellek isabet oranını izle
- [ ] iOS derlemesi (macOS gerektirir) + TestFlight
- [ ] Android imzalama anahtarı üret, Play Console iç test kanalı
      (adımlar: docs/store-launch.md §1-2 — **uygulama sahibinin işi**)

## Monetizasyon (öneri — plan: docs/store-launch.md §5)
- [ ] Ücretsiz: günlük okuma, temel harita, sınırlı sohbet
- [ ] Premium: sınırsız sohbet, derin raporlar (natal/BaZi tam), sinastri,
      yüz okuma; RevenueCat ile abonelik
