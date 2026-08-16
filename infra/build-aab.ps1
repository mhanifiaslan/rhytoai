# RythoAI yayin AAB'sini uretir ve SATIN ALMA ANAHTARININ paketde oldugunu
# DOGRULAR.
#
# Kullanim: infra klasorunden  ./build-aab.ps1
#
# ## Neden bu betik var
#
# 2026-08-16'da 1.5.0+17 duz `flutter build appbundle --release` ile
# uretildi. RevenueCat genel anahtari kaynakta DEGIL, derleme aninda
# `--dart-define-from-file` ile giriyor (bkz. lib/core/subscription.dart).
# Define verilmeyince `String.fromEnvironment` bos dondu, `billingConfigured`
# false oldu, SDK hic baslatilmadi ve cihazda hem abonelik hem jeton
# paketleri "Satin alma su an kullanilamiyor" dedi.
#
# Kotu tarafi sessiz olmasiydi: derleme BASARIYLA bitti, testler yesildi,
# imza ve surum kodu dogruydu. Kusur ancak magaza ekraninda goruldu.
#
# Bu yuzden burada iki kapi var: define dosyasi YOKSA derleme hic
# baslamaz; derleme bittikten sonra uretilen Dart snapshot'i icinde
# anahtar ARANIR ve bulunmazsa betik hata verir. Ikincisi onemli olan -
# "define'i gectim" demek yetmez, paketde OLDUGU olculur.
#
# NOT: bu dosyada ASCII DISI KARAKTER KULLANMA. PowerShell 5.1 BOM'suz
# .ps1 dosyalarini ANSI olarak okur; tek bir uzun tire betigi ayristirma
# hatasiyla dusuruyor (bir kez dusurdu).
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$mobil = Join-Path $repoRoot "apps\mobile"
$defines = Join-Path $mobil "dart_defines.local.json"
$flutter = "C:\flutter\bin\flutter.bat"

if (-not (Test-Path $defines)) {
    throw ("dart_defines.local.json bulunamadi ($defines). " +
           "dart_defines.example.json'u kopyalayip RevenueCat anahtarlarini " +
           "yaz. Bu dosya gitignore'da; depoya GIRMEZ.")
}

# Anahtarin gercek magaza anahtari oldugunu da soyle: `test_` onekli
# anahtar RevenueCat Test Store'a aittir ve satin almalari SIMULE eder.
# Yayin AAB'sinde bu sessiz bir tuzak olurdu.
$defineIcerik = Get-Content $defines -Raw | ConvertFrom-Json
$androidKey = $defineIcerik.REVENUECAT_ANDROID_KEY
if (-not $androidKey) {
    throw "dart_defines.local.json icinde REVENUECAT_ANDROID_KEY yok."
}
if ($androidKey.StartsWith("test_")) {
    Write-Warning ("REVENUECAT_ANDROID_KEY 'test_' onekli - RevenueCat Test " +
                   "Store anahtari. Satin almalar SIMULE edilir, gercek " +
                   "odeme alinmaz.")
}

Write-Host "1/3 Surum bilgisi..."
$surum = (Select-String -Path (Join-Path $mobil "pubspec.yaml") `
    -Pattern "^version:\s*(.+)$").Matches[0].Groups[1].Value.Trim()
Write-Host "    pubspec version: $surum"

Write-Host "2/3 AAB derleniyor (dart-define ile)..."
Push-Location $mobil
try {
    $eskiTercih = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $flutter build appbundle --release `
        --dart-define-from-file=dart_defines.local.json
    $kod = $LASTEXITCODE
    $ErrorActionPreference = $eskiTercih
    if ($kod -ne 0) { throw "flutter build appbundle basarisiz (cikis $kod)." }
} finally {
    Pop-Location
}

Write-Host "3/3 Paket dogrulaniyor..."
$aab = Join-Path $mobil "build\app\outputs\bundle\release\app-release.aab"
if (-not (Test-Path $aab)) { throw "AAB uretilmedi: $aab" }

# Dart snapshot'i (libapp.so) cikarilip icinde anahtar ARANIR. Sabit
# dizeler AOT snapshot'a gomulur; define gecmediyse dize hic olmaz.
$gecici = Join-Path $env:TEMP ("rytho-aab-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force $gecici | Out-Null
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($aab)
    try {
        $girdi = $zip.Entries | Where-Object {
            $_.FullName -eq "base/lib/arm64-v8a/libapp.so" }
        if (-not $girdi) { throw "AAB icinde arm64 libapp.so yok." }
        $libapp = Join-Path $gecici "libapp.so"
        [System.IO.Compression.ZipFileExtensions]::ExtractToFile(
            $girdi, $libapp, $true)
    } finally { $zip.Dispose() }

    $metin = [System.Text.Encoding]::ASCII.GetString(
        [System.IO.File]::ReadAllBytes($libapp))
    # Anahtarin TAMAMI aranir, yalnizca oneki degil: yanlis anahtarla
    # derlenmis bir paket de gecmemeli.
    if ($metin.Contains($androidKey)) {
        Write-Host "    OK: RevenueCat Android anahtari pakette."
    } else {
        throw ("RevenueCat anahtari pakette YOK. Satin almalar cihazda " +
               "'kullanilamiyor' diyecek. Derleme dart-define'siz mi " +
               "yapildi?")
    }

    $entitlement = $defineIcerik.RYTHO_PLUS_ENTITLEMENT
    if ($entitlement -and -not $metin.Contains($entitlement)) {
        throw ("Yetki kimligi ('$entitlement') pakette yok; abonelik " +
               "satin alinsa bile acilmaz.")
    }
    Write-Host "    OK: yetki kimligi pakette ('$entitlement')."
} finally {
    Remove-Item -Recurse -Force $gecici -ErrorAction SilentlyContinue
}

$boyut = [math]::Round((Get-Item $aab).Length / 1MB, 1)
Write-Host ""
Write-Host "Tamamlandi: $aab ($boyut MiB, surum $surum)"
Write-Host "Imzayi dogrulamak icin: keytool -printcert -jarfile `"$aab`""
