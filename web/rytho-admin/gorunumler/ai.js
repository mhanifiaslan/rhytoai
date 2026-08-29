/* AI Kullanımı: usageEvents telemetrisi — çağrı/maliyet/token kırılımları.
   Uç: /admin/usage?days=30. Maliyetler TAHMİNİDİR (sabit birim fiyat ×
   ölçülen token) — gerçek fatura Cloud Console'da. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  RY.gorunumler.ai = async function (icerik) {
    var b = RY.b;
    var veri = await RY.get('/api/v1/admin/usage?days=30');
    var byDay = veri.byDay || {};
    var toplam = veri.totals || {};
    var gunSirali = Object.keys(byDay).sort();
    var bugun = new Date().toISOString().slice(0, 10);
    var bugunku = byDay[bugun] || {};

    if (!toplam.calls) {
      icerik.innerHTML = b.bosDurum(
        'Henüz kullanım olayı yok — ilk LLM çağrısıyla dolmaya başlar. ' +
        'Önbellekten servis edilen istekler burada görünmez (maliyetleri ' +
        'sıfırdır).');
      return;
    }

    function ozellikMaliyeti(kova) {
      var sonuc = {};
      Object.keys(kova || {}).forEach(function (k) {
        sonuc[k] = Math.round((kova[k].estCostUsd || 0) * 10000) / 10000;
      });
      return sonuc;
    }
    function ozellikCagri(kova) {
      var sonuc = {};
      Object.keys(kova || {}).forEach(function (k) {
        sonuc[k] = kova[k].calls || 0;
      });
      return sonuc;
    }

    icerik.innerHTML =
      '<div class="kpi-izgara">' +
      b.kpi(b.sayi(bugunku.calls || 0), 'Bugün çağrı') +
      b.kpi(b.para(bugunku.estCostUsd || 0), 'Bugün maliyet') +
      b.kpi(b.sayi(toplam.calls), '30 gün çağrı') +
      b.kpi(b.para(toplam.estCostUsd), '30 gün maliyet', { altin: true }) +
      b.kpi(b.sayi(toplam.promptTokens), '30g girdi token') +
      b.kpi(b.sayi((toplam.outputTokens || 0) +
                   (toplam.thinkingTokens || 0)),
            '30g çıktı token',
            toplam.thinkingTokens
              ? { alt: b.sayi(toplam.thinkingTokens) + ' düşünme' } : {}) +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-ai-cagri', 'Günlük çağrı (30 gün)') +
      b.grafikPanel('g-ai-gunluk', 'Günlük maliyet $ (30 gün)') +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-ai-ozellik', 'Özellik başına çağrı', true) +
      b.grafikPanel('g-ai-ozellik-usd', 'Özellik başına maliyet $', true) +
      '</div>' +
      b.grafikPanel('g-ai-model', 'Model kırılımı (çağrı)', true) +
      '<p class="dipnot">Tahmini maliyet = ölçülen token × sabit birim ' +
      'fiyat (girdi $0,30/M · çıktı+düşünme $2,50/M). Gerçek fatura için ' +
      'Cloud Console. Yalnız GERÇEK model çağrıları sayılır — önbellek ' +
      'isabetleri bedava ve burada yok.</p>';

    RY.grafik.cizgi(document.getElementById('g-ai-cagri'), {
      degerler: gunSirali.map(function (g) { return byDay[g].calls || 0; }),
      etiketler: gunSirali });
    RY.grafik.cizgi(document.getElementById('g-ai-gunluk'), {
      degerler: gunSirali.map(function (g) {
        return byDay[g].estCostUsd || 0;
      }), etiketler: gunSirali, birim: '$' });
    RY.grafik.cubuk(document.getElementById('g-ai-ozellik'),
      ozellikCagri(veri.byFeature));
    RY.grafik.cubuk(document.getElementById('g-ai-ozellik-usd'),
      ozellikMaliyeti(veri.byFeature), { birim: '$' });
    RY.grafik.cubuk(document.getElementById('g-ai-model'),
      ozellikCagri(veri.byModel));
  };
})();
