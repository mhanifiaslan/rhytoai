# Cihaz üstü segmentasyon modelini indirir.
#
# Model repoya KONMUYOR: 15,6 MB ve git geçmişine bir kez girdiğinde bir daha
# çıkmıyor. Kaynak Google'ın kalıcı adresi ve dosya Apache 2.0 lisanslı
# (model kartı: "LICENSED UNDER Apache License, Version 2.0", Google,
# 10 Mayıs 2023) — yani dağıtım engeli yok, mesele yalnızca depo hijyeni.
#
# Tercihi değiştirmek kolay: `.gitignore` içindeki satırı silip dosyayı
# commit'lemek yeterli. Tersi kolay değil, o yüzden varsayılan bu.
#
# Kullanım:  apps/mobile klasöründen  ./scripts/fetch_models.ps1
$ErrorActionPreference = "Stop"

# Ileri bolu: macOS'ta ters bolu AYIRAC DEGIL, dosya adinin parcasi.
$hedefKlasor = Join-Path $PSScriptRoot "../assets/models"
$hedef = Join-Path $hedefKlasor "selfie_multiclass_256x256.tflite"
$kaynak = "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite"

if (-not (Test-Path $hedefKlasor)) {
    New-Item -ItemType Directory -Force $hedefKlasor | Out-Null
}

if (Test-Path $hedef) {
    Write-Host "Model zaten var: $hedef"
    exit 0
}

Write-Host "Model indiriliyor (~16 MB)..."
Invoke-WebRequest -Uri $kaynak -OutFile $hedef

$boyut = (Get-Item $hedef).Length
if ($boyut -lt 10MB) {
    Remove-Item $hedef
    throw "Indirilen dosya beklenenden kucuk ($boyut bayt); silindi."
}
Write-Host ("Tamam: {0:N1} MB" -f ($boyut / 1MB))
