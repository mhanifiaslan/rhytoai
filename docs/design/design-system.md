# RythoAI Tasarım Sistemi v2 — "Camdan Rasathane"

v1'in "Gök Atlası" kimliği (mürekkep + altın + editoryal tipografi) korunur;
üzerine **cam katmanları, derinlik ve hareket** eklenir. Uygulama artık düz
bir gravür levhası değil, **yıldız alanının önünde asılı duran camdan bir
rasathane** gibi hissettirmeli. "Yapay zeka üretti" izlenimi veren klişe
estetik (mor degrade, neon, emoji yağmuru) hâlâ reddedilir.

## 0. v2'nin üç katmanı

1. **Zemin**: `StarfieldBackground` — uzay degradesi + üç derinlik katmanında
   süzülen, göz kırpan yıldızlar. Her ekran `CosmicScaffold` ile bu zeminin
   üstünde saydam durur.
2. **Cam**: `GlassPanel` — `BackdropFilter` blur (σ≈14), yarı saydam mürekkep
   dolgu, 1px ışıklı üst kenar (`glassEdge`) ve yumuşak kontur (`glassStroke`).
   Plaque artık bu panele delege eder.
3. **Işık**: aktif öğelerde `goldGlow` (yumuşak altın hale) — dock'ta,
   spinner'da, gezegen gliflerinde "nefes alan" animasyonla.

## 1. Renk Paleti

Koyu zemin, mürekkep ve altın varak. Yüzeyler artık yarı saydam camdır;
degrade yalnızca zeminin radyal uzay geçişinde ve cam dolgusunda kullanılır.

