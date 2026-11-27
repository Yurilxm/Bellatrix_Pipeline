import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_processar_video():
    """Testa /processar com mock que cria arquivos reais"""
    temp_files = []
    for i, nome in enumerate(["op1", "op2", "op3"]):
        tf = tempfile.NamedTemporaryFile(suffix='.mxf', delete=False, prefix=f"{nome}_")
        tf.write(b"fake video content")
        tf.close()
        temp_files.append(tf.name)

    # Usa monkeypatch via pytest-mock
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
        assert len(response.json()["arquivos"]) == 3
    finally:
        api.main.executar_pipeline = original
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)