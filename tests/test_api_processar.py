import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@patch('api.main.executar_pipeline')
def test_processar_video_retorna_3_arquivos(mock_pipeline):
    """Testa se /processar retorna 3 arquivos com URLs /output/"""
    # Cria arquivos temporários que o pipeline "retornaria"
    temp_files = []
    for i, nome in enumerate(["OPCAO1_Informativo", "OPCAO2_Humanizado", "OPCAO3_Dinamico"]):
        tf = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False, prefix=f"{nome}_")
        tf.write(b"fake video content")
        tf.close()
        temp_files.append(tf.name)

    mock_pipeline.return_value = temp_files

    try:
        response = client.post(
            "/processar",
            files={"file": ("test.mp4", b"fake video content", "video/mp4")},
            data={"duracao_alvo": 60, "plataforma": "web", "texto_materia": "Teste"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "arquivos" in data
        assert len(data["arquivos"]) == 3
        # URLs devem ser /output/...
        for url in data["arquivos"]:
            assert url.startswith("/output/")
            assert url.endswith(".mp4")
            # Verifica se arquivo existe na pasta output
            filename = url.split("/output/")[-1]
            filepath = os.path.join("/app/output", filename)
            assert os.path.exists(filepath), f"Arquivo não encontrado: {filepath}"
    finally:
        # Limpa arquivos temporários originais
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)


@patch('api.main.executar_pipeline')
def test_processar_video_tv_retorna_mxf(mock_pipeline):
    """Testa se plataforma=tv retorna arquivos .mxf"""
    temp_files = []
    for i, nome in enumerate(["OPCAO1_Informativo", "OPCAO2_Humanizado", "OPCAO3_Dinamico"]):
        tf = tempfile.NamedTemporaryFile(suffix='.mxf', delete=False, prefix=f"{nome}_")
        tf.write(b"fake video content")
        tf.close()
        temp_files.append(tf.name)

    mock_pipeline.return_value = temp_files

    try:
        response = client.post(
            "/processar",
            files={"file": ("test.mxf", b"fake video", "video/mxf")},
            data={"duracao_alvo": 180, "plataforma": "tv", "texto_materia": "Teste TV"}
        )

        assert response.status_code == 200
        data = response.json()
        for url in data["arquivos"]:
            assert url.endswith(".mxf")
            filename = url.split("/output/")[-1]
            filepath = os.path.join("/app/output", filename)
            assert os.path.exists(filepath), f"Arquivo não encontrado: {filepath}"
    finally:
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)


def test_processar_rejeita_arquivo_nao_video():
    """Testa validação de content-type"""
    response = client.post(
        "/processar",
        files={"file": ("test.txt", b"not a video", "text/plain")},
        data={"duracao_alvo": 60, "plataforma": "web"}
    )
    assert response.status_code == 400
    assert "vídeo" in response.json()["detail"].lower()


def test_processar_rejeita_sem_arquivo():
    """Testa se exige arquivo"""
    response = client.post(
        "/processar",
        data={"duracao_alvo": 60, "plataforma": "web"}
    )
    assert response.status_code == 422  # Unprocessable Entity (campo obrigatório)


@patch('api.main.executar_pipeline')
def test_processar_passa_parametros_corretos(mock_pipeline):
    """Verifica se todos os parâmetros do formulário são passados ao pipeline"""
    tf = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    tf.write(b"video")
    tf.close()
    mock_pipeline.return_value = [tf.name]

    try:
        response = client.post(
            "/processar",
            files={"file": ("test.mp4", b"video", "video/mp4")},
            data={
                "duracao_alvo": 90,
                "plataforma": "web",
                "texto_materia": "Texto da matéria",
                "prompt_customizado": "mais emoção",
                "programa": "Bom Dia",
                "editoria": "Cidades",
                "perfil": "Jornalismo"
            }
        )

        assert response.status_code == 200
        args, kwargs = mock_pipeline.call_args
        assert args[0].startswith("temp_test.mp4")
        assert args[1] == 90
        assert args[2] == "web"
        assert args[3] == "Texto da matéria"
        assert args[4] == "mais emoção"
        assert "Programa: Bom Dia" in args[5]
        assert "Editoria: Cidades" in args[5]
        assert "Perfil: Jornalismo" in args[5]
    finally:
        if os.path.exists(tf.name):
            os.remove(tf.name)


@patch('api.main.executar_pipeline', side_effect=Exception("Erro interno"))
def test_processar_trata_erro_pipeline(mock_pipeline):
    """Testa se erro no pipeline retorna 500"""
    response = client.post(
        "/processar",
        files={"file": ("test.mp4", b"video", "video/mp4")},
        data={"duracao_alvo": 60, "plataforma": "web"}
    )
    assert response.status_code == 500
    assert "Erro interno" in response.json()["detail"]