"""
Extractor de parámetros para planos Schindler.
Maneja todos los casos especiales identificados en el PDF real:
  1. Números pegados después:  BS=19981272  → BS=1998
  2. Números pegados antes:    110TKSW=965  → TKSW=965
  3. Parámetros pegados:       TKSW=965TS=1750 → ambos separados
  4. Sin '=' valor en línea siguiente: BKF1\n200 → BKF1=200
  5. Valor partido por salto:  TKS=30\n62  → TKS=3062
"""
from pypdf import PdfReader
import re

# Orden de mayor a menor longitud para evitar matches parciales
PARAMS = sorted([
    "TKSW", "BKS", "TKA", "TKS", "TSW", "BGS", "BKF1", "BKF2",
    "BS", "BT", "BK", "TK", "TS", "SF1", "SF2", "SG", "TG", "BT"
], key=len, reverse=True)
PARAMS = list(dict.fromkeys(PARAMS))  # deduplicar manteniendo orden

# Valores esperados aproximados para validar extracciones (mm)
# Evita aceptar valores absurdos
VALID_RANGES = {
    "BS":   (500,  5000),
    "BT":   (200,  2000),
    "BK":   (500,  3000),
    "BKS":  (500,  3000),
    "TK":   (500,  3000),
    "TKA":  (50,   500),
    "TKS":  (500,  8000),
    "TSW":  (50,   500),
    "TKSW": (500,  3000),
    "TS":   (500,  5000),
    "SF1":  (20,   800),
    "SF2":  (20,   800),
    "SG":   (20,   800),
    "TG":   (50,   500),
    "BGS":  (500,  3000),
    "BKF1": (20,   1200),
    "BKF2": (20,   1200),
}

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
    "SF1":  "Pared izquierda a eje de riel",
    "SF2":  "Pared derecha a eje de riel",
    "SG":   "Centro contrapeso a pared",
    "TG":   "Ancho del contrapeso (guía)",
    "BGS":  "Distancia entre rieles de contrapeso",
    "BKF1": "Retorno frontal izquierdo",
    "BKF2": "Retorno frontal derecho",
}


def _in_range(param, value):
    """Verifica si el valor está en el rango esperado para ese parámetro."""
    lo, hi = VALID_RANGES.get(param, (0, 99999))
    return lo <= value <= hi


def _extract_from_text(text: str, found: dict):
    """
    Extrae parámetros del texto con manejo de todos los casos especiales.
    Modifica `found` in-place.
    """
    # ── Paso 1: Normalizar texto ──────────────────────────
    # Reemplazar saltos de línea entre dígitos (caso TKS=30\n62 → TKS=3062)
    # Solo cuando la siguiente línea empieza con dígitos y no tiene letra antes
    normalized = re.sub(r'(\d)\n(\d)', r'\1\2', text)
    # Eliminar espacios múltiples
    normalized = re.sub(r'  +', ' ', normalized)

    # ── Paso 2: Separar parámetros pegados sin separador ──
    # Caso: TKSW=965TS=1750 → insertar espacio: TKSW=965 TS=1750
    param_pattern = '|'.join(re.escape(p) for p in PARAMS)
    normalized = re.sub(
        rf'(\d)({param_pattern})=',
        r'\1 \2=',
        normalized
    )
    # Caso: SG= 86SF1=179 → SG= 86 SF1=179
    normalized = re.sub(
        rf'(\d)(\s*)({param_pattern})\s*=',
        r'\1 \3=',
        normalized
    )

    # ── Paso 3: Buscar PARAM=VALUE con regex ──────────────
    pattern = re.compile(
        r'\b(' + param_pattern + r')\s*=\s*(\d+(?:\.\d+)?)'
    )
    for m in pattern.finditer(normalized):
        k  = m.group(1)
        v  = float(m.group(2))
        if k in found and found[k] is not None:
            continue
        # Validar rango
        if not _in_range(k, v):
            # Intentar tomar solo los primeros 4 dígitos (caso BS=19981272)
            raw = m.group(2)
            for length in [4, 3]:
                if len(raw) > length:
                    candidate = float(raw[:length])
                    if _in_range(k, candidate):
                        found[k] = candidate
                        break
        else:
            found[k] = v

    # ── Paso 4: BKF1/BKF2 — múltiples formatos observados en PDFs Schindler ──
    # Los planos CAD colocan el valor en tres posiciones distintas:
    #   A) Misma línea sin '=':   "BKF1 200"
    #   B) Valor en línea anterior al label:  "170\nBKF2"  (NORTH SYD)
    #   C) Valor en línea siguiente al label: "BKF2\n936"  (AGECARE)
    # Cuando B y C ambos existen, se prefiere el mayor (heurística: el valor
    # real suele ser más grande que el número flotante adyacente de otro elemento).
    for param in ["BKF1", "BKF2"]:
        if found.get(param) is not None:
            continue

        lines = text.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()

            # A) Misma línea con o sin '=': "BKF1 200" o "BKF1=200"
            m = re.search(rf'\b{re.escape(param)}\s*=?\s*(\d+)', stripped)
            if m:
                v = float(m.group(1))
                if _in_range(param, v):
                    found[param] = v
                    break

            # B y C) Label solo en su propia línea → buscar número antes y después
            if stripped == param:
                candidates = []
                # Valor en línea anterior
                if i > 0:
                    m = re.search(r'(\d+)\s*$', lines[i - 1].strip())
                    if m:
                        v = float(m.group(1))
                        if _in_range(param, v):
                            candidates.append(v)
                # Valor en línea siguiente (solo si la línea es un número puro)
                if i < len(lines) - 1:
                    m = re.fullmatch(r'\s*(\d+)\s*', lines[i + 1])
                    if m:
                        v = float(m.group(1))
                        if _in_range(param, v):
                            candidates.append(v)
                if candidates:
                    found[param] = max(candidates)
                    break


def extract_from_pdf(pdf_file) -> dict:
    """
    Extrae parámetros del PDF Schindler.
    pdf_file: path string o file-like object.
    Retorna dict {param: float|None}.
    """
    found = {p: None for p in PARAMS}

    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text() or ""
            _extract_from_text(text, found)
            # Salir temprano si ya encontramos todo
            if all(v is not None for v in found.values()):
                break
    except Exception as e:
        print(f"[Schindler extractor] Error: {e}")

    return found
