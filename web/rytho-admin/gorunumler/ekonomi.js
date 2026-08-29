/* Ekonomi (AP2): işletme K/Z — marj panosu + KULLANICI BAZLI kâr tablosu
   (sıralanabilir) + gelir kırılımları + jeton akışı + bedel tablosu.
   Uçlar: /admin/economics, /admin/revenue, /admin/stats, /admin/usage.
   Bedeller ve marj matematiği SUNUCUDAN gelir — panel hardcode etmez. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  var SUTUNLAR = [
    ['displayName', 'Kullanıcı'], ['revenueUsd', 'Gelir'],
    ['storeCutUsd', 'Kesinti'], ['aiCostUsd', 'AI maliyeti'],
    ['tokensSpent', 'Jeton'], ['calls', 'Çağrı'],
    ['marginUsd', 'Tahmini marj']
  ];

  function kzTablosu(eko, siraAlan, yon) {
    var b = RY.b;
    var satirlar = eko.users.slice().sort(function (a, c) {
      var x = a[siraAlan], y = c[siraAlan];
      if (typeof x === 'string' || typeof y === 'string') {
        return String(x || '').localeCompare(String(y || ''), 'tr') * yon;
      }
      return ((x || 0) - (y || 0)) * yon;
    });

    var govde = satirlar.map(function (k) {
      return '<tr class="tikla" data-uid="' + b.e(k.uid) + '">' +
        '<td><b>' + b.e(k.displayName || '—') + '</b><br>' +
        '<span style="font-size:11px">' + b.e(k.email || '') + '</span></td>' +
        '<td class="sayi">' + b.para(k.revenueUsd) + '</td>' +
        '<td class="sayi">−' + b.para(k.storeCutUsd) + '</td>' +
        '<td class="sayi">−' + b.para(k.aiCostUsd) + '</td>' +
        '<td class="sayi">' + b.sayi(k.tokensSpent) + '</td>' +
        '<td class="sayi">' + b.sayi(k.calls) + '</td>' +
        '<td class="sayi"><span class="' +
        (k.marginUsd < 0 ? 'eksi' : 'arti') + '">' +
        b.para(k.marginUsd) + '</span></td></tr>';
    }).join('');

    var t = eko.totals;
    govde += '<tr class="toplam"><td>Toplam' +
      (t.sharedAiCostUsd
        ? '<br><span style="font-size:11px">+ paylaşımlı üretim ' +
          b.para(t.sharedAiCostUsd) + ' (burç vb.)</span>'
        : '') + '</td>' +
      '<td class="sayi">' + b.para(t.revenueUsd) + '</td>' +
      '<td class="sayi">−' + b.para(t.storeCutUsd) + '</td>' +
      '<td class="sayi">−' + b.para(t.aiCostUsd) + '</td>' +
      '<td class="sayi"></td><td class="sayi"></td>' +
      '<td class="sayi"><span class="' +
      (t.marginUsd < 0 ? 'eksi' : 'arti') + '">' + b.para(t.marginUsd) +
      '</span></td></tr>';

    var basliklar = SUTUNLAR.map(function (sut) {
      return '<th class="siralanir" data-alan="' + sut[0] + '"' +
        (sut[0] === siraAlan ? ' data-yon="' + yon + '"' : '') + '>' +
        b.e(sut[1]) + '</th>';
    }).join('');

    return '<div class="tablo-sarici"><table class="tablo">' +
      '<thead><tr>' + basliklar + '</tr></thead>' +
      '<tbody>' + govde + '</tbody></table></div>';
  }

  RY.gorunumler.ekonomi = async function (icerik) {
    var b = RY.b;
    // economics + revenue ana; stats/usage yardımcı (düşerse panel daralır).
    var dortlu = await Promise.all([
      RY.get('/api/v1/admin/economics?days=90')
        .catch(function () { return null; }),
      RY.get('/api/v1/admin/revenue?days=90'),
      RY.get('/api/v1/admin/stats?days=30')
        .catch(function () { return { days: [] }; }),
      RY.get('/api/v1/admin/usage?days=30')
        .catch(function () { return { costs: {} }; })
    ]);
    var eko = dortlu[0], veri = dortlu[1];
    var stats = dortlu[2], kullanim = dortlu[3];

    var gunSirali = Object.keys(veri.byDay || {}).sort();
    var olaylar = veri.events || {};
    var gunler = (stats.days || []).slice().reverse();

    var ozellikToplam = {};
    var jetonSeri = gunler.map(function (g) {
      var jt = g.tokens || {};
      Object.keys(jt.spentToday || {}).forEach(function (oz) {
        ozellikToplam[oz] = (ozellikToplam[oz] || 0) + jt.spentToday[oz];
      });
      var v = jt.spentTotalToday;
      return v == null || v === -1 ? 0 : v;
    });

    var bedeller = kullanim.costs || {};
    var bedelSatir = Object.keys(bedeller).sort().map(function (oz) {
      return '<tr><td>' + b.e(oz) + '</td><td class="sayi">' +
        b.sayi(bedeller[oz]) + '</td></tr>';
    }).join('');

    icerik.innerHTML =
      (eko ? b.marjPanosu(eko.totals, 'Son 90 gün') : '') +
      '<div class="kpi-izgara">' +
      b.kpi(b.para(veri.grossUsd), '90 gün brüt', { altin: true }) +
      b.kpi(b.sayi(olaylar.INITIAL_PURCHASE), 'Yeni abonelik') +
      b.kpi(b.sayi(olaylar.RENEWAL), 'Yenileme') +
      b.kpi(b.sayi(olaylar.TRIAL_CONVERTED), 'Deneme dönüşümü') +
      b.kpi(b.sayi(olaylar.NON_RENEWING_PURCHASE), 'Paket satışı') +
      b.kpi(b.sayi(olaylar.REFUND), 'İade',
        olaylar.REFUND ? { alt: 'dikkat' } : {}) +
      '</div>' +
      (eko
        ? '<div class="modul"><div class="modul-baslik">' +
          '<h2>Kullanıcı bazlı kâr/zarar</h2>' +
          b.etiket('90 gün') + '</div>' +
          '<div id="kz-kap"></div>' +
          '<p class="dipnot">Marj = gelir × (1 − mağaza ~%' +
          Math.round((eko.totals.storeCutRate || 0.15) * 100) +
          ') − tahmini AI maliyeti. Sütun başlığına tıklayınca sıralanır; ' +
          'satır kullanıcının 360 ekranını açar.</p></div>'
        : b.bosDurum('Kullanıcı bazlı tablo alınamadı — Tekrar dene.')) +
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
      '<p class="dipnot">Kaynak: revenueEvents (webhook) + usageEvents ' +
      '(canlı telemetri) + cüzdan defteri. Brüt tutarlar vergi/komisyon ' +
      'düşülmemiştir; marj tahminidir.</p>';

    // K/Z tablosu: durum + sıralama tıklamaları
    if (eko) {
      var durum = { alan: 'marginUsd', yon: -1 };
      var kap = document.getElementById('kz-kap');
      function tabloyuBas() {
        kap.innerHTML = kzTablosu(eko, durum.alan, durum.yon);
        kap.querySelectorAll('th.siralanir').forEach(function (th) {
          th.onclick = function () {
            var alan = th.getAttribute('data-alan');
            durum.yon = (durum.alan === alan) ? -durum.yon
              : (alan === 'displayName' ? 1 : -1);
            durum.alan = alan;
            tabloyuBas();
          };
        });
        kap.querySelectorAll('tr[data-uid]').forEach(function (tr) {
          tr.onclick = function () {
            location.hash = '#/kullanicilar/' +
              encodeURIComponent(tr.getAttribute('data-uid'));
          };
        });
      }
      tabloyuBas();
    }

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
