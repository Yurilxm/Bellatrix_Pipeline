# Script de Instalação - Bellatrix Pipeline (Windows)
Write-Host "🚀 Iniciando instalação da Bellatrix Pipeline..." -ForegroundColor Cyan

# 1. Verifica se o Python está instalado
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python não encontrado. Instale o Python 3.10+ e tente novamente." -ForegroundColor Red
    exit 1
}

# 2. Cria o ambiente virtual
Write-Host "📦 Criando ambiente virtual (venv)..." -ForegroundColor Yellow
python -m venv venv

# 3. Ativa o ambiente e instala dependências
Write-Host "📥 Instalando dependências..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verifica se o FFmpeg está instalado (necessário para o motor de corte)
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ ATENÇÃO: FFmpeg não encontrado no PATH do sistema." -ForegroundColor Red
    Write-Host "   Baixe o FFmpeg em https://ffmpeg.org/download.html e adicione ao PATH." -ForegroundColor Red
} else {
    Write-Host "✅ FFmpeg encontrado no sistema." -ForegroundColor Green
}

# 5. Configura o arquivo .env
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "📝 Arquivo .env criado. Lembre-se de configurar a URL do LLaMA." -ForegroundColor Yellow
}

# 6. Cria pastas de trabalho
New-Item -ItemType Directory -Force -Path "output" | Out-Null
New-Item -ItemType Directory -Force -Path "temp_cortes" | Out-Null

Write-Host "✅ Instalação concluída com sucesso!" -ForegroundColor Green
Write-Host "Para rodar o projeto, use: python main.py -h" -ForegroundColor Cyan
