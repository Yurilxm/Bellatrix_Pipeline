import pytest
from datetime import datetime
from core.governance import sanitize_filename, gerar_nome_final, calcular_ajuste_frames

def test_sanitize_filename():
    assert sanitize_filename("vídeo_com_acentuação.mp4") == "video_com_acentuacao.mp4"
    assert sanitize_filename("video_normal.mp4") == "video_normal.mp4"

def test_gerar_nome_final():
    data_hoje = datetime.now().strftime("%d%m%y")
    nome = gerar_nome_final("PET_video.mp4", "/tmp", "MATERIA")
    # Verifica se segue o padrão da cartilha: IN2_ED_DDMMYY_TAG_ASSUNTO.mxf
    assert f"IN2_ED_{data_hoje}_PET_MATERIA.mxf" in nome

def test_calcular_ajuste_frames():
    ajuste = calcular_ajuste_frames()
    assert ajuste['inicio'] == 4 / 29.97
    assert ajuste['fim'] == 3 / 29.97
