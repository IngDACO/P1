"""
Extractor de parámetros para planos Schindler (CAD PDF).

Casos especiales manejados:
  1. Números pegados después:    BS=19981272     → BS=1998
  2. Números pegados antes:      110TKSW=965     → TKSW=965
  3. Parámetros pegados:         TKSW=965TS=1750 → ambos separados
  4. Sin '=' valor en línea sig: BKF2\n936       → BKF2=936
  5. Valor ANTES del label:      170BKF2 30BKF1  → BKF2=170, BKF1=30
  6. Elementos PDF separados:    SF1=51 | 1175   → SF1=51  (visitor_text separa por posición XY)
"""
from pypdf import PdfReader
import logging
import re

logger = logging.getLogger(__name__)

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
    "TKS":  (5,    150),   # umbral cabina → umbral rellano: típico 20-80 mm
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


# ── Extracción posicional con visitor_text ───────────────────────
_CHAR_W  = 8.0   # ancho estimado por carácter (pts) — conservador
_GAP_TH  = 50.0  # gap horizontal mínimo (pts) para insertar espacio separador
_Y_TOL   = 20.0  # tolerancia vertical (pts) para agrupar en misma línea


def _page_text_positional(page) -> str:
    """
    Extrae el texto de una página usando visitor_text para obtener
    posiciones XY de cada elemento.

    Agrupa elementos por línea (misma Y ± _Y_TOL) y dentro de cada línea
    inserta un espacio entre elementos cuyo gap horizontal supera _GAP_TH.
    Esto evita que anotaciones CAD distantes se concatenen con los valores
    de los parámetros (ej. SF1=51 + 1175 → "SF1=51 1175" en lugar de
    "SF1=511175").

    Si el visitor falla, cae silenciosamente a extract_text() convencional.
    """
    elements: list[tuple[float, float, str]] = []   # (y, x, text)

    def _visitor(text, cm, tm, fontdict, fontSize):
        if not text:
            return
        t = text.replace('\n', '').replace('\r', '')
        if not t:
            return
        x = float(tm[4])
        y = float(tm[5])
        elements.append((y, x, t))

    try:
        page.extract_text(visitor_text=_visitor)
    except Exception:
        return page.extract_text() or ""

    if not elements:
        return page.extract_text() or ""

    # Ordenar: Y descendente (arriba primero), X ascendente (izquierda primero)
    elements.sort(key=lambda e: (-round(e[0] / _Y_TOL) * _Y_TOL, e[1]))

    # Agrupar por Y (tolerancia _Y_TOL)
    lines: list[list[tuple[float, str]]] = []   # cada línea: [(x, text), ...]
    cur_y: float | None = None
    cur_line: list[tuple[float, str]] = []

    for y, x, txt in elements:
        if cur_y is None or abs(y - cur_y) > _Y_TOL:
            if cur_line:
                lines.append(cur_line)
            cur_line = [(x, txt)]
            cur_y = y
        else:
            cur_line.append((x, txt))
    if cur_line:
        lines.append(cur_line)

    # Construir texto: elementos de la misma línea se unen;
    # si el gap entre el final estimado de uno y el inicio del siguiente
    # supera _GAP_TH, se inserta un espacio.
    result_lines: list[str] = []
    for line in lines:
        line.sort(key=lambda e: e[0])   # de izquierda a derecha
        out = ""
        prev_x_end: float | None = None
        for x, txt in line:
            if prev_x_end is not None:
                gap = x - prev_x_end
                if gap > _GAP_TH:
                    out += " "
            out += txt
            prev_x_end = x + len(txt) * _CHAR_W
        if out.strip():
            result_lines.append(out)

    return "\n".join(result_lines)


def _extract_from_text(text: str, found: dict) -> None:
    """Extrae parámetros del texto y actualiza `found` in-place."""

    # ── Paso 1: Normalizar saltos de línea ─────────────────────────
    # CRLF (Windows) y CR sueltos → LF
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Unir dígito-salto-dígito: TKS=30\n62 → TKS=3062  (fallback, no debería ocurrir
    # con extracción posicional, pero se mantiene para seguridad)
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
            for length in (4, 3, 2):
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
    Extrae parámetros del PDF Schindler.  Estrategia de dos pasadas:

    Pasada 1 — visitor_text (texto posicional):
      Reconstruye el texto respetando posiciones XY. Evita que anotaciones
      CAD distantes se concatenen con valores de parámetros
      (ej. SF1=51 + anotación 1175 → "SF1=51 1175" en lugar de "SF1=511175").

    Pasada 2 — extract_text() convencional (fallback para None restantes):
      Algunos valores (BKF1, BKF2) aparecen como cotas ANTES del label en
      el plano ("170BKF2") en una línea que extract_text() reconstruye
      correctamente pero que el visitor separa por posición.  Como `found`
      no sobreescribe valores ya hallados, SF1/TKS encontrados en la pasada 1
      no se ven afectados por las concatenaciones del texto plano.
    """
    found: dict = {p: None for p in PARAMS}
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            # Pasada 1: extracción posicional
            text_pos = _page_text_positional(page)
            _extract_from_text(text_pos, found)

            # Pasada 2: texto plano para parámetros aún no encontrados
            if any(v is None for v in found.values()):
                text_plain = page.extract_text() or ""
                _extract_from_text(text_plain, found)

            if all(v is not None for v in found.values()):
                break
    except Exception as e:
        logger.warning("Schindler extractor: %s", e)
    return found
