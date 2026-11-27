import os
from bs4 import BeautifulSoup

def test_frontend_html_exists():
    """Verifica se o arquivo HTML do frontend foi criado."""
    assert os.path.exists("frontend_teste.html")

def test_frontend_has_required_fields():
    """Verifica se todos os campos de input e botões existem no HTML."""
    with open("frontend_teste.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    # Campos de input
    assert soup.find("input", {"id": "videoFile"}) is not None, "Campo de vídeo não encontrado"
    assert soup.find("input", {"id": "duracao"}) is not None, "Campo de duração não encontrado"
    assert soup.find("textarea", {"id": "textoMateria"}) is not None, "Campo de texto da matéria não encontrado"
    assert soup.find("select", {"id": "plataforma"}) is not None, "Select de plataforma não encontrado"
    assert soup.find("input", {"id": "editoria"}) is not None, "Campo de editoria não encontrado"
    assert soup.find("input", {"id": "promptRefazer"}) is not None, "Campo de refazer não encontrado"
    
    # Botões
    assert soup.find("button", {"id": "btnGerar"}) is not None, "Botão de Gerar não encontrado"
    # O botão de refazer não tem ID, mas tem onclick="refazerOpcoes()"
    assert soup.find("button", onclick="refazerOpcoes()") is not None, "Botão de Refazer não encontrado"

def test_frontend_js_functions():
    """Verifica se as funções JavaScript essenciais estão no código."""
    with open("frontend_teste.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "async function chamarAPI" in content, "Função chamarAPI não encontrada"
    assert "function renderizarVideos" in content, "Função renderizarVideos não encontrada"
    assert "function gerarOpcoes" in content, "Função gerarOpcoes não encontrada"
    assert "function refazerOpcoes" in content, "Função refazerOpcoes não encontrada"
