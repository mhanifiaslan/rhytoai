/* El yazması canvas grafikleri v2 (AP-turu). Dış kütüphane yok.

   v1'den farklar: renkler CSS token'larından okunur (hardcode hex öldü),
   çizgi grafiğe eksen/ızgara/imleç ipucu geldi, boş veri dürüst "Veri yok"
   yazar, pencere boyutu değişince tek ResizeObserver yeniden çizer. */
(function () {
  'use strict';

  var RY = window.RY;

  var _renkler = {};
  function renk(ad) {
    if (!_renkler[ad]) {
      _renkler[ad] = getComputedStyle(document.documentElement)
        .getPropertyValue('--' + ad).trim() || '#888';
    }
    return _renkler[ad];
  }

  function hazirla(canvas) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var g = canvas.clientWidth, y = canvas.clientHeight;
    canvas.width = g * dpr;
    canvas.height = y * dpr;
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx: ctx, g: g, y: y };
  }

  function veriYok(canvas) {
    var k = hazirla(canvas);
    k.ctx.fillStyle = renk('parchment-dim');
    k.ctx.font = '12px Manrope, sans-serif';
    k.ctx.textAlign = 'center';
    k.ctx.fillText('Veri yok', k.g / 2, k.y / 2 + 4);
  }

  /* Tek gözlemci: canvas.__ryCiz kapanışını saklar, boyut değişince çağırır. */
  var gozlemci = null;
  function izle(canvas, ciz) {
    canvas.__ryCiz = ciz;
    if (!('ResizeObserver' in window)) return;
    if (!gozlemci) {
      gozlemci = new ResizeObserver(function (girisler) {
        girisler.forEach(function (gi) {
          if (gi.target.__ryCiz) gi.target.__ryCiz();
        });
      });
    }
    gozlemci.observe(canvas);
  }

  function ipucuAl(canvas) {
    var kap = canvas.parentElement;
    var ip = kap.querySelector('.grafik-ipucu');
    if (!ip) {
      ip = document.createElement('div');
      ip.className = 'grafik-ipucu';
      kap.appendChild(ip);
    }
    return ip;
  }

  /* ---- Çizgi grafik: {degerler:[..], etiketler:[..]?, birim:'$'?} ---- */
  function cizgi(canvas, sec) {
    if (!canvas) return;
    var degerler = (sec && sec.degerler) || [];
    var etiketler = (sec && sec.etiketler) || [];
    var birim = (sec && sec.birim) || '';
    if (!degerler.length) { veriYok(canvas); return; }

    var SOL = 40, ALT = 16, UST = 6;

    function ciz(oran) {
      // oran < 1: giriş animasyonu — seri soldan sağa "çizilir".
      oran = oran == null ? 1 : oran;
      var k = hazirla(canvas), ctx = k.ctx;
      if (oran < 1) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(0, 0, SOL + (k.g - SOL - 6) * oran + 6, k.y);
        ctx.clip();
      }
      // Tavan gerçek maksimumdur; 1'e kelepçelemek küçük dolar serilerini
      // düz çizgiye eziyordu. Sıfır seri için 1 yalnız bölme koruması.
      var maks = Math.max.apply(null, degerler);
      if (!(maks > 0)) maks = 1;
      var w = k.g - SOL - 6, h = k.y - ALT - UST;

      function x(i) {
        return SOL + (degerler.length === 1
          ? w / 2 : (i / (degerler.length - 1)) * w);
      }
      function y(v) { return UST + h - (v / maks) * h; }

      // Izgara + y etiketleri (0 / orta / maks)
      ctx.strokeStyle = renk('line');
      ctx.globalAlpha = 0.5;
      ctx.lineWidth = 1;
      ctx.fillStyle = renk('parchment-dim');
      ctx.font = '9.5px "JetBrains Mono", monospace';
      ctx.textAlign = 'right';
      [0, maks / 2, maks].forEach(function (v) {
        var yy = y(v);
        ctx.beginPath();
        ctx.moveTo(SOL, yy);
        ctx.lineTo(k.g - 6, yy);
        ctx.stroke();
        var etiket = v >= 1000 ? (v / 1000).toFixed(1) + 'k'
          : (v % 1 === 0 ? String(v) : v.toFixed(v < 10 ? 2 : 1));
        ctx.fillText(birim + etiket, SOL - 5, yy + 3);
      });
      ctx.globalAlpha = 1;

      // x etiketleri: ilk ve son
      if (etiketler.length) {
        ctx.textAlign = 'left';
        ctx.fillText(String(etiketler[0]).slice(5), SOL, k.y - 3);
        ctx.textAlign = 'right';
        ctx.fillText(String(etiketler[etiketler.length - 1]).slice(5),
          k.g - 6, k.y - 3);
      }

      // Dolgu
      var dolgu = ctx.createLinearGradient(0, UST, 0, UST + h);
      dolgu.addColorStop(0, renk('violet') + '59');
      dolgu.addColorStop(1, renk('violet') + '00');
      ctx.beginPath();
      degerler.forEach(function (v, i) {
        i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v));
      });
      ctx.lineTo(x(degerler.length - 1), UST + h);
      ctx.lineTo(x(0), UST + h);
      ctx.closePath();
      ctx.fillStyle = dolgu;
      ctx.fill();

      // Çizgi
      ctx.beginPath();
      degerler.forEach(function (v, i) {
        i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v));
      });
      ctx.strokeStyle = renk('magenta');
      ctx.lineWidth = (sec && sec.kalin) ? 3 : 2;
      ctx.lineJoin = 'round';
      ctx.stroke();

      canvas.__ryX = x;
      canvas.__ryY = y;
      if (oran < 1) ctx.restore();
    }

    // Giriş: 450ms çizim süpürmesi; reduced-motion'da doğrudan tam kare.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      ciz();
    } else {
      var basla = null;
      (function adim(t) {
        if (basla === null) { basla = t || performance.now(); }
        var f = Math.min(((t || performance.now()) - basla) / 450, 1);
        ciz(1 - Math.pow(1 - f, 3));
        if (f < 1) requestAnimationFrame(adim);
      })(performance.now());
    }
    izle(canvas, function () { ciz(); });

    // İmleç ipucu: en yakın nokta
    var ip = ipucuAl(canvas);
    canvas.onmousemove = function (ev) {
      var kutu = canvas.getBoundingClientRect();
      var mx = ev.clientX - kutu.left;
      var enYakin = 0, enKucuk = 1e9;
      for (var i = 0; i < degerler.length; i++) {
        var f = Math.abs(canvas.__ryX(i) - mx);
        if (f < enKucuk) { enKucuk = f; enYakin = i; }
      }
      var v = degerler[enYakin];
      ip.textContent = (etiketler[enYakin] != null
        ? etiketler[enYakin] + ' · ' : '') + birim +
        (typeof v === 'number' ? v.toLocaleString('tr-TR') : v);
      ip.style.display = 'block';
      ip.style.left = canvas.__ryX(enYakin) + 'px';
      ip.style.top = canvas.__ryY(v) + 'px';
    };
    canvas.onmouseleave = function () { ip.style.display = 'none'; };
  }

  /* ---- Yatay çubuklar: {etiket: sayı} ---- */
  function cubuk(canvas, sozluk, sec) {
    if (!canvas) return;
    sec = sec || {};
    var girisler = Object.keys(sozluk || {}).map(function (a) {
      return [a, Number(sozluk[a]) || 0];
    }).sort(function (a, b) { return b[1] - a[1]; })
      .slice(0, sec.enCok || 8);
    if (!girisler.length) { veriYok(canvas); return; }

    var SATIR = 26;
    canvas.style.height = (girisler.length * SATIR + 6) + 'px';

    function ciz() {
      var k = hazirla(canvas), ctx = k.ctx;
      var maks = Math.max.apply(null, girisler.map(function (g) {
        return Math.abs(g[1]);
      }).concat([1]));
      var SOL = 118, SAG = 52;

      girisler.forEach(function (g, i) {
        var yy = i * SATIR + 5;
        var gen = Math.max((Math.abs(g[1]) / maks) * (k.g - SOL - SAG), 2);

        ctx.fillStyle = renk('parchment-dim');
        ctx.font = '11px Manrope, sans-serif';
        ctx.textAlign = 'left';
        var ad = g[0].length > 15 ? g[0].slice(0, 14) + '…' : g[0];
        ctx.fillText(ad, 0, yy + 11);

        ctx.fillStyle = g[1] < 0 ? renk('madder') : renk('violet');
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(SOL, yy, gen, 14, 7);
        else ctx.rect(SOL, yy, gen, 14);
        ctx.fill();

        ctx.fillStyle = renk('parchment');
        ctx.font = '11px "JetBrains Mono", monospace';
        ctx.textAlign = 'left';
        ctx.fillText((sec.birim || '') + g[1].toLocaleString('tr-TR'),
          SOL + gen + 7, yy + 11);
      });
    }

    ciz();
    izle(canvas, ciz);
  }

  RY.grafik = { renk: renk, cizgi: cizgi, cubuk: cubuk };
})();
