import subprocess
import os

def cortar_video(input_path, output_path, start_time, end_time):
    # Correção crítica: Usar libx264 e aac para evitar freeze de frames
    command = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-ss', str(start_time),
        '-to', str(end_time),
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '192k',
        output_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"OK: Vídeo cortado de {start_time}s a {end_time}s -> {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao cortar vídeo: {e}")
        return False
