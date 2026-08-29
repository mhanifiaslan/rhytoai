/* Paylaşılan arayüz üreticileri (AP-turu): görünümler HTML dizesi kurar,
   buradaki yardımcılar kaçış + biçim + tekrarlanan parçaları tekilleştirir.
   Tüm çıktılar admin.css sınıflarına dayanır — inline stil YOK. */
(function () {
  'use strict';

  var RY = window.RY;

  function e(metin) {
    return String(metin == null ? '-' : metin)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function sayi(v) {
    if (v == null || v === -1) return '—';
    return typeof v === 'number' ? v.toLocaleString('tr-TR') : String(v);
  }

  function para(v, birim) {
    if (v == null || v === -1) return '—';
    var n = Number(v);
    if (isNaN(n)) return '—';
    return (birim || '$') + n.toLocaleString('tr-TR', {
      minimumFractionDigits: n !== 0 && Math.abs(n) < 1 ? 4 : 2,
      maximumFractionDigits: Math.abs(n) < 1 ? 4 : 2
    });
  }

  /* Firestore zaman değeri ISO dizge ya da {_seconds} gelebilir. */
  function tarih(v, saatli) {
    if (!v) return '—';
    var d;
    if (typeof v === 'string') d = new Date(v);
    else if (v.seconds != null) d = new Date(v.seconds * 1000);
    else if (v._seconds != null) d = new Date(v._seconds * 1000);
    else d = new Date(v);
    if (isNaN(d.getTime())) return String(v);
    var gun = d.toLocaleDateString('tr-TR',
      { day: 'numeric', month: 'short', year: 'numeric' });
    if (!saatli) return gun;
    return gun + ' ' + d.toLocaleTimeString('tr-TR',
      { hour: '2-digit', minute: '2-digit' });
  }

  function kpi(deger, ad, sec) {
    sec = sec || {};
    return '<div class="kpi-kart"><div class="kpi-deger' +
      (sec.altin ? ' altin' : '') + '">' + e(deger) + '</div>' +
      '<div class="kpi-ad">' + e(ad) + '</div>' +
      (sec.alt ? '<div class="kpi-alt">' + e(sec.alt) + '</div>' : '') +
      '</div>';
  }

  function rozet(metin, tur) {
    return '<span class="rozet rozet-' + (tur || 'notr') + '">' +
      e(metin) + '</span>';
  }

  /* Abonelik durumundan rozet: tek yerde karar, her ekran aynı dili konuşur. */
  function abonelikRozeti(sub, profil) {
    if (sub && sub.active) {
      if (sub.isTrial) return rozet('Mağaza denemesi', 'deneme');
      return rozet('Abone', 'aktif');
    }
    if (sub && sub.productId) return rozet('Süresi dolmuş', 'dolmus');
    return rozet('Ücretsiz', 'notr');
  }

  function tablo(basliklar, satirlarHtml) {
    var th = basliklar.map(function (b) {
      return '<th>' + e(b) + '</th>';
    }).join('');
    return '<div class="tablo-sarici"><table class="tablo">' +
      '<thead><tr>' + th + '</tr></thead>' +
      '<tbody>' + satirlarHtml + '</tbody></table></div>';
  }

  function iskelet() {
    return '<div class="iskelet-kartlar">' +
      '<div class="iskelet iskelet-kart"></div>'.repeat(4) + '</div>' +
      '<div class="iskelet iskelet-blok"></div>';
  }

  function bosDurum(metin, ekHtml) {
    return '<div class="bos-durum"><span class="yildiz">✦</span>' +
      e(metin) + (ekHtml || '') + '</div>';
  }

  function hataDurum(metin) {
    return '<div class="hata-durum">' + e(metin) +
      '<br><button class="buton ikincil" id="tekrar-dene">Tekrar dene</button>' +
      '</div>';
  }

  function girdi(ad, yertutucu, tur, ekSinif) {
    return '<input class="girdi' + (ekSinif ? ' ' + ekSinif : '') +
      '" name="' + e(ad) + '" placeholder="' + e(yertutucu) + '"' +
      (tur ? ' type="' + e(tur) + '"' : '') +
      ' aria-label="' + e(yertutucu) + '">';
  }

  function grafikPanel(kimlik, baslik, kisa) {
    return '<div class="panel"><h2>' + e(baslik) + '</h2>' +
      '<div class="grafik-kap"><canvas id="' + e(kimlik) +
      '" class="grafik' + (kisa ? ' grafik-kisa' : '') +
      '" role="img" aria-label="' + e(baslik) + '"></canvas></div></div>';
  }

  RY.b = {
    e: e, sayi: sayi, para: para, tarih: tarih,
    kpi: kpi, rozet: rozet, abonelikRozeti: abonelikRozeti,
    tablo: tablo, iskelet: iskelet, bosDurum: bosDurum,
    hataDurum: hataDurum, girdi: girdi, grafikPanel: grafikPanel
  };
})();
