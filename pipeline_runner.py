import os
import shutil
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda, get_frame_rate
from core.validator import is_video_valid
from core.governance import gerar_nome_final
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar

def executar_pipeline(input_path, duracao_alvo=180, output_format="mp4"):
    # 0. Validação (Sirius)
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        raise ValueError(f"Vídeo inválido: {mensagem}")
    
    # Verificação de frame rate (Bellatrix)
    fps = get_frame_rate(input_path)
    if fps and fps != 29.97:
        raise ValueError(f"Frame rate {fps} não suportado. Use vídeos de 29.97 fps.")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = "temp_cortes"
    os.makedirs(temp_dir, exist_ok=True)
    
    detector = DetectorFadesPretos(input_path)
    blocos = detector.detectar()
    if not blocos:
        raise ValueError("Nenhum bloco válido encontrado.")
    
    srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
    transcrever_e_gerar_srt(input_path, srt_temp)
    
    trechos = analisar_e_selecionar(blocos, srt_temp, duracao_alvo)
    
    cortes = []
    for i, trecho in enumerate(trechos):
        output_corte = os.path.join(temp_dir, f"corte_{i}.{output_format}")
        cortar_video(input_path, output_corte, trecho["start"], trecho["end"], output_format)
        cortes.append(output_corte)
    
    video_final = gerar_nome_final(input_path, os.getcwd())
    if len(cortes) > 1:
        juntar_videos(cortes, video_final)
    else:
        shutil.move(cortes[0], video_final)
    
    video_legendado = video_final.replace(f".{output_format}", f"_legendado.{output_format}")
    embutir_legenda(video_final, srt_temp, video_legendado)
    os.remove(video_final)
    
    shutil.rmtree(temp_dir)
    return video_legendado
