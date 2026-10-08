# -*- coding: utf-8 -*-
"""v547 · BARRIDO: TODO DESPLEGABLE CON CONTROLES DENTRO LLEVA CLAVE (trampa nº35).

Visto en producción en v546 (Fichaje): un `st.expander` SIN clave se cierra solo cuando
cambia lo que tiene encima —cada acción deja un aviso por `flash` que aparece una pasada y se
va—, y con controles dentro el usuario pierde el botón a mitad de la tarea. Comprobado en una
mini-app 1.64: con clave sigue abierto. Había 65 así en la app (decisión del usuario: barrido
de una vez, con guardián).

Lo que se protege (sobre el CÓDIGO REAL, con el AST):
1. Todo `expander` con controles dentro tiene `key=`.
2. Las claves fijas son únicas en TODA la app (dos desplegables pueden convivir en una
   pantalla y la sesión es una) y siguen el convenio `exp_…` / `…_exp…`.
3. Dentro de un bucle, la clave usa la variable del bucle (si no, se repetiría: error).
4. Si `expanded=` depende de los datos, la clave lleva esa MISMA condición: con clave,
   Streamlit solo respeta `expanded` la primera vez, y se perdería «abrirse solo cuando…».
5. Ningún CSS `[class*="st-key-exp…"]` atrapa las claves nuevas.
Y las sondas se validan con casos construidos: si no ven el fallo, su «0» no vale (nº12).
"""
import ast
import os
import pathlib
import re
import sys

RAIZ = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


CTRL = {"button", "text_input", "number_input", "selectbox", "radio", "time_input",
        "date_input", "text_area", "checkbox", "data_editor", "file_uploader", "multiselect",
        "toggle", "elegir", "form_submit_button", "download_button", "slider",
        "segmented_control", "pills", "color_picker", "camera_input", "chat_input"}


def _llamadas(nodo):
    out = set()
    for x in ast.walk(nodo):
        if isinstance(x, ast.Call):
            if isinstance(x.func, ast.Name):
                out.add(("N", x.func.id))
            elif isinstance(x.func, ast.Attribute):
                out.add(("A", x.func.attr))
    return out


def con_controles(fuentes):
    """{(módulo, función): ¿pinta controles?}, SIGUIENDO las funciones a las que llama.

    ⚠️ v548 · Ampliado tras una escapada: la primera versión solo miraba las llamadas
    DIRECTAS del cuerpo, y 11 desplegables tenían los controles dentro de una función
    auxiliar («Create field user» → `_crear_usuario_form`, los «Upload drawing» de las 4
    herramientas → `selector`…). Se vio en producción, recorriendo la app tras v547.
    Una llamada `mod.f()` se resuelve por NOMBRE en cualquier módulo: si alguna `f` pinta
    controles, cuenta (conservador: pedir clave de más no rompe nada; de menos, sí).
    """
    funcs = {}
    for m, src in fuentes.items():
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.setdefault((m, n.name), n)
    tiene = {k: any(isinstance(x, ast.Call) and getattr(x.func, "attr", None) in CTRL
                    for x in ast.walk(v)) for k, v in funcs.items()}
    por_nombre = {}
    for k in funcs:
        por_nombre.setdefault(k[1], []).append(k)
    cambio = True
    while cambio:
        cambio = False
        for k, v in funcs.items():
            if tiene[k]:
                continue
            for tipo, nom in _llamadas(v):
                cands = [(k[0], nom)] if tipo == "N" else por_nombre.get(nom, [])
                if any(tiene.get(c) for c in cands):
                    tiene[k] = cambio = True
                    break
    return tiene, por_nombre


