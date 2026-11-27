import pytest
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
from core.detector import DetectorFadesPretos
from core.cutter import cortar_video, juntar_videos, embutir_legenda, get_frame_rate
from core.validator import is_video_valid, get_video_info, check_ffprobe_available

def test_detector_instanciacao():
    detector = DetectorFadesPretos("fake_video.mp4")
    assert detector.threshold == 30
    assert detector.fps == 29.97

def test_detector_is_black_frame():
    detector = DetectorFadesPretos("fake_video.mp4")
    frame_preto = np.zeros((1080, 1920, 3), dtype=np.uint8)
    assert detector.is_black_frame(frame_preto) == True

    frame_colorido = np.full((1080, 1920, 3), 150, dtype=np.uint8)
    assert detector.is_black_frame(frame_colorido) == False

@patch('core.detector.cv2.VideoCapture')
def test_detector_fallback_no_fades(mock_cap):
    # Simula vídeo sem fades -> deve retornar vídeo completo como bloco único
    mock_instance = MagicMock()
    mock_instance.isOpened.return_value = True
    mock_instance.get.side_effect = lambda prop: {
        7: 100,  # CAP_PROP_FRAME_COUNT (poucos frames para teste rápido)
        5: 30.0,  # CAP_PROP_FPS
        0: 33.33  # CAP_PROP_POS_MSEC (simula tempo)
    }.get(prop, 0)

    # Simula 100 frames coloridos e depois fim do vídeo
    frame_colorido = np.full((1080, 1920, 3), 150, dtype=np.uint8)
    read_side_effect = [(True, frame_colorido)] * 100 + [(False, None)]
    mock_instance.read.side_effect = read_side_effect
    mock_instance.release.return_value = None
    mock_cap.return_value = mock_instance

    detector = DetectorFadesPretos("fake.mp4")
    blocos = detector.detectar()
    assert len(blocos) == 1
    assert blocos[0] == (0.0, 100/30.0)  # duração total

@patch('subprocess.run')
def test_cortar_video_web(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    with patch('core.cutter.get_frame_rate', return_value=29.97):
        resultado = cortar_video("input.mp4", "output.mp4", 10.0, 20.0, plataforma="web")
    assert resultado is True
    args_chamados = mock_run.call_args[0][0]
    assert "libx264" in args_chamados
    assert "aac" in args_chamados
    assert "loudnorm" in " ".join(args_chamados)

@patch('subprocess.run')
def test_cortar_video_tv(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    with patch('core.cutter.get_frame_rate', return_value=29.97):
        resultado = cortar_video("input.mp4", "output.mxf", 10.0, 20.0, plataforma="tv")
    assert resultado is True
    args_chamados = mock_run.call_args[0][0]
    assert "mpeg2video" in args_chamados
    assert "pcm_s24le" in args_chamados
    assert "mxf" in args_chamados

@patch('os.remove')
@patch('subprocess.run')
def test_juntar_videos(mock_run, mock_remove):
    mock_run.return_value = MagicMock(returncode=0)
    with patch('builtins.open', MagicMock()):
        resultado = juntar_videos(["c1.mp4", "c2.mp4"], "final.mp4", plataforma="web")
        assert resultado is True
        mock_remove.assert_called_once_with("concat_list.txt")

@patch('subprocess.run')
def test_embutir_legenda(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    resultado = embutir_legenda("video.mp4", "legenda.srt", "video_leg.mp4")
    assert resultado is True

@patch('subprocess.run')
def test_is_video_valid(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout='{"streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}')
    valido, msg = is_video_valid("fake.mp4")
    assert valido == True
    assert "válido" in msg

@patch('subprocess.run')
def test_get_frame_rate(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="30000/1001\n")
    fps = get_frame_rate("fake.mp4")
    assert fps == 29.97

@patch('subprocess.run')
def test_check_ffprobe_available_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    assert check_ffprobe_available() == True

@patch('subprocess.run')
def test_check_ffprobe_available_failure(mock_run):
    mock_run.side_effect = FileNotFoundError()
    assert check_ffprobe_available() == False

@patch('subprocess.run')
def test_get_video_info_success(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"streams": [{"codec_type": "video"}, {"codec_type": "audio"}]}'
    )
    probe, msg = get_video_info("fake.mp4")
    assert probe is not None
    assert "válido" in msg

@patch('subprocess.run')
def test_get_video_info_no_video_stream(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout='{"streams": [{"codec_type": "audio"}]}'
    )
    probe, msg = get_video_info("fake.mp4")
    assert probe is None
    assert "vídeo" in msg.lower()