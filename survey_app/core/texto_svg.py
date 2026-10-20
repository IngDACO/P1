"""Texto que CABE en un SVG de los diagramas (v590).

⚠️ Hasta v589 el nombre de la obra se cortaba a ciegas por número de letras (`[:24]`,
`[:30]`…): «Bondi Junction Tower — Lift 1» salía «Bondi Junction Tower — L» en el cajetín del
plano por piso y de la plomada, en pantalla y en los PDF, con sitio de sobra para el nombre
entero. Y entraba SIN escapar: una obra «Smith & Sons» dejaba el SVG inválido (svglib no lo
lee y el diagrama falta del informe).

Aquí se MIDE con la fuente de los diagramas (Arial/Helvetica, la que usa svglib en el PDF;
`reportlab` ya es dependencia) y se corta con «…» solo si no cabe.
"""
from xml.sax.saxutils import escape


def ancho(texto, tam: float, negrita: bool = False) -> float:
    """Ancho en px de `texto` a `tam` px en Helvetica (≈ Arial)."""
    s = str(texto or "")
    try:
        from reportlab.pdfbase.pdfmetrics import stringWidth
        return stringWidth(s, "Helvetica-Bold" if negrita else "Helvetica", tam)
    except Exception:                       # sin reportlab: estimación prudente (por lo ancho)
        return len(s) * tam * 0.6


def cabe(texto, ancho_px: float, tam: float, negrita: bool = False) -> str:
    """`texto` ESCAPADO para SVG y, si mide más que `ancho_px`, cortado con «…»."""
    s = " ".join(str(texto or "").split())
    if ancho(s, tam, negrita) > ancho_px:
        while s and ancho(s + "…", tam, negrita) > ancho_px:
            s = s[:-1]
        s = s.rstrip(" ·—-") + "…"
    return escape(s)
