# Bellatrix Pipeline — Microserviço de Edição de Vídeo com IA

Microserviço **FastAPI** para edição automatizada de reportagens, alinhado à **Cartilha de Edição de Vídeo para Reportagem** e integrado ao ecossistema **IRIS** via **Ollama (llama3.1:8b)** e **Whisper (CPU)**.

---

## 🎯 Visão Geral

| Item | Detalhe |
|------|---------|
| **Tipo** | Microserviço Python (FastAPI + Uvicorn) |
| **Porta** | 8012 (interno Docker) → `127.0.0.1:8012` no host |
| **Rede** | `infra-stack_default` (Docker externa) |
| **IA** | Ollama `llama3.1:8b` (via `http://ai-ollama:11434/api/chat`) + Whisper `medium` (CPU) |
| **GPU** | **Não usa** — Whisper roda em CPU (`GGML_CPU_ALL=1`) para não disputar a GPU de 8 GB do `ai-ollama` |
| **Exportação** | TV: MXF OP1a / XDCAM HD 50 / 1920×1080 / 29.97 fps / 48 kHz 24-bit / Upper Field First<br>Web: MP4 / H.264 / loudnorm I=-14 TP=-1.5 LRA=11 |
| **Interface** | `frontend_teste.html` servido em `/` (sem autenticação, para testes locais) |

---

## 🧠 Lógica Editorial (Cartilha + IRIS)

O prompt enviado ao **LLaMA** inclui:

### 5 Papéis Editoriais (Cartilha)
1. **LOCOÇÃO / OFF** — narração do repórter (voz guia)
2. **PASSAGEM DE REPÓRTER** — repórter em cena (ponte, contextualização)
3. **SONORAS / ENTREVISTAS** — depoimentos de fontes/personagens (voz A1)
4. **IMAGENS DE COBERTURA / ILUSTRAÇÃO** — b-roll, arquivos, cenas de apoio
5. **SOBE SOM / AMBIENTE** — som ambiente natural sem narração

### 3 Ângulos Editoriais (IRIS)
| Opção | Foco | Prioridade |
|-------|------|------------|
| **1 — Informativo** | Fatos, objetividade, telejornalismo padrão | Locução/OFF + Passagem Repórter + Sonoras factuais |
| **2 — Humanizado** | Emoção, histórias humanas, coerência de tom | Sonoras/Entrevistas com carga emocional + Sobe Som |
| **3 — Dinâmico** | Ação, movimento, ritmo visual | Cobertura/Ilustração com movimento + Sobe Som + Sonoras curtas |

### Guardrails (Anti-alucinação)
- Não inferir o que não está na transcrição/texto
- Separar fatos objetivos de carga emocional
- Não inventar nomes, números, locais, declarações
- Coerência entre gravidade do fato e tom da edição
- **Nunca** cortar depoimentos de vítimas, menores ou pessoas que não podem falar

---

## 🚀 Como Rodar

### Pré-requisitos
- Docker + Docker Compose
- Rede `infra-stack_default` existente (criada pelo `infra-stack`)
- Container `ai-ollama` rodando na mesma rede com modelo `llama3.1:8b`

### Subir o Serviço
```bash
cd /srv/newsrag/bellatrix-pipeline
docker compose up -d --build
```

### Verificar Saúde
```bash
curl http://127.0.0.1:8012/health
# {"status":"ok"}
```

### Acessar a Interface de Teste

#### Opção A — Túnel SSH (recomendado para VMs remotas)
```bash
# No seu computador local:
ssh -L 8012:127.0.0.1:8012 usuario@<IP_DO_SERVIDOR>

# Depois abra no navegador:
http://localhost:8012/
```

#### Opção B — Acesso direto (se na mesma rede/localhost)
```
http://<IP_DO_SERVIDOR>:8012/
```
> **Nota:** A porta 8012 está bindada em `127.0.0.1` no Docker. Para acesso externo direto, configure firewall/Nginx no host ou use o túnel SSH acima.

---

## 📡 Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Serve `frontend_teste.html` |
| `GET` | `/health` | Health check (Docker + monitoramento) |
| `POST` | `/processar` | Pipeline completo (upload → 3 vídeos) |
| `GET` | `/output/<arquivo>` | Download dos vídeos gerados |

### `POST /processar` — Payload (multipart/form-data)
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `file` | File | **Sim** | Vídeo bruto (MP4, MXF, MOV, MKV — máx ~2GB) |
| `duracao_alvo` | int | Não (padrão: 180) | Duração alvo por opção em segundos (5–600) |
| `plataforma` | string | Não (padrão: `web`) | `web` (MP4) ou `tv` (MXF) |
| `texto_materia` | string | Não | Roteiro/OFF do repórter |
| `prompt_customizado` | string | Não | Instrução extra para a IA (ex: "foque no depoimento da dona Maria") |
| `programa` | string | Não | Nome do programa (ex: "Bom Dia Inter") |
| `editoria` | string | Não | Editoria/perfil (ex: "Cidades / Hard News") |

### Resposta de Sucesso
```json
{
  "status": "success",
  "arquivos": [
    "/output/IN2_ED_271126_VT_OPCAO1_Informativo.mp4",
    "/output/IN2_ED_271126_VT_OPCAO2_Humanizado.mp4",
    "/output/IN2_ED_271126_VT_OPCAO3_Dinamico.mp4"
  ]
}
```

---

## 🧪 Testes Automatizados (58 testes — 100% passando)

