/* Genel Bakış v3 (AP3): üç bölgeli "uygulama" panosu.
   Sol geniş: HERO grafik (metrik/aralık pilleri, büyük değer + delta,
   fetch'siz geçiş) + Bugün + En kârlı kullanıcılar + Son olaylar.
   Sağ ray: marj kartı + hızlı kredi + bildirim nabzı.
   Uçlar: /admin/stats?days=90, /admin/live, /admin/economics?days=30,
   /admin/audit, /admin/notify-runs — hepsi mevcut; yardımcılar düşerse
   ilgili modül daralır (kısmi yükleme sözleşmesi). */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  var METRIKLER = {
    gelir: { ad: 'Gelir', birim: '$',
      al: function (g) { return (g.revenue || {}).grossToday || 0; } },
    ai: { ad: 'AI maliyeti', birim: '$',
      al: function (g) {
        var v = (g.ai || {}).estCostToday;
        return v == null || v === -1 ? 0 : v;
      } },
    jeton: { ad: 'Harcanan jeton', birim: '',
      al: function (g) {
        var v = (g.tokens || {}).spentTotalToday;
        return v == null || v === -1 ? 0 : v;
      } },
    dau: { ad: 'Günlük aktif', birim: '',
      al: function (g) { return (g.users || {}).dau || 0; } },
    kayit: { ad: 'Yeni kayıt', birim: '',
      al: function (g) { return (g.users || {}).newToday || 0; } }
  };

  RY.gorunumler.genel = async function (icerik) {
    var b = RY.b;
    var besli = await Promise.all([
      RY.get('/api/v1/admin/stats?days=90'),
      RY.get('/api/v1/admin/live').catch(function () { return {}; }),
      RY.get('/api/v1/admin/economics?days=30')
        .catch(function () { return null; }),
      RY.get('/api/v1/admin/audit?limit=8')
        .catch(function () { return { entries: [] }; }),
      RY.get('/api/v1/admin/notify-runs?days=2')
        .catch(function () { return { runs: [] }; })
    ]);
    var stats = besli[0], canli = besli[1], eko = besli[2];
    var iz = besli[3], kosular = besli[4];

    var gunler = (stats.days || []).slice().reverse();  // eskiden yeniye
    var son = gunler[gunler.length - 1] || {};
    var ai = son.ai || {}, t = son.tokens || {}, bil = son.notify || {};

    var bildirimBugun = Object.keys(bil).reduce(function (top, tur) {
      return top + (bil[tur].sent || 0);
    }, 0);

    /* ---- Modül içerikleri ---- */

    var bugunHtml =
      b.satir({ ikon: 'kayit', ikonSinif: 'yesil', baslik: 'Yeni kayıt',
        alt: 'bugün katılan', sagUst: b.sayi(canli.newUsersToday) }) +
      b.satir({ ikon: 'ai', baslik: 'AI çağrısı',
        alt: ai.estCostToday != null && ai.estCostToday !== -1
          ? b.para(ai.estCostToday) + ' tahmini maliyet' : 'telemetri',
        sagUst: b.sayi(ai.callsToday) }) +
      b.satir({ ikon: 'jeton', ikonSinif: 'altin', baslik: 'Harcanan jeton',
        alt: 'cüzdan defterinden', sagUst: b.sayi(t.spentTotalToday) }) +
      b.satir({ ikon: 'bildirim', baslik: 'Gönderilen bildirim',
        alt: 'tüm türler', sagUst: Object.keys(bil).length
          ? b.sayi(bildirimBugun) : '—' });

    var karliHtml = '';
    if (eko && eko.users) {
      karliHtml = eko.users.slice(0, 5).map(function (k) {
        return b.satir({ avatar: k.displayName || k.email || '?',
          baslik: k.displayName || '—', alt: k.email || '',
          sagUst: b.para(k.marginUsd),
          sagUstSinif: k.marginUsd < 0 ? 'eksi' : 'arti',
          sagAlt: 'gelir ' + b.para(k.revenueUsd),
          veri: { uid: k.uid } });
      }).join('');
    }

    var EYLEM_IKONU = { 'user.credit': 'kredi', 'user.disable': 'sistem',
      'user.enable': 'sistem', 'user.delete': 'iade',
      'stats.collect': 'panel', 'partner.create': 'ortaklar',
      'partner.update': 'ortaklar', 'partner.code': 'ortaklar',
      'partner.payout': 'gelir' };
    var olayHtml = (iz.entries || []).map(function (k) {
      return b.satir({ ikon: EYLEM_IKONU[k.action] || 'denetim',
        baslik: k.action || '?',
        alt: (k.targetUid ? k.targetUid + ' · ' : '') +
          JSON.stringify(k.params || {}).slice(0, 60),
        sagAlt: b.tarih(k.at, true) });
    }).join('');

    var nabizHtml = (kosular.runs || []).slice(0, 6).map(function (k) {
      return b.satir({ ikon: 'bildirim',
        ikonSinif: (k.failed || 0) > 0 ? 'kirmizi' : 'yesil',
        baslik: k.type || '?', alt: k.date || '',
        sagUst: b.sayi(k.sent),
        sagUstSinif: (k.failed || 0) > 0 ? 'eksi' : 'arti',
        sagAlt: (k.failed || 0) > 0
          ? b.sayi(k.failed) + ' başarısız' : 'sorunsuz' });
    }).join('');

    var krediSecenekHtml = '';
    if (eko && eko.users) {
      krediSecenekHtml = eko.users.map(function (k) {
        return '<option value="' + b.e(k.email || k.uid) + '">' +
          b.e(k.displayName || '') + '</option>';
      }).join('');
    }

    /* ---- Yerleşim ---- */

    icerik.innerHTML =
      '<div class="pano-izgara">' +
      '<div class="pano-sol">' +

      '<div class="modul">' +
      '<div class="modul-baslik"><div class="pil-grup" id="metrik-grup">' +
      Object.keys(METRIKLER).map(function (m) {
        return '<button class="pil' + (m === 'gelir' ? ' aktif' : '') +
          '" data-metrik="' + m + '">' + METRIKLER[m].ad + '</button>';
      }).join('') + '</div>' +
      '<div class="pil-grup" id="aralik-grup">' +
      [7, 30, 90].map(function (n) {
        return '<button class="pil' + (n === 30 ? ' aktif' : '') +
          '" data-aralik="' + n + '">' + n + 'g</button>';
      }).join('') + '</div></div>' +
      '<div class="hero-ust"><div class="hero-deger-blok">' +
      '<div class="hero-deger" id="hero-deger">—</div>' +
      '<div class="hero-alt" id="hero-alt"></div></div>' +
      '<div id="hero-delta"></div></div>' +
      '<div class="grafik-kap"><canvas id="g-hero" ' +
      'class="grafik grafik-hero" role="img" ' +
      'aria-label="Seçili metrik eğrisi"></canvas></div></div>' +

      '<div class="izgara-2" style="margin-top:16px">' +
      b.modul('Bugün', '<div class="satir-liste">' + bugunHtml + '</div>',
        b.etiket(son.date || 'bugün')) +
      b.modul('En kârlı kullanıcılar',
        karliHtml
          ? '<div class="satir-liste">' + karliHtml + '</div>'
          : b.bosDurum('Ekonomi verisi alınamadı.'),
        b.etiket('30 gün')) +
      '</div>' +

      b.modul('Son olaylar',
        olayHtml ? '<div class="satir-liste">' + olayHtml + '</div>'
                 : b.bosDurum('Henüz denetim kaydı yok.'),
        b.etiket('denetim izi')) +

      '<p class="dipnot">Son toplama: ' + b.e(son.date || '—') +
      (son.durationMs != null
        ? ' (' + b.sayi(son.durationMs) + ' ms)' : '') +
      ' · <button id="topla" class="buton ikincil kucuk">Şimdi topla' +
      '</button></p>' +
      '</div>' +

      '<div class="pano-ray">' +
      (eko ? '<div class="marj-ray">' +
        b.marjPanosu(eko.totals, 'Son 30 gün') + '</div>' : '') +
      b.modul('Hızlı kredi',
        '<form id="hizli-kredi">' +
        '<div class="giris-form" style="gap:8px">' +
        '<input class="girdi" name="kim" list="kredi-kullanicilar" ' +
        'placeholder="Kullanıcı (e-posta)" aria-label="Kullanıcı">' +
        '<datalist id="kredi-kullanicilar">' + krediSecenekHtml +
        '</datalist>' +
        b.girdi('amount', 'Jeton', 'number') +
        b.girdi('reason', 'Gerekçe (zorunlu)') +
        '<button class="buton kucuk" type="submit">Kredi ver</button>' +
        '</div></form><p id="kredi-sonuc" class="dipnot"></p>',
        RY.ikon('kredi')) +
      b.modul('Bildirim nabzı',
        nabizHtml ? '<div class="satir-liste">' + nabizHtml + '</div>'
                  : b.bosDurum('Henüz koşu kaydı yok.'),
        b.etiket('son 2 gün')) +
      '</div></div>';

    /* ---- Hero durum makinesi (fetch'siz) ---- */

    var hero = { metrik: 'gelir', aralik: 30 };

    function heroCiz() {
      var m = METRIKLER[hero.metrik];
      var dilim = gunler.slice(-hero.aralik);
      var degerler = dilim.map(m.al);
      var sonDeger = degerler.length ? degerler[degerler.length - 1] : 0;
      var onceki = degerler.length > 1 ? degerler[degerler.length - 2] : null;

      document.getElementById('hero-deger').textContent =
        m.birim === '$' ? b.para(sonDeger) : b.sayi(sonDeger);
      document.getElementById('hero-alt').textContent =
        m.ad + ' — son gün (' + hero.aralik + ' günlük eğri)';
      document.getElementById('hero-delta').innerHTML =
        onceki == null ? '' : b.delta(sonDeger - onceki, m.birim);

      RY.grafik.cizgi(document.getElementById('g-hero'), {
        degerler: degerler,
        etiketler: dilim.map(function (g) { return g.date || ''; }),
        birim: m.birim, kalin: true
      });
    }

    document.getElementById('metrik-grup').onclick = function (ev) {
      var pil = ev.target.closest('[data-metrik]');
      if (!pil) return;
      hero.metrik = pil.getAttribute('data-metrik');
      this.querySelectorAll('.pil').forEach(function (p) {
        p.classList.toggle('aktif', p === pil);
      });
      heroCiz();
    };
    document.getElementById('aralik-grup').onclick = function (ev) {
      var pil = ev.target.closest('[data-aralik]');
      if (!pil) return;
      hero.aralik = parseInt(pil.getAttribute('data-aralik'), 10);
      this.querySelectorAll('.pil').forEach(function (p) {
        p.classList.toggle('aktif', p === pil);
      });
      heroCiz();
    };
    heroCiz();

    /* ---- Satır tıklamaları + hızlı kredi + topla ---- */

    icerik.querySelectorAll('.satir[data-uid]').forEach(function (s) {
      s.onclick = function () {
        location.hash = '#/kullanicilar/' +
          encodeURIComponent(s.getAttribute('data-uid'));
      };
    });

    document.getElementById('hizli-kredi').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      var sonucEl = document.getElementById('kredi-sonuc');
      var kim = (f.kim.value || '').trim().toLowerCase();
      var tutar = parseInt(f.amount.value, 10);
      var gerekce = (f.reason.value || '').trim();
      var hedef = (eko && eko.users || []).find(function (k) {
        return (k.email || '').toLowerCase() === kim ||
          k.uid === f.kim.value.trim();
      });
      if (!hedef) { sonucEl.textContent = 'Kullanıcı bulunamadı — listeden seç.'; return; }
      if (!tutar || tutar <= 0 || gerekce.length < 3) {
        sonucEl.textContent = 'Pozitif jeton + en az 3 karakter gerekçe zorunlu.';
        return;
      }
      if (!confirm((hedef.displayName || hedef.email) + ' → +' + tutar +
                   ' jeton: "' + gerekce + '" — onaylıyor musun?')) return;
      var dugme = f.querySelector('button');
      dugme.disabled = true;
      try {
        await RY.post('/api/v1/admin/users/' +
          encodeURIComponent(hedef.uid) + '/credit',
          { amount: tutar, reason: gerekce });
        sonucEl.textContent = '✓ ' + tutar + ' jeton verildi.';
        f.reset();
      } catch (h) {
        sonucEl.textContent = RY.hataMetni(h);
      }
      dugme.disabled = false;
    };

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
