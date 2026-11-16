import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda

def test_detector_instanciacao():
    detector = DetectorFadesPretos("fake_video.mp4")
    assert detector.threshold == 30
    assert detector.fps == 29.97

def test_detector_is_black_frame():
    detector = DetectorFadesPretos("fake_video.mp4")
    frame_preto = np.zeros((1080, 1920, 3), dtype=np.uint8)
    # Correção: Usar == True para evitar o problema do np.True_
    assert detector.is_black_frame(frame_preto) == True
    
    frame_colorido = np.full((1080, 1920, 3), 150, dtype=np.uint8)
    assert detector.is_black_frame(frame_colorido) == False

@patch('subprocess.run')
def test_cortar_video(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    resultado = cortar_video("input.mp4", "output.mp4", 10.0, 20.0)
    assert resultado is True
    args_chamados = mock_run.call_args[0][0]
    assert "-c:v" in args_chamados
    assert "libx264" in args_chamados
    assert "-c" not in args_chamados or "copy" not in args_chamados

@patch('os.remove') # Correção: Mockando a remoção do arquivo
@patch('subprocess.run')
def test_juntar_videos(mock_run, mock_remove):
    mock_run.return_value = MagicMock(returncode=0)
    with patch('builtins.open', MagicMock()):
        resultado = juntar_videos(["c1.mp4", "c2.mp4"], "final.mp4")
        assert resultado is True
        mock_remove.assert_called_once_with("concat_list.txt")

@patch('subprocess.run')
def test_embutir_legenda(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    resultado = embutir_legenda("video.mp4", "legenda.srt", "video_leg.mp4")
    assert resultado is True
