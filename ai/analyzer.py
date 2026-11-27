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
    # Cartilha de Edição: papéis editoriais (locução/OFF, passagem repórter, sonoras, cobertura/ilustração, sobe som)
    prompt = f"""
Você é um editor de vídeo sênior de uma emissora de TV regional (InterTV). Está alinhado ao sistema IRIS de análise jornalística e à Cartilha de Edição de Reportagem.

REGRAS OBRIGATÓRIAS (guardrails do IRIS + Cartilha):
1. NÃO INFIRA o que não está explícito na transcrição ou no texto da matéria.
2. Separe FATOS OBJETIVOS (o que foi dito) de CARGA EMOCIONAL (tom do depoimento).
3. NÃO invente nomes, números, locais ou declarações.
4. Respeite a coerência entre a gravidade do fato e o tom da edição (não use cortes alegres para tragédias).
5. NUNCA proponha cortar depoimentos de vítimas, menores de idade ou pessoas que não podem falar.
6. Identifique e priorize trechos conforme seu papel editorial na reportagem:
   - LOCOÇÃO / OFF: narração do repórter (voz guia, conduz a narrativa)
   - PASSAGEM DE REPÓRTER: repórter em cena (ponte, contextualização)
   - SONORAS / ENTREVISTAS: depoimentos de fontes, personagens (voz A1)
   - IMAGENS DE COBERTURA / ILUSTRAÇÃO: b-roll, arquivos, cenas de apoio (sem áudio principal)
   - SOBE SOM / AMBIENTE: momentos de som ambiente natural (ruas, natureza, eventos) sem narração
7. A SOMA dos cortes de cada opção deve ser próxima de {duracao_alvo} segundos.
8. Não corte no meio de uma frase.
9. Respeite os limites dos blocos disponíveis.

CONTEXTO EDITORIAL: {contexto_editorial}
TEXTO DA MATÉRIA (o que o repórter quer contar):
{texto_materia}

TRANSCRIÇÃO DO BRUTO (o que foi gravado, com timestamps):
{transcricao_completa}

BLOCOS DE VÍDEO DISPONÍVEIS (duração e fades):
{blocos}

SUA TAREFA: Gerar 3 OPÇÕES DE EDIÇÃO DIFERENTES, alinhadas aos ângulos editoriais do IRIS, cada uma com aproximadamente {duracao_alvo} segundos.

OPÇÃO 1 — INFORMATIVO (fatos diretos, objetividade, telejornalismo padrão):
- Priorize: LOCOÇÃO/OFF + PASSAGEM DE REPÓRTER + SONORAS factuais (confirmação de fatos)
- Ritmo de telejornal: claro, direto, sem sensacionalismo.
- Use IMAGENS DE COBERTURA apenas para ilustrar fatos citados na locução.

OPÇÃO 2 — HUMANIZADO (pessoas, emoção, histórias humanas):
- Priorize: SONORAS/ENTREVISTAS com carga emocional (sent_*: solidariedade, esperança, dor, superação)
- Mantenha coerência: se tragédia, tom sóbrio (não celebratório).
- LOCOÇÃO/OFF serve apenas para conectar depoimentos; dê tempo ao "sobe som" de ambientes emocionais.
- Cuidado ético com vítimas, menores, pessoas que não podem falar.

OPÇÃO 3 — DINÂMICO (ação, movimento, ritmo visual):
- Priorize: IMAGENS DE COBERTURA/ILUSTRAÇÃO com movimento + SOBE SOM de ambiente + SONORAS curtas e impactantes
- Ideal para: esporte, operações policiais, resgates, obras, eventos com ação visual.
- LOCOÇÃO/OFF mínima; edição baseada em ritmo visual e sonoro.
- Cortes mais rápidos, transições por ação/movimento.
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
- Cada opção deve refletir seu ângulo editorial na escolha e ordenação dos papéis (locução, sonora, cobertura, sobe som).
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
