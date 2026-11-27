#!/bin/bash
# Script de Instalação - Bellatrix Pipeline (Linux/Mac)
echo "🚀 Iniciando instalação da Bellatrix Pipeline..."

# 1. Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale o Python 3.10+."
    exit 1
fi

# 2. Cria venv
echo "📦 Criando ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

# 3. Instala dependências
echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verifica FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ ATENÇÃO: FFmpeg não encontrado. Instale com 'sudo apt install ffmpeg' (Ubuntu/Debian)."
else
    echo "✅ FFmpeg encontrado."
fi

# 5. Configura .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Arquivo .env criado."
fi

# 6. Cria pastas
mkdir -p output temp_cortes

echo "✅ Instalação concluída!"
echo "Para ativar o ambiente no futuro, use: source venv/bin/activate"
