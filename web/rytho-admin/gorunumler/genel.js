/* Genel Bakış: işletmenin tek ekran özeti.
   Uçlar: /admin/stats?days=30 + /admin/live. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  RY.gorunumler.genel = async function (icerik) {
    var b = RY.b;
    // İkisi paralel; canlı satır YARDIMCIDIR — düşerse ekran düşmez,
    // yalnız "bugün yeni" değeri — olur. stats düşerse gerçek hata.
    var ikisi = await Promise.all([
      RY.get('/api/v1/admin/stats?days=30'),
      RY.get('/api/v1/admin/live').catch(function () { return {}; })
    ]);
    var veri = ikisi[0], canli = ikisi[1];
    var gunler = veri.days || [];
    var son = gunler[0] || {};
    var u = son.users || {}, s = son.subs || {}, r = son.revenue || {};
    var ai = son.ai || {}, t = son.tokens || {};

    icerik.innerHTML =
      '<div class="kpi-izgara">' +
      b.kpi(b.sayi(u.total), 'Toplam kullanıcı') +
      b.kpi(b.sayi(canli.newUsersToday), 'Bugün yeni kayıt') +
      b.kpi(b.sayi(u.dau), 'Günlük aktif (DAU)') +
      b.kpi(b.sayi(s.active), 'Aktif abone', { altin: true,
        alt: s.trial ? b.sayi(s.trial) + ' mağaza denemesi' : null }) +
      b.kpi(b.para(r.grossToday), 'Son gün brüt', { altin: true }) +
      b.kpi(ai.estCostToday != null && ai.estCostToday !== -1
        ? b.para(ai.estCostToday) : '—', 'AI maliyeti (son gün)',
        { alt: ai.callsToday != null && ai.callsToday !== -1
          ? b.sayi(ai.callsToday) + ' çağrı' : null }) +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-kayit', 'Kayıt eğrisi (30 gün)') +
      b.grafikPanel('g-dau', 'Günlük aktif (30 gün)') +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-jeton', 'Jeton harcaması (30 gün)') +
      b.grafikPanel('g-ai-maliyet', 'AI maliyeti $ (30 gün)') +
      '</div>' +
      (gunler.length === 0
        ? b.bosDurum('Henüz istatistik dokümanı yok — gecelik iş ilk ' +
            'kez koşunca dolar.')
        : '') +
      '<p class="dipnot">Son toplama: ' +
      b.e(son.date || '—') +
      (son.durationMs != null ? ' (' + b.sayi(son.durationMs) + ' ms)' : '') +
      ' · <button id="topla" class="buton ikincil kucuk">Şimdi topla</button></p>';

    var eskiden = gunler.slice().reverse();
    var etiketler = eskiden.map(function (g) { return g.date || ''; });
    RY.grafik.cizgi(document.getElementById('g-kayit'), {
      degerler: eskiden.map(function (g) {
        return (g.users || {}).newToday || 0;
      }), etiketler: etiketler });
    RY.grafik.cizgi(document.getElementById('g-dau'), {
      degerler: eskiden.map(function (g) {
        return (g.users || {}).dau || 0;
      }), etiketler: etiketler });
    RY.grafik.cizgi(document.getElementById('g-jeton'), {
      degerler: eskiden.map(function (g) {
        var v = ((g.tokens || {}).spentTotalToday);
        return v == null || v === -1 ? 0 : v;
      }), etiketler: etiketler });
    RY.grafik.cizgi(document.getElementById('g-ai-maliyet'), {
      degerler: eskiden.map(function (g) {
        var v = ((g.ai || {}).estCostToday);
        return v == null || v === -1 ? 0 : v;
      }), etiketler: etiketler, birim: '$' });

    var topla = document.getElementById('topla');
    if (topla) topla.onclick = async function () {
      topla.disabled = true;
      topla.textContent = 'Toplanıyor…';
      try {
        await RY.post('/api/v1/admin/collect');
        RY.rotaYenile();
      } catch (h) {
        topla.disabled = false;
        topla.textContent = 'Şimdi topla';
        alert(RY.hataMetni(h));
      }
    };
  };
})();
