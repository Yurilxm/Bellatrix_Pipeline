import pytest
from unittest.mock import patch, MagicMock, mock_open
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

@patch('requests.post')
@patch('builtins.open', new_callable=mock_open, read_data="Transcrição de teste")
def test_analyzer_llm_success(mock_file, mock_post):
    # Simula resposta bem-sucedida do LLM
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "nome": "Informativo", "cortes": [{"start": 10, "end": 20}]}, {"id": 2, "nome": "Humanizado", "cortes": [{"start": 30, "end": 40}]}, {"id": 3, "nome": "Dinâmico", "cortes": [{"start": 50, "end": 60}]}]}'}}
    )

    blocos = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0), (60.0, 70.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "Texto da matéria", 180)

    assert "opcoes" in resultado
    assert len(resultado["opcoes"]) == 3
    assert resultado["opcoes"][0]["nome"] == "Informativo"
    assert resultado["opcoes"][1]["nome"] == "Humanizado"
    assert resultado["opcoes"][2]["nome"] == "Dinâmico"

    # Verifica se o payload enviado tem as 3 opções do IRIS
    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']
    assert "INFORMATIVO" in prompt
    assert "HUMANIZADO" in prompt
    assert "DINÂMICO" in prompt
    assert "REGRAS OBRIGATÓRIAS" in prompt
    assert "guardrails do IRIS" in prompt

@patch('requests.post')
@patch('builtins.open', new_callable=mock_open, read_data="Transcrição de teste")
def test_analyzer_llm_invalid_response_fallback(mock_file, mock_post):
    # Simula resposta inválida do LLM (sem cortes) -> deve cair no fallback
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "cortes": []}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}}
    )

    blocos = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0), (60.0, 70.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "Texto da matéria", 180)

    # Deve usar fallback
    assert "opcoes" in resultado
    assert len(resultado["opcoes"]) == 3
    assert resultado["opcoes"][0]["nome"] == "Informativo"
    assert resultado["opcoes"][1]["nome"] == "Humanizado"
    assert resultado["opcoes"][2]["nome"] == "Dinâmico"

@patch('requests.post')
@patch('builtins.open', new_callable=mock_open, read_data="Transcrição de teste")
def test_analyzer_prompt_customizado(mock_file, mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "nome": "Custom", "cortes": [{"start": 10, "end": 20}]}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}}
    )

    blocos = [(0.0, 10.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "", 180, prompt_customizado="foco em entrevistas")

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']
    assert "foco em entrevistas" in prompt
    assert "ATENÇÃO DO EDITOR" in prompt

def test_analyzer_fallback_names():
    # Testa se o fallback usa os nomes corretos (Informativo, Humanizado, Dinâmico)
    with patch('requests.post', side_effect=Exception("fail")):
        with patch('builtins.open', mock_open(read_data="test")):
            blocos = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0), (60.0, 70.0)]
            resultado = analisar_e_selecionar(blocos, "fake.srt", 180)

            assert resultado["opcoes"][0]["nome"] == "Informativo"
            assert resultado["opcoes"][1]["nome"] == "Humanizado"
            assert resultado["opcoes"][2]["nome"] == "Dinâmico"
