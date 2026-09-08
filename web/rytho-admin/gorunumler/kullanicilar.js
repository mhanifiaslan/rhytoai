/* Kullanıcılar: aramalı liste + Kullanıcı 360 (destek ekranı).
   Rotalar: #/kullanicilar → liste, #/kullanicilar/{uid} → 360.
   Uçlar: /admin/users, /admin/users/{uid}, /admin/users/{uid}/credit,
   /admin/stats (dağılım grafikleri).

   Mahremiyet: sunucu sohbet/hafıza İÇERİĞİ ve fcmToken değeri zaten
   döndürmez; bu ekran yalnız sayıları ve destek verisini çizer. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  var BURC = { aries: '♈', taurus: '♉', gemini: '♊', cancer: '♋',
               leo: '♌', virgo: '♍', libra: '♎', scorpio: '♏',
               sagittarius: '♐', capricorn: '♑', aquarius: '♒',
               pisces: '♓' };

  function burc(kod) {
    if (!kod) return '';
    return BURC[String(kod).toLowerCase()] || '';
  }

  /* ---- Liste ---- */

  async function liste(icerik, sorgu, siralama) {
    var b = RY.b;
    var yol = '/api/v1/admin/users?limit=100' +
      (sorgu ? '&query=' + encodeURIComponent(sorgu) : '') +
      (siralama ? '&sort=' + encodeURIComponent(siralama) : '');
    var veri = await RY.get(yol);
    var stats = await RY.get('/api/v1/admin/stats?days=1')
      .catch(function () { return { days: [] }; });
    var u = ((stats.days || [])[0] || {}).users || {};
    var satirlar = (veri.users || []).map(function (k) {
      var basHarf = String(k.displayName || k.email || '?')
        .trim().charAt(0).toUpperCase();
      return '<tr class="tikla" data-uid="' + b.e(k.uid) + '">' +
        '<td><div class="hucre-kisi">' +
        '<div class="avatar-hucre">' + b.e(basHarf) + '</div>' +
        '<div><b>' + b.e(k.displayName || '—') + ' ' + burc(k.sunSign) +
        '</b><span>' + b.e(k.email || '') + '</span></div></div></td>' +
        '<td>' + (k.username ? '@' + b.e(k.username) : '—') + '</td>' +
        '<td class="sayi">' + b.tarih(k.createdAt) + '</td>' +
        '<td class="sayi">' + b.e(k.lastSeenDaily || '—') + '</td>' +
        '<td class="sayi">' + b.sayi(k.streakCount || 0) + '</td>' +
        '<td>' + b.e(k.language || '—') + '</td>' +
        '<td>' + b.e(k.platform || '—') + '</td>' +
        '<td>' + (k.hasPush ? b.rozet('push', 'aktif')
                            : b.rozet('yok', 'notr')) + '</td>' +
        '</tr>';
    }).join('');

    icerik.innerHTML =
      '<div class="panel">' +
      '<div class="form-satir" style="margin-top:0">' +
      '<input class="girdi girdi-genis" id="ara" placeholder="Ara: e-posta, ' +
      'kullanıcı adı, görünen ad (önek)" value="' + b.e(sorgu || '') +
      '" aria-label="Kullanıcı ara">' +
      '<select class="girdi" id="sirala" aria-label="Sıralama">' +
      '<option value="createdAt">Kayıt tarihi</option>' +
      '<option value="lastSeenDaily">Son görülme</option>' +
      '<option value="streakCount">Seri</option>' +
      '</select></div>' +
      (satirlar
        ? b.tablo(['Kullanıcı', 'Kullanıcı adı', 'Kayıt',
                   'Son görülme', 'Seri', 'Dil', 'Platform', 'Push'],
                  satirlar)
        : b.bosDurum(sorgu
            ? '"' + sorgu + '" ile eşleşen kullanıcı yok.'
            : 'Henüz kullanıcı yok.')) +
      '</div>' +
      '<div class="izgara-3">' +
      b.grafikPanel('g-dil', 'Dil dağılımı', true) +
      b.grafikPanel('g-platform', 'Platform', true) +
      b.grafikPanel('g-seri', 'Seri kovaları', true) +
      '</div>';

    if (siralama) document.getElementById('sirala').value = siralama;

    RY.grafik.cubuk(document.getElementById('g-dil'), u.byLanguage || {});
    RY.grafik.cubuk(document.getElementById('g-platform'),
      u.byPlatform || {});
    RY.grafik.cubuk(document.getElementById('g-seri'),
      u.streakBuckets || {});

    icerik.querySelectorAll('tr[data-uid]').forEach(function (tr) {
      tr.onclick = function () {
        location.hash = '#/kullanicilar/' +
          encodeURIComponent(tr.getAttribute('data-uid'));
      };
    });

    var ara = document.getElementById('ara');
    var bekleyici = null;
    ara.oninput = function () {
      clearTimeout(bekleyici);
      bekleyici = setTimeout(function () {
        liste(icerik, ara.value.trim(),
              document.getElementById('sirala').value);
      }, 300);
    };
    document.getElementById('sirala').onchange = function () {
      liste(icerik, ara.value.trim(), this.value);
    };
    ara.focus();
  }

  /* ---- Kullanıcı 360 ---- */

  function zamanCizelgesi(d) {
    var b = RY.b;
    var olaylar = [];

    (d.ledger || []).forEach(function (k) {
      var tur = k.type;
      if (tur === 'debit') {
        olaylar.push({ at: k.at, sinif: '',
          metin: '<b>−' + b.sayi(k.amount) + ' jeton</b> · ' +
            b.e(k.feature || '?') });
      } else if (tur === 'credit') {
        olaylar.push({ at: k.at, sinif: 'altin',
          metin: '<b>+' + b.sayi(k.amount) + ' jeton</b> · paket ' +
            b.e(k.productId || '') });
      } else if (tur === 'promo') {
        olaylar.push({ at: k.at, sinif: 'altin',
          metin: '<b>+' + b.sayi(k.amount) + ' jeton</b> · kod ' +
            b.e(k.code || '') });
      } else if (tur === 'admin') {
        olaylar.push({ at: k.at, sinif: 'lilac',
          metin: '<b>+' + b.sayi(k.amount) + ' jeton</b> · yönetici (' +
            b.e(k.reason || '') + ')' });
      } else if (tur === 'refund') {
        olaylar.push({ at: k.at, sinif: 'madder',
          metin: '<b>−' + b.sayi(k.amount) + ' jeton</b> · paket iadesi' });
      } else if (tur === 'spend_refund') {
        olaylar.push({ at: k.at, sinif: 'altin',
          metin: '<b>+' + b.sayi(k.amount) + ' jeton</b> · üretim iadesi (' +
            b.e(k.feature || '') + ')' });
      }
    });

    (d.revenueEvents || []).forEach(function (o) {
      var iade = o.eventType === 'REFUND';
      olaylar.push({ at: o.at, sinif: iade ? 'madder' : 'altin',
        metin: '<b>' + b.e(o.eventType) + '</b> · ' +
          b.e(o.productId || '') + ' · ' + b.para(o.price) });
    });

    var kayit = (d.profile || {}).createdAt;
    if (kayit) {
      olaylar.push({ at: kayit, sinif: 'lilac',
        metin: '<b>Yıldız haritasına katıldı</b> — hesap oluşturuldu' });
    }

    function ts(v) {
      if (!v) return 0;
      if (typeof v === 'string') return new Date(v).getTime() || 0;
      if (v.seconds != null) return v.seconds * 1000;
      return new Date(v).getTime() || 0;
    }
    olaylar.sort(function (a, c) { return ts(c.at) - ts(a.at); });

    if (!olaylar.length) return RY.b.bosDurum('Henüz hareket yok.');
    return '<ol class="zaman-cizelgesi">' +
      olaylar.slice(0, 60).map(function (o) {
        return '<li><span class="nokta ' + o.sinif + '"></span>' +
          '<span class="zaman">' + b.tarih(o.at, true) + '</span>' +
          o.metin + '</li>';
      }).join('') + '</ol>';
  }

  async function detay(icerik, uid) {
    var b = RY.b;
    var d = await RY.get('/api/v1/admin/users/' + encodeURIComponent(uid));
    var p = d.profile || {}, sub = d.subscription || {};
    var w = d.wallet || {}, kul = d.usage || {}, sayilar = d.counts || {};
    var bild = d.notifications || {}, kota = d.quota || {};

    var basHarf = (p.displayName || p.email || '?').trim().charAt(0)
      .toUpperCase();

    var bildSatir = Object.keys(bild).filter(function (k) {
      return k.endsWith('LastSent');
    }).map(function (k) {
      return '<tr><td>' + b.e(k.replace('LastSent', '')) + '</td>' +
        '<td class="sayi">' + b.e(bild[k]) + '</td></tr>';
    }).join('');

    var kotaSatir = Object.keys(kota).filter(function (k) {
      return k !== 'date' && k !== 'resetAtUtc';
    }).map(function (k) {
      return '<tr><td>' + b.e(k) + '</td><td class="sayi">' +
        b.sayi(kota[k]) + '</td></tr>';
    }).join('');

    icerik.innerHTML =
      '<a class="geri-lnk" href="#/kullanicilar">← Kullanıcı listesi</a>' +
      '<div class="kimlik-serit">' +
      '<div class="avatar">' + b.e(basHarf) + '</div>' +
      '<div><div class="ad">' + b.e(p.displayName || '—') + ' ' +
      burc(p.sunSign) + '</div>' +
      '<div class="mono">' + b.e(p.email || '') + ' · ' + b.e(uid) +
      '</div></div>' +
      '<div class="rozetler">' +
      (p.authDisabled === true ? b.rozet('DEVRE DIŞI', 'hata') : '') +
      b.abonelikRozeti(sub, p) +
      (p.platform ? b.rozet(p.platform, 'notr') : '') +
      (p.hasPush ? b.rozet('push açık', 'aktif') : b.rozet('push yok', 'notr')) +
      (p.onboardingCompleted ? '' : b.rozet('onboarding yarım', 'hata')) +
      '</div></div>' +

      '<div class="izgara-3">' +

      '<div class="panel"><h2>Abonelik</h2>' +
      b.tablo(['', ''],
        '<tr><td>Ürün</td><td class="sayi">' + b.e(sub.productId || '—') +
        '</td></tr>' +
        '<tr><td>Mağaza</td><td class="sayi">' + b.e(sub.store || '—') +
        '</td></tr>' +
        '<tr><td>Bitiş</td><td class="sayi">' + b.tarih(sub.expiresAt) +
        '</td></tr>' +
        '<tr><td>Yenilenecek mi</td><td class="sayi">' +
        (sub.willRenew == null ? '—' : (sub.willRenew ? 'evet' : 'hayır')) +
        '</td></tr>' +
        '<tr><td>Son olay</td><td class="sayi">' + b.e(sub.lastEvent || '—') +
        '</td></tr>') + '</div>' +

      '<div class="panel"><h2>Cüzdan</h2>' +
      '<div class="kpi-deger">' +
      b.sayi((w.allowance || 0) + (w.purchased || 0)) +
      ' <span class="kpi-ad" style="display:inline">jeton</span></div>' +
      '<p class="dipnot">Aylık hak: ' + b.sayi(w.allowance || 0) +
      ' · Satın alınan: ' + b.sayi(w.purchased || 0) + '</p>' +
      '<form id="kredi-form" class="form-satir">' +
      b.girdi('amount', 'Jeton', 'number') +
      b.girdi('reason', 'Gerekçe (zorunlu)', null, 'girdi-genis') +
      '<button class="buton ikincil kucuk" type="submit">Kredi ver</button>' +
      '</form>' +
      '<p class="dipnot">Defter + denetim izine yazılır; yalnız pozitif.</p>' +
      '</div>' +

      '<div class="panel"><h2>Kullanım</h2>' +
      '<div class="kpi-deger">' + b.sayi(kul.calls || 0) +
      ' <span class="kpi-ad" style="display:inline">AI çağrısı</span></div>' +
      '<p class="dipnot">Tahmini maliyet: ' + b.para(kul.estCostUsd || 0) +
      ' · Konuşma: ' + b.sayi(sayilar.conversations) +
      ' · Arkadaş: ' + b.sayi(sayilar.friends) + '</p>' +
      '<div class="grafik-kap"><canvas id="g-360-ozellik" ' +
      'class="grafik grafik-kisa" role="img" ' +
      'aria-label="Özellik kırılımı"></canvas></div></div>' +

      // SMS-turu: "kod gelmiyor" başvurusunda ilk bakılacak yer. Google
      // teslim makbuzu yayınlamadığı için bizim tarafımızdaki tek iz bu.
      '<div class="panel"><h2>Telefon denemeleri</h2>' +
      (function () {
        var liste = d.phoneAttempts || [];
        if (!liste.length) {
          return '<p class="dipnot" style="margin-top:0">Kayıt yok.</p>';
        }
        var ASAMA = {
          sent: ['bildirim', 'Kod gönderildi'],
          auto: ['kivilcim', 'Otomatik doğrulandı'],
          verified: ['kayit', 'Doğrulandı'],
          failed: ['sistem', 'Hata']
        };
        return '<div class="satir-liste">' + liste.map(function (a) {
          var m = ASAMA[a.stage] || ['kivilcim', a.stage || '—'];
          return b.satir({
            ikon: m[0],
            baslik: m[1],
            alt: (a.masked || '—') + ' · ' + (a.iso2 || '—') +
              (a.code ? ' · ' + a.code : ''),
            sagAlt: b.tarih(a.at, true),
            ikonSinif: a.stage === 'failed' ? 'eksi' : ''
          });
        }).join('') + '</div>' +
        '<p class="dipnot">Numara maskeli tutulur; ham numara hiçbir ' +
        'yere yazılmaz.</p>';
      })() + '</div>' +

      '</div>' +

      '<div class="izgara-2">' +
      '<div class="panel"><h2>Bu kullanıcının ekonomisi</h2>' +
      (function () {
        var ek = d.economics || {};
        return '<div class="marj-formul" style="margin-top:4px">' +
          '<div class="kalem"><b>' + b.para(ek.revenueUsd) +
          '</b><span>Toplam gelir</span></div>' +
          '<div class="kalem"><b>−' + b.para(ek.aiCostUsd) +
          '</b><span>AI maliyeti (' + b.sayi(ek.calls) +
          ' çağrı)</span></div>' +
          '<div class="kalem"><b class="' +
          ((ek.marginUsd || 0) < 0 ? 'eksi' : 'arti') + '">' +
          b.para(ek.marginUsd) + '</b><span>Tahmini marj</span></div>' +
          '</div>' +
          '<p class="dipnot">Marj = gelir × (1 − mağaza ~%' +
          Math.round((ek.storeCutRate || 0.15) * 100) +
          ') − AI maliyeti; tüm zamanlar.</p>';
      })() + '</div>' +
      '<div class="panel"><h2>Yönetim</h2>' +
      '<p class="dipnot" style="margin-top:0">Her eylem gerekçe ister ve ' +
      'denetim izine yazılır.</p>' +
      '<div class="eylem-satir">' +
      '<button id="y-sifre" class="buton ikincil kucuk">Şifre sıfırlama ' +
      'e-postası gönder</button>' +
      '<button id="y-durum" class="buton ikincil kucuk">' +
      (p.authDisabled === true ? 'Hesabı aktifleştir'
                               : 'Hesabı devre dışı bırak') + '</button>' +
      '<button id="y-sil" class="buton tehlike kucuk">Hesabı sil</button>' +
      '</div><p id="y-mesaj" class="dipnot"></p></div>' +
      '</div>' +
      '<div class="izgara-2">' +
      '<div class="panel"><h2>Bildirimler</h2>' +
      (bild.dailyTheme
        ? '<p class="dipnot" style="margin-top:0">Bugünkü tema: <b>' +
          b.e(bild.dailyTheme) + '</b></p>' : '') +
      (bildSatir ? b.tablo(['Tür', 'Son gönderim'], bildSatir)
                 : b.bosDurum('Gönderim kaydı yok.')) + '</div>' +
      '<div class="panel"><h2>Günlük kota</h2>' +
      (kotaSatir ? b.tablo(['Sayaç', 'Bugün'], kotaSatir)
                 : b.bosDurum('Bugün sayaç yok.')) +
      (d.attribution && d.attribution.code
        ? '<p class="dipnot">Ortak kodu: <b>' + b.e(d.attribution.code) +
          '</b></p>' : '') +
      '</div></div>' +

      '<div class="panel"><h2>Zaman çizelgesi</h2>' +
      zamanCizelgesi(d) + '</div>';

    RY.grafik.cubuk(document.getElementById('g-360-ozellik'),
      (kul.byFeature || {}));
    b.canlandir(icerik);

    /* ---- Yönetim eylemleri (AP2) ---- */
    function yMesaj(metin) {
      document.getElementById('y-mesaj').textContent = metin || '';
    }

    document.getElementById('y-sifre').onclick = function () {
      if (!p.email) { yMesaj('Hesabın e-postası yok.'); return; }
      if (!confirm(p.email + ' adresine şifre sıfırlama e-postası ' +
                   'gönderilsin mi?')) return;
      // İstemci SDK'sı yeter: sıfırlama isteği herkese açık bir akıştır,
      // sunucuya uç eklemek gerekmez.
      RY.auth.sendPasswordResetEmail(p.email)
        .then(function () { yMesaj('Sıfırlama e-postası gönderildi.'); })
        .catch(function () { yMesaj('Gönderilemedi — sonra tekrar dene.'); });
    };

    document.getElementById('y-durum').onclick = async function () {
      var kapat = p.authDisabled !== true;
      var gerekce = prompt(kapat
        ? 'Hesap DEVRE DIŞI kalacak, oturumları düşecek. Gerekçe (zorunlu):'
        : 'Hesap yeniden AKTİF olacak. Gerekçe (zorunlu):');
      if (gerekce == null) return;
      if (gerekce.trim().length < 3) { yMesaj('Gerekçe en az 3 karakter.'); return; }
      this.disabled = true;
      try {
        await RY.post('/api/v1/admin/users/' + encodeURIComponent(uid) +
          '/disable', { disabled: kapat, reason: gerekce.trim() });
        detay(icerik, uid);
      } catch (h) {
        this.disabled = false;
        yMesaj(RY.hataMetni(h));
      }
    };

    document.getElementById('y-sil').onclick = async function () {
      var onay = prompt('Bu hesap ve TÜM verisi kalıcı olarak silinecek ' +
        '(mobildeki "Hesabı sil" ile aynı boru). Onaylamak için SIL yaz:');
      if (onay == null) return;
      if (onay.trim() !== 'SIL') { yMesaj('Silme onaylanmadı.'); return; }
      var gerekce = prompt('Silme gerekçesi (zorunlu, denetim izine yazılır):');
      if (gerekce == null || gerekce.trim().length < 3) {
        yMesaj('Gerekçe en az 3 karakter.');
        return;
      }
      this.disabled = true;
      try {
        await RY.del('/api/v1/admin/users/' + encodeURIComponent(uid),
          { confirm: 'SIL', reason: gerekce.trim() });
        location.hash = '#/kullanicilar';
      } catch (h) {
        this.disabled = false;
        yMesaj(RY.hataMetni(h));
      }
    };

    document.getElementById('kredi-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      var tutar = parseInt(f.amount.value, 10);
      var gerekce = (f.reason.value || '').trim();
      if (!tutar || tutar <= 0 || gerekce.length < 3) {
        alert('Pozitif jeton tutarı ve en az 3 karakterlik gerekçe zorunlu.');
        return;
      }
      if (!confirm(tutar + ' jeton verilecek: "' + gerekce + '" — onaylıyor musun?')) {
        return;
      }
      var dugme = f.querySelector('button');
      dugme.disabled = true;
      try {
        await RY.post('/api/v1/admin/users/' + encodeURIComponent(uid) +
          '/credit', { amount: tutar, reason: gerekce });
        detay(icerik, uid);
      } catch (h) {
        dugme.disabled = false;
        alert(RY.hataMetni(h));
      }
    };
  }

  RY.gorunumler.kullanicilar = async function (icerik, args) {
    // Rota sözleşmesi: /kullanicilar → liste; /kullanicilar/ara/<q> →
    // sorgulu liste (üst çubuktaki global arama); /kullanicilar/<uid> → 360.
    if (args && args[0] === 'ara') {
      return liste(icerik, args[1] || '', 'createdAt');
    }
    if (args && args[0]) return detay(icerik, args[0]);
    return liste(icerik, '', 'createdAt');
  };
})();
