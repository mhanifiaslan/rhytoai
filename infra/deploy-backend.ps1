# RythoAI backend'i Cloud Run'a deploy eder.
# Kullanım: infra klasöründen ./deploy-backend.ps1
$ErrorActionPreference = "Stop"

$PROJECT = "rhytoai"
$REGION = "us-central1"
$SERVICE = "rytho-backend"
$IMAGE = "us-central1-docker.pkg.dev/$PROJECT/rytho/backend:latest"

$repoRoot = Split-Path -Parent $PSScriptRoot

# Vektor artefakti imaja gomuluyor; korpusla uyumsuzsa her sogut baslatma
# yeniden vektorleme faturasi cikarir ve ilk istekler anahtar kelime moduna
# duser. Bu yuzden deploy'dan ONCE kapsama dogrulanir.
Write-Host "0/2 Vektor artefakti dogrulaniyor..."
$pythonExe = Join-Path $repoRoot "backend\.venv\Scripts\python.exe"
if (Test-Path $pythonExe) {
    # PS 5.1 tuzagi: dogrulama betigi INFO loglarini STDERR'e yazar ve
    # ErrorActionPreference=Stop bunu gercek hata sanip deploy'u yarida
    # keser ("INFO [tr] 42 parca, 0 eksik vektor" bir kez tam boyle kesti).
    # Cikti dosyaya yonlendirilir, karar YALNIZCA cikis koduna bakar.
    $eskiTercih = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $pythonExe (Join-Path $repoRoot "backend\scripts\build_embeddings.py") --check 2>$null
    $kontrolKodu = $LASTEXITCODE
    $ErrorActionPreference = $eskiTercih
    if ($kontrolKodu -ne 0) {
        throw "Vektor artefakti korpusla uyumsuz. Once su komutu calistir: backend\scripts\build_embeddings.py"
    }
} else {
    Write-Warning "backend\.venv bulunamadi; artefakt kapsamasi DOGRULANMADI."
}

Write-Host "1/2 Cloud Build ile imaj derleniyor..."
gcloud builds submit $repoRoot `
    --project $PROJECT `
    --config "$PSScriptRoot/cloudbuild.yaml"

Write-Host "2/2 Cloud Run'a deploy ediliyor..."
gcloud run deploy $SERVICE `
    --project $PROJECT `
    --region $REGION `
    --image $IMAGE `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 3 `
    --min-instances 1 `
    # DIKKAT: --set-env-vars mevcut degiskenleri TUMUYLE degistirir.
    # Konsoldan elle verilen RYTHO_FORCE_PLUS / RYTHO_TOKENS_ENFORCE gibi
    # bayraklar bir sonraki deploy'da SESSIZCE silinir. Jeton zorlamasi
    # kalici acilacaksa (M4 gozlemi sonrasi) su satira eklenmeli:
    #   RYTHO_TOKENS_ENFORCE=1
    # RYTHO_MIN_BUILD (F3): istemci versionCode'u bundan kucukse zorunlu
    # guncelleme ekranina kilitlenir. 0 = kapi kapali. Eski surumleri
    # dislayacak bir yayin yapildiginda buradaki deger artirilir.
    --set-env-vars "RYTHO_DEV_MODE=0,GOOGLE_CLOUD_PROJECT=$PROJECT,RYTHO_MIN_BUILD=0" `
    --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest,REVENUECAT_WEBHOOK_SECRET=REVENUECAT_WEBHOOK_SECRET:latest,NOTIFY_SCHEDULER_SECRET=NOTIFY_SCHEDULER_SECRET:latest"

# --min-instances 1 BILINCLI VE UCRETLI bir karar.
#
# Olculen: servis sifira inince sonraki ilk istek 14,65 saniye suruyordu
# (hemen sonraki 0,0036 sn). Kullanicinin "bekliyor bekliyor bekliyor, sonra
# mesajlar geliyor" diye bildirdigi sey buydu. Bir instance surekli ayakta
# tutmak bunu bitiriyor; bedeli aylik ~25 USD ve kullanici sayisindan
# BAGIMSIZ, yani buyudukce kullanici basina dusen pay azaliyor.
#
# Bu tek basina yetmiyor: --max-instances 3 oldugu icin yuk 2. ve 3.
# instance'i actirdiginda onlar hala soguk basliyor. Onun icin agir
# kutuphaneler modul duzeyinden cikarildi (bkz. tests/test_cold_start.py).
#
# Bayrak burada durmali; yalnizca konsoldan verilirse bir sonraki deploy
# sessizce geri alir.
#
# REVENUECAT_WEBHOOK_SECRET olmadan /api/v1/billing/revenuecat 503 doner ve
# hicbir kullanici abone olarak isaretlenemez (dogrulamasiz abonelik yazmaya
# izin verilmiyor). Ayni deger RevenueCat panelindeki webhook'un Authorization
# basligina da yazilmali.
#
# NOTIFY_SCHEDULER_SECRET, Cloud Scheduler'in toplu bildirim ucunu tetiklerken
# tasidigi anahtardir. Anahtar ve zamanlayici isleri ./create-scheduler.ps1
# ile kurulur; bu deploy o anahtari konteynere tasir. Tanimsizken uc 503
# doner — acik birakmak, herkesin tum kullanicilara bildirim gonderebilmesi
# demek olurdu.
#
# Gelistirme sirasinda odemesiz test icin --set-env-vars satirina
# RYTHO_FORCE_PLUS=1 eklenebilir; uretimde ASLA acik birakilmamali.

Write-Host "Tamamlandı. Servis URL'i:"
gcloud run services describe $SERVICE --project $PROJECT --region $REGION --format "value(status.url)"
