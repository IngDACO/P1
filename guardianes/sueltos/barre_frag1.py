"""CUARTA red: fragmentos de f-string de UNA sola palabra, en español.

El hueco que mordió en v443: `f"{g['alarmas']} alarmas"`. Ninguna de las tres redes
anteriores lo ve —la de posición mira el argumento de `st.*` (aquí es una f-string
entera), la de frases pide 3+ palabras y la de cortas pide 2—, y además NO se puede
envolver en `t()` porque es un trozo de f-string.
"""
import ast
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

# Palabras españolas de UNA sola pieza que aparecen como sufijo/prefijo de un dato.
ES = {
    "alarmas", "vencidos", "vencidas", "credenciales", "proyectos", "proyecto",
    "personas", "usuarios", "horas", "dias", "días", "obras", "obra", "activos",
    "pendientes", "pendiente", "retraso", "retrasos", "adelanto", "sitios",
    "trabajos", "actividades", "facturas", "nominas", "nóminas", "cotizaciones",
    "clientes", "gastos", "compras", "recibos", "documentos", "archivos", "fotos",
    "alertas", "avisos", "elevadores", "asignados", "ausencias", "colillas",
    "restantes", "creadas", "omitidas", "guardado", "guardada", "eliminado",
    "sin", "con", "de", "del", "para", "por", "en", "el", "la", "los", "las",
    "y", "o", "un", "una", "que", "más", "mas", "ya", "no", "al",
}


def _sin(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def fragmentos(ruta):
    """Trozos literales de f-string cuyo texto es UNA palabra española."""
    try:
        tr = ast.parse(Path(ruta).read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for n in ast.walk(tr):
        if not isinstance(n, ast.JoinedStr):
            continue
        for p in n.values:
            if not (isinstance(p, ast.Constant) and isinstance(p.value, str)):
                continue
            txt = p.value.strip()
            # una sola palabra (permite puntuación alrededor)
            pal = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]{2,}", txt)
            if len(pal) != 1:
                continue
            if _sin(pal[0]) in {_sin(x) for x in ES}:
                out.append((n.lineno, txt))
    return out


if __name__ == "__main__":
    tot = 0
    for f in sorted(list((RAIZ / "core").glob("*_ui.py")) + [RAIZ / "app.py"]):
        hits = sorted(set(fragmentos(f)))
        if hits:
            print(f"\n── {f.name} ({len(hits)})")
            for ln, s in hits:
                print(f"   {ln}: {s!r}")
            tot += len(hits)
    print(f"\n{tot} fragmentos de una palabra en español")
