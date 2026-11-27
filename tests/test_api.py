import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_processar_video(mocker):
    # Correção: Mock agora retorna uma lista de 3 arquivos
    mocker.patch('api.main.executar_pipeline', return_value=["op1.mxf", "op2.mxf", "op3.mxf"])
    response = client.post(
        "/processar",
        files={"file": ("test.mxf", b"fake video content", "video/mp4")},
        data={"duracao_alvo": 180, "plataforma": "tv", "texto_materia": "Texto"}
    )
    assert response.status_code == 200
    assert len(response.json()["arquivos"]) == 3
