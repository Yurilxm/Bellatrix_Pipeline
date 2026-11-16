import os
import subprocess
from faster_whisper import WhisperModel

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
    
    print("Carregando modelo Whisper (large-v3)...")
    # Usa CPU ou CUDA se disponível
    model = WhisperModel("large-v3", device="cuda" if os.environ.get("USE_CUDA") else "cpu", compute_type="float16" if os.environ.get("USE_CUDA") else "int8")
    
    segments, info = model.transcribe(audio_temp, beam_size=5, language="pt")
    
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = formatar_tempo_srt(segment.start)
            end = formatar_tempo_srt(segment.end)
            f.write(f"{i}\n{start} --> {end}\n{segment.text.strip()}\n\n")
            
    if os.path.exists(audio_temp):
        os.remove(audio_temp)
    
    return output_srt