def desplegables(src, nombre="?", tiene=None, por_nombre=None):
    """[(línea, call, with, en_bucle, nombres_del_bucle, con_controles)] de un fuente."""
    tiene, por_nombre = tiene or {}, por_nombre or {}
    arbol = ast.parse(src)
    padres = {}
    for n in ast.walk(arbol):
        for h in ast.iter_child_nodes(n):
            padres[h] = n
    out = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.With):
            continue
        for it in n.items:
            c = it.context_expr
            if not (isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "expander"):
                continue
            ctrl = any(isinstance(x, ast.Call) and getattr(x.func, "attr", "") in CTRL
                       for b in n.body for x in ast.walk(b))
            if not ctrl:                      # …o dentro de una función a la que llama
                _ll = set()
                for b in n.body:
                    _ll |= _llamadas(b)
                ctrl = any(tiene.get((nombre, nom)) if tipo == "N"
                           else any(tiene.get(k) for k in por_nombre.get(nom, []))
                           for tipo, nom in _ll)
            q, bucle, vars_bucle = n, False, set()
            while q in padres:
                q = padres[q]
                if isinstance(q, (ast.For, ast.comprehension)):
                    bucle = True
                    vars_bucle |= {x.id for x in ast.walk(q.target) if isinstance(x, ast.Name)}
                if isinstance(q, ast.While):
                    bucle = True
            out.append((n.lineno, c, n, bucle, vars_bucle, ctrl))
    return out


# Claves ANTERIORES al barrido, fuera del convenio a propósito (renombrarlas rompería lo
# que cuelga de ellas): `cpxresumen` la usa la CSS del resumen del día (v304) y sus
# guardianes; las otras dos son de v546 y las anclan `verif_v546`/`romper_v546`.
EXENTAS = {"cpxresumen", "cpx_lectura_ia", "tc_corregir"}


def problemas(fuentes):
    """Aplica las reglas 1-4 a {nombre: fuente}. Devuelve (sin_clave, repetidas, convenio,
    bucle_fijo, expanded_suelto)."""
    sin, conv, bucle_fijo, exp_suelto = [], [], [], []
    fijas = {}
    tiene, por_nombre = con_controles(fuentes)
    for nom, src in fuentes.items():
        for ln, c, _w, bucle, vb, ctrl in desplegables(src, nom, tiene, por_nombre):
            kw = next((k.value for k in c.keywords if k.arg == "key"), None)
            if kw is None:
                if ctrl:
                    sin.append("%s:%d" % (nom, ln))
                continue
            txt = ast.unparse(kw)
            if isinstance(kw, ast.Constant):
                fijas.setdefault(kw.value, []).append("%s:%d" % (nom, ln))
                if not str(kw.value).startswith("exp_") and kw.value not in EXENTAS:
                    conv.append("%s:%d %s" % (nom, ln, txt))
            elif "exp" not in txt:
                conv.append("%s:%d %s" % (nom, ln, txt))
            if bucle and not ({x.id for x in ast.walk(kw) if isinstance(x, ast.Name)} & vb):
                bucle_fijo.append("%s:%d %s" % (nom, ln, txt))
            _e = next((k.value for k in c.keywords if k.arg == "expanded"), None)
            if _e is not None and not isinstance(_e, ast.Constant):
                if ast.unparse(_e) not in txt:
                    exp_suelto.append("%s:%d expanded=%s key=%s" % (nom, ln, ast.unparse(_e), txt))
    rep = {k: v for k, v in fijas.items() if len(v) > 1}
    return sin, rep, conv, bucle_fijo, exp_suelto


