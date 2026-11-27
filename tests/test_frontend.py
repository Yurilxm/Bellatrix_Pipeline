import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_frontend_carrega():
    """Testa se o frontend carrega (HTML válido)"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "Bellatrix Pipeline" in html
    assert "Gerar 3 Opções com IA" in html


def test_frontend_tem_campos_obrigatorios():
    """Verifica se o HTML tem todos os campos do formulário"""
    response = client.get("/")
    html = response.text

    # Campos do formulário
    assert 'id="videoFile"' in html
    assert 'id="duracao"' in html
    assert 'id="plataforma"' in html
    assert 'id="textoMateria"' in html
    assert 'id="programa"' in html
    assert 'id="editoria"' in html
    assert 'id="promptRefazer"' in html

    # Botões
    assert 'id="btnGerar"' in html
    assert 'onclick="gerarOpcoes()"' in html
    assert 'onclick="refazerOpcoes()"' in html

    # Seções
    assert 'id="form-section"' in html
    assert 'id="loading-section"' in html
    assert 'id="results-section"' in html
    assert 'id="video-grid"' in html


def test_frontend_api_url_relativa():
    """Verifica se a API_URL usa caminho relativo (não hardcoded localhost)"""
    response = client.get("/")
    html = response.text
    # Não deve ter localhost hardcoded
    assert "localhost:8012" not in html
    # Deve usar /processar relativo
    assert '"/processar"' in html or "'/processar'" in html


def test_frontend_tem_nomes_opcoes():
    """Verifica se os nomes das 3 opções aparecem no JS"""
    response = client.get("/")
    html = response.text
    assert "Informativo" in html
    assert "Humanizado" in html
    assert "Dinâmico" in html


def test_frontend_tem_download_links():
    """Verifica se há links de download para os vídeos"""
    response = client.get("/")
    html = response.text
    assert 'download' in html
    assert 'Baixar Vídeo' in html