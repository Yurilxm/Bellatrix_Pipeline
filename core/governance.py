import os
import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

def is_valid_filename(filename):
    """Verifica se o nome do arquivo é válido (Bellatrix/Sirius)."""
    pattern = r'^(?! )[a-zA-Z0-9 _-]+(?! )(\.[a-zA-Z0-9_-]+)?$'
    return bool(re.match(pattern, filename))

def sanitize_filename(filename):
    """Remove acentos e caracteres especiais do nome."""
    if is_valid_filename(filename):
        return filename
    try:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        normalized = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
        sanitized = re.sub(r'[^\w\s-]', '', normalized)
        return f"{sanitized}.{ext.lower()}" if ext else sanitized
    except Exception as e:
        logger.error(f"Erro ao sanitizar nome: {e}")
        return filename

def extrair_codigo(nome_arquivo):
    """Extrai o código da matéria (antes do primeiro _)."""
    if '_' in nome_arquivo:
        return nome_arquivo.split('_')[0]
    return nome_arquivo.split('.')[0]

def gerar_nome_final(source_path, output_dir):
    """Gera o nome final no padrão CM{codigo}_{nome}.ext (Bellatrix)."""
    base_name = os.path.basename(source_path)
    code = extrair_codigo(base_name)
    new_base_name = f"CM{code}_{base_name}"
    sanitized = sanitize_filename(new_base_name)
    return os.path.join(output_dir, sanitized)

def calcular_ajuste_frames(fps=29.97):
    """Retorna os ajustes de frames para evitar cortar no preto (Bellatrix/Nano)."""
    return {
        'inicio': 4 / fps,  # Pula 4 frames no início
        'fim': 3 / fps      # Adiciona 3 frames no fim
    }
