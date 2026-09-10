/* Uygulama ekranları: seçilen ekranı küçük mockup koleksiyonunda öne alır. */
(function () {
  'use strict';

  document.querySelectorAll('.mini-telefonlar').forEach(function (vitrin) {
    var ekranlar = Array.prototype.slice.call(vitrin.querySelectorAll('.mini-telefon'));

    function sec(ekran) {
      ekranlar.forEach(function (item) {
        var aktif = item === ekran;
        item.classList.toggle('is-selected', aktif);
        item.setAttribute('aria-pressed', aktif ? 'true' : 'false');
      });
    }

    ekranlar.forEach(function (ekran) {
      ekran.addEventListener('click', function () { sec(ekran); });
      ekran.addEventListener('focus', function () { sec(ekran); });
    });
  });
}());
