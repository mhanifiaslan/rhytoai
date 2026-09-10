/* Mobil menü: bir hedef seçildiğinde paneli kapatır, Escape ile de çıkar. */
(function () {
  'use strict';

  document.querySelectorAll('.mobil-menu').forEach(function (menu) {
    menu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () { menu.removeAttribute('open'); });
    });
    menu.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        menu.removeAttribute('open');
        menu.querySelector('summary').focus();
      }
    });
  });
}());
