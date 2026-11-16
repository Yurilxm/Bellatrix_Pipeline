import os
import argparse
import shutil
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar

def processar_video(input_path, output_format="mp4", duracao_alvo=180, gerar_legenda=True):
    print(f"--- Iniciando Pipeline para: {input_path} ---")
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = "temp_cortes"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 1. Detecção Visual (Bellatrix)
    print("1. Detectando blocos (fades)...")
    detector = DetectorFadesPretos(input_path)
    blocos = detector.detectar()
    print(f"   {len(blocos)} blocos encontrados.")
    
    if not blocos:
        print("Nenhum bloco válido encontrado. Abortando.")
        return

    # 2. Transcrição (Whisper)
    print("2. Transcrevendo áudio (Whisper)...")
    srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
    transcrever_e_gerar_srt(input_path, srt_temp)
    
    # 3. Decisão Editorial (LLM)
    print("3. Selecionando melhores trechos (LLM)...")
    trechos_escolhidos = analisar_e_selecionar(blocos, srt_temp, duracao_alvo)
    
    # 4. Corte e Montagem (FFmpeg)
    print("4. Cortando e renderizando vídeo final...")
    cortes_gerados = []
    for i, trecho in enumerate(trechos_escolhidos):
        output_corte = os.path.join(temp_dir, f"corte_{i}.{output_format}")
        cortar_video(input_path, output_corte, trecho["start"], trecho["end"])
        cortes_gerados.append(output_corte)
        
    video_final = f"{base_name}_final.{output_format}"
    if len(cortes_gerados) > 1:
        print("   Juntando os trechos...")
        juntar_videos(cortes_gerados, video_final)
    else:
        shutil.move(cortes_gerados[0], video_final)

    # 5. Legendas (Burn-in)
    if gerar_legenda:
        print("5. Aplicando legendas no vídeo final...")
        video_com_legenda = f"{base_name}_legendado.{output_format}"
        embutir_legenda(video_final, srt_temp, video_com_legenda)
        os.remove(video_final) # Remove o sem legenda
        video_final = video_com_legenda

    # Limpeza
    shutil.rmtree(temp_dir)
    
    print(f"--- Pipeline finalizada! Arquivo salvo: {video_final} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de Edição Automatizada Bellatrix + IA")
    parser.add_argument("-i", "--input", required=True, help="Caminho do vídeo de entrada")
    parser.add_argument("-o", "--output_format", default="mp4", help="Formato de saída (mp4, mov, mkv)")
    parser.add_argument("-d", "--duracao", type=int, default=180, help="Duração alvo em segundos")
    parser.add_argument("--no-subs", action="store_true", help="Desativa a geração de legendas")
    
    args = parser.parse_args()
    
    if os.path.exists(args.input):
        processar_video(args.input, args.output_format, args.duracao, not args.no_subs)
    else:
        print(f"Erro: Arquivo {args.input} não encontrado.")
