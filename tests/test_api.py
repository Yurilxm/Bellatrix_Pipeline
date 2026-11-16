import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Teste de integração do endpoint /processar (mockando a pipeline)
def test_processar_video(mocker):
    mocker.patch('api.main.executar_pipeline', return_value="video_final.mp4")
    response = client.post(
        "/processar",
        files={"file": ("test.mp4", b"fake video content", "video/mp4")},
        data={"duracao_alvo": 30, "formato": "mp4"}
    )
    assert response.status_code == 200
    assert "video_final.mp4" in response.text
