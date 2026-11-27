import os
import shutil
import tempfile
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda
from core.validator import is_video_valid
from core.governance import gerar_nome_final
from ai.transcriber import transcrever_e_gerar_srt
from ai.analyzer import analisar_e_selecionar
import subprocess

def get_video_duration(video_path):
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def executar_pipeline(input_path, duracao_alvo=180, plataforma="tv", texto_materia="", prompt_customizado="", contexto_editorial=""):
    valido, mensagem = is_video_valid(input_path)
    if not valido:
        raise ValueError(f"Vídeo inválido: {mensagem}")
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    temp_dir = tempfile.mkdtemp(prefix="bellatrix_")
    
    try:
        detector = DetectorFadesPretos(input_path)
        blocos = detector.detectar()
        
        # Fallback se não encontrar fades
        if not blocos:
            print("Nenhum fade encontrado. Usando o vídeo completo como bloco único.")
            duracao_total = get_video_duration(input_path)
            if duracao_total > 0:
                blocos = [(0.0, duracao_total)]
            else:
                raise ValueError("Não foi possível determinar a duração do vídeo.")
        
        srt_temp = os.path.join(temp_dir, f"{base_name}_temp.srt")
        transcrever_e_gerar_srt(input_path, srt_temp)
        
        resposta_llm = analisar_e_selecionar(blocos, srt_temp, texto_materia, duracao_alvo, prompt_customizado, contexto_editorial)
        opcoes = resposta_llm.get("opcoes", [])
        
        # Proteção: Se o LLM não gerar opções, usa o fallback baseado nos blocos originais
        if not opcoes:
            print("LLM não retornou opções. Gerando fallback de segurança.")
            opcoes = [
                {"id": 1, "nome": "Geral", "cortes": [{"start": b[0], "end": b[1]} for b in blocos[:3]]},
                {"id": 2, "nome": "Alternativa", "cortes": [{"start": b[0], "end": b[1]} for b in blocos[:1]]},
                {"id": 3, "nome": "Curta", "cortes": [{"start": blocos[0][0], "end": blocos[0][1]}]}
            ]
            
        arquivos_gerados = []
        
        for opcao in opcoes:
            opcao_id = opcao.get("id")
            nome_opcao = opcao.get("nome", f"Opcao{opcao_id}")
            cortes = opcao.get("cortes", [])
            
            # Correção: Se o LLM retornar cortes vazios, força um corte no primeiro bloco
            if not cortes:
                print(f"Aviso: Opcao {opcao_id} ({nome_opcao}) veio vazia. Aplicando corte fallback.")
                cortes = [{"start": blocos[0][0], "end": blocos[0][1]}]
                
            cortes_gerados = []
            for i, trecho in enumerate(cortes):
                ext = "mxf" if plataforma.lower() == "tv" else "mp4"
                output_corte = os.path.join(temp_dir, f"op{opcao_id}_corte_{i}.{ext}")
                sucesso = cortar_video(input_path, output_corte, trecho["start"], trecho["end"], plataforma)
                if sucesso and os.path.exists(output_corte):
                    cortes_gerados.append(output_corte)
            
            if not cortes_gerados:
                continue
                
            video_final = gerar_nome_final(input_path, os.getcwd(), assunto=f"OPCAO{opcao_id}_{nome_opcao}", plataforma=plataforma)
            
            if len(cortes_gerados) > 1:
                juntar_videos(cortes_gerados, video_final, plataforma)
            elif len(cortes_gerados) == 1:
                shutil.move(cortes_gerados[0], video_final)
                
            if os.path.exists(video_final):
                arquivos_gerados.append(video_final)
                
        return arquivos_gerados
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
