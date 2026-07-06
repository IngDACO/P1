"""
Corte de rieles (rail cutting).

Extrae LFKK y LFGK del PDF y calcula los cortes de riel para cada elevador
del shaft, en dos casos:

CASO 1 — el riel a cortar es el PRIMERO instalado (el de más abajo):
    A      = n2500·2500 + n5000·5000           (iguales para todos los elevadores)
    RC     = L + LFKK   (riel de cabina)
    RCW    = L + LFGK   (riel de contrapeso)
    CutRC  = RC − A     CutRCW = RCW − A        (L varía por elevador)

CASO 2 — el riel a cortar es el ÚLTIMO instalado (el de más arriba):
    El usuario llena RZ, RO, RF, RB por elevador. Dos sub-casos:
      penúltimo POR ENCIMA del FFL:  CutR* = LF − R*
      penúltimo POR DEBAJO del FFL:  CutR* = LF + R*
    (LFKK para RZ/RO ; LFGK para RF/RB)
"""
import re


# ── Extracción de LFKK / LFGK del PDF ────────────────────────
def extract_lf(pdf_file) -> dict:
    """Devuelve {'LFKK': float|None, 'LFGK': float|None} leídos del PDF."""
    result = {"LFKK": None, "LFGK": None}
    try:
        from pypdf import PdfReader
        from extractors.schindler import _page_text_positional
        reader = PdfReader(pdf_file)
        text = []
        for page in reader.pages:
            text.append(_page_text_positional(page) or "")
            text.append(page.extract_text() or "")
        full = "\n".join(text)
        for key in ("LFKK", "LFGK"):
            m = re.search(rf"{key}\s*[=:\s]\s*(-?\d+(?:[.,]\d+)?)", full, re.IGNORECASE)
            if m:
                result[key] = float(m.group(1).replace(",", "."))
    except Exception as e:
        print(f"[rail_cut] extracción LF: {e}")
    return result


# ── CASO 1 ───────────────────────────────────────────────────
def compute_case1(lfkk: float, lfgk: float, n2500: int, n5000: int,
                  L_list: list) -> dict:
    """
    L_list: lista con L de cada elevador.
    Devuelve dict con A y, por elevador, RC/RCW/CutRC/CutRCW.
    """
    A = int(n2500) * 2500.0 + int(n5000) * 5000.0
    elevadores = []
    for L in L_list:
        L = float(L or 0)
        rc  = L + float(lfkk)
        rcw = L + float(lfgk)
        elevadores.append({
            "L": L, "RC": rc, "RCW": rcw,
            "CutRC": rc - A, "CutRCW": rcw - A,
        })
    return {"A": A, "elevadores": elevadores}


# ── CASO 2 ───────────────────────────────────────────────────
def compute_case2(lfkk: float, lfgk: float, rows: list, subcaso: str) -> list:
    """
    rows: lista por elevador con {'RZ','RO','RF','RB'}.
    subcaso: 'encima'  → CutR* = LF − R*
             'debajo'  → CutR* = LF + R*
    RZ/RO usan LFKK ; RF/RB usan LFGK.
    """
    sign = -1.0 if subcaso == "encima" else 1.0
    out = []
    for r in rows:
        rz = float(r.get("RZ", 0) or 0)
        ro = float(r.get("RO", 0) or 0)
        rf = float(r.get("RF", 0) or 0)
        rb = float(r.get("RB", 0) or 0)
        out.append({
            "CutRZ": float(lfkk) + sign * rz,
            "CutRO": float(lfkk) + sign * ro,
            "CutRF": float(lfgk) + sign * rf,
            "CutRB": float(lfgk) + sign * rb,
        })
    return out
