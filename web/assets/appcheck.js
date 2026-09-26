/* Firebase App Check — WEB yüzeyleri için ortak kurulum.
 *
 * NEDEN VAR: 2026-09-26'da bot akınına karşı `identitytoolkit` ve
 * `firestore` servislerinde App Check ZORLAMASI açıldı. Mobil uygulamada
 * App Check 1.15.8+43'ten beri var, ama web yüzeylerinde HİÇ yoktu — o an
 * hem panel girişi hem şifre sıfırlama sayfası tamamen kapandı
 * ("Firebase App Check token is invalid"). Ölçüldü, tahmin değil.
 *
 * SİTE ANAHTARI GİZLİ DEĞİLDİR. reCAPTCHA site anahtarları tasarım gereği
 * herkese açıktır (tarayıcıya gidiyor); gizli olan, Firebase Console'a
 * girilen "secret"tir ve o buraya ASLA yazılmaz.
 *
 * Anahtar BOŞ bırakılırsa kurulum atlanır ve sayfa eskisi gibi çalışır.
 * Bu bilinçli: boş anahtarla `activate()` çağırmak sayfayı açılışta
 * düşürürdü ve zorlama kapalıyken de kimse giremezdi.
 */
(function (w) {
  'use strict';

  /* Firebase Console → App Check → "Default Web App" → reCAPTCHA v3
     kaydedildiğinde verilen SİTE anahtarı buraya yazılır. */
  var SITE_ANAHTARI = '';

  /* App Check ÖRNEK BAŞINADIR. Panel, giriş açılır penceresini same-origin
     yapmak için ikinci bir Firebase örneği ('yonetim') kuruyor
     (rytho-admin/app.js). Yalnız birini etkinleştirmek, diğerinin
     isteklerini jetonsuz bırakır ve giriş yine reddedilir — bu yüzden
     çağıran taraf her örnek için ayrı çağırır. */
  w.RY_appCheckKur = function (app) {
    if (!SITE_ANAHTARI) return false;
    try {
      var ac = app ? firebase.appCheck(app) : firebase.appCheck();
      ac.activate(new firebase.appCheck.ReCaptchaV3Provider(SITE_ANAHTARI),
                  /* isTokenAutoRefreshEnabled */ true);
      return true;
    } catch (e) {
      /* Yutulur: App Check kurulamadıysa bile sayfa açılmalı. Zorlama
         açıkken istekler zaten reddedilecek ve kullanıcı o hatayı görecek;
         burada çökmek teşhisi zorlaştırmaktan başka işe yaramaz. */
      if (w.console && console.warn) {
        console.warn('App Check etkinleştirilemedi:', e && e.message);
      }
      return false;
    }
  };

  /* Teşhis için: anahtar girilmiş mi? Konsoldan bakılabilsin. */
  w.RY_appCheckHazir = function () { return !!SITE_ANAHTARI; };
})(window);
