import os
import subprocess
from pywhispercpp.model import Model

def extrair_audio(video_path, audio_path):
    command = ['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def formatar_tempo_srt(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    milis = int((segundos - int(segundos)) * 1000)
    return f"{horas:02}:{minutos:02}:{segs:02},{milis:03}"

def transcrever_e_gerar_srt(video_path, output_srt):
    audio_temp = "audio_temp.wav"
    extrair_audio(video_path, audio_temp)
    
    # Usa modelo medium se não especificado (melhor para PT-BR)
    model_name = os.getenv("WHISPER_MODEL", "medium")
    print(f"Carregando modelo Whisper ({model_name})...")
    
    model = Model(model_name, print_realtime=False, print_progress=False)
    segments = model.transcribe(audio_temp)
    
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = formatar_tempo_srt(segment.t0 / 100.0)
            end = formatar_tempo_srt(segment.t1 / 100.0)
            f.write(f"{i}\n{start} --> {end}\n{segment.text.strip()}\n\n")
            
    if os.path.exists(audio_temp):
        os.remove(audio_temp)
    return output_srt