print("1. Las sondas VEN cada fallo (casos construidos)")
_MALO = {
    "a.py": "import streamlit as st\n"
            "with st.expander('x'):\n    st.button('b')\n",                       # sin clave
    "b.py": "import streamlit as st\n"
            "with st.expander('y', key='exp_dup'):\n    st.button('c')\n"
            "with st.expander('z', key='exp_dup'):\n    st.button('d')\n",           # repetida
    "c.py": "import streamlit as st\n"
            "for e in L:\n    with st.expander(e, key='exp_fija'):\n        st.button(e)\n",
    "d.py": "import streamlit as st\n"
            "with st.expander('w', expanded=bool(x), key='exp_w'):\n    st.button('e')\n",
    "e.py": "import streamlit as st\n"
            "with st.expander('v', key='raro'):\n    st.button('f')\n",
    # v548 · los controles, dentro de una función auxiliar (local y de otro módulo)
    "g.py": "import streamlit as st\nimport h\n"
            "def _form():\n    st.text_input('n')\n"
            "with st.expander('s'):\n    _form()\n"
            "with st.expander('r'):\n    h.selector()\n",
    "h.py": "import streamlit as st\n"
            "def selector():\n    st.selectbox('o', [1])\n",
}
_s, _r, _c, _b, _e = problemas(_MALO)
chk("ve el desplegable con controles SIN clave", "a.py:2" in _s, _s)
chk("⚠️ v548 · ve los controles dentro de una función AUXILIAR (local y de otro módulo)",
    "g.py:5" in _s and "g.py:7" in _s, _s)
chk("...y no marca más de la cuenta", sorted(_s) == ["a.py:2", "g.py:5", "g.py:7"], _s)
chk("ve la clave fija REPETIDA", "exp_dup" in _r, _r)
chk("ve la clave FIJA dentro de un bucle", any("c.py" in x for x in _b), _b)
chk("ve el `expanded` que depende de datos y no va en la clave", any("d.py" in x for x in _e), _e)
chk("ve la clave fuera de convenio", any("e.py" in x for x in _c), _c)
_BUENO = {"f.py": "import streamlit as st\n"
                  "with st.expander('solo texto'):\n    st.write('nada')\n"                # sin controles
                  "for d in L:\n    with st.expander(d, key=f\"exp_h_{d['id']}\"):\n"
                  "        st.button(d)\n"
                  "with st.expander('u', expanded=bool(x), key=f'exp_u_{bool(x)}'):\n"
                  "    st.button('g')\n"}
chk("...y no marca lo que está bien (sin controles, bucle con su variable, condición en la "
    "clave)", problemas(_BUENO) == ([], {}, [], [], []), problemas(_BUENO))

print("\n2. El código REAL cumple las 4 reglas")
_F = {}
for p in sorted(list((RAIZ / "core").glob("*.py")) + [RAIZ / "app.py"]):
    _F[p.name] = p.read_text(encoding="utf-8")
_tot = sum(1 for s in _F.values() for _ in desplegables(s))
_ti, _pn = con_controles(_F)
_ctl = sum(1 for _m, s in _F.items() for d in desplegables(s, _m, _ti, _pn) if d[5])
print("         (%d desplegables en la app, %d con controles dentro)" % (_tot, _ctl))
chk("se encontraron desplegables (no es un paso en vacío)", _ctl >= 75, _ctl)
_s, _r, _c, _b, _e = problemas(_F)
chk("⚠️ TODO desplegable con controles dentro lleva clave", _s == [], _s)
chk("ninguna clave fija se repite en la app", _r == {}, _r)
chk("todas siguen el convenio exp_… / …_exp…", _c == [], _c)
chk("dentro de un bucle, la clave usa la variable del bucle", _b == [], _b)
chk("si `expanded` depende de los datos, la condición va en la clave", _e == [], _e)

print("\n3. Ningún CSS atrapa las claves nuevas")
_css = [m for s in _F.values() for m in re.findall(r"class\*=.{0,3}st-key-(\w*)", s)]
chk("ningún selector por subcadena empieza por un trozo de «exp_»",
    not [x for x in _css if "exp_".startswith(x) or x.startswith("exp")], sorted(set(_css)))

print("\n4. Los que se abren solos según los datos conservan su regla")
for _nom, _frag in (("auth_ui.py", 'key=f"exp_own_upman_{not ups}"'),
                    ("auth_ui.py", 'key=f"exp_own_addrail_{not data}"'),
                    ("projects_ui.py", 'key=f"exp_ind_{pid}_{bool(links)}"'),
                    ("xero_ui.py", 'key=f"exp_xero_quien_{bool(sin_confirmar)}"')):
    chk("%s: %s" % (_nom, _frag), _frag in _F[_nom])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
