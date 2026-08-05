/* El yapımı canvas grafikler (W6) — dış kütüphane yok, marka renkleri
   rytho.css token'larından. */
(function () {
  'use strict';

  function hazirla(tuval) {
    var oran = Math.min(window.devicePixelRatio || 1, 2);
    var w = tuval.clientWidth || 300;
    var h = tuval.clientHeight || 120;
    tuval.width = w * oran;
    tuval.height = h * oran;
    var ctx = tuval.getContext('2d');
    ctx.scale(oran, oran);
    return { ctx: ctx, w: w, h: h };
  }

  /* Çizgi grafik (sparkline): değer dizisi, altın dolgu + magenta çizgi. */
  function sparkline(tuval, degerler) {
    if (!degerler.length) return;
    var c = hazirla(tuval), ctx = c.ctx;
    var maks = Math.max.apply(null, degerler.concat([1]));
    var adim = c.w / Math.max(degerler.length - 1, 1);
    ctx.beginPath();
    degerler.forEach(function (v, i) {
      var x = i * adim;
      var y = c.h - 8 - (v / maks) * (c.h - 24);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#E64ACF';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.lineTo((degerler.length - 1) * adim, c.h);
    ctx.lineTo(0, c.h);
    ctx.closePath();
    var dolgu = ctx.createLinearGradient(0, 0, 0, c.h);
    dolgu.addColorStop(0, 'rgba(123,47,247,0.35)');
    dolgu.addColorStop(1, 'rgba(123,47,247,0)');
    ctx.fillStyle = dolgu;
    ctx.fill();
  }

  /* Yatay çubuklar: {etiket: sayi} sözlüğü, en büyükten küçüğe ilk 8. */
  function cubuklar(tuval, sozluk) {
    var girisler = Object.keys(sozluk).map(function (k) {
      return [k, sozluk[k]];
    }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 8);
    if (!girisler.length) return;
    var satirY = 26;
    tuval.style.height = (girisler.length * satirY + 8) + 'px';
    var c = hazirla(tuval), ctx = c.ctx;
    var maks = Math.max.apply(null, girisler.map(function (g) {
      return Math.abs(g[1]);
    }).concat([1]));
    girisler.forEach(function (g, i) {
      var y = i * satirY + 6;
      var gen = Math.max((Math.abs(g[1]) / maks) * (c.w - 150), 2);
      ctx.fillStyle = g[1] < 0 ? '#FF6B81' : '#7B2FF7';
      ctx.beginPath();
      ctx.roundRect(120, y, gen, 14, 7);
      ctx.fill();
      ctx.fillStyle = '#A99EC2';
      ctx.font = '11px Manrope, sans-serif';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(g[0]).slice(0, 16), 0, y + 7);
      ctx.fillStyle = '#F4EFFA';
      ctx.font = '11px "JetBrains Mono", monospace';
      ctx.fillText(String(g[1]), 126 + gen, y + 7);
    });
  }

  window.RY = window.RY || {};
  window.RY.sparkline = sparkline;
  window.RY.cubuklar = cubuklar;
})();
