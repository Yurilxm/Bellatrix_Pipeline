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

def get_video_info(file_path):
    """Retorna streams e fps do vídeo."""
    if not check_ffprobe_available():
        return None, "ffprobe não encontrado"
    
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_streams', '-of', 'json', file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        probe = json.loads(result.stdout)
        video_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'video']
        audio_streams = [s for s in probe.get('streams', []) if s.get('codec_type') == 'audio']
        
        if not video_streams:
            return None, "Nenhuma stream de vídeo encontrada"
        if not audio_streams:
            return None, "Nenhuma stream de áudio encontrada"
            
        return probe, "Vídeo válido"
    except Exception as e:
        return None, f"Erro ao analisar vídeo: {str(e)}"

def is_video_valid(file_path):
    probe, msg = get_video_info(file_path)
    if not probe:
        return False, msg
    return True, "Vídeo válido e íntegro"
