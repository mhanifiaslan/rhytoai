/* Ortaklar (W7 → AD19): affiliate liste + detay; kod üretimi, atıf,
   hakediş, ödeme. Okuma admin (owner+support), YAZIMLAR owner — düğmeler
   rol'e göre gizlenir, sunucu zaten 403'ler.

   Rotalar: #/ortaklar (liste) · #/ortaklar/{id} (detay).
   Uçlar:
   - GET   /api/v1/admin/partners → {partners:[{id, name, contact,
     sharePercent, active, notes, createdAt}]}
   - POST  /api/v1/admin/partners {name, contact, sharePercent, notes}
   - GET   /api/v1/admin/partners/{id} → {partner, codes:[{code, bonusTokens,
     maxRedemptions, redemptionCount, expiresAt, active}], attributedGrossUsd,
     attributedEvents, earnedUsd, paidUsd, balanceUsd, payouts:[{id, amount,
     currency, note, at}]}
   - PATCH /api/v1/admin/partners/{id} {active|name|contact|sharePercent|notes}
   - POST  /api/v1/admin/partners/{id}/codes {code|null, bonusTokens,
     maxRedemptions|null, expiresAt|null}
   - POST  /api/v1/admin/partners/{id}/payouts {amount, currency, note}
     (ön-izli: iz yazılamazsa 503 mesajı olduğu gibi)

   Dürüst model: kod kullanıcıya jeton bonusu verir ve SONRAKİ satın
   almaları ortağa atfeder; mağaza fiyatı koddan değişmez. Tüm promise'ler
   yakalanır → toast. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  /* Kırıntıda kimlik yerine ad görünsün diye son görülen adlar. */
  var adOnbellek = {};

  function yol(id, ek) {
    return '/api/v1/admin/partners' + (id ? '/' + encodeURIComponent(id) : '') + (ek || '');
  }

  function durumRozeti(b, p) {
    return p.active === false ? b.rozet('Pasif', 'notr') : b.rozet('Aktif', 'aktif');
  }

  function hataToast(h) {
    var m = RY.hataMetni(h);
    if (m) RY.b.toast(m, 'hata');
  }

  /* ---------------- Liste ---------------- */

  async function liste(icerik) {
    var b = RY.b;
    var veri = await RY.get(yol());
    var ortaklar = Array.isArray(veri.partners) ? veri.partners : [];
    ortaklar.forEach(function (p) { adOnbellek[p.id] = p.name; });
    var sahip = RY.sahipMi();

    var aktifSayisi = ortaklar.filter(function (p) { return p.active !== false; }).length;

    icerik.innerHTML = b.sayfaBaslik({
      baslik: 'Ortaklar',
      alt: ortaklar.length
        ? b.sayi(ortaklar.length) + ' ortak · ' + b.sayi(aktifSayisi) + ' aktif'
        : 'Affiliate kodları ve hakediş',
      eylemlerHtml: sahip
        ? '<button type="button" class="buton" id="ortak-yeni">' + b.ik('arti', 16) + 'Yeni ortak</button>'
        : ''
    }) + b.modul('Ortak listesi', '<div id="ortak-liste"></div>', '',
      { alt: 'satıra git: kodlar, hakediş, ödemeler' }) +
      '<p class="dipnot">Kod, kullanıcıya jeton bonusu verir ve SONRAKİ satın almaları bu ' +
      'ortağa atfeder. Mağaza fiyat indirimi buradan yapılamaz — gerekiyorsa RevenueCat/Play ' +
      'konsolundan elle.</p>';

    var vt = b.veriTablosu({
      kimlik: 'ortak-tablo', etiket: 'Ortaklar',
      sutunlar: [
        { ad: 'name', baslik: 'Ad', siralanir: true,
          bicim: function (p) { return b.e(p.name || '—'); } },
        { ad: 'contact', baslik: 'İletişim',
          bicim: function (p) { return '<span class="mono">' + b.e(p.contact || '—') + '</span>'; } },
        { ad: 'sharePercent', baslik: 'Pay', hizala: 'sag', siralanir: true,
          bicim: function (p) { return b.e('%' + b.sayi(Number(p.sharePercent) || 0)); } },
        { ad: 'active', baslik: 'Durum', deger: function (p) { return p.active === false ? 0 : 1; },
          siralanir: true, bicim: function (p) { return durumRozeti(b, p); } },
        { ad: 'createdAt', baslik: 'Kayıt', siralanir: true,
          deger: function (p) { var d = b.tarihNesnesi(p.createdAt); return d ? d.getTime() : null; },
          bicim: function (p) { return '<span class="mono">' + b.e(b.tarih(p.createdAt)) + '</span>'; } }
      ],
      anahtar: function (p) { return p.id; },
      satirHref: function (p) { return RY.rotaBagi('ortaklar', [p.id]); },
      satirSinif: function (p) { return p.active === false ? 'durum-pasif' : ''; },
      siralama: { ad: 'name', yon: 'asc' },
      bosMetin: sahip ? 'Henüz ortak yok — "Yeni ortak" ile ekle.' : 'Henüz ortak yok.'
    });
    icerik.querySelector('#ortak-liste').appendChild(vt.el);
    vt.guncelle(ortaklar);

    var yeni = icerik.querySelector('#ortak-yeni');
    if (yeni) yeni.addEventListener('click', yeniOrtakAc);
  }

  function yeniOrtakAc() {
    var b = RY.b;
    var f = b.form({
      alanlar: [
        { ad: 'name', etiket: 'Ad', zorunlu: true, max: 80, otomatik: 'off',
          dogrula: function (v) { return v.length < 2 ? 'En az 2 karakter.' : null; } },
        { ad: 'contact', etiket: 'İletişim', tur: 'text', max: 160, yertutucu: 'e-posta / telefon',
          yardim: 'Ödeme yazışması için; kullanıcıya görünmez.' },
        { ad: 'sharePercent', etiket: 'Pay (%)', tur: 'number', zorunlu: true, min: 0, max: 90,
          adim: '0.5', deger: 20, yardim: '0–90 · atfedilen brütün yüzdesi (sunucu tavanı %90)' },
        { ad: 'notes', etiket: 'Not', tur: 'textarea', max: 500, satir: 2 }
      ],
      gonderMetin: 'Ortak ekle',
      iptal: { metin: 'Vazgeç', onTikla: function () { m.kapat(); } },
      onGonder: function (d) {
        return RY.post(yol(), {
          name: d.name, contact: d.contact || '', sharePercent: Number(d.sharePercent) || 0,
          notes: d.notes || ''
        }).then(function (res) {
          var p = (res && res.partner) || {};
          if (p.id) adOnbellek[p.id] = p.name;
          b.toast('Ortak eklendi: ' + (p.name || d.name), 'basari');
          m.kapat();
          if (p.id) RY.rotaYaz('ortaklar', [p.id]); else RY.rotaYenile();
        });
      }
    });
    var m = b.modal({ baslik: 'Yeni ortak', icerik: f.el, genislik: 520 });
    m.ac();
  }

  /* ---------------- Detay ---------------- */

  async function detay(icerik, id) {
    var b = RY.b;
    var d = await RY.get(yol(id));
    var p = d.partner || {};
    var kodlar = Array.isArray(d.codes) ? d.codes : [];
    var odemeler = Array.isArray(d.payouts) ? d.payouts : [];
    var sahip = RY.sahipMi();
    var pasif = p.active === false;
    adOnbellek[id] = p.name;
    RY.kirinti([{ metin: 'Yönetim', href: '#/genel' }, { metin: 'Ortaklar', href: '#/ortaklar' },
                { metin: p.name || id }]);

    var eylemler = '<a class="buton ikincil" href="#/ortaklar">' + b.ik('daralt', 16) + 'Listeye dön</a>';
    if (sahip) {
      eylemler += '<button type="button" class="' + (pasif ? 'buton' : 'buton tehlike') +
        '" id="ortak-durum">' + b.ik(pasif ? 'basari' : 'kilit', 16) +
        (pasif ? 'Aktifleştir' : 'Pasifleştir') + '</button>';
    }

    icerik.innerHTML =
      b.sayfaBaslik({
        baslik: p.name || 'Ortak',
        alt: [p.contact, 'pay %' + b.sayi(Number(p.sharePercent) || 0),
              p.createdAt ? 'kayıt ' + b.tarih(p.createdAt) : null]
          .filter(Boolean).join(' · '),
        eylemlerHtml: eylemler
      }) +
      (pasif ? b.bant('Bu ortak PASİF — kodları çalışmaya devam eder, listede soluk görünür.', 'bilgi') : '') +
      '<section class="izgara-kpi" aria-label="Hakediş özeti">' +
      b.istatistikKarti({ ad: 'Atfedilen brüt', deger: b.para(d.attributedGrossUsd), altin: true,
        alt: b.sayi(d.attributedEvents || 0) + ' olay · iade düşülmüş' }) +
      b.istatistikKarti({ ad: 'Hakediş', deger: b.para(d.earnedUsd),
        alt: '%' + b.sayi(Number(p.sharePercent) || 0) + ' pay' }) +
      b.istatistikKarti({ ad: 'Ödenen', deger: b.para(d.paidUsd) }) +
      b.istatistikKarti({ ad: 'Bakiye', deger: b.para(d.balanceUsd),
        altin: Number(d.balanceUsd) > 0,
        alt: Number(d.balanceUsd) > 0 ? 'ödeme bekliyor' : 'kapalı' }) +
      '</section>' +
      (p.notes ? b.modul('Not', '<p class="dipnot">' + b.e(p.notes) + '</p>') : '') +
      '<div class="izgara-2">' +
      b.modul('Kodlar', '<div id="ortak-kodlar"></div>' +
        (sahip ? '<div id="ortak-kod-form"></div>' : ''),
        b.etiket(b.sayi(kodlar.length) + ' kod'),
        { alt: 'kullanıcıya jeton bonusu · sonraki alımlar atfedilir' }) +
      b.modul('Ödemeler', '<div id="ortak-odemeler"></div>' +
        (sahip ? '<div id="ortak-odeme-form"></div>' : ''),
        b.etiket(b.sayi(odemeler.length) + ' kayıt'),
        { alt: 'hakediş ödemesi kaydı — mali işlem, ön-izli' }) +
      '</div>';

    /* Kodlar tablosu */
    var kodVt = b.veriTablosu({
      kimlik: 'ortak-kod-tablo', etiket: 'Kodlar', yogunluk: 'sik',
      sutunlar: [
        { ad: 'code', baslik: 'Kod', siralanir: true,
          bicim: function (k) { return '<b class="mono">' + b.e(k.code) + '</b>'; } },
        { ad: 'bonusTokens', baslik: 'Bonus', hizala: 'sag', siralanir: true },
        { ad: 'redemptionCount', baslik: 'Kullanım', hizala: 'sag', siralanir: true,
          bicim: function (k) {
            return b.e(b.sayi(k.redemptionCount || 0) + (k.maxRedemptions ? ' / ' + b.sayi(k.maxRedemptions) : ''));
          } },
        { ad: 'expiresAt', baslik: 'Son gün',
          deger: function (k) { var t = b.tarihNesnesi(k.expiresAt); return t ? t.getTime() : null; },
          siralanir: true,
          bicim: function (k) { return '<span class="mono">' + b.e(k.expiresAt ? b.tarih(k.expiresAt) : '—') + '</span>'; } },
        { ad: 'active', baslik: 'Durum', deger: function (k) { return k.active ? 1 : 0; },
          bicim: function (k) {
            var dolu = k.maxRedemptions && Number(k.redemptionCount || 0) >= Number(k.maxRedemptions);
            var t = b.tarihNesnesi(k.expiresAt);
            var gecmis = t && t.getTime() < Date.now();
            if (!k.active) return b.rozet('Pasif', 'notr');
            if (gecmis) return b.rozet('Süresi doldu', 'dolmus');
            if (dolu) return b.rozet('Limit doldu', 'uyari');
            return b.rozet('Aktif', 'aktif');
          } }
      ],
      anahtar: function (k) { return k.code; },
      siralama: { ad: 'code', yon: 'asc' },
      bosMetin: 'Kod yok.'
    });
    icerik.querySelector('#ortak-kodlar').appendChild(kodVt.el);
    kodVt.guncelle(kodlar);

    /* Ödemeler tablosu */
    var odemeVt = b.veriTablosu({
      kimlik: 'ortak-odeme-tablo', etiket: 'Ödemeler', yogunluk: 'sik',
      sutunlar: [
        { ad: 'at', baslik: 'Tarih', siralanir: true,
          deger: function (o) { var t = b.tarihNesnesi(o.at); return t ? t.getTime() : null; },
          bicim: function (o) { return '<span class="mono">' + b.e(b.tarih(o.at, true)) + '</span>'; } },
        { ad: 'amount', baslik: 'Tutar', hizala: 'sag', siralanir: true,
          bicim: function (o) {
            var birim = String(o.currency || 'USD').toUpperCase();
            return b.e(birim === 'USD' ? b.para(o.amount) : b.sayi(o.amount) + ' ' + birim);
          } },
        { ad: 'note', baslik: 'Not', bicim: function (o) { return b.e(o.note || '—'); } }
      ],
      anahtar: function (o) { return o.id || (String(o.at) + '-' + o.amount); },
      siralama: { ad: 'at', yon: 'desc' },
      bosMetin: 'Ödeme kaydı yok.'
    });
    icerik.querySelector('#ortak-odemeler').appendChild(odemeVt.el);
    odemeVt.guncelle(odemeler);

    if (!sahip) return;

    /* Aktif/pasif */
    icerik.querySelector('#ortak-durum').addEventListener('click', function () {
      b.onayla({
        baslik: pasif ? 'Ortağı aktifleştir' : 'Ortağı pasifleştir',
        mesaj: pasif
          ? (p.name || 'Ortak') + ' yeniden AKTİF olacak.'
          : (p.name || 'Ortak') + ' PASİF olacak — kodları çalışmaya devam eder, listede soluk görünür.',
        tehlike: !pasif, onaylaMetin: pasif ? 'Aktifleştir' : 'Pasifleştir'
      }).then(function (r) {
        if (!r) return;
        return RY.patch(yol(id), { active: pasif }).then(function () {
          b.toast(pasif ? 'Ortak aktifleştirildi.' : 'Ortak pasifleştirildi.', 'basari');
          RY.rotaYenile();
        });
      }).catch(hataToast);
    });

    /* Kod üret */
    var kodForm = b.form({
      alanlar: [
        { ad: 'code', etiket: 'Kod', yertutucu: 'boş = otomatik', max: 24, otomatik: 'off',
          yardim: '4–24 karakter, harf/rakam/_/-; küçük girilse de BÜYÜK saklanır.',
          dogrula: function (v) {
            return /^[A-Za-z0-9_-]{4,24}$/.test(v) ? null : '4–24 karakter; yalnız harf, rakam, _ ve -.';
          } },
        { ad: 'bonusTokens', etiket: 'Bonus jeton', tur: 'number', zorunlu: true, min: 0, max: 5000,
          adim: '1', deger: 0 },
        { ad: 'maxRedemptions', etiket: 'Kullanım limiti', tur: 'number', min: 1, adim: '1',
          yertutucu: 'sınırsız' },
        { ad: 'expiresAt', etiket: 'Son gün', tur: 'date', yardim: 'Gün sonu UTC; boş = süresiz.' }
      ],
      gonderMetin: 'Kod üret',
      onGonder: function (v) {
        return RY.post(yol(id, '/codes'), {
          code: v.code || null,
          bonusTokens: Math.round(Number(v.bonusTokens) || 0),
          maxRedemptions: v.maxRedemptions != null ? Math.round(Number(v.maxRedemptions)) : null,
          expiresAt: v.expiresAt || null
        }).then(function (res) {
          var k = (res && res.code) || {};
          b.toast('Kod üretildi: ' + (k.code || '—'), 'basari', { sure: 6000 });
          RY.rotaYenile();
        });
      }
    });
    icerik.querySelector('#ortak-kod-form').appendChild(kodForm.el);

    /* Ödeme işaretle */
    var odemeForm = b.form({
      alanlar: [
        { ad: 'amount', etiket: 'Tutar', tur: 'number', zorunlu: true, min: 0.01, adim: '0.01',
          dogrula: function (v) { return v > 0 ? null : 'Sıfırdan büyük olmalı.'; } },
        { ad: 'currency', etiket: 'Para birimi', deger: 'USD', zorunlu: true, max: 3, otomatik: 'off',
          dogrula: function (v) { return /^[A-Za-z]{3}$/.test(v) ? null : '3 harfli kod (USD).'; } },
        { ad: 'note', etiket: 'Not', max: 300, yertutucu: 'ör. Eylül hakedişi, havale' }
      ],
      gonderMetin: 'Ödeme işaretle',
      onGonder: function (v) {
        var birim = String(v.currency || 'USD').toUpperCase();
        var tutar = Number(v.amount);
        return b.onayla({
          baslik: 'Ödemeyi kaydet',
          mesaj: (p.name || 'Ortak') + ' için ' +
            (birim === 'USD' ? b.para(tutar) : b.sayi(tutar) + ' ' + birim) +
            ' ödeme işaretlenecek' + (v.note ? ' — "' + v.note + '"' : '') + '.',
          aciklama: 'Mali işlem: ön-izli denetim kaydı düşer; bakiye bu tutar kadar azalır. Geri alma yok.',
          onaylaMetin: 'Kaydet'
        }).then(function (r) {
          if (!r) { var h = new Error('iptal'); h.iptal = true; throw h; }
          return RY.post(yol(id, '/payouts'), { amount: tutar, currency: birim, note: v.note || '' });
        }).then(function () {
          b.toast('Ödeme kaydedildi.', 'basari');
          RY.rotaYenile();
        });
      }
    });
    icerik.querySelector('#ortak-odeme-form').appendChild(odemeForm.el);
  }

  /* ---------------- Rota ---------------- */

  RY.gorunumler.ortaklar = async function (icerik, args) {
    if (args && args[0]) return detay(icerik, args[0]);
    return liste(icerik);
  };

  RY.kirintiSaglayici.ortaklar = function (args) {
    var parcalar = [{ metin: 'Yönetim', href: '#/genel' }];
    if (args && args[0]) {
      parcalar.push({ metin: 'Ortaklar', href: '#/ortaklar' });
      parcalar.push({ metin: adOnbellek[args[0]] || 'Ortak' });
    } else parcalar.push({ metin: 'Ortaklar' });
    return parcalar;
  };

  RY.palet.eylemEkle({ ad: 'ortak-yeni', etiket: 'Yeni ortak ekle', aciklama: 'Affiliate kaydı',
    ikon: 'ortaklar', rol: 'owner', calistir: yeniOrtakAc });
})();
