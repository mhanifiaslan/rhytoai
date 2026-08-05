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

  /* ---- Ortaklar (W8) ---- */

  function girdi(ad, yertutucu, tur) {
    return '<input name="' + ad + '" placeholder="' + yertutucu + '"' +
      (tur ? ' type="' + tur + '"' : '') +
      ' style="background:var(--ink-lighter);border:1px solid var(--glass-stroke);' +
      'border-radius:10px;color:var(--parchment);padding:9px 12px;' +
      'font-family:inherit;font-size:13px;min-width:0">';
  }

  async function ortaklar(icerik) {
    var veri = await RY.get('/api/v1/admin/partners');
    var liste = veri.partners || [];

    var satirlar = '';
    for (var i = 0; i < liste.length; i++) {
      var p = liste[i];
      satirlar += '<tr style="cursor:pointer" data-pid="' + e(p.id) + '">' +
        '<td>' + e(p.name) + (p.active === false ? ' <span style="color:var(--madder)">(pasif)</span>' : '') + '</td>' +
        '<td>' + e(p.contact) + '</td>' +
        '<td class="sayi">%' + e(p.sharePercent) + '</td></tr>';
    }

    icerik.innerHTML =
      '<div class="panel" style="margin-bottom:14px"><h2>Yeni ortak</h2>' +
      '<form id="ortak-form" style="display:flex;gap:8px;flex-wrap:wrap">' +
      girdi('name', 'Ad') + girdi('contact', 'İletişim (e-posta)') +
      girdi('sharePercent', 'Pay % (ör. 20)', 'number') +
      '<button class="buton ikincil" type="submit">Ekle</button></form></div>' +
      '<div class="panel"><h2>Ortaklar</h2>' +
      (liste.length
        ? '<table><tr><th>Ad</th><th>İletişim</th><th>Pay</th></tr>' + satirlar + '</table>'
        : '<p class="bos">Henüz ortak yok — yukarıdan ekle.</p>') +
      '</div><div id="ortak-detay"></div>';

    document.getElementById('ortak-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      await RY.post('/api/v1/admin/partners', {
        name: f.name.value, contact: f.contact.value,
        sharePercent: parseFloat(f.sharePercent.value || '0')
      });
      rotaYenile();
    };

    icerik.querySelectorAll('tr[data-pid]').forEach(function (tr) {
      tr.onclick = function () { ortakDetay(tr.getAttribute('data-pid')); };
    });
  }

  function rotaYenile() { window.dispatchEvent(new Event('hashchange')); }

  async function ortakDetay(pid) {
    var kutu = document.getElementById('ortak-detay');
    kutu.innerHTML = '<div class="bos">Yükleniyor…</div>';
    var d = await RY.get('/api/v1/admin/partners/' + encodeURIComponent(pid));
    var p = d.partner || {};

    var kodSatir = '';
    (d.codes || []).forEach(function (k) {
      kodSatir += '<tr><td class="sayi" style="text-align:left">' + e(k.code) + '</td>' +
        '<td class="sayi">' + e(k.bonusTokens) + '</td>' +
        '<td class="sayi">' + e(k.redemptionCount || 0) +
        (k.maxRedemptions ? '/' + e(k.maxRedemptions) : '') + '</td>' +
        '<td>' + (k.active ? 'aktif' : 'pasif') + '</td></tr>';
    });

    var odemeSatir = '';
    (d.payouts || []).forEach(function (o) {
      odemeSatir += '<tr><td class="sayi" style="text-align:left">' +
        e(o.amount) + ' ' + e(o.currency) + '</td><td>' + e(o.note) + '</td></tr>';
    });

    kutu.innerHTML =
      '<div class="kartlar" style="margin-top:14px">' +
      kart('$' + sayi(d.attributedGrossUsd), e(p.name) + ' — atfedilen brüt', true) +
      kart('$' + sayi(d.earnedUsd), 'Hakediş (%' + e(p.sharePercent) + ')') +
      kart('$' + sayi(d.paidUsd), 'Ödenen') +
      kart('$' + sayi(d.balanceUsd), 'Bakiye', true) +
      '</div>' +
      '<div class="izgara-2">' +
      '<div class="panel"><h2>Kodlar</h2>' +
      (kodSatir
        ? '<table><tr><th>Kod</th><th>Bonus</th><th>Kullanım</th><th>Durum</th></tr>' + kodSatir + '</table>'
        : '<p class="bos">Kod yok.</p>') +
      '<form id="kod-form" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px">' +
      girdi('code', 'Kod (boş = otomatik)') +
      girdi('bonusTokens', 'Bonus jeton', 'number') +
      girdi('maxRedemptions', 'Kullanım limiti', 'number') +
      '<button class="buton ikincil" type="submit">Kod üret</button></form>' +
      '<p style="color:var(--parchment-dim);font-size:11.5px;margin-top:10px">' +
      'Not: kod, kullanıcıya jeton bonusu verir ve SONRAKİ satın almaları bu ' +
      'ortağa atfeder. Mağaza fiyat indirimi buradan yapılamaz — gerekiyorsa ' +
      'RevenueCat/Play konsolundan elle tanımlanır.</p></div>' +
      '<div class="panel"><h2>Ödemeler</h2>' +
      (odemeSatir
        ? '<table><tr><th>Tutar</th><th>Not</th></tr>' + odemeSatir + '</table>'
        : '<p class="bos">Ödeme kaydı yok.</p>') +
      '<form id="odeme-form" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px">' +
      girdi('amount', 'Tutar (USD)', 'number') + girdi('note', 'Not') +
      '<button class="buton ikincil" type="submit">Ödeme işaretle</button></form>' +
      '</div></div>';

    document.getElementById('kod-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      await RY.post('/api/v1/admin/partners/' + encodeURIComponent(pid) + '/codes', {
        code: f.code.value || null,
        bonusTokens: parseInt(f.bonusTokens.value || '0', 10),
        maxRedemptions: f.maxRedemptions.value
          ? parseInt(f.maxRedemptions.value, 10) : null
      });
      ortakDetay(pid);
    };
    document.getElementById('odeme-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      await RY.post('/api/v1/admin/partners/' + encodeURIComponent(pid) + '/payouts', {
        amount: parseFloat(f.amount.value), note: f.note.value
      });
      ortakDetay(pid);
    };
    kutu.scrollIntoView({ behavior: 'smooth' });
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
