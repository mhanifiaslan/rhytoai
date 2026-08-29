/* Ortaklar (W8 + AP giydirmesi): affiliate CRUD — kod üretimi, atıf,
   hakediş, ödeme. Yeni: pasifleştir/aktifleştir (backend PATCH hazırdı,
   panel ilk kez kullanıyor). */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  async function listeCiz(icerik) {
    var b = RY.b;
    var veri = await RY.get('/api/v1/admin/partners');
    var liste = veri.partners || [];

    var satirlar = liste.map(function (p) {
      return '<tr class="tikla" data-pid="' + b.e(p.id) + '">' +
        '<td><b>' + b.e(p.name) + '</b> ' +
        (p.active === false ? b.rozet('pasif', 'notr') : '') + '</td>' +
        '<td>' + b.e(p.contact) + '</td>' +
        '<td class="sayi">%' + b.e(p.sharePercent) + '</td></tr>';
    }).join('');

    icerik.innerHTML =
      '<div class="panel"><h2>Yeni ortak</h2>' +
      '<form id="ortak-form" class="form-satir">' +
      b.girdi('name', 'Ad') +
      b.girdi('contact', 'İletişim (e-posta)') +
      b.girdi('sharePercent', 'Pay % (ör. 20)', 'number') +
      '<button class="buton ikincil" type="submit">Ekle</button></form>' +
      '</div>' +
      '<div class="panel"><h2>Ortaklar</h2>' +
      (satirlar
        ? b.tablo(['Ad', 'İletişim', 'Pay'], satirlar)
        : b.bosDurum('Henüz ortak yok — yukarıdan ekle.')) +
      '</div><div id="ortak-detay"></div>';

    document.getElementById('ortak-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      try {
        await RY.post('/api/v1/admin/partners', {
          name: f.name.value, contact: f.contact.value,
          sharePercent: parseFloat(f.sharePercent.value || '0')
        });
        RY.rotaYenile();
      } catch (h) { alert(RY.hataMetni(h)); }
    };

    icerik.querySelectorAll('tr[data-pid]').forEach(function (tr) {
      tr.onclick = function () { detayCiz(tr.getAttribute('data-pid')); };
    });
  }

  async function detayCiz(pid) {
    var b = RY.b;
    var kutu = document.getElementById('ortak-detay');
    kutu.innerHTML = '<div class="iskelet iskelet-blok"></div>';
    var d = await RY.get('/api/v1/admin/partners/' + encodeURIComponent(pid));
    var p = d.partner || {};

    var kodSatir = (d.codes || []).map(function (k) {
      return '<tr><td class="sayi sol">' + b.e(k.code) + '</td>' +
        '<td class="sayi">' + b.e(k.bonusTokens) + '</td>' +
        '<td class="sayi">' + b.e(k.redemptionCount || 0) +
        (k.maxRedemptions ? '/' + b.e(k.maxRedemptions) : '') + '</td>' +
        '<td>' + (k.active ? b.rozet('aktif', 'aktif')
                           : b.rozet('pasif', 'notr')) + '</td></tr>';
    }).join('');

    var odemeSatir = (d.payouts || []).map(function (o) {
      return '<tr><td class="sayi sol">' + b.e(o.amount) + ' ' +
        b.e(o.currency) + '</td><td>' + b.e(o.note) + '</td></tr>';
    }).join('');

    var pasif = p.active === false;

    kutu.innerHTML =
      '<div class="kpi-izgara" style="margin-top:14px">' +
      b.kpi(b.para(d.attributedGrossUsd),
        b.e(p.name) + ' — atfedilen brüt', { altin: true }) +
      b.kpi(b.para(d.earnedUsd), 'Hakediş (%' + b.e(p.sharePercent) + ')') +
      b.kpi(b.para(d.paidUsd), 'Ödenen') +
      b.kpi(b.para(d.balanceUsd), 'Bakiye', { altin: true }) +
      '</div>' +
      '<p class="dipnot" style="margin:0 0 14px">' +
      '<button id="ortak-durum" class="buton ikincil kucuk">' +
      (pasif ? 'Aktifleştir' : 'Pasifleştir') + '</button></p>' +
      '<div class="izgara-2">' +
      '<div class="panel"><h2>Kodlar</h2>' +
      (kodSatir
        ? b.tablo(['Kod', 'Bonus', 'Kullanım', 'Durum'], kodSatir)
        : b.bosDurum('Kod yok.')) +
      '<form id="kod-form" class="form-satir">' +
      b.girdi('code', 'Kod (boş = otomatik)') +
      b.girdi('bonusTokens', 'Bonus jeton', 'number') +
      b.girdi('maxRedemptions', 'Kullanım limiti', 'number') +
      '<button class="buton ikincil" type="submit">Kod üret</button></form>' +
      '<p class="dipnot">Kod, kullanıcıya jeton bonusu verir ve SONRAKİ ' +
      'satın almaları bu ortağa atfeder. Mağaza fiyat indirimi buradan ' +
      'yapılamaz — gerekiyorsa RevenueCat/Play konsolundan elle.</p></div>' +
      '<div class="panel"><h2>Ödemeler</h2>' +
      (odemeSatir
        ? b.tablo(['Tutar', 'Not'], odemeSatir)
        : b.bosDurum('Ödeme kaydı yok.')) +
      '<form id="odeme-form" class="form-satir">' +
      b.girdi('amount', 'Tutar (USD)', 'number') +
      b.girdi('note', 'Not') +
      '<button class="buton ikincil" type="submit">Ödeme işaretle</button>' +
      '</form></div></div>';

    document.getElementById('ortak-durum').onclick = async function () {
      var soru = pasif
        ? 'Ortak yeniden AKTİF olacak — onaylıyor musun?'
        : 'Ortak PASİF olacak (kodları çalışmaya devam eder, listede soluk ' +
          'görünür) — onaylıyor musun?';
      if (!confirm(soru)) return;
      try {
        await RY.patch('/api/v1/admin/partners/' + encodeURIComponent(pid),
          { active: pasif });
        RY.rotaYenile();
      } catch (h) { alert(RY.hataMetni(h)); }
    };

    document.getElementById('kod-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      try {
        await RY.post('/api/v1/admin/partners/' + encodeURIComponent(pid) +
          '/codes', {
            code: f.code.value || null,
            bonusTokens: parseInt(f.bonusTokens.value || '0', 10),
            maxRedemptions: f.maxRedemptions.value
              ? parseInt(f.maxRedemptions.value, 10) : null
          });
        detayCiz(pid);
      } catch (h) { alert(RY.hataMetni(h)); }
    };
    document.getElementById('odeme-form').onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      try {
        await RY.post('/api/v1/admin/partners/' + encodeURIComponent(pid) +
          '/payouts', {
            amount: parseFloat(f.amount.value), note: f.note.value
          });
        detayCiz(pid);
      } catch (h) { alert(RY.hataMetni(h)); }
    };
    kutu.scrollIntoView({ behavior: 'smooth' });
  }

  RY.gorunumler.ortaklar = listeCiz;
})();
