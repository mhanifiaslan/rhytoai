/* Panel kabuğu (W6 + AP): Firebase Google girişi + claim kontrolü +
   PARAMETRELİ hash router (#/kullanicilar/{uid} gibi alt rotalar).
   YETKİ SUNUCUDA: buradaki claim kontrolü yalnız UX — claim'siz kullanıcı
   jenerik "bulunamadı" görür, backend zaten her isteği 403'ler. */
(function () {
  'use strict';

  var RY = window.RY;

  /* Kimlik işleyicisi AYNI ORIGIN'den (AP onarımı).

     Varsayılan authDomain (rhytoai.firebaseapp.com) panel web.app'ten
     açılınca popup el sıkışmasını ÇAPRAZ origin yapıyordu; Chrome'un
     COOP'u window.closed izlemesini kesince SDK "pencere kapandı" sanıp
     düşüyor, redirect yedeği de üçüncü-taraf depolama bölümlemesine
     takılıyordu — net etki: giriş sessizce başarısız. Hosting /__/auth/*
     işleyicisini HER alanında sunar; authDomain'i bulunduğumuz alana
     çevirince akış tamamen same-origin olur (Firebase'in belgelediği
     1 numaralı çözüm). Yalnız varsayılan Hosting alanlarında yapılır —
     özel alan adı gelirse OAuth istemcisine handler URI'si eklenmeden
     açılmamalı. */
  var auth = (function () {
    var ana = location.hostname;
    var uygun = /\.web\.app$|\.firebaseapp\.com$/.test(ana);
    if (!uygun) return firebase.auth();
    var cfg = Object.assign({}, firebase.app().options,
                            { authDomain: ana });
    return firebase.initializeApp(cfg, 'yonetim').auth();
  })();
  RY.auth = auth;

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

  function girisHatasi(metin) {
    var kutu = document.getElementById('giris-hata');
    kutu.textContent = metin || '';
    kutu.style.display = metin ? 'block' : 'none';
    if (metin) girisBilgi('');
  }

  function girisBilgi(metin) {
    var kutu = document.getElementById('giris-bilgi');
    kutu.textContent = metin || '';
    kutu.style.display = metin ? 'block' : 'none';
  }

  /* ---- E-posta + şifre girişi ----
     Yetki YÖNTEMDEN değil admin claim'inden gelir: şifreyle giren
     claim'siz hesap da sahte-404 görür. Hata metinleri hesap varlığını
     ele vermez (mobil anti-enumeration duruşuyla aynı). */
  document.getElementById('eposta-form').onsubmit = function (ev) {
    ev.preventDefault();
    girisHatasi('');
    var f = ev.target;
    var dugme = f.querySelector('button');
    dugme.disabled = true;
    auth.signInWithEmailAndPassword(f.email.value.trim(), f.password.value)
      .catch(function (hata) {
        var kod = (hata && hata.code) || '';
        if (kod === 'auth/wrong-password' || kod === 'auth/user-not-found' ||
            kod === 'auth/invalid-credential' ||
            kod === 'auth/invalid-login-credentials') {
          girisHatasi('E-posta ya da şifre hatalı.');
        } else if (kod === 'auth/too-many-requests') {
          girisHatasi('Çok fazla deneme — biraz bekleyip tekrar dene.');
        } else if (kod === 'auth/invalid-email') {
          girisHatasi('Geçerli bir e-posta gir.');
        } else {
          girisHatasi('Giriş başarısız: ' + (kod || hata));
        }
      })
      .finally(function () { dugme.disabled = false; });
  };

  /* Şifre sıfırlama: sonuç her durumda AYNI metin (hesap varlığı
     sızdırılmaz). Google-bağlı hesaba şifre eklemenin yolu da budur —
     bağlantıyı tamamlamak hesaba şifre yöntemini ekler. */
  document.getElementById('sifre-unut').onclick = function () {
    girisHatasi('');
    var eposta = document.querySelector('#eposta-form [name=email]')
      .value.trim();
    if (!eposta) { girisHatasi('Önce e-posta alanını doldur.'); return; }
    auth.sendPasswordResetEmail(eposta).catch(function () {})
      .then(function () {
        girisBilgi('E-posta kayıtlıysa sıfırlama bağlantısı gönderildi — ' +
          'spam kutusunu da kontrol et.');
      });
  };

  document.getElementById('google-gir').onclick = function () {
    girisHatasi('');
    var saglayici = new firebase.auth.GoogleAuthProvider();
    auth.signInWithPopup(saglayici).catch(function (hata) {
      var kod = (hata && hata.code) || '';
      if (kod === 'auth/popup-blocked') {
        // Tarayıcı popup'ı hiç açmadı: yönlendirme akışı tek seçenek.
        auth.signInWithRedirect(saglayici);
        return;
      }
      if (kod === 'auth/popup-closed-by-user' ||
          kod === 'auth/cancelled-popup-request') {
        girisHatasi('Pencere kapandı — tekrar dene.');
        return;
      }
      // Eskiden her hata SESSİZCE redirect'e düşüyordu ve redirect de
      // sessizce sonuçsuz kalınca "hiçbir şey olmuyor" görünüyordu.
      // Hata artık görünür; teşhis buradan başlar.
      girisHatasi('Giriş başarısız: ' + (kod || hata));
    });
  };

  // Redirect yedeğinden dönüşte hata varsa o da görünür olsun.
  auth.getRedirectResult().catch(function (hata) {
    girisHatasi('Giriş başarısız: ' + ((hata && hata.code) || hata));
  });

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

  /* ---- Kabuk süslemeleri (AP3): nav ikonları + arama + durum ---- */
  document.querySelectorAll('#yan-nav a').forEach(function (a) {
    a.insertAdjacentHTML('afterbegin', RY.ikon(a.getAttribute('data-ikon')));
  });
  document.getElementById('ara-ikon').innerHTML = RY.ikon('arama', 15);

  document.getElementById('genel-ara').addEventListener('keydown',
    function (ev) {
      if (ev.key !== 'Enter') return;
      var q = this.value.trim();
      location.hash = q
        ? '#/kullanicilar/ara/' + encodeURIComponent(q)
        : '#/kullanicilar';
      this.blur();
    });

  function backendDurumu() {
    RY.saglik('/health').then(function () {
      document.getElementById('backend-nokta').className =
        'durum-nokta iyi';
      document.getElementById('backend-durum').textContent =
        'Backend çalışıyor';
    }).catch(function () {
      document.getElementById('backend-nokta').className =
        'durum-nokta kotu';
      document.getElementById('backend-durum').textContent =
        'Backend erişilemiyor';
    });
  }

  /* ---- Oturum akışı ---- */
  auth.onAuthStateChanged(function (kullanici) {
    if (!kullanici) { goster('giris'); return; }
    kullanici.getIdTokenResult().then(function (sonuc) {
      if (sonuc.claims.admin === true) {
        goster('uygulama');
        document.getElementById('admin-eposta').textContent =
          kullanici.email || '';
        document.getElementById('admin-avatar').textContent =
          (kullanici.email || '?').charAt(0).toUpperCase();
        var saat = document.getElementById('sunucu-saat');
        saat.textContent = new Date().toLocaleString('tr-TR',
          { dateStyle: 'medium', timeStyle: 'short' });
        backendDurumu();
        rota();
      } else {
        // Claim yok: panelin varlığı ele verilmez — jenerik görünüm.
        // (Claim yeni basıldıysa çıkış/giriş gerekir; ~1 saat.)
        RY.yetkisiz();
      }
    });
  });
})();
