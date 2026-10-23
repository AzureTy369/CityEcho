$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "backend"
python -m pytest backend\tests -q
npm --prefix frontend run build

Write-Host "CityEcho verification passed." -ForegroundColor Green
