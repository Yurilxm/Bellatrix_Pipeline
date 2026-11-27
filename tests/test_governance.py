import pytest
from datetime import datetime
from core.governance import sanitize_filename, gerar_nome_final, calcular_ajuste_frames

def test_sanitize_filename():
    assert sanitize_filename("vídeo_com_acentuação.mp4") == "video_com_acentuacao.mp4"

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

def test_calcular_ajuste_frames():
    ajuste = calcular_ajuste_frames()
    assert ajuste['inicio'] == 4 / 29.97
    assert ajuste['fim'] == 3 / 29.97
