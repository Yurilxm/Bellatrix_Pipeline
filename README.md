# Bellatrix Pipeline (Microserviço de Edição com IA)

Este projeto é a evolução do sistema de edição automatizada de vídeo para a emissora. Ele une a inteligência de três sistemas internos (**Bellatrix**, **Sirius** e **Nano**) com modelos de Inteligência Artificial (Whisper e LLaMA) para entregar reportagens editadas, com áudio normalizado e no padrão de exportação exigido pelo MAM (wTVision), seguindo estritamente a **Cartilha de Edição de Vídeo para Reportagem**.

## 🚀 Arquitetura e Funcionalidades

O projeto é um **Microserviço** (FastAPI) e possui uma interface CLI para uso local, atendendo a todos os requisitos técnicos da Cartilha.

### 1. Organização do Projeto (Bins / Pastas)
O sistema padroniza a nomenclatura dos arquivos para o fluxo de trabalho do telejornalismo:
- **EDIÇÃO:** Nomenclatura oficial \`IN2_ED_DDMMYY_ASSUNTO\` para os cortes principais.
- **OFF E PASSAGENS:** Vozes e locuções.
- **IMAGENS DE COBERTURA:** Ilustrações.
- **SOBE SOM:** Áudios ambientes.

### 2. Timeline e Hierarquia de Áudio (Mixagem)
A pipeline processa o áudio respeitando a prioridade de inteligibilidade:
- **V1 (Vídeo):** Imagens e passagens.
- **A1 (Voz Principal):** Normalizada para **-12dB a -6dB** via \`loudnorm\` para clareza máxima.
- **A2 (Som Ambiente):** Atenuado para não cobrir a voz.
- **A3 (Trilhas/efeitos):** Volume sutil.

### 3. Inteligência Artificial Editorial
Diferente de cortes cegos, a IA entende o contexto jornalístico:
- **Whisper (pywhispercpp):** Transcreve o áudio bruto localmente.
- **LLaMA:** Atua como editor sênior. O sistema recebe o **Vídeo Bruto** e o **Texto da Matéria** (roteiro) e a IA seleciona os trechos que cobrem o texto, sem cortar frases no meio.

### 4. Especificações de Exportação (Padrão Broadcast)
O FFmpeg foi configurado com precisão cirúrgica para gerar o arquivo compatível com o MAM (wTVision):
- **Contêiner:** MXF OP1a
- **Preset:** XDCAM HD 50 NTSC 60i
- **Vídeo:** 1920x1080, 29.97 fps, YUV 4:2:2, Entrelaçado (Upper Field First), 50 Mbps.
- **Áudio:** PCM 24 bits, 48.000 Hz, 2 Canais (Estéreo).
- **Ajuste de Corte:** Pula 4 frames no início e adiciona 3 frames no fim (evita o preto da transição).

## 💻 Como Usar (CLI)

Para processar uma matéria, o editor envia o vídeo bruto, o tempo alvo e o texto do roteiro:

\`\`\`bash
python main.py -i "C:\videos\bruto.MXF" -t "O repórter mostra o buraco na rua..." -d 180 -o mxf
\`\`\`

### Argumentos disponíveis:
| Argumento | Obrigatório | Padrão | Descrição |
| :--- | :---: | :--- | :--- |
| \`-i\` ou \`--input\` | **Sim** | - | Caminho do vídeo bruto. |
| \`-t\` ou \`--texto\` | Não | \`""\` | Texto da matéria (roteiro) para guiar a IA. |
| \`-o\` ou \`--output_format\` | Não | \`mxf\` | Formato de saída (\`mxf\` para TV, \`mp4\` para web). |
| \`-d\` ou \`--duracao\` | Não | \`180\` | Duração alvo em segundos. |

## 🌐 Microserviço API (Integração IRIS)

O projeto roda como um servidor web (FastAPI) para ser consumido pela IRIS:
\`\`\`bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

**Endpoints:**
- \`GET /health\`: Status do serviço.
- \`POST /metadata\`: Extrai metadados (para telas de edição manual).
- \`POST /processar\`: Recebe vídeo/texto, aplica a IA e devolve a matéria finalizada.

## 🧪 Testes Automatizados (20 testes)
A qualidade e o cumprimento da Cartilha são validados por 20 testes automatizados (Pytest) que cobrem:
- Validação de integridade (Sirius).
- Parâmetros exatos do FFmpeg (Codec, Bitrate 50M, Áudio 48kHz/24-bit, Upper Field First).
- Ajuste de frames (4 no início, 3 no fim).
- Normalização de áudio (A1).
- Nomenclatura de Bins.
- Prompt da IA (LLaMA).
- Rotas da API e Fallbacks.

\`\`\`bash
python -m pytest -v tests/
\`\`\`

## 📦 Status do Projeto

**Concluído:**
- [x] Integração Bellatrix + Sirius + Nano.
- [x] Transcrição local (Whisper).
- [x] Motor de corte rigoroso (MXF XDCAM HD 50 / MP4).
- [x] Microserviço FastAPI + CLI profissional.
- [x] 20 Testes automatizados baseados na Cartilha.

**Próximos Passos:**
- [ ] Apontar o LLM para o servidor LLaMA oficial da empresa.
- [ ] Criar interface visual (Front-end) na IRIS para o editor selecionar o texto e visualizar os cortes.
