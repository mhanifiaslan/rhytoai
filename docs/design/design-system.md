# RythoAI Tasarım Sistemi — "Gök Atlası" (Celestial Atlas)

Amaç: "Yapay zeka üretti" izlenimi veren klişe estetiği (mor degrade, neon,
emoji yağmuru, cam efektli kartlar) tamamen reddedip; **eski gökyüzü atlasları,
usturlap gravürleri ve bilimsel enstrüman** estetiğinde, editoryal ve zamansız
bir arayüz kurmak. Uygulama bir "fal uygulaması" gibi değil, **18. yüzyıl
rasathanesinden çıkmış canlı bir enstrüman** gibi hissettirmeli.

## 1. Renk Paleti

Koyu zemin, mürekkep ve altın varak. Degrade YOK; düz, mat yüzeyler ve ince
çizgi işi dokular VAR.

| Token | Hex | Kullanım |
|---|---|---|
| `ink` | `#0B1026` | Ana zemin (gece mürekkebi — siyah değil, çok koyu lacivert) |
| `inkLight` | `#141B33` | Kart/yüzey zemini |
| `inkLighter` | `#1E2742` | Yükseltilmiş yüzey, girdi alanları |
| `parchment` | `#EDE4CF` | Ana metin (fildişi/parşömen — saf beyaz değil) |
| `parchmentDim` | `#B7AE99` | İkincil metin |
| `gold` | `#C9A227` | Vurgu: aktif ikonlar, önemli değerler, çizgi işi süslemeler |
| `goldBright` | `#E8C55A` | Basılı durum, parlak vurgu |
| `copper` | `#A66A3E` | İkincil vurgu: retro gezegen, uyarılar |
| `celadon` | `#7FA98F` | Olumlu durum (nadir kullanım) |
| `madder` | `#B4524B` | Hata/kritik (kırmızı değil, kök boyası kızılı) |
| `line` | `#2C3552` | Ayraç ve gravür çizgileri |

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
gövde 15/Spectral, veri 13/JetBrains Mono.

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
- **Köşe yarıçapı**: 4px (keskin, enstrüman hissi). Tam yuvarlak yalnızca
  gezegen rozetlerinde.
- **Gölge yok**: derinlik, gölge yerine 1px `line` konturu ve zemin tonu
  farkıyla verilir.

## 4. Bileşen Kuralları

- **Kart ("Levha")**: `inkLight` zemin, 1px `line` kontur, 4px köşe; başlık
  üstte mono küçük etiketle ("LEVHA I — DOĞUM HARİTASI" gibi).
- **Birincil buton**: altın kontur + parşömen metin, dolgu YOK; basılınca
  `goldBright` dolgu + `ink` metin. 48px yükseklik.
- **Alt gezinme**: 5 sekme; ikonlar çizgi işi, aktif sekme altında 16px'lik
  ince altın çizgi. Sekmeler: **Gökyüzü** (ana), **Atlas** (haritalar),
  **Kehanet** (I Ching/BaZi/Yüz), **Meclis** (sosyal+DM), **Sicil** (profil).
- **AI mesaj balonu**: balon değil, sol kenarında altın dikey çizgi olan
  parşömen renkli **marjinal not** bloğu; kullanıcı mesajı sağda mürekkep bloğu.
- **Grafikler**: natal harita SVG'si `dark` temayla backend'den gelir; çevresine
  mono derece cetveli işlenir.

## 5. Hareket

- Süreler 200-300ms, `easeOutCubic`. Sıçrayan/elastik animasyon yok.
- Sayfa geçişi: hafif dikey parallax + solma ("atlas sayfası çevirme").
- Yükleme göstergesi: dönen usturlap kadranı (dairesel tik animasyonu),
  spinner yok.
- İskelet ekran yerine "mürekkep dolumu": metin satırları soldan sağa
  %8 opaklıkta çizgiyle belirir.

## 6. Ses ve Dil (copy)

- Üslup: bilge, ölçülü, edebi; asla çocuksu değil. Emoji kullanılmaz
  (yalnızca astronomik semboller: ☉ ☽ ♄ ✦ ve Ay evresi glifleri).
- "Fal", "şans" yerine: "okuma", "harita", "kehanet", "levha", "sema".
- AI kendini "Rytho" olarak tanıtır; "yapay zeka" ifadesi arayüzde geçmez.

## 7. Erişilebilirlik

- Metin kontrastı: parchment/ink = 13.4:1 (AAA). parchmentDim minimum 16px.
- Dokunma hedefleri ≥ 44px; mono veriler için `FontFeature.tabularFigures()`.
