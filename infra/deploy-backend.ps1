# RythoAI backend'i Cloud Run'a deploy eder.
# Kullanım: infra klasöründen ./deploy-backend.ps1
$ErrorActionPreference = "Stop"

$PROJECT = "rhytoai"
$REGION = "us-central1"
$SERVICE = "rytho-backend"
$IMAGE = "us-central1-docker.pkg.dev/$PROJECT/rytho/backend:latest"

$repoRoot = Split-Path -Parent $PSScriptRoot

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
    --set-env-vars "RYTHO_DEV_MODE=0,GOOGLE_CLOUD_PROJECT=$PROJECT" `
    --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest"

Write-Host "Tamamlandı. Servis URL'i:"
gcloud run services describe $SERVICE --project $PROJECT --region $REGION --format "value(status.url)"
