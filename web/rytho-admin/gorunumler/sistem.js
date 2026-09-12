/* Sistem (AD10/AD19): sağlık kartları, rollup tazeliği, zamanlayıcı son
   koşuları, indeks yoklaması, build; zorunlu güncelleme eşiği (owner),
   panel duyurusu (owner), denetim izi (süzgeç + imleç), "Topla" (owner).

   Rota: #/sistem (parametre yok).
   Uçlar:
   - GET  /api/v1/admin/system → {health:{firestore, fcm, rag:{healthy,
     bases:{dil:{mode, chunks, artifact}}}}, rollups:{lastStatsDate,
     lastStatsAt, lastStatsMs, lastEconomicsDate}, scheduler:{notify:{tür:
     {lastRunAt, lastStatus, date}}, stats:{lastRunAt}}, indexes:[{name, ok,
     error}], build:{revision, service, startedAt}, config:{minBuild,
     envFloor, notice}}
   - GET  /health (herkese açık) → backend ayakta mı + revizyon
   - GET  /api/v1/admin/min-build → {min_build, env_floor, doc, below_min_live}
   - GET  /api/v1/admin/stats?days=1 → days[0].builds {byBuild, unknown}
   - POST /api/v1/admin/min-build {min_build, reason} (owner; K9: 400
     "eşiğin üstünde kullanıcı görülmedi" mesajı olduğu gibi)
   - POST /api/v1/admin/config/notice {text, level} (owner; boş = kaldır)
   - GET  /api/v1/admin/audit?action&adminUid&targetUid&from&to&limit&cursor
     → {entries:[…], nextCursor}
   - POST /api/v1/admin/collect (owner)

   Nav sayacı RY.dikkat'ten gelir (app.js) — burada tekrarlanmaz. Ham JSON
   basılmaz; her bölüm kendi tablosuyla. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  var ROLLUP_BAYAT_SAAT = 30;
  var DENETIM_SAYFA = 50;

  var NOTIFY_TURLERI = { daily: 'Günlük (sabah)', midday: 'Öğle', checkin: 'Check-in', streak: 'Seri' };

  /* Bilinen denetim eylemleri (api/admin.py `_audit` çağrıları). */
  var EYLEMLER = [
    ['user.credit', 'Kredi'], ['user.disable', 'Devre dışı bırak'], ['user.enable', 'Devreye al'],
    ['user.delete', 'Hesap sil'], ['user.auth_link', 'Kimlik bağlantısı'],
    ['device.release', 'Cihaz kilidi sıfırla'], ['config.min_build', 'Eşik yaz'],
    ['config.notice', 'Duyuru'], ['notify.dry_run', 'Bildirim provası'],
    ['notify.test_send', 'Test bildirimi'], ['partner.create', 'Ortak ekle'],
    ['partner.update', 'Ortak güncelle'], ['partner.code', 'Ortak kodu'],
    ['partner.payout', 'Ortak ödemesi'], ['export.users', 'CSV: kullanıcılar'],
    ['export.revenue', 'CSV: gelir'], ['stats.collect', 'Topla'],
    ['stats.recompute', 'Yeniden hesapla']
  ];
  var EYLEM_ADI = {};
  EYLEMLER.forEach(function (x) { EYLEM_ADI[x[0]] = x[1]; });
  function eylemTuru(a) {
    if (/delete|disable/.test(a)) return 'hata';
    if (/min_build|payout|export|recompute/.test(a)) return 'uyari';
    if (/credit|enable|create|code/.test(a)) return 'altin';
    return 'notr';
  }

  function hataToast(h) {
    var m = RY.hataMetni(h);
    if (m) RY.b.toast(m, 'hata');
  }

  function durumRozeti(b, v, evet, hayir, bilinmiyor) {
    if (v === true) return b.rozet(evet || 'Sağlıklı', 'aktif');
    if (v === false) return b.rozet(hayir || 'Sorun', 'hata');
    return b.rozet(bilinmiyor || 'Bilinmiyor', 'notr');
  }

  function saatFarki(b, v) {
    var d = b.tarihNesnesi(v);
    return d ? (Date.now() - d.getTime()) / 3600000 : null;
  }

  /* ---------------- Zorunlu güncelleme modülü (v2 mantığı korunur) ----------------
     İki kaynak, iki etiket: `mb` (/admin/min-build) CANLI — etkin eşik, env
     tabanı, count() ile "eşiğin altında"; `builds` (adminStats.builds)
     GECELİK — sürüm kırılımı ve başlık göndermeyen ≤34 istemcilerin
     "bilinmiyor" sayısı. Canlı sayım alanı olmayanları görmez, o yüzden
     "bilinmiyor" ayrı KPI'dır. */
  function esikCiz(kap, mb, builds) {
    var b = RY.b;
    var esik = mb ? mb.min_build : null;
    var dokuman = (mb && mb.doc) || null;
    var byBuild = (builds && builds.byBuild) || {};
    var kapiAcik = esik != null && esik > 0;
    var sahip = RY.sahipMi();

    var sonYazim = dokuman && dokuman.minBuild != null
      ? 'Son yazım: eşik ' + b.sayi(dokuman.minBuild) + ' — "' + (dokuman.reason || '') + '" · ' +
        (dokuman.updatedBy || '?') + ' · ' + b.tarih(dokuman.updatedAt, true)
      : (mb ? 'Henüz panelden yazılmadı — eşik yalnız env tabanından.' : 'Eşik durumu alınamadı.');

    kap.innerHTML =
      '<section class="izgara-kpi" aria-label="Eşik durumu">' +
      b.istatistikKarti({ ad: 'Etkin eşik', deger: mb ? b.sayi(esik) : '—', altin: kapiAcik,
        alt: kapiAcik ? 'X-App-Build < eşik → 426' : 'kapı kapalı (0)' }) +
      b.istatistikKarti({ ad: 'Env tabanı', deger: mb ? b.sayi(mb.env_floor) : '—',
        alt: 'RYTHO_MIN_BUILD · isteğe bağlı' }) +
      b.istatistikKarti({ ad: 'Eşiğin altında (canlı)', deger: mb ? b.sayi(mb.below_min_live) : '—',
        alt: 'appBuild < eşik · count()' }) +
      b.istatistikKarti({ ad: 'Bilinmiyor (≤34)', deger: builds ? b.sayi(builds.unknown) : '—',
        alt: 'başlık göndermeyen · son toplama' }) +
      '</section>' +
      '<div id="esik-tablo"></div>' +
      '<p class="dipnot">' + b.e(sonYazim) + '</p>' +
      (sahip ? '<div id="esik-form"></div>' : '<p class="dipnot">Eşiği yalnız sahip yazar.</p>') +
      '<p class="dipnot">Sunucu 0\'dan büyük eşiği ancak o sürümü canlı görmüşse kabul eder (K9): ' +
      'önce yeni sürümü bir cihazda açıp giriş yap. Sıra: rules → backend → AAB mağazada → eşik ' +
      '(docs/konsol-gorevleri.md §6).</p>';

    var satirlar = Object.keys(byBuild).map(function (s) {
      return { surum: s, sira: Number(s), kullanici: Number(byBuild[s]) || 0,
               altinda: kapiAcik && Number(s) < esik, bilinmiyor: false };
    });
    if (builds && builds.unknown > 0) {
      satirlar.push({ surum: 'bilinmiyor (≤34)', sira: -1, kullanici: Number(builds.unknown),
                      altinda: kapiAcik, bilinmiyor: true });
    }
    var vt = b.veriTablosu({
      kimlik: 'esik-surum-tablo', etiket: 'Sürüm kırılımı', yogunluk: 'sik',
      sutunlar: [
        { ad: 'sira', baslik: 'Sürüm (versionCode)', siralanir: true,
          bicim: function (s) { return '<span class="mono">' + b.e(s.surum) + '</span>'; } },
        { ad: 'kullanici', baslik: 'Kullanıcı', hizala: 'sag', siralanir: true },
        { ad: 'altinda', baslik: 'Durum', deger: function (s) { return s.altinda ? 1 : 0; },
          bicim: function (s) {
            if (!s.altinda) return b.rozet('geçer', 'aktif');
            return b.rozet(s.bilinmiyor ? 'kilitli (başlıksız)' : 'eşiğin altında', 'hata');
          } }
      ],
      anahtar: function (s) { return s.surum; },
      satirSinif: function (s) { return s.altinda ? 'durum-hata' : ''; },
      siralama: { ad: 'sira', yon: 'desc' },
      bosMetin: 'Henüz sürüm aynası yok — 35+ istemcinin ilk kimlikli isteğiyle dolar, gecelik toplamayla görünür.'
    });
    kap.querySelector('#esik-tablo').appendChild(vt.el);
    vt.guncelle(satirlar);

    if (!sahip) return;
    var f = b.form({
      alanlar: [
        { ad: 'min_build', etiket: 'Yeni eşik', tur: 'number', zorunlu: true, min: 0, max: 100000,
          adim: '1', deger: esik != null ? esik : 0, yardim: 'versionCode; 0 = kapıyı kapat' },
        { ad: 'reason', etiket: 'Gerekçe', tur: 'textarea', zorunlu: true, max: 300, satir: 2,
          yardim: 'Denetim izine yazılır (en az 3 karakter).',
          dogrula: function (v) { return v.length < 3 ? 'En az 3 karakter.' : null; } }
      ],
      gonderMetin: 'Eşiği yaz',
      onGonder: function (d) {
        var yeni = Math.round(Number(d.min_build));
        var soru = yeni > 0
          ? { baslik: 'Eşiği ' + yeni + ' yap', tehlike: true, onaylaMetin: 'Eşiği yaz',
              mesaj: 'X-App-Build < ' + yeni + ' olan HER istek 426 alır — başlık göndermeyen ' +
                'eski istemciler (≤34) dahil. Bu istemciler güncelleme ekranına kilitlenir.',
              aciklama: 'Gerekçe: "' + d.reason + '"' }
          : { baslik: 'Kapıyı kapat', onaylaMetin: 'Kapat',
              mesaj: 'Eşik 0 olacak; env tabanı varsa o geçerli kalır.',
              aciklama: 'Gerekçe: "' + d.reason + '"' };
        return b.onayla(soru).then(function (r) {
          if (!r) { var h = new Error('iptal'); h.iptal = true; throw h; }
          return RY.post('/api/v1/admin/min-build', { min_build: yeni, reason: d.reason });
        }).then(function (res) {
          b.toast('Eşik yazıldı: ' + b.sayi(res && res.min_build != null ? res.min_build : yeni), 'basari');
          esikCiz(kap, res && res.min_build != null ? res : null, builds);
          if (RY.dikkat && RY.dikkat.yukle) RY.dikkat.yukle();
          var h1 = kap.closest('.modul') && kap.closest('.modul').querySelector('h2');
          if (h1) h1.focus();
        });
        // 400 (K9) ve 503 (denetim izi) mesajları form özetine olduğu gibi düşer.
      }
    });
    kap.querySelector('#esik-form').appendChild(f.el);
  }

  /* ---------------- Duyuru ---------------- */

  function duyuruBant(b, notice) {
    if (!notice || !notice.text) return '';
    var tur = notice.level === 'warn' ? 'uyari' : 'bilgi';
    return '<div id="sistem-duyuru">' + b.bant('<b>Panel duyurusu</b> — ' + b.e(notice.text) +
      (notice.updatedAt ? ' <span class="dipnot">(' + b.e(b.tarih(notice.updatedAt, true)) + ')</span>' : ''),
      tur, { html: true }) + '</div>';
  }

  function duyuruModulu(icerik, notice) {
    var b = RY.b;
    var kap = icerik.querySelector('#duyuru-form');
    if (!kap) return;
    var f = b.form({
      alanlar: [
        { ad: 'text', etiket: 'Metin', tur: 'textarea', max: 300, satir: 2,
          deger: notice && notice.text ? notice.text : '',
          yardim: 'Boş kaydedersen duyuru kalkar. Mobil bunu OKUMAZ — yalnız panel.' },
        { ad: 'level', etiket: 'Seviye', tur: 'select',
          secenekler: [{ deger: 'info', etiket: 'Bilgi' }, { deger: 'warn', etiket: 'Uyarı' }],
          deger: notice && notice.level ? notice.level : 'info' }
      ],
      gonderMetin: 'Duyuruyu kaydet',
      onGonder: function (d) {
        return RY.post('/api/v1/admin/config/notice', { text: d.text || '', level: d.level })
          .then(function (res) {
            var yeni = res && res.notice;
            var eski = icerik.querySelector('#sistem-duyuru');
            if (eski) eski.remove();
            if (yeni && yeni.text) {
              var bas = icerik.querySelector('.sayfa-bas');
              if (bas) bas.insertAdjacentHTML('afterend', duyuruBant(b, yeni));
            }
            b.toast(yeni && yeni.text ? 'Duyuru güncellendi.' : 'Duyuru kaldırıldı.', 'basari');
          });
      }
    });
    kap.appendChild(f.el);
  }

  /* ---------------- Denetim izi ---------------- */

  function ayrintiHtml(b, k) {
    var params = k.params && typeof k.params === 'object' ? k.params : {};
    var parcalar = Object.keys(params).filter(function (a) {
      var v = params[a];
      return v !== null && v !== undefined && v !== '' && typeof v !== 'object';
    }).map(function (a) {
      var v = String(params[a]);
      if (v.length > 80) v = v.slice(0, 77) + '…';
      return '<span>' + b.e(a) + '<b>' + b.e(v) + '</b></span>';
    });
    Object.keys(params).forEach(function (a) {
      var v = params[a];
      if (v && typeof v === 'object') {
        var ic = Object.keys(v).filter(function (x) { return v[x] != null && v[x] !== ''; })
          .map(function (x) { return x + '=' + v[x]; }).join(', ');
        if (ic) parcalar.push('<span>' + b.e(a) + '<b>' + b.e(ic.length > 80 ? ic.slice(0, 77) + '…' : ic) + '</b></span>');
      }
    });
    if (k.error) parcalar.push('<span>hata<b>' + b.e(String(k.error).slice(0, 80)) + '</b></span>');
    return parcalar.length ? '<span class="ayrinti-liste">' + parcalar.join('') + '</span>' : '—';
  }

  function hedefHtml(b, k) {
    if (k.targetUid) {
      return '<a class="mono" href="' + b.e(RY.rotaBagi('kullanicilar', [k.targetUid])) + '">' +
        b.e(k.targetUid) + '</a>';
    }
    var p = k.params || {};
    if (p.partnerId) {
      return '<a class="mono" href="' + b.e(RY.rotaBagi('ortaklar', [p.partnerId])) + '">ortak ' +
        b.e(String(p.partnerId).slice(0, 8)) + '</a>';
    }
    return '<span class="dipnot">—</span>';
  }

  function denetimKur(icerik) {
    var b = RY.b;
    var kap = icerik.querySelector('#denetim-kap');
    if (!kap) return;
    var suzgec = { action: '', adminUid: '', targetUid: '', from: '', to: '' };
    var imlec = null;

    var secenekler = '<option value="">Tümü</option>' + EYLEMLER.map(function (x) {
      return '<option value="' + b.e(x[0]) + '">' + b.e(x[1]) + ' · ' + b.e(x[0]) + '</option>';
    }).join('');
    kap.innerHTML =
      '<form class="form-satir suzgec-form" id="denetim-suzgec" novalidate>' +
      '<div class="form-alan"><label for="dz-action">Eylem</label>' +
      '<select class="girdi" id="dz-action">' + secenekler + '</select></div>' +
      '<div class="form-alan"><label for="dz-action-serbest">Eylem (serbest)</label>' +
      '<input class="girdi girdi-kisa" id="dz-action-serbest" placeholder="ör. user.x" maxlength="60" autocomplete="off"></div>' +
      '<div class="form-alan"><label for="dz-admin">Yönetici uid</label>' +
      '<input class="girdi" id="dz-admin" maxlength="128" autocomplete="off" spellcheck="false"></div>' +
      '<div class="form-alan"><label for="dz-hedef">Hedef uid</label>' +
      '<input class="girdi" id="dz-hedef" maxlength="128" autocomplete="off" spellcheck="false"></div>' +
      '<div class="form-alan"><label for="dz-bas">Başlangıç</label>' +
      '<input class="girdi girdi-kisa" id="dz-bas" type="date"></div>' +
      '<div class="form-alan"><label for="dz-son">Bitiş (dahil)</label>' +
      '<input class="girdi girdi-kisa" id="dz-son" type="date"></div>' +
      '<div class="form-alan"><span class="form-etiket" aria-hidden="true">&nbsp;</span>' +
      '<span class="eylem-satir"><button type="submit" class="buton ikincil">' + b.ik('filtre', 16) +
      'Uygula</button><button type="button" class="buton sade" id="dz-temizle">Temizle</button></span></div>' +
      '</form>' +
      '<div id="denetim-tablo"></div>';

    var vt = b.veriTablosu({
      kimlik: 'denetim-vt', etiket: 'Denetim izi', yogunluk: 'sik',
      sutunlar: [
        { ad: 'at', baslik: 'Zaman',
          bicim: function (k) {
            return '<span class="mono" title="' + b.e(b.tarih(k.at, true)) + '">' +
              b.e(b.goreliZaman(k.at)) + '</span><span class="dipnot"> ' + b.e(b.tarih(k.at, true)) + '</span>';
          } },
        { ad: 'adminEmail', baslik: 'Yönetici',
          bicim: function (k) {
            return b.e(k.adminEmail || k.adminUid || '—') +
              (k.adminRole ? ' ' + b.rolRozeti(k.adminRole) : '');
          } },
        { ad: 'action', baslik: 'Eylem',
          bicim: function (k) {
            var a = String(k.action || '?');
            return b.rozet(EYLEM_ADI[a] || a, eylemTuru(a)) +
              (EYLEM_ADI[a] ? ' <span class="mono dipnot">' + b.e(a) + '</span>' : '');
          } },
        { ad: 'targetUid', baslik: 'Hedef', bicim: function (k) { return hedefHtml(b, k); } },
        { ad: 'phase', baslik: 'Faz',
          bicim: function (k) {
            if (!k.phase) return '<span class="dipnot">—</span>';
            var t = k.phase === 'done' ? 'aktif' : (k.phase === 'failed' ? 'hata' : 'uyari');
            var ad = k.phase === 'done' ? 'tamam' : (k.phase === 'failed' ? 'düştü' : 'niyet');
            return b.rozet(ad, t);
          } },
        { ad: 'params', baslik: 'Ayrıntı', bicim: function (k) { return ayrintiHtml(b, k); } }
      ],
      anahtar: function (k) { return k.id; },
      satirSinif: function (k) {
        if (k.phase === 'failed') return 'durum-hata';
        if (k.phase === 'intent') return 'durum-uyari';
        return '';
      },
      onSirala: function () { /* sunucu sıralı (at DESC) */ },
      bosMetin: 'Kayıt yok — süzgeci gevşet ya da ilk yazan admin eylemini bekle.',
      onTekrar: function () { yukle(false); }
    });
    kap.querySelector('#denetim-tablo').appendChild(vt.el);

    function yukle(devam) {
      if (!devam) { vt.durum('yukleniyor'); imlec = null; }
      var params = {
        action: suzgec.action, adminUid: suzgec.adminUid, targetUid: suzgec.targetUid,
        from: suzgec.from, to: suzgec.to, limit: DENETIM_SAYFA, cursor: devam ? imlec : null
      };
      return RY.sorgu('/api/v1/admin/audit', params).then(function (res) {
        var kayitlar = Array.isArray(res.entries) ? res.entries : [];
        imlec = res.nextCursor || null;
        var sayfa = { daha: !!imlec, onDaha: function () { return yukle(true); } };
        if (devam) vt.ekle(kayitlar, sayfa); else vt.guncelle(kayitlar, sayfa);
      }).catch(function (h) {
        if (h && h.iptal) return;
        if (devam) hataToast(h); else vt.durum('hata', RY.hataMetni(h));
      });
    }

    var form = kap.querySelector('#denetim-suzgec');
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var serbest = form.querySelector('#dz-action-serbest').value.trim();
      suzgec = {
        action: serbest || form.querySelector('#dz-action').value,
        adminUid: form.querySelector('#dz-admin').value.trim(),
        targetUid: form.querySelector('#dz-hedef').value.trim(),
        from: form.querySelector('#dz-bas').value,
        to: form.querySelector('#dz-son').value
      };
      if (suzgec.from && suzgec.to && suzgec.to < suzgec.from) {
        b.toast('Bitiş, başlangıçtan önce olamaz.', 'uyari');
        return;
      }
      yukle(false);
    });
    kap.querySelector('#dz-temizle').addEventListener('click', function () {
      form.reset();
      suzgec = { action: '', adminUid: '', targetUid: '', from: '', to: '' };
      yukle(false);
      form.querySelector('#dz-action').focus();
    });
    yukle(false);
  }

  /* ---------------- Topla (owner) ---------------- */

  function toplaAc() {
    var b = RY.b;
    return b.onayla({
      baslik: 'İstatistikleri şimdi topla',
      mesaj: 'Bugünün adminStats ve adminEconomics dokümanları canlı taramayla yeniden üretilir; ' +
        'gecelik işle aynıdır ve idempotenttir (aynı gün ezilir, birikmez).',
      aciklama: 'Binlerce kullanıcıda bir-iki dakika sürebilir; denetim izine düşer.',
      onaylaMetin: 'Topla'
    }).then(function (r) {
      if (!r) return null;
      var t = b.toast('Toplanıyor…', 'bilgi', { sure: 0 });
      return RY.post('/api/v1/admin/collect').then(function (res) {
        t.kapat();
        b.toast('Toplandı: ' + (res && res.date ? res.date : 'bugün') +
          (res && res.durationMs != null ? ' · ' + b.sayi(res.durationMs) + ' ms' : ''), 'basari', { sure: 7000 });
        if (RY.dikkat && RY.dikkat.yukle) RY.dikkat.yukle();
        var r2 = RY.rotaMevcut();
        if (r2.ad === 'sistem' || r2.ad === 'genel') RY.rotaYenile();
      }).catch(function (h) { t.kapat(); throw h; });
    }).catch(hataToast);
  }
  RY.palet.eylemEkle({ ad: 'sistem-topla', etiket: 'İstatistikleri şimdi topla',
    aciklama: 'adminStats / adminEconomics · bugün', ikon: 'yenile', rol: 'owner', calistir: toplaAc });

  /* ---------------- Görünüm ---------------- */

  RY.gorunumler.sistem = async function (icerik) {
    var b = RY.b;
    // /admin/system görünümün omurgası — düşerse router hata durumunu çizer.
    // Yardımcı uçlar düşse de sayfa açılır; ilgili bölüm "—" gösterir.
    var hepsi = await Promise.all([
      RY.get('/api/v1/admin/system'),
      RY.saglik('/health').catch(function () { return null; }),
      RY.get('/api/v1/admin/min-build').catch(function () { return null; }),
      RY.sorgu('/api/v1/admin/stats', { days: 1 }).catch(function () { return { days: [] }; })
    ]);
    var sys = hepsi[0] || {}, saglik = hepsi[1], mb = hepsi[2];
    var builds = (((hepsi[3] || {}).days || [])[0] || {}).builds || null;
    var health = sys.health || {}, rag = health.rag || {};
    var rollups = sys.rollups || {}, scheduler = sys.scheduler || {};
    var indexes = Array.isArray(sys.indexes) ? sys.indexes : [];
    var build = sys.build || {}, config = sys.config || {};
    var sahip = RY.sahipMi();

    var statsSaat = saatFarki(b, rollups.lastStatsAt);
    var bayat = statsSaat == null || statsSaat > ROLLUP_BAYAT_SAAT;
    var indeksEksik = indexes.filter(function (i) { return i.ok === false; }).length;
    var indeksBilinmiyor = indexes.filter(function (i) { return i.ok == null; }).length;
    var revizyon = (saglik && (saglik.revision || saglik.rev || saglik.build)) || build.revision || null;

    var eylemler = '';
    if (sahip) {
      eylemler = '<button type="button" class="buton" id="sistem-topla">' + b.ik('yenile', 16) + 'Topla</button>';
    }

    var kartlar = '<section class="izgara-kpi" aria-label="Sağlık">' +
      b.istatistikKarti({ ad: 'Backend', deger: saglik ? 'Açık' : 'Erişilemiyor', altin: !!saglik,
        alt: revizyon ? 'rev ' + String(revizyon).slice(-12) : 'revizyon yok' }) +
      b.istatistikKarti({ ad: 'Firestore', deger: health.firestore === true ? 'Sağlıklı'
        : (health.firestore === false ? 'Sorun' : '—'), alt: 'config/app okuması' }) +
      b.istatistikKarti({ ad: 'FCM', deger: health.fcm === true ? 'Hazır'
        : (health.fcm === false ? 'Kapalı' : '—'), alt: 'push mesajlaşma istemcisi' }) +
      b.istatistikKarti({ ad: 'RAG', deger: rag.healthy === true ? 'Vektör' : (rag.healthy === false ? 'Eksik' : '—'),
        alt: Object.keys(rag.bases || {}).length + ' dil tabanı' }) +
      b.istatistikKarti({ ad: 'Rollup', deger: statsSaat == null ? '—' : b.goreliZaman(rollups.lastStatsAt),
        alt: bayat ? 'BAYAT (>' + ROLLUP_BAYAT_SAAT + ' sa)' : (rollups.lastStatsDate || ''), altin: !bayat }) +
      b.istatistikKarti({ ad: 'İndeksler', deger: b.sayi(indexes.length - indeksEksik - indeksBilinmiyor) + ' / ' + b.sayi(indexes.length),
        alt: indeksEksik ? indeksEksik + ' eksik' : (indeksBilinmiyor ? indeksBilinmiyor + ' bilinmiyor' : 'hepsi tamam') }) +
      '</section>';

    var ragSatirlar = Object.keys(rag.bases || {}).map(function (dil) {
      var t = rag.bases[dil] || {};
      return '<tr><th scope="row" class="mono">' + b.e(dil) + '</th><td>' +
        (t.mode === 'vector' ? b.rozet('vektör', 'aktif') : b.rozet(t.mode || '—', 'uyari')) +
        '</td><td class="sayi">' + b.e(b.sayi(t.chunks)) + '</td><td>' +
        (t.artifact ? b.rozet('var', 'aktif') : b.rozet('yok', 'hata')) + '</td></tr>';
    }).join('');
    var ragTablo = ragSatirlar
      ? '<div class="tablo-sarici"><table class="tablo"><thead><tr><th scope="col">Dil</th>' +
        '<th scope="col">Mod</th><th scope="col">Parça</th><th scope="col">Artifact</th></tr></thead>' +
        '<tbody>' + ragSatirlar + '</tbody></table></div>'
      : b.bosDurum(rag.healthy == null ? 'RAG özeti alınamadı.' : 'Taban yok.');

    var zamanlayiciSatir = [
      '<tr><th scope="row">İstatistik toplama</th><td class="mono">' + b.e(b.tarih(scheduler.stats && scheduler.stats.lastRunAt, true)) +
      '</td><td>' + (rollups.lastStatsDate ? '<span class="mono">' + b.e(rollups.lastStatsDate) + '</span>' : '—') +
      '</td><td>' + (bayat ? b.rozet('bayat', 'hata') : b.rozet('taze', 'aktif')) + '</td></tr>'
    ].concat(Object.keys(NOTIFY_TURLERI).map(function (tur) {
      var k = (scheduler.notify || {})[tur] || {};
      var yok = !k.lastRunAt;
      return '<tr><th scope="row">Bildirim · ' + b.e(NOTIFY_TURLERI[tur]) + '</th><td class="mono">' +
        b.e(b.tarih(k.lastRunAt, true)) + '</td><td>' + (k.date ? '<span class="mono">' + b.e(k.date) + '</span>' : '—') +
        '</td><td>' + (yok ? b.rozet('kayıt yok', 'notr')
          : (k.lastStatus === 'ok' ? b.rozet('ok', 'aktif') : b.rozet(String(k.lastStatus || '?'), 'uyari'))) + '</td></tr>';
    })).join('');
    var zamanlayiciTablo = '<div class="tablo-sarici"><table class="tablo"><thead><tr>' +
      '<th scope="col">İş</th><th scope="col">Son koşu</th><th scope="col">Gün</th><th scope="col">Durum</th>' +
      '</tr></thead><tbody>' + zamanlayiciSatir + '</tbody></table></div>';

    var tazelik = '<dl class="alan-liste">' +
      '<dt>Son adminStats günü</dt><dd>' + b.e(rollups.lastStatsDate || '—') + '</dd>' +
      '<dt>Üretildi</dt><dd>' + b.e(b.tarih(rollups.lastStatsAt, true)) + '</dd>' +
      '<dt>Süre</dt><dd>' + b.e(rollups.lastStatsMs != null ? b.sayi(rollups.lastStatsMs) + ' ms' : '—') + '</dd>' +
      '<dt>Son adminEconomics günü</dt><dd>' + b.e(rollups.lastEconomicsDate || '—') + '</dd>' +
      '<dt>Build revizyonu</dt><dd>' + b.e(build.revision || '—') + '</dd>' +
      '<dt>Servis</dt><dd>' + b.e(build.service || '—') + '</dd>' +
      '<dt>Instance ayakta</dt><dd>' + b.e(build.startedAt ? b.goreliZaman(build.startedAt) + 'den beri' : '—') + '</dd>' +
      '</dl>';

    var indeksSatir = indexes.map(function (i) {
      return '<tr' + (i.ok === false ? ' class="durum-hata"' : '') + '><th scope="row" class="mono">' + b.e(i.name) + '</th><td>' +
        durumRozeti(b, i.ok, 'ok', 'eksik', 'bilinmiyor') + '</td><td class="dipnot">' +
        b.e(i.ok === true ? '' : (i.error || '')) + '</td></tr>';
    }).join('');
    var indeksTablo = indeksSatir
      ? '<div class="tablo-sarici"><table class="tablo"><thead><tr><th scope="col">Sorgu</th>' +
        '<th scope="col">Durum</th><th scope="col">Hata</th></tr></thead><tbody>' + indeksSatir + '</tbody></table></div>'
      : b.bosDurum('İndeks yoklaması yapılamadı (Firestore yok).');

    icerik.innerHTML =
      b.sayfaBaslik({ baslik: 'Sistem', alt: 'Sağlık, rollup tazeliği, zamanlayıcı, indeksler, eşik, duyuru, denetim izi',
        eylemlerHtml: eylemler }) +
      duyuruBant(b, config.notice) +
      (bayat ? b.bant('<b>Rollup bayat</b> — adminStats ' + (statsSaat == null ? 'hiç üretilmemiş'
        : Math.round(statsSaat) + ' saattir yenilenmemiş') + '; gecelik iş kaçmış olabilir.' +
        (sahip ? ' "Topla" ile bugünü üret.' : ''), 'uyari', { html: true }) : '') +
      (indeksEksik ? b.bant('<b>' + indeksEksik + ' indeks eksik</b> — ilgili panel sorguları boş/hata döner. ' +
        '`firebase deploy --only firestore:indexes` sonrası derleme dakikalar sürer.', 'hata', { html: true }) : '') +
      kartlar +
      '<div class="izgara-2">' +
      b.modul('Rollup ve build', tazelik, '', { alt: 'gecelik toplama · Cloud Run revizyonu' }) +
      b.modul('Zamanlayıcı son koşular', zamanlayiciTablo, '', { alt: 'bugün, yoksa dün' }) +
      '</div>' +
      '<div class="izgara-2">' +
      b.modul('RAG tabanları', ragTablo, '', { alt: 'dil başına vektör tabanı' }) +
      b.modul('İndeks yoklaması', indeksTablo, '', { alt: 'limit(1) · FailedPrecondition = eksik' }) +
      '</div>' +
      b.modul('Zorunlu güncelleme', '<div id="sistem-esik"></div>', b.etiket('canlı · config/app'),
        { alt: 'X-App-Build < eşik → 426 · sıcak anahtar' }) +
      b.modul('Panel duyurusu', sahip ? '<div id="duyuru-form"></div>'
        : '<p class="dipnot">' + b.e(config.notice && config.notice.text
          ? 'Geçerli duyuru sayfanın üstünde. Yalnız sahip değiştirir.' : 'Duyuru yok. Yalnız sahip yazar.') + '</p>',
        '', { alt: 'config/app.notice · yalnız panel bandı, mobil okumaz' }) +
      b.modul('Denetim izi', '<div id="denetim-kap"></div>', b.etiket('adminAudit'),
        { alt: 'yazan her admin eylemi · at DESC · imleçli' });

    esikCiz(icerik.querySelector('#sistem-esik'), mb, builds);
    duyuruModulu(icerik, config.notice);
    denetimKur(icerik);

    var topla = icerik.querySelector('#sistem-topla');
    if (topla) topla.addEventListener('click', toplaAc);
  };

  RY.kirintiSaglayici.sistem = function () {
    return [{ metin: 'Yönetim', href: '#/genel' }, { metin: 'Sistem' }];
  };
})();
