# RythoAI Maliyet ve Fiyatlama Çalışması (K-turu, 2026-08-13)

> Tüm sayılar KODDAN ölçülmüş girdilerle (prompt boyutları, önbellek
> tasarımı, jeton tablosu) ve Gemini'nin güncel liste fiyatlarıyla
> hesaplandı. Kur varsayımı **1 USD ≈ 42 ₺** (duyarlılık: 40-45 aralığı
> sonuçları ±%7 oynatır). KDV %20, Google Play komisyonu %15
> (küçük geliştirici katmanı).

## 1. Birim maliyetler (LLM: gemini-flash-latest ≈ 2.5 Flash)

Fiyat: ~$0,30 / 1M girdi token'ı · ~$2,50 / 1M çıktı token'ı (düşünme
kapalı — gemini_service thinking_budget=0). Embedding sorgusu ihmal
edilebilir (~$0,000008/çağrı; önbellek isabetinde hiç yok).

| İş | Girdi (token) | Çıktı (token) | Maliyet/çağrı | Jeton bedeli | Jeton başına gelir* | Marj |
|---|---|---|---|---|---|---|
| Sohbet turu | ~4.000 (tavanlı en kötü ~9.000†) | ≤300 | **~$0,0020** (kötü $0,0034) | 1 | ~$0,010 | %80+ |
| Natal / BaZi / SR / Progresyon / Firasa | ~3.500 | 700-900 | **~$0,0033** | 5 | ~$0,050 | %93 |
| İching (+soru hükmü çağrısı) | ~3.500+800 | ~500 | **~$0,0030** | 2 | ~$0,020 | %85 |
| Dyad (çift başına günlük) | ~2.700 | ~200 | **~$0,0018** | 3 | ~$0,030 | %94 |
| Kişisel günlük (abone, jetonsuz) | ~3.000 | ~250 | ~$0,0015 × 30/ay = **~$0,045/ay** | — | abonelik içinde | — |
| Genel burç yorumu (paylaşımlı) | ~2.800 | ~250 | 72 üretim/gün → **~$4,5/AY TOPLAM** (kullanıcı sayısından bağımsız) | — | — | — |
| Hafıza çıkarımı (günde ≤1) | ~2.000 | ~100 | ~$0,0009 → ≤$0,03/ay/kullanıcı | — | — | — |
| Günlük push metni (paylaşımlı, burç başına) | ~1.100 | ~30 | ihmal | — | — | — |

\* Jeton başına gelir: 100'lük paketin KDV+komisyon sonrası neti
(~$1,0) / 100. †K4 tavanı sonrası (son 12 mesaj × 1.200 kr).

Önbellek çarpanı: raporlar kişi başına 24s-90g önbellekli; harcama ve
LLM çağrısı YALNIZ önbellek kaçırıldığında. İkinci okuma hem ücretsiz
hem maliyetsiz — yani yukarıdaki maliyetler kullanım başına ÜST sınır.

## 2. Gelir ve marj — abonelik

| Kalem | Değer |
|---|---|
| Tüketici fiyatı (KDV dahil, alıcının gördüğü) | **₺179,99/ay** |
| KDV −%20 | ₺149,99 |
| Google Play −%15 | **net ≈ ₺127,5 ≈ $3,0/ay** |

Abonenin aylık LLM maliyeti (senaryolar, jeton zorlaması AÇIK):

| Senaryo | Kullanım | LLM maliyeti | Brüt marj |
|---|---|---|---|
| Hafif | 50 jeton (karışık) + günlük | ~$0,15 | **~%95** |
| Orta | 150 jeton + günlük | ~$0,35 | **~%88** |
| Yoğun (tavan) | 300 jetonun TAMAMI sohbete + günlük + hafıza | **~$0,70** | **~%77** |
| Yoğun + 100'lük ek paket | +$1,0 gelir, +$0,20 maliyet | — | ek paket marjı %80 |

**Sonuç: en kötü durumda bile %77, tipikte %88-95 brüt marj.** Jeton
zorlaması (K5) bu tavanın MATEMATİKSEL garantisidir — kapalıyken tavan
yoktur ve "yoğun kullanıcı" maliyeti sınırsız büyüyebilirdi.

## 3. Jeton paketleri

| Paket | Tüketici (KDV dahil) | Net gelir | Gerçek maliyet aralığı | Marj |
|---|---|---|---|---|
| 100 jeton | ~₺59,99 | ~$1,0 | $0,07 (rapor ağırlıklı) – $0,20 (sohbet) | **%80-93** |
| 300 jeton | ~₺155,99 | ~$2,6 | $0,20-0,60 | **%77-92** |
| 1000 jeton | ~₺419,99 | ~$7,0 | $0,66-2,00 | **%71-91** |

