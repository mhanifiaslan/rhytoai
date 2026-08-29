/* Sistem: sağlık + bildirim koşuları (notifyRuns) + denetim izi
   (adminAudit) + RAG ayrıntısı.
   Uçlar: /health, /health/rag, /admin/stats, /admin/notify-runs,
   /admin/audit. */
(function () {
  'use strict';

  var RY = window.RY;
  RY.gorunumler = RY.gorunumler || {};

  RY.gorunumler.sistem = async function (icerik) {
    var b = RY.b;
    var saglik = await RY.saglik('/health').catch(function () { return null; });
    var rag = await RY.saglik('/health/rag').catch(function () { return null; });
    var veri = await RY.get('/api/v1/admin/stats?days=1');
    var kosular = await RY.get('/api/v1/admin/notify-runs?days=7')
      .catch(function () { return { runs: [] }; });
    var iz = await RY.get('/api/v1/admin/audit?limit=50')
      .catch(function () { return { entries: [] }; });

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
      '<div class="panel"><h2>Bildirim sağlığı (7 gün)</h2>' +
      (kosuSatir
        ? b.tablo(['Gün', 'Tür', 'Koşu', 'Taranan', 'Gönderilen',
                   'Başarısız', 'Atlanan'], kosuSatir)
        : b.bosDurum('Henüz koşu kaydı yok — bir sonraki zamanlayıcı ' +
            'koşusuyla dolar (AP-turu öncesi koşular kayıtsızdı).')) +
      '</div>' +
      '<div class="panel"><h2>Denetim izi</h2>' +
      (izSatir
        ? b.tablo(['Zaman', 'Yönetici', 'Eylem', 'Hedef', 'Ayrıntı'],
                  izSatir)
        : b.bosDurum('Henüz denetim kaydı yok — yazan ilk admin eylemiyle ' +
            'başlar.')) +
      '</div>' +
      '<div class="panel"><h2>RAG ayrıntısı</h2>' +
      '<div class="tablo-sarici"><pre class="mono" style="font-size:12px">' +
      b.e(JSON.stringify(rag, null, 2)) + '</pre></div></div>';
  };
})();
