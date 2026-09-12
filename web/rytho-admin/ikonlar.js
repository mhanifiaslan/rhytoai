/* El çizimi ikon seti v3 (AD-turu) — bağımlılıksız inline SVG.
   Hepsi 24x24, stroke: currentColor; renk CSS'ten gelir.
   RY.ikon(ad, boyut) → '<svg …aria-hidden>' dizesi (innerHTML'e gömülür). */
(function () {
  'use strict';

  var RY = window.RY = window.RY || {};

  var CIZIMLER = {
    /* Rotalar */
    panel: '<rect x="3" y="3" width="8" height="8" rx="2"/>' +
      '<rect x="13" y="3" width="8" height="5" rx="2"/>' +
      '<rect x="13" y="11" width="8" height="10" rx="2"/>' +
      '<rect x="3" y="14" width="8" height="7" rx="2"/>',
    kullanicilar: '<circle cx="9" cy="8.5" r="3.5"/>' +
      '<path d="M3.5 19.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/>' +
      '<path d="M15.5 5.6a3.5 3.5 0 0 1 0 5.8M17.5 14.9c1.8.8 3 2.4 3 4.6"/>',
    kullanici: '<circle cx="12" cy="8" r="4"/>' +
      '<path d="M4 20c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    gelir: '<path d="M4 18l5-6 4 3 7-8"/><path d="M15 7h5v5"/>',
    ekonomi: '<circle cx="12" cy="12" r="8.5"/>' +
      '<path d="M12 7.5v9M14.8 9.2c-.6-1-1.6-1.4-2.8-1.4-1.5 0-2.6.8-2.6 ' +
      '2.1 0 2.9 5.6 1.5 5.6 4.3 0 1.3-1.2 2.2-2.9 2.2-1.4 0-2.5-.6-3-1.6"/>',
    ai: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>' +
      '<path d="M18.5 16.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
    kullanim: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>' +
      '<path d="M18.5 16.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
    bildirim: '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/>' +
      '<path d="M10 20a2 2 0 0 0 4 0"/>',
    zil: '<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/>' +
      '<path d="M10 20a2 2 0 0 0 4 0"/>',
    ortaklar: '<circle cx="8" cy="9" r="3"/><circle cx="16" cy="9" r="3"/>' +
      '<path d="M2 20c1-3.5 3.5-5 6-5s5 1.5 6 5M12 20c1-3.5 3.5-5 6-5"/>',
    sistem: '<circle cx="12" cy="12" r="3"/>' +
      '<path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 ' +
      '2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',

    /* Eylemler */
    arama: '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
    cikis: '<path d="M14.5 8V5.5a1.5 1.5 0 0 0-1.5-1.5H6.5A1.5 1.5 0 0 0 5 ' +
      '5.5v13A1.5 1.5 0 0 0 6.5 20H13a1.5 1.5 0 0 0 1.5-1.5V16"/>' +
      '<path d="M9.5 12h11M17.5 9l3 3-3 3"/>',
    kayit: '<circle cx="12" cy="9" r="4"/>' +
      '<path d="M5.5 20c.8-3.2 3.4-5 6.5-5s5.7 1.8 6.5 5"/>' +
      '<path d="M19.5 4.5v4M21.5 6.5h-4"/>',
    jeton: '<circle cx="12" cy="12" r="8"/>' +
      '<path d="M12 8v8M9.5 10.5h3.5a1.5 1.5 0 0 1 0 3H9.5"/>',
    kredi: '<rect x="3.5" y="6.5" width="17" height="12" rx="2.5"/>' +
      '<path d="M3.5 10.5h17M7 15h4"/>',
    kivilcim: '<path d="M13 3.5L5.5 13.5H11l-1 7 8-10.5h-5.5z"/>',
    iade: '<path d="M9 7.5H5.5V4"/><path d="M5.5 7.4A8.5 8.5 0 1 1 4 13.5"/>',
    denetim: '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.5l2.3 2.3 4.7-5"/>',
    cihaz: '<rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/>',
    anahtar: '<circle cx="8" cy="14" r="4"/><path d="M11 11l9-9M16 6l2 2M13 9l2 2"/>',
    kilit: '<rect x="5" y="11" width="14" height="10" rx="2"/>' +
      '<path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    'kilit-acik': '<rect x="5" y="11" width="14" height="10" rx="2"/>' +
      '<path d="M8 11V8a4 4 0 0 1 7.5-2"/>',
    cop: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    ok: '<path d="M9 6l6 6-6 6"/>',
    'ok-sol': '<path d="M15 6l-6 6 6 6"/>',
    'ok-yukari': '<path d="M6 15l6-6 6 6"/>',
    'ok-asagi': '<path d="M6 9l6 6 6-6"/>',
    daralt: '<path d="M15 6l-6 6 6 6"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    uyari: '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17h.01"/>',
    bilgi: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8h.01"/>',
    basari: '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.5l2.3 2.3 4.7-5"/>',
    hata: '<circle cx="12" cy="12" r="8.5"/><path d="M9 9l6 6M15 9l-6 6"/>',
    kapat: '<path d="M6 6l12 12M18 6L6 18"/>',
    'disa-aktar': '<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5"/>' +
      '<path d="M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2"/>',
    indir: '<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5"/>' +
      '<path d="M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2"/>',
    yenile: '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>',
    prova: '<circle cx="12" cy="12" r="8.5"/><path d="M10 8.5l5 3.5-5 3.5z"/>',
    gonder: '<path d="M4 12l16-8-5 16-3-6z"/><path d="M12 14l8-10"/>',
    sekmeler: '<rect x="3" y="5" width="18" height="14" rx="2"/>' +
      '<path d="M3 10h18M9 5v5"/>',
    sirala: '<path d="M8 4v16M8 20l-3-3M8 20l3-3"/><path d="M16 20V4M16 4l-3 3M16 4l3 3"/>',
    filtre: '<path d="M4 5h16l-6 7v6l-4 2v-8z"/>',
    kopyala: '<rect x="9" y="9" width="11" height="11" rx="2"/>' +
      '<path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
    arti: '<path d="M12 5v14M5 12h14"/>',
    eksi: '<path d="M5 12h14"/>',
    goz: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/>' +
      '<circle cx="12" cy="12" r="3"/>',
    klavye: '<rect x="3" y="6" width="18" height="12" rx="2"/>' +
      '<path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/>',
    takvim: '<rect x="3.5" y="5" width="17" height="15" rx="2"/>' +
      '<path d="M3.5 10h17M8 3v4M16 3v4"/>',
    zaman: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    'dis-baglanti': '<path d="M14 4h6v6M20 4l-9 9"/>' +
      '<path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/>',
    ayar: '<circle cx="12" cy="12" r="3"/>' +
      '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 ' +
      '1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-' +
      '1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 ' +
      '1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-' +
      '.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 ' +
      '1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 ' +
      '2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 ' +
      '1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    eposta: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    dil: '<circle cx="12" cy="12" r="8.5"/>' +
      '<path d="M3.5 12h17M12 3.5c2.5 2.5 3.5 5.5 3.5 8.5s-1 6-3.5 8.5c-2.5-2.5-3.5-5.5-3.5-8.5s1-6 3.5-8.5z"/>',
    yildiz: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    grafik: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    tablo: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16"/>',
    kalem: '<path d="M4 20l4-1 10-10-3-3L5 16z"/><path d="M13 7l3 3"/>',
    ev: '<path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1z"/>',
    duyuru: '<path d="M4 10v4h3l7 4V6l-7 4z"/><path d="M17 9a4 4 0 0 1 0 6"/>',
    cuzdan: '<rect x="3" y="6" width="18" height="13" rx="2"/>' +
      '<path d="M3 10h18M16 14h2"/>'
  };

  RY.ikon = function (ad, boyut) {
    var cizim = CIZIMLER[ad] || CIZIMLER.kivilcim;
    var b = boyut || 18;
    return '<svg viewBox="0 0 24 24" width="' + b + '" height="' + b +
      '" fill="none" stroke="currentColor" stroke-width="1.8" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ' +
      'focusable="false">' + cizim + '</svg>';
  };
  RY.ikonVar = function (ad) { return !!CIZIMLER[ad]; };
})();
