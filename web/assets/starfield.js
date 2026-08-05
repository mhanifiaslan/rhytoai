/* Yıldız alanı (W1) — mobil StarfieldBackground'ın canvas aynası:
   140 yıldız, 3 derinlik katmanı, sinüs fazıyla göz kırpma + derinliğe
   göre dikey süzülme, 120 saniyelik döngü. prefers-reduced-motion'da
   TEK statik kare çizilir — tasarım sistemi kuralı. */
(function () {
  'use strict';

  var tuval = document.getElementById('yildizlar');
  if (!tuval) return;
  var ctx = tuval.getContext('2d');

  // Deterministik yıldızlar (mobildeki Random(7) ruhu — her yüklemede aynı gök).
  var tohum = 7;
  function rasgele() {
    tohum = (tohum * 16807) % 2147483647;
    return (tohum - 1) / 2147483646;
  }

  var yildizlar = [];
  for (var i = 0; i < 140; i++) {
    var derinlik = i % 3; // 0 uzak, 2 yakın
    yildizlar.push({
      x: rasgele(),
      y: rasgele(),
      boy: 0.5 + derinlik * 0.45 + rasgele() * 0.5,
      faz: rasgele() * Math.PI * 2,
      derinlik: derinlik,
      sicak: rasgele() < 0.22
    });
  }

  function boyutla() {
    var oran = Math.min(window.devicePixelRatio || 1, 2);
    tuval.width = tuval.clientWidth * oran;
    tuval.height = tuval.clientHeight * oran;
  }

  function ciz(t) {
    var w = tuval.width, h = tuval.height;
    ctx.clearRect(0, 0, w, h);
    for (var i = 0; i < yildizlar.length; i++) {
      var y = yildizlar[i];
      var kayma = t * (0.02 + y.derinlik * 0.03);
      var dy = (y.y + kayma) % 1.0;
      var kirpma = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(y.faz + t * Math.PI * 12));
      var alfa = kirpma * (0.10 + y.derinlik * 0.10);
      ctx.fillStyle = y.sicak
        ? 'rgba(183,156,255,' + alfa + ')'   /* lilac */
        : 'rgba(255,255,255,' + alfa + ')';
      ctx.beginPath();
      ctx.arc(y.x * w, dy * h, y.boy * (window.devicePixelRatio || 1), 0, Math.PI * 2);
      ctx.fill();
    }
  }

  boyutla();
  window.addEventListener('resize', function () { boyutla(); ciz(0); });

  var sabit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (sabit) {
    ciz(0.3); // tek statik kare — yıldızlar durur, gök kalır
    return;
  }

  var baslangic = performance.now();
  var DONGU = 120000; // 120 sn
  (function kare(simdi) {
    ciz(((simdi - baslangic) % DONGU) / DONGU);
    requestAnimationFrame(kare);
  })(baslangic);
})();
