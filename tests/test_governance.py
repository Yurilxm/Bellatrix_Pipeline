import pytest
from datetime import datetime
from core.governance import sanitize_filename, gerar_nome_final, calcular_ajuste_frames, is_valid_filename

def test_sanitize_filename():
    assert sanitize_filename("vídeo_com_acentuação.mp4") == "video_com_acentuacao.mp4"

def test_sanitize_filename_espacos_especiais():
    assert sanitize_filename("arquivo@#$.mp4") == "arquivo.mp4"
    # Acentos são removidos pela normalização NFKD -> ASCII
    assert sanitize_filename("nome com espaços.mxf") == "nome com espacos.mxf"
    # Espaços no início/fim são preservados (apenas caracteres especiais são removidos)
    assert sanitize_filename("  inicio_fim  .mp4") == "  inicio_fim  .mp4"

def test_is_valid_filename():
    assert is_valid_filename("video_valido.mp4") == True
    assert is_valid_filename("video-com_tracos.mxf") == True
    assert is_valid_filename("123_video.mp4") == True
    assert is_valid_filename("@invalido.mp4") == False
    assert is_valid_filename(" video.mp4") == False  # espaço no início
    assert is_valid_filename("video.mp4 ") == False  # espaço no fim

def test_gerar_nome_final_tv():
    data_hoje = datetime.now().strftime("%d%m%y")
    nome = gerar_nome_final("PET_video.mp4", "/tmp", "MATERIA", plataforma="tv")
    # Padrão TV: IN2_ED_DDMMYY_TAG_ASSUNTO.mxf
    assert f"IN2_ED_{data_hoje}_PET_MATERIA.mxf" in nome

def test_gerar_nome_final_web():
    data_hoje = datetime.now().strftime("%d%m%y")
    nome = gerar_nome_final("PET_video.mp4", "/tmp", "MATERIA", plataforma="web")
    # Padrão Web: WEB_DDMMYY_TAG_ASSUNTO.mp4
    assert f"WEB_{data_hoje}_PET_MATERIA.mp4" in nome

def test_gerar_nome_final_sem_tag():
    data_hoje = datetime.now().strftime("%d%m%y")
    nome = gerar_nome_final("video.mp4", "/tmp", "ASSUNTO", plataforma="tv")
    assert f"IN2_ED_{data_hoje}_VT_ASSUNTO.mxf" in nome

def test_gerar_nome_final_sanitiza_assunto():
    data_hoje = datetime.now().strftime("%d%m%y")
    nome = gerar_nome_final("TAG_video.mp4", "/tmp", "ASSUNTO@#$", plataforma="tv")
    assert "ASSUNTO" in nome
    assert "@" not in nome
    assert "#" not in nome
    assert "$" not in nome

def test_calcular_ajuste_frames():
    ajuste = calcular_ajuste_frames()
    assert ajuste['inicio'] == 4 / 29.97
    assert ajuste['fim'] == 3 / 29.97

def test_calcular_ajuste_frames_custom_fps():
    ajuste = calcular_ajuste_frames(fps=30.0)
    assert ajuste['inicio'] == 4 / 30.0
    assert ajuste['fim'] == 3 / 30.0