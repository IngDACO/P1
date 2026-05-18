"""
Extractor de parámetros para planos Schindler (CAD PDF).

Casos especiales manejados:
  1. Números pegados después:    BS=19981272     → BS=1998
  2. Números pegados antes:      110TKSW=965     → TKSW=965
  3. Parámetros pegados:         TKSW=965TS=1750 → ambos separados
  4. Sin '=' valor en línea sig: BKF2\n936       → BKF2=936
  5. Valor partido por salto:    TKS=30\n62      → TKS=3062
  6. Saltos Windows CRLF:        TKS=30\r\n62    → TKS=3062
  7. Valor ANTES del label:      170BKF2 30BKF1  → BKF2=170, BKF1=30
"""
from pypdf import PdfReader
import re

# ── Parámetros a buscar (de mayor a menor longitud) ──────────────
PARAMS = sorted([
    "TKSW", "BKS", "TKA", "TKS", "TSW", "BGS", "BKF1", "BKF2",
    "BS", "BT", "BK", "TK", "TS", "SF1", "SF2", "SG", "TG",
], key=len, reverse=True)
PARAMS = list(dict.fromkeys(PARAMS))

# ── Rangos válidos (mm) ──────────────────────────────────────────
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


def _in_range(param: str, value: float) -> bool:
    lo, hi = VALID_RANGES.get(param, (0, 99999))
    return lo <= value <= hi


def _extract_from_text(text: str, found: dict) -> None:
    """Extrae parámetros del texto y actualiza `found` in-place."""

    # ── Paso 1: Normalizar saltos de línea ─────────────────────────
    # CRLF (Windows) y CR sueltos → LF
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Unir dígito-salto-dígito: TKS=30\n62 → TKS=3062
    normalized = re.sub(r'(\d)\n(\d)', r'\1\2', text)
    normalized = re.sub(r'  +', ' ', normalized)

    # ── Paso 2: Separar parámetros pegados ─────────────────────────
    param_pattern = '|'.join(re.escape(p) for p in PARAMS)
    # TKSW=965TS=1750 → TKSW=965 TS=1750
    normalized = re.sub(rf'(\d)({param_pattern})=', r'\1 \2=', normalized)
    # SG= 86SF1=179  → SG= 86 SF1=179
    normalized = re.sub(rf'(\d)(\s*)({param_pattern})\s*=', r'\1 \3=', normalized)

    # ── Paso 3: Regex PARAM=VALUE (texto normalizado) ──────────────
    pattern = re.compile(r'\b(' + param_pattern + r')\s*=\s*(\d+(?:\.\d+)?)')
    for m in pattern.finditer(normalized):
        k = m.group(1)
        if found.get(k) is not None:
            continue
        v = float(m.group(2))
        if _in_range(k, v):
            found[k] = v
        else:
            # Truncar para casos como BS=19981272 → 1998
            raw = m.group(2)
            for length in (4, 3):
                if len(raw) > length:
                    candidate = float(raw[:length])
                    if _in_range(k, candidate):
                        found[k] = candidate
                        break

    # ── Paso 4: Búsqueda por líneas (texto original sin join) ──────
    # Cubre formatos que no siguen "PARAM=VALUE":
    #   A) Misma línea sin '=':     "BKF1 200"
    #   B/C) Label solo:            "BKF2\n936" o "170\nBKF2"
    #   D) Valor antes del label:   "170BKF2  30BKF1"  ← Schindler CAD
    lines = text.split('\n')
    for param in PARAMS:
        if found.get(param) is not None:
            continue
        for i, line in enumerate(lines):
            stripped = line.strip()

            # A) Valor DESPUÉS del label (con o sin '=')
            m = re.search(rf'\b{re.escape(param)}\s*=?\s*(\d+)', stripped)
            if m:
                v = float(m.group(1))
                if _in_range(param, v):
                    found[param] = v
                    break

            # D) Valor ANTES del label (sin '='): "170BKF2"
            # El \b final asegura que el label no está pegado a otra letra
            m = re.search(rf'(?<!\w)(\d+)\s*{re.escape(param)}\b', stripped)
            if m:
                v = float(m.group(1))
                if _in_range(param, v):
                    found[param] = v
                    break

            # B/C) Label solo en su propia línea → número antes o después
            if stripped == param:
                candidates: list[float] = []
                if i > 0:
                    m2 = re.search(r'(\d+)\s*$', lines[i - 1].strip())
                    if m2:
                        v = float(m2.group(1))
                        if _in_range(param, v):
                            candidates.append(v)
                if i < len(lines) - 1:
                    m2 = re.fullmatch(r'\s*(\d+)\s*', lines[i + 1])
                    if m2:
                        v = float(m2.group(1))
                        if _in_range(param, v):
                            candidates.append(v)
                if candidates:
                    found[param] = max(candidates)
                    break


def extract_from_pdf(pdf_file) -> dict:
    """
    Extrae parámetros del PDF Schindler.
    Una sola pasada con pypdf modo normal — rápido y suficiente.
    """
    found: dict = {p: None for p in PARAMS}
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text = page.extract_text() or ""
            _extract_from_text(text, found)
            if all(v is not None for v in found.values()):
                break
    except Exception as e:
        print(f"[Schindler extractor] Error: {e}")
    return found
