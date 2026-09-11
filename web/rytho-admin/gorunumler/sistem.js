/* Sistem: sağlık + bildirim koşuları (notifyRuns) + denetim izi
   (adminAudit) + zorunlu güncelleme anahtarı (config/app.minBuild, PBZ)
   + RAG ayrıntısı.
   Uçlar: /health, /health/rag, /admin/stats, /admin/notify-runs,
   /admin/audit, /admin/min-build (GET durum · POST eşik). */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  /* Zorunlu güncelleme modülü. İki kaynak, iki etiket: `mb`
     (/admin/min-build) CANLI — etkin eşik, env tabanı, count() ile
     "eşiğin altında"; `builds` (adminStats.builds) GECELİK — sürüm
     kırılımı ve başlık göndermeyen ≤34 istemcilerin "bilinmiyor"
     sayısı. Karıştırılmaz: canlı sayım alanı olmayanları görmez, o
     yüzden "bilinmiyor" ayrı KPI'dır. */
  function esikModulu(b, mb, builds) {
    var esik = mb ? mb.min_build : null;
    var dokuman = (mb && mb.doc) || null;
    var byBuild = (builds && builds.byBuild) || {};
    var kapiAcik = esik != null && esik > 0;

    var surumSatir = Object.keys(byBuild).sort(function (x, y) {
      return Number(y) - Number(x);
    }).map(function (s) {
      var altinda = kapiAcik && Number(s) < esik;
      return '<tr><td class="sayi sol">' + b.e(s) + '</td>' +
        '<td class="sayi">' + b.sayi(byBuild[s]) + '</td>' +
        '<td>' + (altinda ? b.rozet('eşiğin altında', 'hata')
                          : b.rozet('geçer', 'aktif')) + '</td></tr>';
    }).join('');
    if (builds && builds.unknown > 0) {
      // Başlıksız istek 0 sayılır (K7): kapı açıkken bunlar da kilitli.
      surumSatir += '<tr><td class="sayi sol">bilinmiyor (≤34)</td>' +
        '<td class="sayi">' + b.sayi(builds.unknown) + '</td>' +
        '<td>' + (kapiAcik ? b.rozet('kilitli (başlıksız)', 'hata')
                           : b.rozet('geçer', 'aktif')) + '</td></tr>';
    }

    var sonYazim = dokuman
      ? 'Son yazım: eşik ' + b.sayi(dokuman.minBuild) + ' — "' +
        b.e(dokuman.reason || '') + '" · ' +
        b.e(dokuman.updatedBy || '?') + ' · ' +
        b.tarih(dokuman.updatedAt, true)
      : (mb ? 'Henüz panelden yazılmadı — doküman yok; eşik yalnız env ' +
              'tabanından.'
            : 'Eşik durumu alınamadı.');

    return '<div class="kpi-izgara">' +
      b.kpi(mb ? b.sayi(esik) : '—', 'Etkin eşik', {
        altin: kapiAcik,
        alt: kapiAcik ? 'X-App-Build < eşik → 426' : 'kapı kapalı (0)'
      }) +
      b.kpi(mb ? b.sayi(mb.env_floor) : '—', 'Env tabanı',
        { alt: 'RYTHO_MIN_BUILD — isteğe bağlı' }) +
      b.kpi(mb ? b.sayi(mb.below_min_live) : '—',
        'Eşiğin altında (canlı)', { alt: 'appBuild < eşik · count()' }) +
      b.kpi(builds ? b.sayi(builds.unknown) : '—', 'Bilinmiyor (≤34)',
        { alt: 'başlık göndermeyen · son toplama' }) +
      '</div>' +
      (surumSatir
        ? b.tablo(['Sürüm (versionCode)', 'Kullanıcı', 'Durum'], surumSatir)
        : b.bosDurum('Henüz sürüm aynası yok — 35+ istemcinin ilk ' +
            'kimlikli isteğiyle dolar, gecelik toplamayla görünür.')) +
      '<form id="esik-form" class="form-satir">' +
      b.girdi('min_build', 'Yeni eşik (versionCode; 0 = kapat)', 'number') +
      b.girdi('reason', 'Gerekçe (zorunlu, en az 3 karakter)', '',
        'girdi-genis') +
      '<button class="buton ikincil kucuk" type="submit">Eşiği yaz</button>' +
      '</form>' +
      '<p id="esik-sonuc" class="dipnot">' + sonYazim + '</p>' +
      '<p class="dipnot">Sunucu 0\'dan büyük eşiği ancak o sürümü canlı ' +
      'görmüşse kabul eder (K9): önce yeni sürümü bir cihazda açıp giriş ' +
      'yap. Sıra: rules → backend → AAB mağazada → eşik ' +
      '(docs/konsol-gorevleri.md §6).</p>';
  }

  function esikFormunuBagla() {
    var form = document.getElementById('esik-form');
    if (!form) return;
    form.onsubmit = async function (ev) {
      ev.preventDefault();
      var f = ev.target;
      var sonucEl = document.getElementById('esik-sonuc');
      var yeni = parseInt(f.min_build.value, 10);
      var gerekce = (f.reason.value || '').trim();
      if (isNaN(yeni) || yeni < 0 || gerekce.length < 3) {
        sonucEl.textContent = 'Eşik 0 ya da pozitif tam sayı + en az 3 ' +
          'karakter gerekçe zorunlu.';
        return;
      }
      var soru = yeni > 0
        ? 'Eşik ' + yeni + ' olacak: X-App-Build < ' + yeni +
          ' olan HER istek 426 alır — başlık göndermeyen eski istemciler ' +
          '(≤34) dahil. Gerekçe: "' + gerekce + '". Onaylıyor musun?'
        : 'Kapı KAPANACAK (eşik 0; env tabanı varsa o geçerli kalır). ' +
          'Gerekçe: "' + gerekce + '". Onaylıyor musun?';
      if (!confirm(soru)) return;
      var dugme = f.querySelector('button');
      dugme.disabled = true;
      try {
        await RY.post('/api/v1/admin/min-build',
          { min_build: yeni, reason: gerekce });
        RY.rotaYenile();
      } catch (h) {
        dugme.disabled = false;
        sonucEl.textContent = RY.hataMetni(h);
      }
    };
  }

  RY.gorunumler.sistem = async function (icerik) {
    var b = RY.b;
    // Hepsi paralel ve hepsi yardımcı: sağlık ekranı tek uç düştü diye
    // düşmemeli — düşen bölüm boş durumuyla görünür.
    var hepsi = await Promise.all([
      RY.saglik('/health').catch(function () { return null; }),
      RY.saglik('/health/rag').catch(function () { return null; }),
      RY.get('/api/v1/admin/stats?days=1')
        .catch(function () { return { days: [] }; }),
      RY.get('/api/v1/admin/notify-runs?days=7')
        .catch(function () { return { runs: [] }; }),
      RY.get('/api/v1/admin/audit?limit=50')
        .catch(function () { return { entries: [] }; }),
      RY.get('/api/v1/admin/min-build')
        .catch(function () { return null; })
    ]);
    var saglik = hepsi[0], rag = hepsi[1], veri = hepsi[2];
    var kosular = hepsi[3], iz = hepsi[4], minBuild = hepsi[5];

    var son = (veri.days || [])[0] || {};
    var sys = son.system || {}, sosyal = son.social || {};

    var kosuSatir = (kosular.runs || []).map(function (k) {
      var atlanan = k.skipped || {};
      var atlananOzet = Object.keys(atlanan).map(function (g) {
        return g + ':' + atlanan[g];
      }).join(' · ') || '—';
      return '<tr><td class="sayi sol">' + b.e(k.date || '') + '</td>' +
        '<td>' + b.e(k.type || '') + '</td>' +
        '<td class="sayi">' + b.sayi(k.runs) + '</td>' +
        '<td class="sayi">' + b.sayi(k.scanned) + '</td>' +
        '<td class="sayi">' + b.sayi(k.sent) + '</td>' +
        '<td>' + (k.failed
          ? b.rozet(String(k.failed), 'hata')
          : b.rozet('0', 'aktif')) + '</td>' +
        '<td title="' + b.e(atlananOzet) + '">' + b.e(atlananOzet) +
        '</td></tr>';
    }).join('');

    var izSatir = (iz.entries || []).map(function (k) {
      return '<tr><td class="sayi sol">' + b.tarih(k.at, true) + '</td>' +
        '<td>' + b.e(k.adminEmail || k.adminUid || '') + '</td>' +
        '<td>' + b.rozet(k.action || '?', 'notr') + '</td>' +
        '<td class="sayi">' + b.e(k.targetUid || '—') + '</td>' +
        '<td class="sayi sol">' +
        b.e(JSON.stringify(k.params || {})) + '</td></tr>';
    }).join('');

    icerik.innerHTML =
      '<div class="kpi-izgara">' +
      b.kpi(saglik ? 'AÇIK' : 'KAPALI', 'Backend', { altin: !!saglik }) +
      b.kpi(rag ? b.e(rag.status).toUpperCase() : '—', 'RAG tabanı') +
      b.kpi(b.sayi(sys.aiCacheCount), 'AI önbellek dokümanı') +
      b.kpi(b.sayi(sys.conversationsCount), 'Konuşma') +
      b.kpi(b.sayi(sosyal.reportsOpen), 'Şikayet kuyruğu') +
      b.kpi(son.durationMs != null ? b.sayi(son.durationMs) + ' ms' : '—',
        'Son toplama süresi') +
      '</div>' +
      b.modul('Zorunlu güncelleme',
        esikModulu(b, minBuild, son.builds || null),
        b.etiket('canlı · config/app')) +
      '<div class="modul"><div class="modul-baslik">' +
      '<h2>Bildirim sağlığı</h2>' + b.etiket('7 gün') + '</div>' +
      (kosuSatir
        ? b.tablo(['Gün', 'Tür', 'Koşu', 'Taranan', 'Gönderilen',
                   'Başarısız', 'Atlanan'], kosuSatir)
        : b.bosDurum('Henüz koşu kaydı yok — bir sonraki zamanlayıcı ' +
            'koşusuyla dolar (AP-turu öncesi koşular kayıtsızdı).')) +
      '</div>' +
      '<div class="modul"><div class="modul-baslik">' +
      '<h2>Denetim izi</h2>' + b.etiket('son 50') + '</div>' +
      (izSatir
        ? b.tablo(['Zaman', 'Yönetici', 'Eylem', 'Hedef', 'Ayrıntı'],
                  izSatir)
        : b.bosDurum('Henüz denetim kaydı yok — yazan ilk admin eylemiyle ' +
            'başlar.')) +
      '</div>' +
      '<div class="panel"><h2>RAG ayrıntısı</h2>' +
      '<div class="tablo-sarici"><pre class="mono" style="font-size:12px">' +
      b.e(JSON.stringify(rag, null, 2)) + '</pre></div></div>';

    esikFormunuBagla();
  };
})();
