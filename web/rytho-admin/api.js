/* Panel API katmanı (W6 + AP sertleştirmesi): her veri backend'den,
   Firestore'a doğrudan erişim YOK (kurallar kapalı kalır). Kimlik:
   Firebase ID token. */
(function () {
  'use strict';

  var BACKEND = 'https://rytho-backend-770582338651.us-central1.run.app';

  async function apiIste(yol, secenekler) {
    // Oturum app.js'in kurduğu SAME-ORIGIN auth örneğinde yaşar
    // (RY.auth); varsayılan uygulamaya düşüş yalnız emniyet.
    var kullanici = (window.RY.auth || firebase.auth()).currentUser;
    if (!kullanici) throw new Error('oturum-yok');
    var token = await kullanici.getIdToken();
    secenekler = secenekler || {};
    // Başlıklar AYRI birleştirilir: Object.assign(secenekler) çağıranın
    // headers'ı verdiği anda Authorization'ı eziyordu (eski kusur).
    var basliklar = Object.assign({
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    }, secenekler.headers || {});
    var yanit;
    try {
      yanit = await fetch(BACKEND + yol,
        Object.assign({}, secenekler, { headers: basliklar }));
    } catch (aghata) {
      // Anlık ağ kesintisi/uyku dönüşü için TEK otomatik tekrar —
      // yalnız güvenli metotlarda (POST/PATCH çift işlem yapmasın).
      var metot = (secenekler.method || 'GET').toUpperCase();
      if (metot !== 'GET') throw new Error('ag-hatasi');
      await new Promise(function (t) { setTimeout(t, 700); });
      try {
        yanit = await fetch(BACKEND + yol,
          Object.assign({}, secenekler, { headers: basliklar }));
      } catch (yine) {
        throw new Error('ag-hatasi');
      }
    }
    if (yanit.status === 401 || yanit.status === 403) {
      // Yetki düştü: oturumu kapat, jenerik görünüme dön.
      window.RY.yetkisiz();
      throw new Error('yetkisiz');
    }
    if (!yanit.ok) {
      var hata = new Error('api-' + yanit.status);
      hata.durum = yanit.status;
      try {
        var govde = await yanit.json();
        if (govde && govde.detail) {
          hata.detay = typeof govde.detail === 'string'
            ? govde.detail : JSON.stringify(govde.detail);
        }
      } catch (yok) { /* gövdesiz hata */ }
      throw hata;
    }
    return yanit.json();
  }

  /* Ham hata → yöneticinin okuyacağı cümle. */
  function hataMetni(hata) {
    if (!hata) return 'Bilinmeyen hata.';
    if (hata.message === 'ag-hatasi') {
      return 'Bağlantı kurulamadı — ağını kontrol edip tekrar dene.';
    }
    if (hata.message === 'oturum-yok') return 'Oturum bulunamadı.';
    if (hata.detay) return hata.detay;
    if (hata.durum === 404) return 'Kayıt bulunamadı.';
    if (hata.durum >= 500) return 'Sunucu hatası — birazdan tekrar dene.';
    return 'Veri alınamadı (' + (hata.message || hata) + ').';
  }

  window.RY = window.RY || {};
  window.RY.get = function (yol) { return apiIste(yol); };
  window.RY.post = function (yol, govde) {
    return apiIste(yol, { method: 'POST',
                          body: govde ? JSON.stringify(govde) : undefined });
  };
  window.RY.patch = function (yol, govde) {
    return apiIste(yol, { method: 'PATCH',
                          body: JSON.stringify(govde || {}) });
  };
  window.RY.del = function (yol, govde) {
    return apiIste(yol, { method: 'DELETE',
                          body: JSON.stringify(govde || {}) });
  };
  // Sağlık uçları herkese açık — token gerekmez.
  window.RY.saglik = function (yol) {
    return fetch(BACKEND + yol).then(function (y) { return y.json(); });
  };
  window.RY.hataMetni = hataMetni;
  window.RY.BACKEND = BACKEND;
})();
