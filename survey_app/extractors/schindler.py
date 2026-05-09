"""
Extractor de parámetros para planos Schindler (PDF con texto seleccionable).
Usa pypdf para extracción rápida. Maneja texto normal e invertido (labels rotados).
"""
from pypdf import PdfReader
import re

# Parámetros que buscamos en el PDF
PARAMS = [
    "TKSW", "TKSW", "BKS", "TKA", "TKS", "TSW", "BGS",
    "BKF1", "BKF2", "BS", "BT", "BK", "TK", "TS",
    "SF1", "SF2", "SG", "TG"
]
# Orden importa: primero los más largos para evitar match parcial
PARAMS = sorted(set(PARAMS), key=len, reverse=True)

# Pattern combinado (más rápido que iterar param por param)
_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(p) for p in PARAMS) + r')\s*=\s*(\d+(?:\.\d+)?)'
)

def extract_from_pdf(pdf_file) -> dict:
    """
    Extrae parámetros del PDF Schindler.
    pdf_file: path string o file-like object (Streamlit UploadedFile).
    Retorna dict {param: float} — None si no se encontró.
    """
    found = {p: None for p in PARAMS}

    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text() or ""

            # Búsqueda directa
            for m in _PATTERN.finditer(text):
                k, v = m.group(1), float(m.group(2))
                if found[k] is None:
                    found[k] = v

            # Búsqueda en texto invertido (labels rotados en el plano)
            rev = text[::-1]
            for m in _PATTERN.finditer(rev):
                k, v = m.group(1), float(m.group(2))
                if found[k] is None:
                    found[k] = v

            # Si ya encontramos todo, salir temprano
            if all(v is not None for v in found.values()):
                break

    except Exception as e:
        print(f"[Schindler extractor] Error: {e}")

    return found


# Descripciones para mostrar en la UI
PARAM_DESCRIPTIONS = {
    "BS":   "Ancho del hueco (shaft width)",
    "BT":   "Ancho del contrapeso",
    "BK":   "Ancho de cabina",
    "BKS":  "Distancia entre rieles de cabina",
    "TK":   "Profundidad de cabina",
    "TKA":  "Profundidad del umbral de cabina",
    "TKS":  "Cabina umbral a umbral de rellano",
    "TSW":  "Pared frontal a umbral de cabina",
    "TKSW": "Pared frontal a eje de rieles",
    "TS":   "Profundidad del hueco",
    "SF1":  "Pared izquierda a eje de riel (SF1)",
    "SF2":  "Pared derecha a eje de riel (SF2)",
    "SG":   "Centro contrapeso a pared",
    "TG":   "Ancho del contrapeso (TG)",
    "BGS":  "Distancia entre rieles de contrapeso",
    "BKF1": "Retorno frontal izquierdo",
    "BKF2": "Retorno frontal derecho",
}
