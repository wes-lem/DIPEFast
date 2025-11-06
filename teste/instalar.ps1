# Script para instalar dependências de testes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Instalando dependências de testes" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ativar venv
& "..\venv\Scripts\Activate.ps1"

# Instalar dependências
pip install -r ..\requirements.txt

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Instalação concluída!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para executar os testes, use:" -ForegroundColor Yellow
Write-Host "  pytest teste/" -ForegroundColor Yellow
Write-Host ""

