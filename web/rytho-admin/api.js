/* Panel API katmanı (W6): her veri backend'den, Firestore'a doğrudan
   erişim YOK (kurallar kapalı kalır). Kimlik: Firebase ID token. */
(function () {
  'use strict';

  var BACKEND = 'https://rytho-backend-770582338651.us-central1.run.app';

  async function apiIste(yol, secenekler) {
    var kullanici = firebase.auth().currentUser;
    if (!kullanici) throw new Error('oturum-yok');
    var token = await kullanici.getIdToken();
    var yanit = await fetch(BACKEND + yol, Object.assign({
      headers: { 'Authorization': 'Bearer ' + token,
                 'Content-Type': 'application/json' }
    }, secenekler || {}));
    if (yanit.status === 401 || yanit.status === 403) {
      // Yetki düştü: oturumu kapat, jenerik görünüme dön.
      window.RY.yetkisiz();
      throw new Error('yetkisiz');
    }
    if (!yanit.ok) throw new Error('api-' + yanit.status);
    return yanit.json();
  }

  window.RY = window.RY || {};
  window.RY.get = function (yol) { return apiIste(yol); };
  window.RY.post = function (yol, govde) {
    return apiIste(yol, { method: 'POST',
                          body: govde ? JSON.stringify(govde) : undefined });
  };
  // Sağlık uçları herkese açık — token gerekmez.
  window.RY.saglik = function (yol) {
    return fetch(BACKEND + yol).then(function (y) { return y.json(); });
  };
  window.RY.BACKEND = BACKEND;
})();
