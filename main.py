import os
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video
from ai.transcriber import transcrever
from ai.analyzer import analisar_e_selecionar

def processar_video(video_path):
    print(f"--- Iniciando Pipeline para: {video_path} ---")
    
    # 1. Detecção Visual (Base Bellatrix)
    print("1. Detectando blocos (fades)...")
    detector = DetectorFadesPretos(video_path)
    blocos = detector.detectar()
    print(f"   {len(blocos)} blocos encontrados.")
    
    # 2. Transcrição (Whisper)
    print("2. Transcrevendo áudio...")
    transcricao = transcrever(video_path)
    
    # 3. Decisão Editorial (LLM)
    print("3. Selecionando melhores trechos (LLM)...")
    trechos_escolhidos = analisar_e_selecionar(transcricao, duracao_alvo=180) # 3 minutos
    
    # 4. Corte (FFmpeg Corrigido)
    print("4. Cortando e renderizando vídeo final...")
    os.makedirs("output", exist_ok=True)
    for i, (start, end) in enumerate(trechos_escolhidos):
        output_file = f"output/corte_{i+1}.mp4"
        cortar_video(video_path, output_file, start, end)
        
    print("--- Pipeline finalizada! ---")

if __name__ == "__main__":
    # Exemplo de uso
    video_teste = "caminho/para/seu/video_bruto.mp4"
    # processar_video(video_teste)
    print("Pipeline pronta. Descomente a linha acima e insira um vídeo para testar.")
