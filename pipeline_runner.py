import os
import shutil
import tempfile
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda
from core.validator import is_video_valid
from core.governance import gerar_nome_final
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar

def executar_pipeline(input_path, duracao_alvo=180, plataforma="tv", texto_materia="", prompt_customizado="", contexto_editorial=""):
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        raise ValueError(f"Vídeo inválido: {mensagem}")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    # Cria um diretório temporário seguro para concorrência
    temp_dir = tempfile.mkdtemp(prefix="bellatrix_")
    
    try:
        detector = DetectorFadesPretos(input_path)
        blocos = detector.detectar()
        if not blocos:
            raise ValueError("Nenhum bloco válido encontrado.")
        
        srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
        transcrever_e_gerar_srt(input_path, srt_temp)
        
        resposta_llm = analisar_e_selecionar(blocos, srt_temp, texto_materia, duracao_alvo, prompt_customizado, contexto_editorial)
        opcoes = resposta_llm.get("opcoes", [])
        
        arquivos_gerados = []
        
        for opcao in opcoes:
            opcao_id = opcao.get("id")
            nome_opcao = opcao.get("nome", f"Opcao{opcao_id}")
            cortes = opcao.get("cortes", [])
            
            cortes_gerados = []
            for i, trecho in enumerate(cortes):
                ext = "mxf" if plataforma.lower() == "tv" else "mp4"
                output_corte = os.path.join(temp_dir, f"op{opcao_id}_corte_{i}.{ext}")
                cortar_video(input_path, output_corte, trecho["start"], trecho["end"], plataforma)
                cortes_gerados.append(output_corte)
                
            video_final = gerar_nome_final(input_path, os.getcwd(), assunto=f"OPCAO{opcao_id}_{nome_opcao}", plataforma=plataforma)
            
            if len(cortes_gerados) > 1:
                juntar_videos(cortes_gerados, video_final, plataforma)
            elif len(cortes_gerados) == 1:
                shutil.move(cortes_gerados[0], video_final)
                
            if os.path.exists(video_final):
                arquivos_gerados.append(video_final)
                
        return arquivos_gerados
    finally:
        # Garante a limpeza do temp mesmo se der erro
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