| Token | Hex | Kullanım |
|---|---|---|
| `ink` | `#0B1026` | Zemin degradenin merkezi (gece mürekkebi) |
| `inkDeep` | `#070B1C` | Zemin degradenin dış ucu (uzay derinliği) |
| `inkLight` | `#141B33` | Opak yüzeyler (bottom sheet vb.) |
| `inkLighter` | `#1E2742` | Yükseltilmiş yüzey, girdi alanları |
| `parchment` | `#F0E8D6` | Ana metin |
| `parchmentDim` | `#C9C0AB` | İkincil metin (v2'de kontrast yükseltildi) |
| `gold` | `#C9A227` | Vurgu |
| `goldBright` | `#E8C55A` | Basılı/aktif durum |
| `copper` | `#B87848` | Retro gezegen, uyarılar |
| `celadon` | `#7FA98F` | Olumlu durum |
| `madder` | `#C4625B` | Hata |
| `line` | `#323C5E` | Çizgiler |
| `glassFill` | `#141B33 @55%` | Cam panel dolgusu |
| `glassEdge` | `#E8C55A @20%` | Cam üst kenar ışığı |
| `glassStroke` | `#4A5580 @30%` | Cam kontur |
| `goldGlow` | `#C9A227 @33%` | Altın hale/glow |

Kural: Bir ekranda altın vurgusu toplam alanın %10'unu geçmez. Renk cömertliği
değil, mürekkep disiplini.

## 2. Tipografi

Editoryal ikili sistem — serif başlık + mono veri. (Google Fonts, ücretsiz)

| Rol | Font | Not |
|---|---|---|
| Display / başlık | **Cormorant Garamond** (600) | Eski kitap kapağı havası; büyük puntoda harf aralığı +0.5 |
| Gövde metni | **Cormorant Garamond** (400) yerine gövdede **Spectral** (400) | Uzun okumada Spectral daha rahat |
| Veri / koordinat / derece | **JetBrains Mono** (400) | "17°42′ Akrep" gibi tüm sayısal astronomik veriler daima mono |
| Buton / etiket | Spectral (500), harf aralığı +1.2, BÜYÜK HARF | Enstrüman kadranı etiketi hissi |

Örnek hiyerarşi: ekran başlığı 32/Cormorant, bölüm başlığı 20/Cormorant,
gövde 16/Spectral (v2'de +1pt, satır aralığı 1.6), veri 13/JetBrains Mono.

## 3. Görsel Dil

- **Çizgi işi (line-art) her yerde**: dolgulu ikonlar yerine 1px altın/mürekkep
  konturlu gravür ikonlar. Gezegen sembolleri (☉ ☽ ☿ ♀ ♂ ♃ ♄) tipografik olarak
  kullanılır — resimli maskot yok.
- **Canlı gökyüzü zemini**: ana ekran arka planında, backend'in `/sky/now`
  verisinden çizilen **gerçek zamanlı gezegen konumlu** minimal bir zodyak
  çemberi (CustomPainter). Dekor değil, veri.
- **Kadran ve cetvel motifleri**: ilerleme göstergeleri bar değil, usturlap
  kadranı (dairesel tik işaretleri); ayraçlar ince çizgi + merkezde küçük ✦.
- **Doku**: %2-3 opaklıkta yıldız noktası dokusu; gürültü/grain yok.
- **Köşe yarıçapı**: v2'de 14-18px (cam panel), 26px (dock). Keskin 4px köşe
  yalnızca mono veri çiplerinde kalır.
- **Derinlik**: 1px kontur + blur + `goldGlow` halesiyle verilir; sert gölge yok.

## 4. Bileşen Kuralları

- **Cam panel (`GlassPanel`)**: blur'lu yarı saydam yüzey, ışıklı üst kenar,
  mono etiket başlık ("LEVHA I — DOĞUM HARİTASI" gibi). `Plaque` buna delege eder.
- **Birincil buton (`GoldButton`)**: altın kontur + cam dolgu, 14px köşe,
  aktifken yumuşak altın glow. 50px yükseklik.
- **Alt gezinme (`CosmicDock`)**: yüzen cam dock; aktif sekme yay animasyonlu
  büyür ve altın glow alır. Sekmeler: **Gökyüzü**, **Atlas**, **Kehanet**,
  **Meclis**, **Sicil**.
- **AI mesaj balonu**: cam panelde daktilo-akış (`TypewriterText`) ile belirir;
  kullanıcı mesajı sağda mürekkep bloğu.
- **Natal çark (`NatalWheel`)**: yerli CustomPainter — burç dilimleri, ev
  çizgileri, gezegen glifleri, merkezde açı ağı; sweep animasyonuyla kurulur,
  gezegene dokununca cam bilgi çipi açılır. Backend SVG'si kullanılmaz.
- **Segment seçici (`GlassSegments`)**: Takip/Keşfet gibi ikili akış seçimleri.

## 5. Hareket

- Süreler 250-350ms, `easeOutCubic`; dock'ta `easeOutBack` yay hissi.
- Sekme geçişi: çapraz solma + 12px dikey kayma (paylaşılan eksen).
- Kart girişleri: 45ms aralıklı stagger (`flutter_animate`).
- Basmalarda scale + haptic (`HapticFeedback.selectionClick`).
- Yükleme: glow'lu usturlap kadranı; AI metinleri daktilo-akışla belirir.
- Tören animasyonları: I Ching'de üç paranın 3D dönüşü, yüz analizinde altın
  tarama çizgisi, natal çarkın çizilerek kurulması, beğenide ✦ patlaması.

## 6. Ses ve Dil (copy)

- Üslup: bilge, ölçülü, edebi; asla çocuksu değil. Emoji kullanılmaz
  (yalnızca astronomik semboller: ☉ ☽ ♄ ✦ ve Ay evresi glifleri).
- "Fal", "şans" yerine: "okuma", "harita", "kehanet", "levha", "sema".
- AI kendini "Rytho" olarak tanıtır; "yapay zeka" ifadesi arayüzde geçmez.

## 7. Erişilebilirlik

- Metin kontrastı: parchment/ink = 13.4:1 (AAA). parchmentDim minimum 16px.
- Dokunma hedefleri ≥ 44px; mono veriler için `FontFeature.tabularFigures()`.
