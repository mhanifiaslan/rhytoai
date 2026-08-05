/* Panel kabuğu (W6): Firebase Google girişi + claim kontrolü + hash router.
   YETKİ SUNUCUDA: buradaki claim kontrolü yalnız UX — claim'siz kullanıcı
   jenerik "bulunamadı" görür, backend zaten her isteği 403'ler. */
(function () {
  'use strict';

  var RY = window.RY;
  var auth = firebase.auth();

  function goster(id) {
    ['bulunamadi', 'giris', 'uygulama'].forEach(function (ad) {
      document.getElementById(ad).style.display = ad === id
        ? (ad === 'uygulama' ? 'block' : 'flex') : 'none';
    });
  }

  RY.yetkisiz = function () {
    auth.signOut().catch(function () {});
    goster('bulunamadi');
  };

  document.getElementById('google-gir').onclick = function () {
    var saglayici = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(saglayici).catch(function () {
      // Popup engellendiyse yönlendirmeye düş.
      auth.signInWithRedirect(saglayici);
    });
  };

  document.getElementById('cikis').onclick = function () {
    auth.signOut().then(function () { goster('giris'); });
  };

  /* ---- Hash router ---- */
  function rota() {
    var ad = (location.hash || '#/genel').replace('#/', '') || 'genel';
    if (!RY.gorunumler[ad]) ad = 'genel';
    document.querySelectorAll('nav.sekmeler a').forEach(function (a) {
      a.classList.toggle('aktif', a.getAttribute('href') === '#/' + ad);
    });
    var icerik = document.getElementById('icerik');
    icerik.innerHTML = '<div class="bos">Yükleniyor…</div>';
    RY.gorunumler[ad](icerik).catch(function (hata) {
      if (hata.message === 'yetkisiz') return;
      icerik.innerHTML = '<p class="hata">Veri alınamadı: ' +
        String(hata.message || hata) + '</p>';
    });
  }
  window.addEventListener('hashchange', rota);

  /* ---- Oturum akışı ---- */
  auth.onAuthStateChanged(function (kullanici) {
    if (!kullanici) { goster('giris'); return; }
    kullanici.getIdTokenResult().then(function (sonuc) {
      if (sonuc.claims.admin === true) {
        goster('uygulama');
        var saat = document.getElementById('sunucu-saat');
        saat.textContent = kullanici.email || '';
        rota();
      } else {
        // Claim yok: panelin varlığı ele verilmez — jenerik görünüm.
        // (Claim yeni basıldıysa çıkış/giriş gerekir; ~1 saat.)
        RY.yetkisiz();
      }
    });
  });
})();
