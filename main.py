import os
import argparse
import shutil
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda
from core.validator import is_video_valid
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar
from core.governance import gerar_nome_final

def processar_video(input_path, output_format="mp4", duracao_alvo=180, gerar_legenda=True):
    print(f"\n🚀 Iniciando Pipeline para: {input_path}")
    
    # 0. Validação
    print("⏳ [0/5] Validando integridade do vídeo...")
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        print(f"❌ Vídeo inválido: {mensagem}")
        return
    print(f"✅ {mensagem}")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = "temp_cortes"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 1. Detecção Visual
    print("⏳ [1/5] Detectando blocos (fades)...")
    detector = DetectorFadesPretos(input_path)
    blocos = detector.detectar()
    print(f"✅ {len(blocos)} blocos encontrados.")
    
    if not blocos:
        print("❌ Nenhum bloco válido encontrado. Abortando.")
        return

    # 2. Transcrição
    print("⏳ [2/5] Transcrevendo áudio (Whisper)...")
    srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
    transcrever_e_gerar_srt(input_path, srt_temp)
    print("✅ Transcrição concluída.")
    
    # 3. Decisão Editorial
    print("⏳ [3/5] Selecionando melhores trechos (LLM)...")
    trechos_escolhidos = analisar_e_selecionar(blocos, srt_temp, duracao_alvo)
    print(f"✅ {len(trechos_escolhidos)} trechos selecionados.")
    
    # 4. Corte e Montagem
    print("⏳ [4/5] Cortando e renderizando vídeo final...")
    cortes_gerados = []
    for i, trecho in enumerate(trechos_escolhidos):
        output_corte = os.path.join(temp_dir, f"corte_{i}.{output_format}")
        cortar_video(input_path, output_corte, trecho["start"], trecho["end"], output_format)
        cortes_gerados.append(output_corte)
        
    video_final = gerar_nome_final(input_path, os.getcwd())
    if len(cortes_gerados) > 1:
        juntar_videos(cortes_gerados, video_final)
    else:
        shutil.move(cortes_gerados[0], video_final)
    print("✅ Montagem concluída.")

    # 5. Legendas (Burn-in)
    if gerar_legenda:
        print("⏳ [5/5] Aplicando legendas no vídeo final...")
        video_com_legenda = video_final.replace(f".{output_format}", f"_legendado.{output_format}")
        embutir_legenda(video_final, srt_temp, video_com_legenda)
        if os.path.exists(video_final): os.remove(video_final)
        video_final = video_com_legenda
        print("✅ Legendas aplicadas.")

    # Limpeza
    shutil.rmtree(temp_dir)
    
    print(f"\n🎉 Pipeline finalizada! Arquivo salvo como: {video_final}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="=== Bellatrix Pipeline (Edição Automatizada com IA) ===",
        epilog="Exemplos de uso:\n"
               "  python main.py -i video.mp4 -d 180 -o mp4\n"
               "  python main.py -i bruto.mxf -d 60 -o mxf --no-subs\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-i", "--input", required=True, help="Caminho do vídeo de entrada (Ex: C:\\videos\\bruto.mp4)")
    parser.add_argument("-o", "--output_format", default="mp4", choices=["mp4", "mxf", "mov", "mkv"], help="Formato de saída (padrão: mp4). Use 'mxf' para broadcast.")
    parser.add_argument("-d", "--duracao", type=int, default=180, help="Duração alvo em segundos (padrão: 180)")
    parser.add_argument("--no-subs", action="store_true", help="Desativa a geração de legendas")
    
    args = parser.parse_args()
    
    if os.path.exists(args.input):
        processar_video(args.input, args.output_format, args.duracao, not args.no_subs)
    else:
        print(f"Erro: Arquivo '{args.input}' não encontrado.")
