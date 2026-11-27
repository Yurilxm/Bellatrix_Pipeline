import os
import re
import unicodedata
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def is_valid_filename(filename):
    pattern = r'^(?! )[a-zA-Z0-9 _-]+(?! )(\.[a-zA-Z0-9_-]+)?$'
    return bool(re.match(pattern, filename))

def sanitize_filename(filename):
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

def gerar_nome_final(source_path, output_dir, assunto="MATERIA", plataforma="tv"):
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    data_hoje = datetime.now().strftime("%d%m%y")
    tag = base_name.split('_')[0] if '_' in base_name else "VT"
    
    ext = "mxf" if plataforma.lower() == "tv" else "mp4"
    prefixo = "IN2_ED" if plataforma.lower() == "tv" else "WEB"
    
    new_base_name = f"{prefixo}_{data_hoje}_{tag}_{assunto}"
    sanitized = sanitize_filename(new_base_name)
    return os.path.join(output_dir, f"{sanitized}.{ext}")

def calcular_ajuste_frames(fps=29.97):
    return {
        'inicio': 4 / fps,
        'fim': 3 / fps
    }
