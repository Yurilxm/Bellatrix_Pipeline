import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def analisar_e_selecionar(blocos, srt_path, duracao_alvo=180):
    print(f"Lendo transcrição de {srt_path} e enviando para o LLM...")
    
    # Lê o arquivo SRT para enviar como contexto
    with open(srt_path, "r", encoding="utf-8") as f:
        transcricao_completa = f.read()
        
    prompt = f"""
    Você é um editor de vídeo sênior de uma emissora de TV.
    Aqui estão os blocos de vídeo disponíveis com seus tempos (em segundos): {blocos}
    Aqui está a transcrição com os tempos:
    {transcricao_completa}
    
    Sua tarefa: Selecionar os melhores trechos para criar um vídeo final de aproximadamente {duracao_alvo} segundos.
    Regras:
    1. Mantenha a coerência jornalística (não corte no meio de uma frase).
    2. Priorize as falas do repórter e momentos de destaque.
    3. O tempo total dos trechos escolhidos deve ser próximo de {duracao_alvo} segundos.
    
    Retorne APENAS um JSON válido (sem formatação markdown) com a lista de trechos no formato:
    [ {{"start": 10.5, "end": 45.2}}, {{"start": 60.0, "end": 120.0}} ]
    """
    
    api_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/chat")
    model = os.getenv("LLM_MODEL", "llama3")
    
    # Payload para Ollama ou OpenAI
    if "ollama" in api_url:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}
    else:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        
    headers = {"Content-Type": "application/json"}
    if os.getenv("OPENAI_API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('OPENAI_API_KEY')}"
        
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extrai a resposta dependendo da API
        content = data.get("message", {}).get("content") if "ollama" in api_url else data.get("choices")[0].get("message", {}).get("content")
        
        # Limpa a string para garantir que é um JSON válido
        content = content.replace("```json", "").replace("```", "").strip()
        trechos = json.loads(content)
        return trechos
        
    except Exception as e:
        print(f"Erro ao chamar o LLM: {e}")
        print("Fallback: Retornando os 3 primeiros blocos para não quebrar a pipeline.")
        return [{"start": b[0], "end": b[1]} for b in blocos[:3]]
