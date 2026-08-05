# Konsol görevleri — senin yapman gerekenler (Revize R9)

Bu dosya, Revize 2 turunda kodun DIŞINDA kalan ve konsollardan elle
yapılması gereken işlerin adım adım listesi. Her bölümün başında hangi
özelliğin buna bağlı olduğu yazıyor: yapılmadan o özellik üretimde
çalışmaz.

Sunucu tarafı hazır ve yayında: cüzdan uçları, webhook'un paket/iade
işleme sırası, tek cihaz kilidi, telefon eşleme, rehber eşleşmesi, sohbet
arşivi + gece 03:20 temizlik cron'u (`rytho-cleanup`) ve `aiCache` TTL
politikası kuruldu. Aşağıdakiler sende.

---

## 1. Firebase: Telefon sağlayıcısını aç (R2 — SMS doğrulama)

Açılmadan: Profil > "Telefonunu doğrula" akışı SMS gönderemez ve
`auth/operation-not-allowed` hatası verir. Rehber eşleşmesi de telefona
bağlı olduğu için o da fiilen kapalı kalır.

1. console.firebase.google.com → **rhytoai** projesi.
2. Sol menü **Authentication → Sign-in method**.
3. **Add new provider → Phone** → aç (Enable) → **Save**.
4. Aynı sayfada **Settings → SMS region policy**: **Allow** listesine
   yalnızca hedef ülkeleri ekle (ilk sürüm için Türkiye yeter).
   Bu ayar SMS-pompalama istismarına karşı: açık bırakılırsa botlar
   pahalı ülkelere SMS attırıp fatura şişirebiliyor.
5. İstersen **Phone numbers for testing** bölümüne kendi numaranı sabit
   bir kodla ekle — mağaza incelemesi için de işe yarar.

Not: SMS gönderimi Blaze planında ücretlidir (Türkiye ~0,01-0,05 USD/SMS).

## 2. RevenueCat: 3 token paketi + entitlement adı (R1 — token ekonomisi)

