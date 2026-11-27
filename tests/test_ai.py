import pytest
from unittest.mock import patch, MagicMock
from ai.transcriber import formatar_tempo_srt, extrair_audio
from ai.analyzer import analisar_e_selecionar

def test_formatar_tempo_srt():
    assert formatar_tempo_srt(65.5) == "00:01:05,500"
    assert formatar_tempo_srt(3600) == "01:00:00,000"
    assert formatar_tempo_srt(0.1) == "00:00:00,100"

@patch('subprocess.run')
def test_extrair_audio(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    extrair_audio("video.mp4", "audio.wav")
    args_chamados = mock_run.call_args[0][0]
    assert "-vn" in args_chamados
    assert "pcm_s16le" in args_chamados

@patch('requests.post')
def test_analyzer_fallback(mock_post):
    # Simula uma falha na API do LLaMA
    mock_post.side_effect = Exception("Connection refused")
    
    # Mock de um arquivo SRT falso
    with patch('builtins.open', MagicMock()):
        blocos = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0), (60.0, 70.0)]
        resultado = analisar_e_selecionar(blocos, "fake.srt", 180)
        
        # Correção: Agora o fallback retorna um dicionário com 3 opções
        assert "opcoes" in resultado
        assert len(resultado["opcoes"]) == 3
        assert resultado["opcoes"][0]["id"] == 1
