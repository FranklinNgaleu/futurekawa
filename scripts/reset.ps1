Write-Host "Resetting FutureKawa environment..."
docker compose down -v
docker compose up --build