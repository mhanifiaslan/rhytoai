/* Panel görünümleri (W6). Her görünüm #icerik'e çizer; veri yalnız
   backend admin uçlarından (RY.get) — Firestore'a doğrudan erişim yok. */
(function () {
  'use strict';

  var RY = window.RY;

  function e(metin) {
    return String(metin == null ? '-' : metin)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function kart(deger, ad, altin) {
    return '<div class="panel kart"><div class="deger' +
      (altin ? ' altin' : '') + '">' + e(deger) + '</div>' +
      '<div class="ad">' + e(ad) + '</div></div>';
  }

  function sayi(v) {
    if (v == null || v === -1) return '—';
    return typeof v === 'number' ? v.toLocaleString('tr-TR') : String(v);
  }

  /* ---- Genel Bakış ---- */
  async function genel(icerik) {
    var veri = await RY.get('/api/v1/admin/stats?days=30');
    var canli = await RY.get('/api/v1/admin/live');
    var gunler = veri.days || [];
    var son = gunler[0] || {};
    var u = son.users || {}, s = son.subs || {}, r = son.revenue || {};

    icerik.innerHTML =
      '<div class="kartlar">' +
      kart(sayi(u.total), 'Toplam kullanıcı') +
      kart(sayi(u.onboarded), 'Onboarding tamam') +
      kart(sayi(canli.newUsersToday), 'Bugün yeni kayıt') +
      kart(sayi(u.dau), 'Dünkü aktif (DAU)') +
      kart(sayi(s.active), 'Aktif abone', true) +
      kart('$' + sayi(r.grossToday), 'Son gün brüt', true) +
      '</div>' +
      '<div class="izgara-2">' +
      '<div class="panel"><h2>Kayıt eğrisi (30 gün)</h2><canvas id="g-kayit" class="grafik"></canvas></div>' +
      '<div class="panel"><h2>Günlük aktif (30 gün)</h2><canvas id="g-dau" class="grafik"></canvas></div>' +
      '</div>' +
      (gunler.length === 0
        ? '<p class="bos">Henüz istatistik dokümanı yok — gecelik iş ilk kez koşunca dolar. Şimdi toplamak için: <button id="topla" class="buton ikincil">Topla</button></p>'
        : '');

    var eskiden = gunler.slice().reverse();
    RY.sparkline(document.getElementById('g-kayit'),
      eskiden.map(function (g) { return (g.users || {}).newToday || 0; }));
    RY.sparkline(document.getElementById('g-dau'),
      eskiden.map(function (g) { return (g.users || {}).dau || 0; }));

    var topla = document.getElementById('topla');
    if (topla) topla.onclick = async function () {
      topla.disabled = true; topla.textContent = 'Toplanıyor…';
      await RY.post('/api/v1/admin/collect');
      location.reload();
    };
  }

  /* ---- Kullanıcılar ---- */
  async function kullanicilar(icerik) {
    var veri = await RY.get('/api/v1/admin/stats?days=30');
    var son = (veri.days || [])[0] || {};
    var u = son.users || {}, sosyal = son.social || {};

    icerik.innerHTML =
      '<div class="kartlar">' +
      kart(sayi(u.total), 'Toplam') +
      kart(sayi(u.push), 'Push erişilebilir') +
      kart(sayi(u.usernames), 'Kullanıcı adı almış') +
      kart(sayi(sosyal.friendships), 'Arkadaşlık') +
      kart(sayi(u.contactMatchOn), 'Rehber eşleşmesi açık') +
      kart(sayi(u.streakVisibleOn), 'Seri görünür') +
      '</div>' +
      '<div class="izgara-2">' +
      '<div class="panel"><h2>Dil dağılımı</h2><canvas id="g-dil" class="grafik"></canvas></div>' +
      '<div class="panel"><h2>Seri kovaları</h2><canvas id="g-seri" class="grafik"></canvas></div>' +
      '<div class="panel"><h2>Saat dilimi (ilk 8)</h2><canvas id="g-tz" class="grafik"></canvas></div>' +
      '</div>';

    RY.cubuklar(document.getElementById('g-dil'), u.byLanguage || {});
    RY.cubuklar(document.getElementById('g-seri'), u.streakBuckets || {});
    RY.cubuklar(document.getElementById('g-tz'), u.byTimezone || {});
  }

  /* ---- Gelir ---- */
  async function gelir(icerik) {
    var veri = await RY.get('/api/v1/admin/revenue?days=90');
    var gunSirali = Object.keys(veri.byDay || {}).sort();

    icerik.innerHTML =
      '<div class="kartlar">' +
      kart('$' + sayi(veri.grossUsd), '90 gün brüt (USD)', true) +
      kart(sayi((veri.events || {}).INITIAL_PURCHASE), 'Yeni abonelik') +
      kart(sayi((veri.events || {}).RENEWAL), 'Yenileme') +
      kart(sayi((veri.events || {}).TRIAL_CONVERTED), 'Deneme dönüşümü') +
      kart(sayi((veri.events || {}).NON_RENEWING_PURCHASE), 'Paket satışı') +
      kart(sayi((veri.events || {}).REFUND), 'İade') +
      '</div>' +
      '<div class="panel" style="margin-bottom:14px"><h2>Günlük brüt (USD)</h2><canvas id="g-gun" class="grafik"></canvas></div>' +
      '<div class="izgara-2">' +
      '<div class="panel"><h2>Ürün kırılımı (USD)</h2><canvas id="g-urun" class="grafik"></canvas></div>' +
      '<div class="panel"><h2>Para birimi (yerel tutar)</h2><canvas id="g-pb" class="grafik"></canvas></div>' +
      '</div>' +
      '<p class="ad" style="margin-top:12px;color:var(--parchment-dim);font-size:12px">' +
      'Kaynak: revenueEvents (webhook, ' + new Date().getFullYear() +
      '). Mağaza komisyonu ve vergi düşülmemiş brüt tutarlardır.</p>';

    RY.sparkline(document.getElementById('g-gun'),
      gunSirali.map(function (g) { return veri.byDay[g]; }));
    RY.cubuklar(document.getElementById('g-urun'), veri.byProduct || {});
    RY.cubuklar(document.getElementById('g-pb'), veri.byCurrency || {});
  }

  /* ---- Ortaklar (W8'de dolar) ---- */
  async function ortaklar(icerik) {
    icerik.innerHTML =
      '<div class="panel"><h2>Ortaklar</h2>' +
      '<p class="bos">Henüz ortak tanımlı değil. Ortak ve kod yönetimi bir ' +
      'sonraki sürümde bu ekrana gelecek.</p></div>';
  }

  /* ---- Sistem ---- */
  async function sistem(icerik) {
    var saglik = await RY.saglik('/health').catch(function () { return null; });
    var rag = await RY.saglik('/health/rag').catch(function () { return null; });
    var veri = await RY.get('/api/v1/admin/stats?days=1');
    var son = (veri.days || [])[0] || {};
    var sys = son.system || {}, sosyal = son.social || {};

    icerik.innerHTML =
      '<div class="kartlar">' +
      kart(saglik ? 'AÇIK' : 'KAPALI', 'Backend', !!saglik) +
      kart(rag ? e(rag.status).toUpperCase() : '—', 'RAG tabanı') +
      kart(sayi(sys.aiCacheCount), 'AI önbellek dokümanı') +
      kart(sayi(sys.conversationsCount), 'Konuşma') +
      kart(sayi(sosyal.reportsOpen), 'Şikayet kuyruğu') +
      kart(son.durationMs != null ? sayi(son.durationMs) + ' ms' : '—',
           'Son toplama süresi') +
      '</div>' +
      '<div class="panel"><h2>RAG ayrıntısı</h2><pre class="mono" style="font-size:12px;overflow-x:auto">' +
      e(JSON.stringify(rag, null, 2)) + '</pre></div>';
  }

  window.RY.gorunumler = {
    genel: genel,
    kullanicilar: kullanicilar,
    gelir: gelir,
    ortaklar: ortaklar,
    sistem: sistem
  };
})();
