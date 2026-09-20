"""v413: en Planificación, dos personas con el mismo nombre no pueden verse iguales.

`auth.etiqueta_usuarios` existe desde v319 y **solo la usaba Nóminas**. La Planificación
pintaba `Nombre or Usuario` en sus 8 vistas, y en el grupo real hay DOS «Mei Chen»: en el
tablero salían dos filas idénticas y no había forma de saber a cuál se le asignaba la
obra — en la pantalla donde se reparte el trabajo. Sexta aparición del patrón (v151,
v306, v319, v348).

Lo que se protege, y lo que NO hay que tocar:
  (a) toda vista de PERSONAS de `roster_ui` desempata con `_etq`;
  (b) ⚠️ `_ficha_rapida` conserva el nombre CRUDO, porque alimenta el deep-link
      `gp_fichasel = f"{nom} ({usuario})"` — con la etiqueta quedaría
      «Mei Chen (mchen) (mchen)». Es el fallo de v308: cambiar lo que se MUESTRA y
      romper lo que se GUARDA;
  (c) ⚠️ el `nom` de `_catalogo` NO es una persona: es el nombre de un TRABAJO;
  (d) el desempate se hace sobre TODO el grupo, no sobre la lista visible — si no, la
      misma persona cambiaría de nombre según la pantalla.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


src = (RAIZ / "core" / "roster_ui.py").read_text(encoding="utf-8")
sin_com = tokenize.untokenize(
    [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
     if t.type != tokenize.COMMENT])
arb = ast.parse(sin_com)
lineas = sin_com.splitlines()

# ── (a) Ninguna vista de personas puede pintar el nombre crudo ──────────────
# Un sitio «de personas» es el que asigna `nom` a partir de `u.get("Name")`.
# `_catalogo` no aparece aquí porque su `nom` viene de un `text_input` (c).
EXENTAS = {"_ficha_rapida"}          # (b), justificada abajo
crudas, resueltas = [], []
for fn in [n for n in ast.walk(arb) if isinstance(n, ast.FunctionDef)]:
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "nom" for t in n.targets)):
            continue
        txt = lineas[n.lineno - 1]
        if 'get("Name")' not in txt:
            continue                                   # no es un nombre de persona
        (resueltas if "_et.get" in txt or "_etq(" in txt
         else crudas).append((fn.name, n.lineno))

print("== a) las vistas de personas desempatan ==")
chk("hay vistas que auditar (si no, el chequeo pasa en vacío)", len(resueltas) >= 5)
print(f"         desempatadas: {[f for f,_ in resueltas]}")
chk("ninguna vista de personas pinta el nombre crudo…",
    [f for f, _ in crudas if f not in EXENTAS], [])
print(f"         crudas (deben ser solo las exentas): {[f for f,_ in crudas]}")

# ── (b) La ficha rápida conserva el crudo Y pinta la etiqueta ───────────────
print("\n== b) el deep-link de la ficha rápida sigue con el nombre CRUDO ==")
fr = next((n for n in ast.walk(arb)
           if isinstance(n, ast.FunctionDef) and n.name == "_ficha_rapida"), None)
chk("existe `_ficha_rapida`", fr is not None)
# ⚠️ Por ESTRUCTURA, no por texto: un f-string se descompone en trozos (`" ("`, `")"`),
# así que buscar el literal `"{nom} ({usuario})"` daba FALLO con el código correcto.
# Tercera vez hoy que un chequeo mío lee texto donde tenía que leer el árbol.
_deeplink_usa_crudo = None
for n in ast.walk(fr):
    if not (isinstance(n, ast.Assign) and len(n.targets) == 1):
        continue
    t = n.targets[0]
    if not (isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
            and t.slice.value == "gp_fichasel"):
        continue
    nombres = {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name)}
    _deeplink_usa_crudo = ("nom" in nombres and "_nom_v" not in nombres)
chk("se localiza la asignación del deep-link `gp_fichasel`",
    _deeplink_usa_crudo is not None)
chk("...y se arma con `nom` (crudo), NO con la etiqueta", _deeplink_usa_crudo)
chk("...y para PINTAR usa una variable aparte",
    any(isinstance(n, ast.Name) and n.id == "_nom_v" for n in ast.walk(fr)))

# ── (c) El catálogo no es una persona ──────────────────────────────────────
print("\n== c) el `nom` del catálogo (un TRABAJO) no se ha tocado ==")
cat = next((n for n in ast.walk(arb)
            if isinstance(n, ast.FunctionDef) and n.name == "_catalogo"), None)
_toca = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_etq"
            for n in ast.walk(cat)) if cat else False
chk("`_catalogo` NO usa `_etq` (su `nom` es el nombre de un trabajo)", not _toca)

# ── (d) El ámbito del desempate ────────────────────────────────────────────
print("\n== d) se desempata sobre TODO el grupo, no sobre lo visible ==")
h = next((n for n in ast.walk(arb) if isinstance(n, ast.FunctionDef) and n.name == "_etq"), None)
chk("existe el helper `_etq`", h is not None)
_usa_list_users = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                      and n.func.attr == "list_users" for n in ast.walk(h))
chk("...y consulta a TODO el grupo (`list_users`), no solo a `staff`", _usa_list_users)
_delega = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "etiqueta_usuarios" for n in ast.walk(h))
chk("...delegando en `auth.etiqueta_usuarios` (una sola definición de la regla)", _delega)

# ── Comportamiento real ────────────────────────────────────────────────────
print("\n== y funciona ==")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "x", "grupo": "g", "rol": "administrator"}
from core import roster_ui as RU, auth                            # noqa: E402

G = [{"User": "mchen", "Name": "Mei Chen"},
     {"User": "mchen2", "Name": "Mei Chen"},
     {"User": "jl", "Name": "Javier López"}]
_orig = auth.list_users
try:
    auth.list_users = lambda grupo=None, **k: G
    et = RU._etq(G, "g")
    chk("dos homónimos se distinguen", (et["mchen"], et["mchen2"]),
        ("Mei Chen (mchen)", "Mei Chen (mchen2)"))
    chk("un nombre único no se ensucia", et["jl"], "Javier López")
    chk("la etiqueta no cambia según a quién se vea en pantalla",
        RU._etq([G[0], G[2]], "g")["mchen"], "Mei Chen (mchen)")
    auth.list_users = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sin conexión"))
    chk("si falla la lectura, degrada a la lista visible y no deja el nombre vacío",
        RU._etq(G, "g")["mchen"], "Mei Chen (mchen)")
finally:
    auth.list_users = _orig

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
