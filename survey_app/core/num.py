"""Lectura de valores de celda: número, fecha y letra de columna (v323).

⚠️ Módulo HOJA: no importa nada de `core`, así que puede usarlo cualquiera sin
riesgo de import circular.

Existía UNA copia de cada uno de estos helpers en cada módulo que tocaba la hoja
(`_num` ×14, `_parse_date` ×3, `_col_letter` ×7) y **habían divergido**: cinco
implementaciones distintas de `_num` y dos de `_parse_date`. La divergencia no era
cosmética, era el fallo — ver abajo.
"""
import re
from datetime import date, datetime

# separadores de miles: 1,234,567 (AU/US) o 1.234.567 (EU)
_MILES = re.compile(r"^[+-]?\d{1,3}(?:([.,])\d{3})+$")
_LIMPIA = re.compile(r"[^\d,.\-+]")


def num(v, default=0.0) -> float:
    """Valor de celda → float, tolerante al formato con que Sheets lo devuelva.

    ⚠️ EL FALLO QUE ARREGLA (v323): las 5 variantes anteriores hacían
    `float(str(v).replace(",", "."))` o directamente `float(v)`, así que un
    importe con **separador de miles** —`1,234.56`, que es justo como Sheets
    formatea el dinero en AU/US— reventaba y devolvía **0.0 en silencio**.
    Cualquier cifra de $1.000 para arriba escrita a mano en la hoja se leía
    como cero, sin un solo aviso, en costos, facturas, nóminas e inventario.

    Reglas (probadas en `verif_v323.py`):
      - `1,234.56` / `1.234,56` → hay los dos separadores: el ÚLTIMO es el
        decimal y el otro es de miles.
      - `1,234` → solo coma en grupos de 3 → es separador de miles → 1234.
      - `1234,56` → solo coma sin forma de grupo → es decimal → 1234.56.
      - `1.234` → solo punto: **decimal, siempre**. Es lo que la app escribe
        (tarifas, horas, pesos), así que tratarlo como miles cambiaría números
        que hoy son correctos.
      - símbolos de moneda y espacios se ignoran; vacío/basura → `default`.
    """
    if isinstance(v, bool):                      # bool ES int en Python
        return default
    if isinstance(v, (int, float)):
        return float(v)

    s = _LIMPIA.sub("", str(v).strip())
    if not s or s in ("-", "+", ".", ","):
        return default

    tiene_c, tiene_p = "," in s, "." in s
    if tiene_c and tiene_p:                      # el último manda: es el decimal
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif tiene_c:
        s = s.replace(",", "") if _MILES.match(s) else s.replace(",", ".")
    # solo punto → ya está en formato float

    try:
        return float(s)
    except ValueError:
        return default


def parse_date(v):
    """Texto de celda → `date`, o `None` si no hay fecha legible.

    ⚠️ EL FALLO QUE ARREGLA (v323): `invoices` e `inventory` usaban
    `date.fromisoformat`, que **solo** acepta ISO. Una fecha `16/08/2026` —el
    formato de texto libre que hubo hasta v149— se leía como `None`, y una fila
    sin fecha legible queda FUERA de todo filtro por periodo: esa factura
    desaparecía del P&L sin decir nada.

    Día primero (`%d/%m`), que es la convención de AU, igual que `admin_digest`.
    """
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v or "").strip()
    if not s:
        return None
    s = s[:10] if len(s) >= 10 and (s[4] in "-/" or s[2] in "-/") else s
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def col_letter(n: int) -> str:
    """Índice de columna 1-based → letra(s) A1 (1→A, 26→Z, 27→AA)."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s
