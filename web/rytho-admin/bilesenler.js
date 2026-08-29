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
    // sec.sayac: ham sayı verilirse değer 0'dan hedefe sayarak belirir
    // (canlandir ile; reduced-motion'da animasyonsuz son değer).
    var sayacAttr = (typeof sec.sayac === 'number' && isFinite(sec.sayac))
      ? ' data-hedef="' + sec.sayac + '"' : '';
    return '<div class="kpi-kart"><div class="kpi-deger' +
      (sec.altin ? ' altin' : '') + '"' + sayacAttr + '>' + e(deger) +
      '</div>' +
      '<div class="kpi-ad">' + e(ad) + '</div>' +
      (sec.alt ? '<div class="kpi-alt">' + e(sec.alt) + '</div>' : '') +
      '</div>';
  }

  /* Tam sayı KPI'ları 0'dan hedefe sayar (~600ms, easeOut). */
  function canlandir(kok) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    kok.querySelectorAll('[data-hedef]').forEach(function (el) {
      var hedef = Number(el.getAttribute('data-hedef'));
      if (!isFinite(hedef) || hedef <= 0) return;
      var basla = null;
      function adim(t) {
        if (basla === null) basla = t;
        var f = Math.min((t - basla) / 600, 1);
        f = 1 - Math.pow(1 - f, 3);
        el.textContent = Math.round(hedef * f).toLocaleString('tr-TR');
        if (f < 1) requestAnimationFrame(adim);
      }
      requestAnimationFrame(adim);
    });
  }

  /* İşletme marjı panosu (AP2): gelir − mağaza − AI = tahmini katkı marjı.
     Her kalem "tahmini" dilinde — gerçek hakediş mağaza raporunda. */
  function marjPanosu(t, donemEtiketi) {
    var marj = t.marginUsd || 0;
    return '<div class="marj-panosu">' +
      '<div class="marj-etiket">' + e(donemEtiketi) +
      ' — tahmini katkı marjı</div>' +
      '<div class="marj-deger' + (marj < 0 ? ' eksi' : '') + '">' +
      para(marj) + '</div>' +
      '<div class="marj-formul">' +
      '<div class="kalem"><b>' + para(t.revenueUsd) +
      '</b><span>Brüt gelir</span></div>' +
      '<div class="kalem"><b>−' + para(t.storeCutUsd) +
      '</b><span>Mağaza kesintisi (~%' +
      Math.round((t.storeCutRate || 0.15) * 100) + ')</span></div>' +
      '<div class="kalem"><b>−' + para(t.aiCostUsd) +
      '</b><span>Tahmini AI maliyeti</span></div>' +
      '</div>' +
      '<div class="marj-not">Sabit giderler (Cloud Run + Firestore, ' +
      '~$32-35/ay — maliyet-calismasi §4) hariçtir; AI maliyeti ölçülen ' +
      'token × birim fiyattır.</div></div>';
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
    return '<div class="modul"><div class="modul-baslik"><h2>' +
      e(baslik) + '</h2></div>' +
      '<div class="grafik-kap"><canvas id="' + e(kimlik) +
      '" class="grafik' + (kisa ? ' grafik-kisa' : '') +
      '" role="img" aria-label="' + e(baslik) + '"></canvas></div></div>';
  }

  /* ---- Modül dili (AP3) ---- */

  function modul(baslik, icHtml, kontrolHtml) {
    return '<div class="modul"><div class="modul-baslik"><h2>' +
      e(baslik) + '</h2>' +
      (kontrolHtml ? '<div class="modul-kontrol">' + kontrolHtml + '</div>'
                   : '') +
      '</div>' + icHtml + '</div>';
  }

  function etiket(metin) {
    return '<span class="modul-etiket">' + e(metin) + '</span>';
  }

  /* İkonlu liste satırı. sec: {ikon, ikonSinif, avatar, baslik, alt,
     sagUst, sagUstSinif ('arti'|'eksi'), sagAlt, veri: {ad:deger}} */
  function satir(sec) {
    var ikonHucre;
    if (sec.avatar) {
      ikonHucre = '<div class="satir-ikon avatar-hucre">' +
        e(String(sec.avatar).trim().charAt(0).toUpperCase() || '?') +
        '</div>';
    } else {
      ikonHucre = '<div class="satir-ikon' +
        (sec.ikonSinif ? ' ' + sec.ikonSinif : '') + '">' +
        (RY.ikon ? RY.ikon(sec.ikon || 'kivilcim') : '') + '</div>';
    }
    var veriAttr = '';
    Object.keys(sec.veri || {}).forEach(function (ad) {
      veriAttr += ' data-' + ad + '="' + e(sec.veri[ad]) + '"';
    });
    return '<div class="satir' + (sec.veri ? ' tikla' : '') + '"' +
      veriAttr + '>' + ikonHucre +
      '<div class="satir-govde"><b>' + e(sec.baslik) + '</b>' +
      (sec.alt ? '<span>' + e(sec.alt) + '</span>' : '') + '</div>' +
      ((sec.sagUst != null || sec.sagAlt != null)
        ? '<div class="satir-sag">' +
          (sec.sagUst != null
            ? '<b class="' + (sec.sagUstSinif || '') + '">' + e(sec.sagUst) +
              '</b>' : '') +
          (sec.sagAlt != null ? '<span>' + e(sec.sagAlt) + '</span>' : '') +
          '</div>'
        : '') +
      '</div>';
  }

  function delta(fark, birim) {
    if (fark == null || !isFinite(fark)) return '';
    var yon = fark > 0 ? 'yukari' : (fark < 0 ? 'asagi' : 'duz');
    var ok = fark > 0 ? '▲' : (fark < 0 ? '▼' : '◆');
    var deger = Math.abs(fark);
    var metin = birim === '$'
      ? para(deger)
      : deger.toLocaleString('tr-TR');
    return '<span class="delta ' + yon + '">' + ok + ' ' + metin + '</span>';
  }

  RY.b = {
    e: e, sayi: sayi, para: para, tarih: tarih,
    kpi: kpi, rozet: rozet, abonelikRozeti: abonelikRozeti,
    tablo: tablo, iskelet: iskelet, bosDurum: bosDurum,
    hataDurum: hataDurum, girdi: girdi, grafikPanel: grafikPanel,
    canlandir: canlandir, marjPanosu: marjPanosu,
    modul: modul, etiket: etiket, satir: satir, delta: delta
  };
})();
