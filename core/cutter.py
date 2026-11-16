import subprocess
import os
import json
import logging

logger = logging.getLogger(__name__)

def get_video_metadata(video_path):
    command = ['ffprobe', '-v', 'quiet', '-show_format', '-show_streams', '-of', 'json', video_path]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

def get_frame_rate(video_path):
    """Retorna o frame rate do vídeo."""
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        num, den = result.stdout.strip().split('/')
        return round(float(num) / float(den), 2)
    except Exception:
        return None

def cortar_video(input_path, output_path, start_time, end_time, output_format="mp4"):
    """Corta o vídeo com ajuste de frames e suporte a MXF."""
    fps = get_frame_rate(input_path) or 29.97
    ajuste = 4 / fps if output_format != "mxf" else 3 / fps  # Ajuste baseado no formato
    
    # Ajusta o início (pula 4 frames) e o fim (adiciona 3 frames)
    start_adjusted = max(0, start_time + ajuste)
    end_adjusted = end_time - (3 / fps)
    
    if output_format.lower() == "mxf":
        # Formato broadcast (Nano)
        command = [
            'ffmpeg', '-y', '-ss', f"{start_adjusted:.3f}", '-to', f"{end_adjusted:.3f}",
            '-i', input_path,
            '-c:v', 'mpeg2video', '-q:v', '2',
            '-c:a', 'pcm_s24le',
            '-map', '0:v', '-map', '0:a',
            '-f', 'mxf',
            output_path
        ]
    else:
        # Formato web (mp4, mov, mkv)
        command = [
            'ffmpeg', '-y', '-ss', f"{start_adjusted:.3f}", '-to', f"{end_adjusted:.3f}",
            '-i', input_path,
            '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
            '-c:a', 'aac', '-b:a', '192k',
            output_path
        ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao cortar vídeo: {e}")
        return False

def juntar_videos(lista_videos, output_path):
    with open("concat_list.txt", "w") as f:
        for video in lista_videos:
            f.write(f"file '{video}'\n")
    command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt', '-c', 'copy', output_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    os.remove("concat_list.txt")
    return True

def embutir_legenda(video_path, srt_path, output_path):
    srt_path_formatado = srt_path.replace('\\', '/').replace(':', '\\:')
    command = ['ffmpeg', '-y', '-i', video_path, '-vf', f"subtitles='{srt_path_formatado}'", '-c:a', 'copy', output_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return True