```bash
# Dentro do container:
docker exec bellatrix-api python -m pytest -v tests/

# Ou localmente (precisa do container rodando):
docker compose exec bellatrix-api python -m pytest -v tests/
```

### Suíte de Testes
| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_prompt_cartilha.py` | 5 | Papéis editoriais, 3 ângulos IRIS, duração alvo, contexto editorial, prompt customizado |
| `test_api_processar.py` | 8 | `/processar` (validação tipo, parâmetros, erros, web/tv, URLs `/output/`) |
| `test_integration_synthetic.py` | 5 | **Pipeline real** com vídeo sintético ffmpeg (5s) — web, tv, duração curta, contexto completo |
| `test_frontend.py` | 6 | HTML carrega, campos obrigatórios, URL relativa, nomes opções, links download |
| `test_ai.py` | 7 | Transcriber, analyzer (sucesso, fallback, prompt customizado, nomes fallback) |
| `test_core.py` | 13 | Detector (fades, fallback), cutter (web/tv, frame rate), validator, ffprobe |
| `test_governance.py` | 10 | Sanitização, nomenclatura (TV/Web), ajuste de frames |
| `test_cartilha.py` | 4 | Export MXF XDCAM50, MP4 loudnorm, prompt LLM, API estrita |
| `test_api.py` | 2 | Health check, processar com mock real |

**Total: 58 testes** — rodam com mocks (sem rede externa) + 5 testes de integração real com vídeo sintético.

---

## 📁 Estrutura do Projeto

```
/srv/newsrag/bellatrix-pipeline/
├── ai/
│   ├── analyzer.py          # Prompt LLaMA + chamada Ollama (Cartilha + IRIS)
│   └── transcriber.py       # Whisper (pywhispercpp) → SRT
├── api/
│   └── main.py              # FastAPI app (/, /health, /processar, /output)
├── core/
│   ├── cutter.py            # FFmpeg: corte, concatenação, legendas, metadados
│   ├── detector.py          # Detecção de fades pretos (OpenCV)
│   ├── governance.py        # Nomes de arquivo, ajuste frames, sanitização
│   └── validator.py         # ffprobe: valida streams vídeo/áudio
├── tests/                   # 58 testes (pytest + mocks + integração sintética)
├── output/                  # Vídeos gerados (montado em /app/output no container)
├── logs/                    # Logs da aplicação
├── data/                    # Dados temporários
├── frontend_teste.html      # Interface de teste (sem auth)
├── pipeline_runner.py       # Orquestração do pipeline
├── main.py                  # CLI (python main.py -i video.mp4 ...)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env                     # LLM_API_URL, LLM_MODEL, WHISPER_MODEL
```

---

## ⚙️ Variáveis de Ambiente (`.env`)

```bash
# LLM (Ollama na rede infra-stack_default)
LLM_API_URL=http://ai-ollama:11434/api/chat
LLM_MODEL=llama3.1:8b

# Whisper (CPU)
WHISPER_MODEL=medium

# Opcional: OpenAI (fallback futuro)
# OPENAI_API_KEY=sua_chave
```

---

## 🐳 Docker Compose (Resumo)

```yaml
services:
  bellatrix-api:
    build: .
    container_name: bellatrix-api
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8012/health', timeout=8)"]
      interval: 60s; timeout: 15s; retries: 3; start_period: 30s
    env_file: .env
    environment:
      WHISPER_MODEL: ${WHISPER_MODEL:-medium}
      GGML_CPU_ALL: "1"
      OUTPUT_DIR: /app/output
    ports: ["127.0.0.1:8012:8012"]
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./output:/app/output
    networks:
      - default
networks:
  default:
    external: true
    name: infra-stack_default
```

---

## 🔧 Desenvolvimento Local

```bash
# Rodar testes (dentro do container)
docker exec bellatrix-api python -m pytest -v tests/

# Ver logs
docker logs -f bellatrix-api

# Acessar shell no container
docker exec -it bellatrix-api bash

# Rebuild após mudanças no código Python
docker compose up -d --build
```

---

## 📦 Deploy em Produção (Padrão IRIS)

> **Não integra Django/IRIS automaticamente** — este documento serve de referência.

1. **Build da imagem** a partir do checkout `main`:
   ```bash
   docker build -t bellatrix-pipeline:v1.3 .
   ```
2. **Tag de rollback**: `docker tag bellatrix-pipeline:latest bellatrix-pipeline:antes-<data>`
3. **Subida**: `docker compose up -d --no-build --no-deps bellatrix-api`
4. **Validação**: `curl http://127.0.0.1:8012/health` + teste de vídeo real

---

## 📋 Status Atual

| Componente | Status |
|------------|--------|
| Pipeline completo (upload → 3 opções) | ✅ Funcionando |
| Whisper CPU (medium) | ✅ Transcreve |
| Ollama `llama3.1:8b` (rede infra-stack) | ✅ Conectado |
| Export TV (MXF XDCAM HD 50) | ✅ Testado |
| Export Web (MP4 H.264 loudnorm) | ✅ Testado |
| Interface de teste (`frontend_teste.html`) | ✅ Visual moderno, responsivo |
| Testes automatizados (58) | ✅ 100% passando |
| Integração IRIS/Django | ⏳ Pendente (fora do escopo) |
| Autenticação/Rate limiting | ⏳ Pendente (fora do escopo) |

---

## 📄 Licença

Uso interno — InterTV / Projeto IRIS.