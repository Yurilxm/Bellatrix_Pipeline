# Bellatrix Pipeline (Microserviço de Edição com IA)

Este projeto é um microserviço de edição automatizada de vídeo para TV, unindo a inteligência da **Bellatrix** (detecção de fades), a validação do **Sirius** (integridade de arquivos) e a precisão do **Nano** (corte em MXF).

## 🚀 Funcionalidades
- **Validação (Sirius):** Verifica integridade do vídeo via \fprobe\ (gaps, codecs, streams) antes de processar.
- **Governança (Bellatrix):** Sanitiza nomes de arquivos, valida FPS (29.97) e renomeia no padrão \CM{codigo}_{nome}\.
- **Transcrição (Whisper):** Usa \pywhispercpp\ para transcrever o áudio localmente (sem depender de GPUs ou CTranslate2).
- **Decisão Editorial (LLM):** Integração com Ollama/LLaMA para escolher os melhores trechos (com fallback seguro).
- **Corte e Montagem (FFmpeg/Nano):** Corta com ajuste de frames e suporta formatos web (mp4) e broadcast (mxf).
- **Legendas:** Embuti legendas no vídeo final.

## 🛠️ Instalação

**Windows:**
\\powershell
.\setup.ps1
\
**Linux / Mac:**
\\ash
bash setup.sh
\
## 💻 Como Usar (CLI)

Para processar um vídeo localmente:
\\ash
python main.py -i caminho/do/video.mp4 -d 180 -o mp4
\
## 🌐 Como Usar (Microserviço API)

Suba o servidor FastAPI:
\\ash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
\
Acesse a documentação interativa (Swagger) em: \http://localhost:8000/docs
**Endpoints disponíveis:**
- \GET /health\: Verifica se o serviço está online.
- \POST /metadata\: Retorna metadados do vídeo (para interfaces de edição).
- \POST /processar\: Recebe o vídeo, aplica a pipeline de IA e retorna o vídeo finalizado.

## 🧪 Testes

O projeto conta com cobertura de testes para o core, IA, governança e API:
\\ash
python -m pytest -v tests/
\
## 📦 Arquitetura
- \pi/\: Microserviço FastAPI.
- \core/\: Motor de corte, validação e governança.
- \i/\: Módulos de transcrição (Whisper) e análise (LLM).
- \	ests/\: Testes automatizados.
