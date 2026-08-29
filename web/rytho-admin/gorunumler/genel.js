/* Genel Bakış v2 (AP2): işletmenin tek ekranı — marj panosu (gelir −
   mağaza − AI), bugün şeridi, sayaçlı KPI'lar, eğriler ve en kârlı
   kullanıcılar. Uçlar: /admin/stats, /admin/live, /admin/economics. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  RY.gorunumler.genel = async function (icerik) {
    var b = RY.b;
    // stats ana veridir; canlı satır ve ekonomi YARDIMCI — düşerlerse
    // ilgili bölüm sessizce daralır, ekran ayakta kalır.
    var uclu = await Promise.all([
      RY.get('/api/v1/admin/stats?days=30'),
      RY.get('/api/v1/admin/live').catch(function () { return {}; }),
      RY.get('/api/v1/admin/economics?days=30')
        .catch(function () { return null; })
    ]);
    var veri = uclu[0], canli = uclu[1], eko = uclu[2];
    var gunler = veri.days || [];
    var son = gunler[0] || {};
    var u = son.users || {}, s = son.subs || {}, r = son.revenue || {};
    var ai = son.ai || {}, t = son.tokens || {}, bil = son.notify || {};

    var bildirimBugun = Object.keys(bil).reduce(function (top, tur) {
      return top + (bil[tur].sent || 0);
    }, 0);

    var karliSatirlar = '';
    if (eko && eko.users) {
      karliSatirlar = eko.users.slice(0, 5).map(function (k) {
        return '<tr class="tikla" data-uid="' + b.e(k.uid) + '">' +
          '<td><b>' + b.e(k.displayName || k.email || k.uid) + '</b></td>' +
          '<td class="sayi">' + b.para(k.revenueUsd) + '</td>' +
          '<td class="sayi">' + b.para(k.aiCostUsd) + '</td>' +
          '<td class="sayi"><span class="' +
          (k.marginUsd < 0 ? 'eksi' : 'arti') + '">' +
          b.para(k.marginUsd) + '</span></td></tr>';
      }).join('');
    }

    icerik.innerHTML =
      (eko ? b.marjPanosu(eko.totals, 'Son 30 gün') : '') +
      '<div class="bugun-serit">' +
      '<span class="bugun-cip">Bugün yeni kayıt <b>' +
      b.sayi(canli.newUsersToday) + '</b></span>' +
      '<span class="bugun-cip">AI çağrısı <b>' +
      b.sayi(ai.callsToday) + '</b></span>' +
      '<span class="bugun-cip">AI maliyeti <b>' +
      (ai.estCostToday != null && ai.estCostToday !== -1
        ? b.para(ai.estCostToday) : '—') + '</b></span>' +
      '<span class="bugun-cip">Harcanan jeton <b>' +
      b.sayi(t.spentTotalToday) + '</b></span>' +
      '<span class="bugun-cip">Gönderilen bildirim <b>' +
      (Object.keys(bil).length ? b.sayi(bildirimBugun) : '—') +
      '</b></span></div>' +
      '<div class="kpi-izgara">' +
      b.kpi(b.sayi(u.total), 'Toplam kullanıcı',
        { sayac: typeof u.total === 'number' ? u.total : null }) +
      b.kpi(b.sayi(u.dau), 'Günlük aktif (DAU)',
        { sayac: typeof u.dau === 'number' ? u.dau : null }) +
      b.kpi(b.sayi(s.active), 'Aktif abone', { altin: true,
        alt: s.trial ? b.sayi(s.trial) + ' mağaza denemesi' : null }) +
      b.kpi(b.para(r.grossToday), 'Son gün brüt', { altin: true }) +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-kayit', 'Kayıt eğrisi (30 gün)') +
      b.grafikPanel('g-dau', 'Günlük aktif (30 gün)') +
      '</div>' +
      '<div class="izgara-2">' +
      b.grafikPanel('g-jeton', 'Jeton harcaması (30 gün)') +
      b.grafikPanel('g-ai-maliyet', 'AI maliyeti $ (30 gün)') +
      '</div>' +
      (karliSatirlar
        ? '<div class="panel"><h2>En kârlı kullanıcılar (30 gün)</h2>' +
          b.tablo(['Kullanıcı', 'Gelir', 'AI maliyeti', 'Tahmini marj'],
                  karliSatirlar) +
          '<p class="dipnot">Tam tablo Ekonomi sekmesinde.</p></div>'
        : '') +
      (gunler.length === 0
        ? b.bosDurum('Henüz istatistik dokümanı yok — gecelik iş ilk ' +
            'kez koşunca dolar.')
        : '') +
      '<p class="dipnot">Son toplama: ' + b.e(son.date || '—') +
      (son.durationMs != null ? ' (' + b.sayi(son.durationMs) + ' ms)' : '') +
      ' · <button id="topla" class="buton ikincil kucuk">Şimdi topla</button></p>';

    b.canlandir(icerik);

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

    icerik.querySelectorAll('tr[data-uid]').forEach(function (tr) {
      tr.onclick = function () {
        location.hash = '#/kullanicilar/' +
          encodeURIComponent(tr.getAttribute('data-uid'));
      };
    });

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
