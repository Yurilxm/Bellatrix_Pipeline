import os
import shutil
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda, get_frame_rate
from core.validator import is_video_valid
from core.governance import gerar_nome_final
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar

def executar_pipeline(input_path, duracao_alvo=180, output_format="mxf", texto_materia="", prompt_customizado=""):
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        raise ValueError(f"Vídeo inválido: {mensagem}")
    
    fps = get_frame_rate(input_path)
    if fps and fps != 29.97:
        raise ValueError(f"Frame rate {fps} não suportado.")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = "temp_cortes"
    os.makedirs(temp_dir, exist_ok=True)
    
    detector = DetectorFadesPretos(input_path)
    blocos = detector.detectar()
    if not blocos:
        raise ValueError("Nenhum bloco válido encontrado.")
    
    srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
    transcrever_e_gerar_srt(input_path, srt_temp)
    
    # O LLM agora retorna um dicionário com 3 opções
    resposta_llm = analisar_e_selecionar(blocos, srt_temp, texto_materia, duracao_alvo, prompt_customizado)
    opcoes = resposta_llm.get("opcoes", [])
    
    arquivos_gerados = []
    
    for opcao in opcoes:
        opcao_id = opcao.get("id")
        nome_opcao = opcao.get("nome", f"Opcao_{opcao_id}")
        cortes = opcao.get("cortes", [])
        
        cortes_gerados = []
        for i, trecho in enumerate(cortes):
            output_corte = os.path.join(temp_dir, f"op{opcao_id}_corte_{i}.{output_format}")
            cortar_video(input_path, output_corte, trecho["start"], trecho["end"], output_format)
            cortes_gerados.append(output_corte)
            
        # Gera o nome do arquivo com o ID da opção
        video_final = gerar_nome_final(input_path, os.getcwd(), assunto=f"OPCAO{opcao_id}_{nome_opcao}")
        
        if len(cortes_gerados) > 1:
            juntar_videos(cortes_gerados, video_final, output_format)
        elif len(cortes_gerados) == 1:
            shutil.move(cortes_gerados[0], video_final)
            
        if os.path.exists(video_final):
            arquivos_gerados.append(video_final)

    shutil.rmtree(temp_dir)
    return arquivos_gerados
