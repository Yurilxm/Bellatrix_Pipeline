import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def check_ffprobe_available():
    try:
        subprocess.run(['ffprobe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_timestamp_gaps(file_path, max_gap_seconds=1.0):
    """Verifica gaps anormais nos timestamps (Integração Sirius)."""
    if not check_ffprobe_available():
        return False, "ffprobe não disponível"
    
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'frame=pkt_dts_time,pkt_size',
             '-of', 'csv=p=0', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        lines = result.stdout.strip().split('\n')
        prev_dts = None
        for line in lines:
            if not line: continue
            parts = line.split(',')
            try:
                dts = float(parts[0])
                if prev_dts is not None and (dts - prev_dts) > max_gap_seconds:
                    return True, f"Gap de {dts - prev_dts:.2f}s detectado nos frames"
                prev_dts = dts
            except ValueError:
                continue
        return False, "Nenhum gap detectado"
    except Exception as e:
        return True, f"Erro na verificação estrutural: {str(e)[:100]}"

def is_video_valid(file_path):
    """Verifica se o vídeo é válido e sem falhas estruturais."""
    if not check_ffprobe_available():
        return False, "ffprobe não encontrado"
    
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_streams', '-of', 'json', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        probe = json.loads(result.stdout)
        
        video_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
        audio_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
        
        if not video_streams:
            return False, "Nenhuma stream de vídeo encontrada"
        if not audio_streams:
            return False, "Nenhuma stream de áudio encontrada"
            
        # Verificação do Sirius
        has_gaps, gap_msg = check_timestamp_gaps(file_path)
        if has_gaps:
            return False, f"Vídeo com problema estrutural: {gap_msg}"
            
        return True, "Vídeo válido e íntegro"
        
    except subprocess.CalledProcessError as e:
        return False, f"Erro ao executar ffprobe: {e.stderr[:100]}"
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"