Yapılmadan: Token mağazası ekranı paketleri listeleyemez ("ürün
bulunamadı") ve satın alma yapılamaz. Sunucudaki miktarlar SABİT:
`small=100 · medium=300 · large=1000` token — mağazadaki ürün kimlikleri
birebir şu olmalı:

    rytho_tokens_small
    rytho_tokens_medium
    rytho_tokens_large

### 2a. Play Console

1. play.google.com/console → uygulama → **Para kazanma → Ürünler →
   Uygulama içi ürünler → Ürün oluştur**.
2. Ürün kimliği: `rytho_tokens_small` · ad: "100 Token" ·
   fiyat önerisi: $1.99 karşılığı.
3. Aynısını `rytho_tokens_medium` ("300 Token", ~$4.99) ve
   `rytho_tokens_large` ("1000 Token", ~$12.99) için tekrarla.
4. Üçünü de **Etkinleştir**.

### 2b. App Store Connect

1. appstoreconnect.apple.com → uygulama → **Uygulama İçi Satın Almalar**.
2. **+ → Sarf Edilebilir (Consumable)** — Product ID'ler yukarıdakiyle
   BİREBİR aynı olmalı. Üç ürünü de oluştur, fiyat basamaklarını seç,
   yerelleştirilmiş ad/açıklama gir.

### 2c. RevenueCat paneli

1. app.revenuecat.com → proje → **Products** → **+ New** ile üç ürünü de
   ekle ve ilgili mağaza ürünlerine bağla.
2. Bu üç ürünü HİÇBİR entitlement'a BAĞLAMA: bunlar aboneliğe değil
   cüzdana gidiyor; krediyi webhook'taki `NON_RENEWING_PURCHASE` olayı
   ürün kimliğinden veriyor.
3. **Entitlement adı tutarsızlığı**: mobil kod varsayılan olarak
   `rytho_plus` entitlement'ına bakıyor (`RYTHO_PLUS_ENTITLEMENT`
   define'ı ile değiştirilebilir). RevenueCat'te entitlement'ın
   "RhytoAI Pro" ise iki seçenekten birini yap:
   - (önerilen) RevenueCat → Entitlements → kimliği `rytho_plus` yap; YA DA
   - `apps/mobile/dart_defines.local.json` içine
     `"RYTHO_PLUS_ENTITLEMENT": "RhytoAI Pro"` ekle.
4. **Webhook** (kuruluysa atla): Project settings → Integrations →
   Webhooks → URL:
   `https://rytho-backend-770582338651.us-central1.run.app/api/v1/billing/revenuecat`
   Authorization başlığına Secret Manager'daki
   `REVENUECAT_WEBHOOK_SECRET` değerini yaz.

## 3. Gerçek RevenueCat API anahtarları (#17 — yayın öncesi şart)

`dart_defines.local.json` hâlâ `test_` anahtarları taşıyorsa gerçek satın
alma çalışmaz:

1. RevenueCat → **Project settings → API keys**.
2. **Public app-specific API keys** bölümünden Google (goog_...) ve
   Apple (appl_...) anahtarlarını kopyala.
3. `apps/mobile/dart_defines.local.json` içinde
   `REVENUECAT_ANDROID_KEY` ve `REVENUECAT_IOS_KEY` değerlerini değiştir.
   (Dosya gitignore'da; anahtarlar repoya girmez.)

## 3b. Test kilidi: RYTHO_FORCE_PLUS (yayın öncesi GERİ ALINACAK)

Test sürecinde tüm Rytho+ kilitleri açık dursun diye backend'e
`RYTHO_FORCE_PLUS=1` ortam değişkeni verildi (R10): sunucu herkesi abone
sayar, mobil kilitler de `/billing/status` üzerinden buna uyar.

**Yayına çıkmadan önce mutlaka kaldır** (yoksa ücretli içerik herkese
açık gider):

```
gcloud run services update rytho-backend --region us-central1 \
  --project rhytoai --remove-env-vars RYTHO_FORCE_PLUS
```

Aynı kapanış listesinde: `RYTHO_TOKENS_ENFORCE` hâlâ 0 (jeton harcaması
kuru çalışma modunda) — gözlem bitince 1 yapılacak.

## 4. Mağaza veri güvenliği formları (R2/R3/R4/R5 sonrası güncelleme)

Yapılmadan: form ile uygulamanın gerçek davranışı çelişir; iki mağaza da
bunu tespit ederse yayından kaldırma sebebi.

Tek doğru kaynak repo'da hazır: **`docs/store-privacy-labels.md`** —
satır satır bu dosyadan aktar. Bu turda DEĞİŞEN beyanlar:

- **Telefon numarası** (isteğe bağlı): App functionality; ham numara
  saklanmaz, yalnızca SHA-256 özeti.
- **Rehber**: yalnızca ayar AÇIKKEN, yalnızca numara özetleri, sunucuda
  SAKLANMAZ (geçici işleme). Ad/soyad okunmaz.
- **Sohbet arşivi**: konuşmalar artık hesapta saklanıyor (30 gün
  kullanılmayan silinir) — "Messages" beyanı güncellenmeli.
- **Galeriden yüz okuma**: görüntü toplanmıyor (cihazda işlenir,
  kopya silinir) — "Photos" beyanı YİNE GEREKMEZ; sadece açıklama
  metinlerinde galeri yolunun geçtiğinden emin ol.

Adımlar:
1. Play Console → **Politika → Uygulama içeriği → Veri güvenliği** →
   formu yukarıdaki değişikliklerle güncelle → gönder.
2. App Store Connect → **Uygulama Gizliliği** → aynı güncellemeler.

## 5. Kuruldu — dokunman gerekmiyor (kayıt için)

- `aiCache.expiresAt` Firestore TTL politikası (gcloud ile kuruldu;
  konsoldan görmek istersen: Firestore → TTL sekmesi).
- `rytho-cleanup` Cloud Scheduler işi (her gece 03:20 UTC, 30 günlük
  konuşma temizliği) — elle tetiklendi ve doğrulandı.
- `rytho-notify-daily` / `rytho-notify-streak` işleri güncellendi.
- Backend revizyon 00027 yayında; Firestore kuralları ve collection-group
  indeksi deploy edildi.
