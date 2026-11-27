import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def analisar_e_selecionar(blocos, srt_path, texto_materia="", duracao_alvo=180, prompt_customizado="", contexto_editorial=""):
    print(f"Lendo transcrição e enviando para o LLM (Gerando 3 Opções)...")
    
    with open(srt_path, "r", encoding="utf-8") as f:
        transcricao_completa = f.read()
        
    instrucao_extra = ""
    if prompt_customizado:
        instrucao_extra = f"""
ATENÇÃO DO EDITOR: Gere as opções focando especificamente em: {prompt_customizado}
Isso substitui as 3 opções padrão. Gere 3 variações dentro deste foco específico."""

    # Alinhamento com IRIS: Anti-alucinação, vocabulário editorial, coerência
    prompt = f"""
Você é um editor de vídeo sênior de uma emissora de TV regional (InterTV). Está alinhado ao sistema IRIS de análise jornalística.

REGRAS OBRIGATÓRIAS (guardrails do IRIS):
1. NÃO INFIRA o que não está explícito na transcrição ou no texto da matéria.
2. Separe FATOS OBJETIVOS (o que foi dito) de CARGA EMOCIONAL (tom do depoimento).
3. NÃO invente nomes, números, locais ou declarações.
4. Respeite a coerência entre a gravidade do fato e o tom da edição (não use cortes alegres para tragédias).
5. NUNCA proponha cortar depoimentos de vítimas, menores de idade ou pessoas que não podem falar.
6. Priorize as falas que realmente importam para a matéria (voz A1 — locução do repórter e sonoras).

CONTEXTO EDITORIAL: {contexto_editorial}
TEXTO DA MATÉRIA (o que o repórter quer contar):
{texto_materia}

TRANSCRIÇÃO DO BRUTO (o que foi gravado, com timestamps):
{transcricao_completa}

BLOCOS DE VÍDEO DISPONÍVEIS (duração e fades):
{blocos}

SUA TAREFA: Gerar 3 OPÇÕES DE EDIÇÃO DIFERENTES, alinhadas aos ângulos editoriais do IRIS, cada uma com aproximadamente {duracao_alvo} segundos.

OPÇÃO 1 — INFORMATIVO (fatos diretos, objetividade):
- Foque nas informações factuais, no que aconteceu, onde, quando, quem.
- Ritmo de telejornal: claro, direto, sem sensacionalismo.
- Priorize a locução do repórter (off) e sonoras que confirmam fatos.

OPÇÃO 2 — HUMANIZADO (pessoas, emoção, histórias humanas):
- Foque nos depoimentos que trazem sentimento (sent_*: solidariedade, esperança, dor, superação).
- Mantenha a coerência: se a matéria é sobre tragédia, o tom é sóbrio (não celebratório).
- Priorize sonoras de pessoas afetadas, moradores, vítimas (com cuidado ético).

OPÇÃO 3 — DINÂMICO (ação, movimento, ritmo):
- Foque em cenas com movimento, ação, cortes mais rápidos.
- Ideal para matérias de esporte, operações policiais, resgates, obras.
- Priorize trechos com ação visual e sonoras curtas e impactantes.
{instrucao_extra}

FORMATO DE RETORNO (APENAS JSON válido, sem markdown):
{{
  "opcoes": [
    {{"id": 1, "nome": "Informativo", "cortes": [{{"start": 10.0, "end": 25.0}}, {{"start": 45.0, "end": 60.0}}]}},
    {{"id": 2, "nome": "Humanizado", "cortes": [{{"start": 30.0, "end": 50.0}}]}},
    {{"id": 3, "nome": "Dinâmico", "cortes": [{{"start": 5.0, "end": 15.0}}, {{"start": 70.0, "end": 85.0}}]}}
  ]
}}

Regras finais:
- A SOMA dos cortes de cada opção deve ser próxima de {duracao_alvo} segundos.
- Não corte no meio de uma frase.
- Respeite os limites dos blocos disponíveis.
"""
    
    api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/chat")
    model = os.getenv("LLM_MODEL", "llama3.1:8b")
    
    if "ollama" in api_url:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    else:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        
    headers = {"Content-Type": "application/json"}
    if os.getenv("OPENAI_API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('OPENAI_API_KEY')}"
        
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content") if "ollama" in api_url else data.get("choices")[0].get("message", {}).get("content")
        content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        
        if not parsed.get("opcoes") or all(len(o.get("cortes", [])) == 0 for o in parsed["opcoes"]):
            raise ValueError("LLM retornou opções sem cortes válidos.")
            
        return parsed
    except Exception as e:
        print(f"Erro ao chamar o LLM ou resposta inválida: {e}")
        print("Fallback: Gerando 3 opções baseadas no tempo alvo.")
        
        opcoes_fallback = []
        nomes_fallback = ["Informativo", "Humanizado", "Dinâmico"]
        for i in range(1, 4):
            tempo_acumulado = 0
            cortes = []
            for b in blocos:
                duracao_bloco = b[1] - b[0]
                if tempo_acumulado + duracao_bloco <= duracao_alvo or not cortes:
                    cortes.append({"start": b[0], "end": b[1]})
                    tempo_acumulado += duracao_bloco
                if tempo_acumulado >= duracao_alvo * 0.9:
                    break
            opcoes_fallback.append({"id": i, "nome": nomes_fallback[i-1], "cortes": cortes})
            
        return {"opcoes": opcoes_fallback}