Jeton bedelleri (1/2/3/5) maliyet oranına değil ALGILANAN değere göre
bilinçli: derin rapor sohbet turundan yalnızca %65 pahalı ama 5 kat
jeton — kullanıcı gözünde rapor "büyük iş"tir ve bu doğru fiyatlanmış
hissettirir. Değiştirmeye gerek yok.

## 4. Sabit giderler ve başabaş

| Kalem | Aylık |
|---|---|
| Cloud Run (min-instance 1, 2 vCPU/2Gi — soğuk başlatmayı öldüren bilinçli karar) | ~$25 |
| Genel burç üretimi (paylaşımlı LLM) | ~$4,5 |
| Firestore (küçük ölçek; aiCache+kullanıcı verisi) | ~$1-5 |
| SMS (Türkiye ~$0,01-0,05/adet; kayıt başına 1) | kullanıcıyla ölçeklenir, ~$0,03/yeni kullanıcı |
| NASA/GeoNames/RevenueCat (ücretsiz katman) | $0 |
| **Toplam sabit** | **~$32-35 ≈ ₺1.400** |

**Başabaş: ~11 abone.** Sonrası: her abone net ~$2,3-2,9 katkı
(senaryoya göre). 100 abonede kaba tablo: gelir ~$300, LLM ~$15-70,
sabit ~$35 → **aylık net ~$200-250 ≈ ₺8-10 bin**.

Ücretsiz kullanıcı maliyeti: günde ≤5 sohbet + 1 İching → tavan
~$0,013/gün, tipik ~$0,10-0,15/AY/aktif ücretsiz kullanıcı. 1.000
aktif ücretsiz kullanıcı ≈ $100-150/ay — dönüşüm %3+ olduğu sürece
kendini fazlasıyla öder; değilse FREE_CHAT_PER_DAY tek ayar noktasıdır.

## 5. Fiyat konumlandırması (TR pazarı)

Pazar: AI destekli benzer uygulamalar ~₺600/ay'dan satılıyor. Rytho
₺179,99'da **bilinçli penetrasyon** konumunda — pazar liderinin ~%30'u.
KARAR (kullanıcı, 2026-08-12): fiyatlar ŞİMDİLİK korunur.

Fiyat merdiveni (ileri adımlar, şimdi uygulanmaz):
1. **0-1.000 abone**: ₺179,99 koru — büyüme ve yorum/puan birikimi.
2. **1.000+ abone**: yeni abonelere ₺229-249 (Play'de mevcut abonelerin
   fiyatı korunabilir); marj zaten yüksek, artış aciliyet değil güç işi.
3. **Yıllık plan**: ₺1.499-1.699 (aylığın ~8 katı) — nakit akışı +
   kayıp (churn) azaltma. RevenueCat offering'e paket eklemek yeterli.
4. Jeton fiyatları enflasyonla birlikte yılda bir gözden geçirilir.

## 6. "Sürpriz yok" garantileri (bu turda kapatılanlar)

| Risk | Durum |
|---|---|
| "Sınırsız sohbet" vaadi vs jetonlu sohbet | ✅ K3: paywall metni "Ayda 300 jeton" oldu — vaat edilen = verilen |
| İlk alımda bakiye 0 görünmesi | ✅ K2: mobil cüzdan tazeleme + sunucu 35 günlük hak yedeği |
| Jeton düşmeden hizmet (gelir kaçağı) / tavansız maliyet | ✅ K5: RYTHO_TOKENS_ENFORCE=1 kalıcı |
| Sohbet girdisinin sınırsız büyümesi | ✅ K4: prompt geçmişi 12 mesaj × 1.200 kr tavanı |
| Önbellek kaçağı çifte harcama | ✅ (mevcut) harcama yalnız cache-miss'te; üretim hatasında iade |
| Fiyat KDV sürprizi | ✅ (B3) alıcı KDV dahil fiyatı görür; tablolar buna göre |

## 7. İzlenecek metrikler (canlıda)

- aiCache isabet oranı (maliyet öngörüsünün temeli — production-checklist
  notu) ve `TOKENS kuru-çalışma` logunun SIFIRLANDIĞI (enforce kanıtı).
- Abone başına aylık jeton tüketimi dağılımı (adminStats'a eklenebilir).
- Ücretsiz→abone dönüşüm oranı (%3 eşiği ücretsiz katman maliyetinin
  dengesi).
- Kur 45+₺/$ kalıcılaşırsa: fiyat merdiveni adım 2 öne çekilir.
