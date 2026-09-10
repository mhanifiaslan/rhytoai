/* Hero uzayı: yalnız hassas imleçte, hareket azaltma tercihini koruyarak. */
(function () {
  'use strict';

  var hero = document.querySelector('.kahraman');
  if (!hero) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var precisePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  var frame = null;
  var targetX = 0;
  var targetY = 0;

  function reset() {
    targetX = 0;
    targetY = 0;
    requestUpdate();
  }

  function update() {
    frame = null;
    if (reduce.matches || !precisePointer.matches) {
      hero.style.removeProperty('--hero-dust-x');
      hero.style.removeProperty('--hero-dust-y');
      hero.style.removeProperty('--hero-glow-x');
      hero.style.removeProperty('--hero-glow-y');
      return;
    }

    hero.style.setProperty('--hero-dust-x', (targetX * 7).toFixed(2) + 'px');
    hero.style.setProperty('--hero-dust-y', (targetY * 7).toFixed(2) + 'px');
    hero.style.setProperty('--hero-glow-x', (targetX * 28).toFixed(2) + 'px');
    hero.style.setProperty('--hero-glow-y', (targetY * 16).toFixed(2) + 'px');
  }

  function requestUpdate() {
    if (frame === null) frame = window.requestAnimationFrame(update);
  }

  hero.addEventListener('pointermove', function (event) {
    if (reduce.matches || !precisePointer.matches) return;
    var bounds = hero.getBoundingClientRect();
    targetX = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2;
    targetY = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2;
    requestUpdate();
  });
  hero.addEventListener('pointerleave', reset);
  reduce.addEventListener('change', reset);
  precisePointer.addEventListener('change', reset);
  reset();
})();
