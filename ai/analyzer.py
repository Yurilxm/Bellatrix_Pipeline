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
        instrucao_extra = f"\nATENÇÃO DO EDITOR: Gere as opções focando especificamente em: {prompt_customizado}"

    prompt = f"""
    Você é um editor de vídeo sênior de uma emissora de TV.
    Nós temos o TEXTO DA MATÉRIA (o que precisa ser dito) e a TRANSCRIÇÃO DO BRUTO (o que foi gravado).
    
    CONTEXTO EDITORIAL: {contexto_editorial}
    
    TEXTO DA MATÉRIA:
    {texto_materia}
    
    TRANSCRIÇÃO DO BRUTO:
    {transcricao_completa}
    
    BLOCOS DISPONÍVEIS:
    {blocos}
    
    Sua tarefa: Criar 3 OPÇÕES DIFERENTES de edição para um vídeo de aproximadamente {duracao_alvo} segundos.
    - Opção 1: Foco em Ação e Movimento.
    - Opção 2: Foco em Emoção e Sonoras.
    - Opção 3: Foco na Narrativa/Locução.
    {instrucao_extra}
    
    Regras:
    1. Priorize as falas que realmente importam (voz A1).
    2. Mantenha a coerência jornalística (não corte no meio de uma frase).
    3. A SOMA dos cortes de cada opção deve ser próxima de {duracao_alvo} segundos.
    
    Retorne APENAS um JSON válido com esta estrutura:
    {{
      "opcoes": [
        {{"id": 1, "nome": "Ação", "cortes": [{{"start": 10.0, "end": 20.0}}]}},
        {{"id": 2, "nome": "Emoção", "cortes": [{{"start": 30.0, "end": 45.0}}]}},
        {{"id": 3, "nome": "Narrativa", "cortes": [{{"start": 50.0, "end": 70.0}}]}}
      ]
    }}
    """
    
    api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/chat")
    model = os.getenv("LLM_MODEL", "llama3")
    
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
        
        # Se o LLM retornar opções, mas todas vazias, força o fallback
        if not parsed.get("opcoes") or all(len(o.get("cortes", [])) == 0 for o in parsed["opcoes"]):
            raise ValueError("LLM retornou opções sem cortes válidos.")
            
        return parsed
    except Exception as e:
        print(f"Erro ao chamar o LLM ou resposta inválida: {e}")
        print("Fallback: Gerando 3 opções baseadas no tempo alvo.")
        
        # Fallback Inteligente: Pega blocos até atingir o tempo alvo
        opcoes_fallback = []
        for i in range(1, 4):
            tempo_acumulado = 0
            cortes = []
            for b in blocos:
                duracao_bloco = b[1] - b[0]
                # Adiciona o bloco se couber OU se for o primeiro (para não ficar vazio)
                if tempo_acumulado + duracao_bloco <= duracao_alvo or not cortes:
                    cortes.append({"start": b[0], "end": b[1]})
                    tempo_acumulado += duracao_bloco
                if tempo_acumulado >= duracao_alvo * 0.9:
                    break
            opcoes_fallback.append({"id": i, "nome": f"Fallback {i}", "cortes": cortes})
            
        return {"opcoes": opcoes_fallback}
