/* El çizimi ikon seti (AP3) — bağımlılıksız inline SVG.
   Hepsi 24x24, stroke: currentColor; renk CSS'ten gelir. */
(function () {
  'use strict';

  var RY = window.RY = window.RY || {};

  var CIZIMLER = {
    panel: '<rect x="3.5" y="3.5" width="7" height="7" rx="2"/>' +
      '<rect x="13.5" y="3.5" width="7" height="7" rx="2"/>' +
      '<rect x="3.5" y="13.5" width="7" height="7" rx="2"/>' +
      '<rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
    kullanicilar: '<circle cx="9" cy="8.5" r="3.5"/>' +
      '<path d="M3.5 19.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5"/>' +
      '<path d="M15.5 5.6a3.5 3.5 0 0 1 0 5.8M17.5 14.9c1.8.8 3 2.4 3 4.6"/>',
    ekonomi: '<circle cx="12" cy="12" r="8.5"/>' +
      '<path d="M12 7.5v9M14.8 9.2c-.6-1-1.6-1.4-2.8-1.4-1.5 0-2.6.8-2.6 ' +
      '2.1 0 2.9 5.6 1.5 5.6 4.3 0 1.3-1.2 2.2-2.9 2.2-1.4 0-2.5-.6-3-1.6"/>',
    ai: '<path d="M12 3.5l1.8 4.7 4.7 1.8-4.7 1.8L12 16.5l-1.8-4.7-4.7-1.8 ' +
      '4.7-1.8z"/><path d="M18.5 15.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 ' +
      '2.1-.9z"/>',
    ortaklar: '<path d="M7 12.5l3.2 3.2c.8.8 2 .8 2.8 0l4.5-4.5"/>' +
      '<path d="M3.5 12l4-5.5h9L20.5 12"/>' +
      '<path d="M11.5 8.5l-3 3c.9 1.2 2.6 1.3 3.7.3l1-1"/>',
    sistem: '<path d="M3.5 12h4l2-5 3.5 10 2-5h5.5"/>',
    arama: '<circle cx="10.5" cy="10.5" r="6"/>' +
      '<path d="M15.2 15.2l5 5"/>',
    cikis: '<path d="M14.5 8V5.5a1.5 1.5 0 0 0-1.5-1.5H6.5A1.5 1.5 0 0 0 5 ' +
      '5.5v13A1.5 1.5 0 0 0 6.5 20H13a1.5 1.5 0 0 0 1.5-1.5V16"/>' +
      '<path d="M9.5 12h11M17.5 9l3 3-3 3"/>',
    kayit: '<circle cx="12" cy="9" r="4"/>' +
      '<path d="M5.5 20c.8-3.2 3.4-5 6.5-5s5.7 1.8 6.5 5"/>' +
      '<path d="M18.5 5.5v4M20.5 7.5h-4" transform="translate(1 -1)"/>',
    jeton: '<ellipse cx="12" cy="7" rx="7" ry="3.2"/>' +
      '<path d="M5 7v5c0 1.8 3.1 3.2 7 3.2s7-1.4 7-3.2V7"/>' +
      '<path d="M5 12v5c0 1.8 3.1 3.2 7 3.2s7-1.4 7-3.2v-5"/>',
    gelir: '<path d="M4 19.5h16"/>' +
      '<path d="M5.5 15.5l4-4.5 3 2.5 5.5-6"/>' +
      '<path d="M14.5 7.5H18V11"/>',
    bildirim: '<path d="M12 4.5a5.5 5.5 0 0 0-5.5 5.5c0 4.5-1.5 5.5-2 6.5h15c' +
      '-.5-1-2-2-2-6.5A5.5 5.5 0 0 0 12 4.5z"/>' +
      '<path d="M10 19.5a2 2 0 0 0 4 0"/>',
    kredi: '<rect x="3.5" y="6.5" width="17" height="12" rx="2.5"/>' +
      '<path d="M3.5 10.5h17M7 15h4"/>',
    kivilcim: '<path d="M13 3.5L5.5 13.5H11l-1 7 8-10.5h-5.5z"/>',
    iade: '<path d="M9 7.5H5.5V4"/>' +
      '<path d="M5.5 7.4A8.5 8.5 0 1 1 4 13.5"/>',
    denetim: '<circle cx="12" cy="12" r="8.5"/>' +
      '<path d="M8.5 12.5l2.3 2.3 4.7-5"/>'
  };

  RY.ikon = function (ad, boyut) {
    var cizim = CIZIMLER[ad] || CIZIMLER.kivilcim;
    return '<svg viewBox="0 0 24 24" width="' + (boyut || 18) +
      '" height="' + (boyut || 18) + '" fill="none" ' +
      'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true">' + cizim + '</svg>';
  };
})();
