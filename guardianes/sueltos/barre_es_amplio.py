# -*- coding: utf-8 -*-
"""SÉPTIMA red: español por MORFOLOGÍA, no por lista de palabras.

⚠️ Las seis redes anteriores usan un léxico, y un léxico siempre se queda corto: no
veían «vencida», «devuelto», «mantenimiento» ni «retraso», que estaban a la vista en
la campana de avisos. Es la trampa nº28 por quinta vez.

Aquí la señal es la FORMA de la palabra: acentos y ñ, o terminaciones que en inglés
no existen (-ción, -miento, -ado/-ada, -ido/-ida, -mente, -aje…). Coge más ruido que
un léxico, y ese es el punto: el ruido se descarta leyendo, un hueco no se ve.

⚠️ Sigue sin ser un oráculo: «Total», «Base» o «Normal» se escriben igual en los dos
idiomas y no los marca nadie. Un «0» aquí significa «0 de lo que esta red ve».
"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
MODULOS = sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"])

ACENTO = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
SUFIJO = re.compile(
    r"\b\w{4,}(ción|ciones|miento|mientos|dad|ado|ada|ados|adas|ido|ida|idos|idas"
    r"|ando|endo|mente|aje|anza|ecer|arse|irse)\b", re.I)
# palabras cortas frecuentes que la morfología no alcanza
# ⚠️ SOLO palabras que en inglés no existen. Meter «no», «si» o «solo» disparaba
# sobre `'(no name)'`, `'no hours yet'` y `'— no client —'`, que están en inglés: un
# detector que grita sobre lo ya traducido acaba ignorándose entero.
CORTAS = {
    "del", "los", "las", "unos", "unas", "una", "con", "sin", "por", "para", "que",
    "sus", "son", "más", "menos", "hace", "hasta", "desde", "cada", "otro", "otra",
    "otros", "otras", "todo", "toda", "todos", "todas", "este", "esta", "esto",
    "ese", "esa", "aún", "cuando", "donde", "quien", "falta", "faltan", "sitio",
    "sitios", "obra", "obras", "hoy", "ayer", "mañana", "vencido", "vencida",
    "vencidos", "vencidas", "guardados", "guardadas", "enviando", "preparando",
    "vacío", "vacía", "todos", "ninguno", "ninguna", "cálculos", "calculos",
}
# lo que no es texto de pantalla ni aunque lo parezca
NO_TEXTO = re.compile(r"^(#[0-9a-fA-F]{3,8}|[a-z0-9_]+_|[a-z_]+)$")
# ruido que NO es pantalla
RUIDO = re.compile(r"^\s*(<style|<div|<span|<rect|<svg|/\*|%[YmdHMS]|https?://)")


def _lit_visibles(ruta):
    tr = ast.parse(ruta.read_text(encoding="utf-8"))
    # ⚠️ Fuera lo que es DATO, o el barrido se ahoga en su propio ruido y deja de
    # servir para decidir nada: claves de dict (la cabecera la resuelve `tabla.cfg`),
    # lo que se compara, lo que indexa y el primer argumento de un `.get()`.
    datos = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Dict):
            datos |= {id(k) for k in n.keys if k is not None}
        if isinstance(n, ast.Compare):
            for x in [n.left] + list(n.comparators):
                datos |= {id(y) for y in ast.walk(x)}
        if isinstance(n, ast.Subscript):
            datos |= {id(y) for y in ast.walk(n.slice)}
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") in {
                "get", "setdefault", "pop", "startswith", "endswith", "split",
                "strip", "rsplit", "replace", "join"} and n.args:
            datos |= {id(y) for y in ast.walk(n.args[0])}
    dentro = set(datos)
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
           and n.func.id in {"t", "d", "_d"}:
            dentro |= {id(x) for x in ast.walk(n)}
    docs = set()
    for n in ast.walk(tr):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
               and isinstance(b[0].value.value, str):
                docs.add(id(b[0].value))
    logs = set()
    for n in ast.walk(tr):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
           and isinstance(n.func.value, ast.Name) \
           and n.func.value.id in {"logger", "log", "logging"}:
            logs |= {id(x) for x in ast.walk(n)}
    out = []
    for n in ast.walk(tr):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
            continue
        if id(n) in dentro or id(n) in docs or id(n) in logs:
            continue
        out.append((n.lineno, n.value))
    return out


def sospechosas(ruta):
    out = []
    for ln, s in _lit_visibles(ruta):
        t = s.strip()
        if not t or len(t) > 160 or RUIDO.match(t) or NO_TEXTO.match(t):
            continue
        pal = re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]{2,}", t)
        if not pal:
            continue
        marca = (bool(ACENTO.search(t)) or bool(SUFIJO.search(t))
                 or any(p.lower() in CORTAS for p in pal))
        if marca:
            out.append((ln, t))
    return sorted(set(out))


if __name__ == "__main__":
    solo = [a for a in sys.argv[1:] if not a.startswith("-")]
    tot = 0
    for f in MODULOS:
        if solo and f.stem not in solo:
            continue
        hits = sospechosas(f)
        if hits:
            print(f"\n── {f.name} ({len(hits)})")
            for ln, s in hits:
                print(f"   L{ln:<5} {s[:110]!r}")
            tot += len(hits)
    print(f"\n{tot} literales sospechosos de español")
