import pytest
from unittest.mock import patch, MagicMock
from core.cutter import cortar_video
from core.governance import gerar_nome_final, calcular_ajuste_frames
from ai.analyzer import analisar_e_selecionar
from api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

@patch('subprocess.run')
def test_cartilha_export_mxf_xdcam50(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    cortar_video("input.mp4", "output.mxf", 10.0, 20.0, output_format="mxf")
    args = mock_run.call_args[0][0]
    assert "mpeg2video" in args
    assert "50M" in args
    assert "yuv422p" in args
    assert "+ilme+ildct" in args
    assert "-top" in args
    assert "29.97" in args
    assert "pcm_s24le" in args
    assert "48000" in args

@patch('subprocess.run')
def test_cartilha_export_mp4_audio_norm(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    cortar_video("input.mp4", "output.mp4", 10.0, 20.0, output_format="mp4")
    args = mock_run.call_args[0][0]
    assert "loudnorm=I=-14:TP=-1.5:LRA=11" in args
    assert "libx264" in args

@patch('subprocess.run')
def test_cartilha_frame_adjustment(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    with patch('core.cutter.get_frame_rate', return_value=29.97):
        cortar_video("input.mp4", "output.mxf", 10.0, 20.0, output_format="mxf")
        args = mock_run.call_args[0][0]
        assert "10.133" in args
        assert "19.900" in args

def test_cartilha_nomenclatura_bins():
    nome = gerar_nome_final("PET_MOBILIZA.mp4", "C:\\", assunto="VT_MOBILIZA")
    assert "IN2_ED_" in nome
    assert "PET_VT_MOBILIZA.mxf" in nome

@patch('requests.post')
@patch('builtins.open', new_callable=MagicMock)
def test_cartilha_llm_prompt_3_opcoes(mock_open, mock_post):
    # Mock do LLM retornando a estrutura de 3 opções
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.json.return_value = {
        "message": {"content": '{"opcoes": [{"id": 1, "cortes": [{"start": 10, "end": 20}]}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}
    }
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = "Fala do reporter"
    mock_open.return_value = mock_file
    
    resultado = analisar_e_selecionar(blocos=[(0, 10)], srt_path="fake.srt", texto_materia="Buraco na rua", duracao_alvo=180)
    
    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']
    
    assert "3 OPÇÕES DIFERENTES" in prompt
    assert "Buraco na rua" in prompt
    assert len(resultado["opcoes"]) == 3

@patch('subprocess.run')
def test_cartilha_legendas_srt(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    from core.cutter import embutir_legenda
    embutir_legenda("video.mp4", "legenda.srt", "video_leg.mp4")
    args = mock_run.call_args[0][0]
    assert "subtitles=" in " ".join(args)

# Teste da API esperando a lista de 3 arquivos
def test_api_processar_3_opcoes(mocker):
    mocker.patch('api.main.executar_pipeline', return_value=["video_op1.mxf", "video_op2.mxf", "video_op3.mxf"])
    response = client.post(
        "/processar",
        files={"file": ("test.mxf", b"fake video content", "video/mp4")},
        data={"duracao_alvo": 180, "formato": "mxf", "texto_materia": "Texto", "prompt_customizado": ""}
    )
    assert response.status_code == 200
    assert len(response.json()["arquivos"]) == 3
