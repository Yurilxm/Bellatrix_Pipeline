import subprocess
import os

def cortar_video(input_path, output_path, start_time, end_time):
    command = [
        'ffmpeg', '-y', '-ss', str(start_time), '-to', str(end_time),
        '-i', input_path,
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '192k',
        output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return True

def juntar_videos(lista_videos, output_path):
    with open("concat_list.txt", "w") as f:
        for video in lista_videos:
            f.write(f"file '{video}'\n")
    
    command = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat_list.txt',
        '-c', 'copy', output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    os.remove("concat_list.txt")
    return True

def embutir_legenda(video_path, srt_path, output_path):
    # Queima a legenda no vídeo (burn-in)
    command = [
        'ffmpeg', '-y', '-i', video_path,
        '-vf', f"subtitles={srt_path}",
        '-c:a', 'copy',
        output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return True
