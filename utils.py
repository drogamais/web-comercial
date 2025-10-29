# /utils.py

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Funções de Manipulação de Código de Barras ---

def pad_barcode(barcode):
    """Limpa o código de barras e adiciona zeros à esquerda até 14 caracteres.
    USADA PARA codigo_barras_normalizado e busca de codigo_interno."""
    if barcode and isinstance(barcode, str) and barcode.strip():
        # Retorna o código limpo, padronizado com zeros à esquerda (zfill)
        return barcode.strip().zfill(14)
    return None

def clean_barcode(barcode):
    """Apenas limpa o código de barras (remove espaços) sem padding.
    USADA PARA validação no campo codigo_barras do DB externo (raw GTIN)."""
    if barcode and isinstance(barcode, str) and barcode.strip():
        # Retorna o código apenas limpo, sem padding
        return barcode.strip()
    return None