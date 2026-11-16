import pytest
from core.detector import DetectorFadesPretos
from core.cutter import formatar_tempo_srt

def test_detector_instanciacao(mocker):
    # Mock do cv2 para não precisar de vídeo real
    mocker.patch('cv2.VideoCapture')
    detector = DetectorFadesPretos("fake_video.mp4")
    assert detector.threshold == 30
    assert detector.fps == 29.97

def test_formatar_tempo_srt():
    # Testa a conversão de segundos para o formato SRT
    assert formatar_tempo_srt(65.5) == "00:01:05,500"
    assert formatar_tempo_srt(3600) == "01:00:00,000"
