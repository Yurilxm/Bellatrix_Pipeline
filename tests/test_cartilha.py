import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from core.cutter import cortar_video
from ai.analyzer import analisar_e_selecionar
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


@patch('subprocess.run')
def test_cartilha_export_mxf_xdcam50(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    cortar_video("input.mp4", "output.mxf", 10.0, 20.0, plataforma="tv")
    args = mock_run.call_args[0][0]
    assert "mpeg2video" in args
    assert "50M" in args
    assert "yuv422p" in args
    assert "+ilme+ildct" in args
    assert "-top" in args
    assert "pcm_s24le" in args


@patch('subprocess.run')
def test_cartilha_export_mp4_audio_norm(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    cortar_video("input.mp4", "output.mp4", 10.0, 20.0, plataforma="web")
    args = mock_run.call_args[0][0]
    assert "loudnorm=I=-14:TP=-1.5:LRA=11" in args
    assert "libx264" in args


@patch('requests.post')
@patch('builtins.open', new_callable=MagicMock)
def test_cartilha_llm_prompt_3_opcoes(mock_open, mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.json.return_value = {
        "message": {"content": '{"opcoes": [{"id": 1, "cortes": [{"start": 10, "end": 20}]}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}
    }
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = "Fala do reporter"
    mock_open.return_value = mock_file

    resultado = analisar_e_selecionar(blocos=[(0, 10)], srt_path="fake.srt", texto_materia="Buraco", duracao_alvo=180)

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']

    assert "3 OPÇÕES DE EDIÇÃO DIFERENTES" in prompt
    assert len(resultado["opcoes"]) == 3


# Correção do teste fraco da API
def test_api_processar_3_opcoes_estritas():
    """Testa API com arquivos reais criados pelo mock"""
    temp_files = []
    for i, nome in enumerate(["op1", "op2", "op3"]):
        tf = tempfile.NamedTemporaryFile(suffix='.mxf', delete=False, prefix=f"{nome}_")
        tf.write(b"fake video content")
        tf.close()
        temp_files.append(tf.name)

    import api.main
    original = api.main.executar_pipeline
    api.main.executar_pipeline = lambda *args, **kwargs: temp_files

    try:
        response = client.post(
            "/processar",
            files={"file": ("test.mxf", b"fake video content", "video/mp4")},
            data={"duracao_alvo": 180, "plataforma": "tv", "texto_materia": "Texto"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "arquivos" in data
        assert len(data["arquivos"]) == 3
    finally:
        api.main.executar_pipeline = original
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)