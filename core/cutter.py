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
    command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        num, den = result.stdout.strip().split('/')
        return round(float(num) / float(den), 2)
    except Exception:
        return None

def cortar_video(input_path, output_path, start_time, end_time, output_format="mp4"):
    fps = get_frame_rate(input_path) or 29.97
    
    # Correção Cartilha: Pula 4 frames no início e remove 3 frames no fim (evita o preto)
    start_adjusted = max(0, start_time + (4 / fps))
    end_adjusted = end_time - (3 / fps)
    
    if output_format.lower() == "mxf":
        # Padrão Broadcast: XDCAM HD 50 NTSC 60i
        command = [
            'ffmpeg', '-y', '-ss', f"{start_adjusted:.3f}", '-to', f"{end_adjusted:.3f}",
            '-i', input_path,
            '-c:v', 'mpeg2video', '-b:v', '50M', '-minrate', '50M', '-maxrate', '50M', '-bufsize', '17825792',
            '-pix_fmt', 'yuv422p', '-flags', '+ilme+ildct', '-top', '1', '-r', '29.97',
            '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2',
            '-f', 'mxf',
            output_path
        ]
    else:
        # Formato Web (mp4) com normalização de áudio (A1 entre -12dB e -6dB)
        command = [
            'ffmpeg', '-y', '-ss', f"{start_adjusted:.3f}", '-to', f"{end_adjusted:.3f}",
            '-i', input_path,
            '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
            '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
            output_path
        ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao cortar vídeo: {e}")
        return False

def juntar_videos(lista_videos, output_path, output_format="mp4"):
    with open("concat_list.txt", "w") as f:
        for video in lista_videos:
            f.write(f"file '{video}'\n")
            
    if output_format.lower() == "mxf":
        command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt', '-c', 'copy', '-f', 'mxf', output_path]
    else:
        command = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt', '-c', 'copy', output_path]
        
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    os.remove("concat_list.txt")
    return True

def embutir_legenda(video_path, srt_path, output_path):
    srt_path_formatado = srt_path.replace('\\', '/').replace(':', '\\:')
    command = ['ffmpeg', '-y', '-i', video_path, '-vf', f"subtitles='{srt_path_formatado}'", '-c:a', 'copy', output_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return True
