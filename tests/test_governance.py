import pytest
from core.governance import sanitize_filename, extrair_codigo, gerar_nome_final, calcular_ajuste_frames

def test_sanitize_filename():
    assert sanitize_filename("vídeo_com_acentuação.mp4") == "video_com_acentuacao.mp4"
    assert sanitize_filename("video_normal.mp4") == "video_normal.mp4"
    assert sanitize_filename("file@#$%.mp4") == "file.mp4"

def test_extrair_codigo():
    assert extrair_codigo("MAT123_video.mp4") == "MAT123"
    assert extrair_codigo("video_sem_codigo.mp4") == "video"

def test_gerar_nome_final():
    nome = gerar_nome_final("MAT123_video.mp4", "/tmp")
    assert "CMMAT123_MAT123_video.mp4" in nome

def test_calcular_ajuste_frames():
    ajuste = calcular_ajuste_frames()
    assert ajuste['inicio'] == 4 / 29.97
    assert ajuste['fim'] == 3 / 29.97
