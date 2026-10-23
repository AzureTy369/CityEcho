$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "backend"
python -m pytest backend\tests -q
npm --prefix frontend run build
npm --prefix frontend run test:e2e

Write-Host "CityEcho verification passed." -ForegroundColor Green
