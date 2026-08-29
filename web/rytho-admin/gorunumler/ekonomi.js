/* Ekonomi: gelir (revenueEvents) + jeton akışı (debit ledger) + salt-okur
   bedel tablosu. Uçlar: /admin/revenue, /admin/stats, /admin/usage.
   Bedeller SUNUCUDAN gelir (wallet.TOKEN_COSTS) — panel hardcode etmez. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  RY.gorunumler.ekonomi = async function (icerik) {
    var b = RY.b;
    // Üçü paralel; gelir ana veridir, stats/usage yardımcı — düşerlerse
    // ilgili paneller boş kalır, ekran ayakta durur.
    var ucu = await Promise.all([
      RY.get('/api/v1/admin/revenue?days=90'),
      RY.get('/api/v1/admin/stats?days=30')
        .catch(function () { return { days: [] }; }),
      RY.get('/api/v1/admin/usage?days=30')
        .catch(function () { return { costs: {} }; })
    ]);
    var veri = ucu[0], stats = ucu[1], kullanim = ucu[2];

    var gunSirali = Object.keys(veri.byDay || {}).sort();
    var olaylar = veri.events || {};
    var gunler = (stats.days || []).slice().reverse();

    // 30 günün jeton akışı: özellik kırılımı toplamı + günlük seri.
    var ozellikToplam = {};
    var jetonSeri = gunler.map(function (g) {
      var t = g.tokens || {};
      Object.keys(t.spentToday || {}).forEach(function (oz) {
        ozellikToplam[oz] = (ozellikToplam[oz] || 0) + t.spentToday[oz];
      });
      var v = t.spentTotalToday;
      return v == null || v === -1 ? 0 : v;
    });

    var bedeller = kullanim.costs || {};
    var bedelSatir = Object.keys(bedeller).sort().map(function (oz) {
      return '<tr><td>' + b.e(oz) + '</td><td class="sayi">' +
        b.sayi(bedeller[oz]) + '</td></tr>';
    }).join('');

    icerik.innerHTML =
      '<div class="kpi-izgara">' +
      b.kpi(b.para(veri.grossUsd), '90 gün brüt', { altin: true }) +
      b.kpi(b.sayi(olaylar.INITIAL_PURCHASE), 'Yeni abonelik') +
      b.kpi(b.sayi(olaylar.RENEWAL), 'Yenileme') +
      b.kpi(b.sayi(olaylar.TRIAL_CONVERTED), 'Deneme dönüşümü') +
      b.kpi(b.sayi(olaylar.NON_RENEWING_PURCHASE), 'Paket satışı') +
      b.kpi(b.sayi(olaylar.REFUND), 'İade',
        olaylar.REFUND ? { alt: 'dikkat' } : {}) +
      '</div>' +
      b.grafikPanel('g-gun', 'Günlük brüt USD (90 gün)') +
      '<div class="izgara-2">' +
      b.grafikPanel('g-urun', 'Ürün kırılımı (USD)', true) +
      b.grafikPanel('g-pb', 'Para birimi (yerel tutar)', true) +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-jeton-seri', 'Jeton harcaması (30 gün)') +
      '<div class="panel"><h2>Jeton akışı — özellik kırılımı (30 gün)</h2>' +
      '<div class="grafik-kap"><canvas id="g-jeton-oz" ' +
      'class="grafik grafik-kisa" role="img" ' +
      'aria-label="Özellik kırılımı"></canvas></div></div>' +
      '</div>' +
      '<div class="panel"><h2>Jeton bedelleri (sunucu gerçeği)</h2>' +
      (bedelSatir ? b.tablo(['Özellik', 'Jeton'], bedelSatir)
                  : b.bosDurum('Bedel tablosu alınamadı.')) +
      '</div>' +
      '<p class="dipnot">Kaynak: revenueEvents (webhook). Mağaza komisyonu ' +
      've vergi düşülmemiş brüt tutarlardır. Jeton akışı cüzdan defterinin ' +
      'debit kayıtlarından gelir (AP-turu öncesi günlerde boştur).</p>';

    RY.grafik.cizgi(document.getElementById('g-gun'), {
      degerler: gunSirali.map(function (g) { return veri.byDay[g]; }),
      etiketler: gunSirali, birim: '$' });
    RY.grafik.cubuk(document.getElementById('g-urun'),
      veri.byProduct || {}, { birim: '$' });
    RY.grafik.cubuk(document.getElementById('g-pb'), veri.byCurrency || {});
    RY.grafik.cizgi(document.getElementById('g-jeton-seri'), {
      degerler: jetonSeri,
      etiketler: gunler.map(function (g) { return g.date || ''; }) });
    RY.grafik.cubuk(document.getElementById('g-jeton-oz'), ozellikToplam);
  };
})();
