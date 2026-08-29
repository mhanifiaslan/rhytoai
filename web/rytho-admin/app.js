/* Panel kabuğu (W6 + AP): Firebase Google girişi + claim kontrolü +
   PARAMETRELİ hash router (#/kullanicilar/{uid} gibi alt rotalar).
   YETKİ SUNUCUDA: buradaki claim kontrolü yalnız UX — claim'siz kullanıcı
   jenerik "bulunamadı" görür, backend zaten her isteği 403'ler. */
(function () {
  'use strict';

  var RY = window.RY;
  var auth = firebase.auth();

  var BASLIKLAR = {
    genel: 'Genel Bakış',
    kullanicilar: 'Kullanıcılar',
    ekonomi: 'Ekonomi',
    ai: 'AI Kullanımı',
    ortaklar: 'Ortaklar',
    sistem: 'Sistem'
  };
  /* Eski yer imleri kırılmasın. */
  var TAKMA_ADLAR = { gelir: 'ekonomi' };

  function goster(id) {
    ['bulunamadi', 'giris', 'uygulama'].forEach(function (ad) {
      document.getElementById(ad).style.display = ad === id
        ? (ad === 'uygulama' ? 'grid' : 'flex') : 'none';
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

  /* ---- Parametreli hash router ---- */
  function rota() {
    var parcalar = (location.hash || '#/genel')
      .replace(/^#\//, '').split('/').filter(Boolean);
    var ad = TAKMA_ADLAR[parcalar[0]] || parcalar[0] || 'genel';
    if (!RY.gorunumler[ad]) ad = 'genel';
    var argumanlar = parcalar.slice(1).map(decodeURIComponent);

    document.querySelectorAll('.yan-menu nav a, nav.sekme-ust a')
      .forEach(function (a) {
        var aktif = a.getAttribute('href') === '#/' + ad;
        a.classList.toggle('aktif', aktif);
        if (aktif) a.setAttribute('aria-current', 'page');
        else a.removeAttribute('aria-current');
      });
    document.getElementById('sayfa-baslik').textContent =
      BASLIKLAR[ad] || 'Rytho Yönetim';

    var icerik = document.getElementById('icerik');
    icerik.setAttribute('aria-busy', 'true');
    icerik.innerHTML = RY.b.iskelet();
    RY.gorunumler[ad](icerik, argumanlar).then(function () {
      icerik.setAttribute('aria-busy', 'false');
    }).catch(function (hata) {
      icerik.setAttribute('aria-busy', 'false');
      if (hata && hata.message === 'yetkisiz') return;
      icerik.innerHTML = RY.b.hataDurum(RY.hataMetni(hata));
      var tekrar = document.getElementById('tekrar-dene');
      if (tekrar) tekrar.onclick = rota;
    });
  }
  window.addEventListener('hashchange', rota);
  RY.rotaYenile = rota;

  /* ---- Oturum akışı ---- */
  auth.onAuthStateChanged(function (kullanici) {
    if (!kullanici) { goster('giris'); return; }
    kullanici.getIdTokenResult().then(function (sonuc) {
      if (sonuc.claims.admin === true) {
        goster('uygulama');
        document.getElementById('admin-eposta').textContent =
          kullanici.email || '';
        var saat = document.getElementById('sunucu-saat');
        saat.textContent = new Date().toLocaleString('tr-TR',
          { dateStyle: 'medium', timeStyle: 'short' });
        rota();
      } else {
        // Claim yok: panelin varlığı ele verilmez — jenerik görünüm.
        // (Claim yeni basıldıysa çıkış/giriş gerekir; ~1 saat.)
        RY.yetkisiz();
      }
    });
  });
})();
