import pytest
import subprocess
import os
import tempfile
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def gerar_video_sintetico(output_path, duracao=5, largura=640, altura=480):
    """Gera um vídeo sintético curto com ffmpeg (testsrc + sine audio)."""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'testsrc=duration={duracao}:size={largura}x{altura}:rate=30',
        '-f', 'lavfi', '-i', f'sine=frequency=440:duration={duracao}',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest', output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    assert result.returncode == 0, f"ffmpeg falhou: {result.stderr.decode()}"
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    return output_path


@pytest.fixture(scope="session")
def video_sintetico():
    """Fixture que gera um vídeo sintético temporário para os testes."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        temp_path = f.name
    try:
        gerar_video_sintetico(temp_path, duracao=5)
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_video_sintetico_valido(video_sintetico):
    """Verifica se o vídeo sintético foi gerado corretamente."""
    assert os.path.exists(video_sintetico)
    assert os.path.getsize(video_sintetico) > 1000  # Pelo menos 1KB


def test_pipeline_com_video_sintetico_web(video_sintetico):
    """Testa o pipeline completo com vídeo sintético (plataforma web)."""
    with open(video_sintetico, 'rb') as f:
        response = client.post(
            "/processar",
            files={"file": ("sintetico.mp4", f, "video/mp4")},
            data={"duracao_alvo": 10, "plataforma": "web", "texto_materia": "Vídeo de teste sintético"}
        )

    # Deve processar sem erro (pode usar fallback se LLM falhar)
    assert response.status_code == 200, f"Erro: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert "arquivos" in data
    assert len(data["arquivos"]) == 3

    # Verifica se arquivos existem no filesystem (pasta output)
    for url in data["arquivos"]:
        assert url.startswith("/output/")
        filename = url.split("/output/")[-1]
        filepath = os.path.join("/app/output", filename)
        assert os.path.exists(filepath), f"Arquivo não encontrado: {filepath}"
        assert os.path.getsize(filepath) > 0, f"Arquivo vazio: {filepath}"
        assert filename.endswith(".mp4")


def test_pipeline_com_video_sintetico_tv(video_sintetico):
    """Testa o pipeline completo com vídeo sintético (plataforma tv)."""
    with open(video_sintetico, 'rb') as f:
        response = client.post(
            "/processar",
            files={"file": ("sintetico.mp4", f, "video/mp4")},
            data={"duracao_alvo": 10, "plataforma": "tv", "texto_materia": "Vídeo de teste sintético TV"}
        )

    assert response.status_code == 200, f"Erro: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert len(data["arquivos"]) == 3

    for url in data["arquivos"]:
        assert url.startswith("/output/")
        filename = url.split("/output/")[-1]
        filepath = os.path.join("/app/output", filename)
        assert os.path.exists(filepath), f"Arquivo não encontrado: {filepath}"
        assert filename.endswith(".mxf")


def test_pipeline_duracao_curta(video_sintetico):
    """Testa com duração alvo menor que o vídeo (deve cortar)."""
    with open(video_sintetico, 'rb') as f:
        response = client.post(
            "/processar",
            files={"file": ("sintetico.mp4", f, "video/mp4")},
            data={"duracao_alvo": 3, "plataforma": "web", "texto_materia": "Corte curto"}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["arquivos"]) == 3


def test_pipeline_com_texto_materia_e_contexto(video_sintetico):
    """Testa com todos os campos preenchidos."""
    with open(video_sintetico, 'rb') as f:
        response = client.post(
            "/processar",
            files={"file": ("sintetico.mp4", f, "video/mp4")},
            data={
                "duracao_alvo": 5,
                "plataforma": "web",
                "texto_materia": "Reportagem sobre teste automatizado do pipeline Bellatrix.",
                "programa": "Teste Automatizado",
                "editoria": "Tecnologia",
                "perfil": "Desenvolvimento"
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["arquivos"]) == 3