import pytest
from unittest.mock import patch, MagicMock, mock_open
from ai.analyzer import analisar_e_selecionar


@patch('requests.post')
@patch('builtins.open', new_callable=mock_open(read_data="Transcrição de teste com locução do repórter e sonora da entrevistada."))
def test_prompt_contem_papeis_editoriais_cartilha(mock_file, mock_post):
    """Verifica se o prompt inclui os 5 papéis editoriais da Cartilha."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "nome": "Informativo", "cortes": [{"start": 10, "end": 20}]}, {"id": 2, "nome": "Humanizado", "cortes": [{"start": 30, "end": 40}]}, {"id": 3, "nome": "Dinâmico", "cortes": [{"start": 50, "end": 60}]}]}'}}
    )

    blocos = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0), (60.0, 70.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "Texto da matéria", 180)

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']

    # Papéis editoriais da Cartilha (com acentos como no prompt real)
    assert "LOCOÇÃO / OFF" in prompt
    assert "PASSAGEM DE REPÓRTER" in prompt
    assert "SONORAS / ENTREVISTAS" in prompt
    assert "IMAGENS DE COBERTURA / ILUSTRAÇÃO" in prompt
    assert "SOBE SOM / AMBIENTE" in prompt

    # Guardrails do IRIS
    assert "NÃO INFIRA" in prompt
    assert "NÃO invente" in prompt
    assert "coerência entre a gravidade" in prompt
    assert "NUNCA proponha cortar depoimentos de vítimas" in prompt


@patch('requests.post')
@patch('builtins.open', new_callable=mock_open(read_data="Transcrição teste"))
def test_prompt_tres_angulos_editoriais(mock_file, mock_post):
    """Verifica se as 3 opções (Informativo, Humanizado, Dinâmico) estão no prompt."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "nome": "Informativo", "cortes": [{"start": 10, "end": 20}]}, {"id": 2, "nome": "Humanizado", "cortes": [{"start": 30, "end": 40}]}, {"id": 3, "nome": "Dinâmico", "cortes": [{"start": 50, "end": 60}]}]}'}}
    )

    blocos = [(0.0, 10.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "", 180)

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']

    # Três ângulos editoriais
    assert "OPÇÃO 1 — INFORMATIVO" in prompt
    assert "OPÇÃO 2 — HUMANIZADO" in prompt
    assert "OPÇÃO 3 — DINÂMICO" in prompt

    # Cada opção tem diretrizes específicas
    assert "LOCOÇÃO/OFF + PASSAGEM DE REPÓRTER + SONORAS factuais" in prompt
    assert "SONORAS/ENTREVISTAS com carga emocional" in prompt
    assert "IMAGENS DE COBERTURA/ILUSTRAÇÃO com movimento + SOBE SOM" in prompt


@patch('requests.post')
@patch('builtins.open', new_callable=mock_open(read_data="Transcrição teste"))
def test_prompt_inclui_duracao_alvo(mock_file, mock_post):
    """Verifica se a duração alvo é passada corretamente no prompt."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "cortes": []}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}}
    )

    blocos = [(0.0, 10.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "", 120)

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']

    assert "120 segundos" in prompt


@patch('requests.post')
@patch('builtins.open', new_callable=mock_open(read_data="Transcrição teste"))
def test_prompt_inclui_contexto_editorial(mock_file, mock_post):
    """Verifica se contexto editorial (programa, editoria, perfil) aparece no prompt."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "cortes": []}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}}
    )

    blocos = [(0.0, 10.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "", 180, "", "Programa: Bom Dia, Editoria: Cidades, Perfil: Hard News")

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']

    assert "Bom Dia" in prompt
    assert "Cidades" in prompt
    assert "Hard News" in prompt


@patch('requests.post')
@patch('builtins.open', new_callable=mock_open(read_data="Transcrição teste"))
def test_prompt_inclui_prompt_customizado(mock_file, mock_post):
    """Verifica se prompt_customizado é incluído como instrução extra."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"message": {"content": '{"opcoes": [{"id": 1, "cortes": []}, {"id": 2, "cortes": []}, {"id": 3, "cortes": []}]}'}}
    )

    blocos = [(0.0, 10.0)]
    resultado = analisar_e_selecionar(blocos, "fake.srt", "", 180, "foque no depoimento da dona Maria")

    payload = mock_post.call_args[1]['json']
    prompt = payload['messages'][0]['content']

    assert "dona Maria" in prompt
    assert "ATENÇÃO DO EDITOR" in prompt