# -*- coding: utf-8 -*-
"""v478 · La autogestion del campo: las tres «mias» bajo un nivel, y el movil.

Lo que hay que proteger:
  (a) la nav del campo baja a 6 y **no se pierde nada**: las tres siguen alcanzables;
  (b) el despachador compara contra el **ID exacto** (comparar el display navega a
      ninguna parte y no da ningun error — el fallo real de v303);
  (c) el atajo de «avisar de una baja» existe, apunta a un destino que EXISTE y solo
      sale cuando NO se ha fichado (si no, es ruido en la pantalla mas usada);
  (d) el aviso de credenciales solo aparece si hay algo que vence — EJECUTADO, porque
      importar no ejecuta (v378);
  (e) la tabla de credenciales lleva delante lo que se mira primero y ancla la
      identidad: a 375 px glide recorta SIN elipsis (v408).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)                      # los secrets se buscan desde el CWD (trampa n19)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "rol": "field", "grupo": "cliente1"}

from core import home_ui as H                                     # noqa: E402

fallos = []
n_ok = 0


def ok(m, det=""):
    """⚠️ Acepta el 2º argumento y lo IGNORA: el idioma de estos guardianes es
    `(ok if cond else fallo)(msg, det)`, y con `ok(m)` a secas el guardian revienta
    justo cuando PASA — y uno que revienta devuelve != 0 SIEMPRE, asi que una tanda de
    roturas saldria «cazada» sin probar nada (v459/v463)."""
    global n_ok
    n_ok += 1
    print("   ok   " + m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO " + m + (" -> %r" % (det,) if det else ""))


SRC_H = io.open(os.path.join("core", "home_ui.py"), encoding="utf-8").read()
SRC_T = io.open(os.path.join("core", "timeclock_ui.py"), encoding="utf-8").read()
SRC_A = io.open(os.path.join("core", "auth_ui.py"), encoding="utf-8").read()

# ── 1 ────────────────────────────────────────────────────────────────────────
print("1. La nav del campo baja a 6 y no se pierde nada")
_secs = [k for k, _d in H._secciones()]
(ok if len(_secs) == 6 else fallo)("son 6 secciones, no 8", _secs)
_sub = H._subsecciones().get("autogestion", ("", []))
_ids = [i for i, _d in _sub[1]]
(ok if sorted(_ids) == sorted(["🌴 Ausencias", "🎫 Credenciales", "💰 Colillas"])
 else fallo)("las tres «mias», bajo autogestion", _ids)
(ok if "autogestion" in _secs else fallo)("y la seccion existe en su nav")
# ⚠️ y NINGUNA de las tres sigue suelta como seccion: si quedara, estaria en DOS
# sitios — el patron de v140 que este cambio viene justo a evitar.
_sueltas = [x for x in ("credenciales", "colillas", "ausencias") if x in _secs]
(ok if not _sueltas else fallo)("ninguna quedo tambien suelta (v140)", _sueltas)

# ── 2 ────────────────────────────────────────────────────────────────────────
print("\n2. El despachador compara contra el ID EXACTO (el fallo de v303)")
for _id in ("🎫 Credenciales", "💰 Colillas"):
    (ok if '"%s"' % _id in SRC_H else fallo)("despacha %r" % _id)
# el display NO puede usarse para comparar
_displays = [d for _i, d in _sub[1]]
_mal = [d for d in _displays if 'sub == "%s"' % d in SRC_H or "_sub == \"%s\"" % d in SRC_H]
(ok if not _mal else fallo)("no compara contra el display", _mal)

# ── 3 ────────────────────────────────────────────────────────────────────────
print("\n3. El atajo de «avisar de una baja» en Fichaje")
_arb = ast.parse(SRC_T)
_nav = [n for n in ast.walk(_arb)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "navegar"]
(ok if _nav else fallo)("existe el salto")
_dest = [(a.args[0].value, a.args[1].value) for a in _nav
         if len(a.args) == 2 and all(isinstance(x, ast.Constant) for x in a.args)]
(ok if ("autogestion", "🌴 Ausencias") in _dest else fallo)(
    "apunta a un destino que EXISTE en la nav del campo", _dest)
# ⚠️ y cuelga de NO estar fichado: quien ya ficho no va a avisar de una baja
_cond = [n for n in ast.walk(_arb) if isinstance(n, ast.If)
         and "tc_baja" in ast.unparse(n)]
_txt = ast.unparse(_cond[0].test) if _cond else ""
(ok if ("not gen" in _txt and "not prj" in _txt and "field" in _txt)
 else fallo)("solo si NO esta fichado y es del campo", _txt)

# ── 4 ────────────────────────────────────────────────────────────────────────
print("\n4. El aviso de credenciales solo sale si hay algo que vence (EJECUTADO)")
from core import credentials as C                                 # noqa: E402
_entra = lambda f: C.status(f) in ("por_vencer", "vencido")
(ok if _entra("2026-09-15") else fallo)("una por vencer entra en el aviso")
(ok if _entra("2026-01-01") else fallo)("una vencida entra")
(ok if not _entra("2027-12-31") else fallo)("una vigente NO entra")
(ok if not _entra("") else fallo)("sin fecha NO entra")
(ok if "do not have to chase it" in SRC_A else fallo)("el texto esta en la pantalla")

# ── 5 ────────────────────────────────────────────────────────────────────────
print("\n5. La tabla de credenciales, ordenada para un movil (v408)")
_orden = []
for fn in ast.walk(ast.parse(SRC_A)):
    if isinstance(fn, ast.FunctionDef) and fn.name == "render_credenciales":
        for d in ast.walk(fn):
            if (isinstance(d, ast.Dict) and d.keys
                    and all(isinstance(k, ast.Constant) for k in d.keys)
                    and "Tipo" in [k.value for k in d.keys]):
                _orden = [k.value for k in d.keys]
                break
(ok if _orden[:3] == ["Tipo", "Estado", "Vence"] else fallo)(
    "lo que se mira primero va primero", _orden)
(ok if len(_orden) == 6 else fallo)("y NO se oculto ninguna (priorizar != encoger)", _orden)
(ok if "pinned=True" in SRC_A else fallo)("la identidad va anclada")

# ── 6 ────────────────────────────────────────────────────────────────────────
print("\n6. Ninguna pantalla del campo tiene un ANCHO fijo mayor que un movil")
_malos = []
for _f in ("projects_ui.py", "timeclock_ui.py", "prestart_ui.py", "ausencias_ui.py",
           "payroll_ui.py", "auth_ui.py", "library_ui.py"):
    for c in ast.walk(ast.parse(io.open(os.path.join("core", _f), encoding="utf-8").read())):
        if not isinstance(c, ast.Call):
            continue
        for k in c.keywords:
            if (k.arg == "width" and isinstance(k.value, ast.Constant)
                    and isinstance(k.value.value, int) and k.value.value > 375):
                _malos.append("%s:%d width=%s" % (_f, c.lineno, k.value.value))
# ⚠️ La sonda, validada contra un caso construido antes de creerse su cero (trampa n12)
_probe = ast.parse("st_canvas(width=600)")
_ve = [c for c in ast.walk(_probe) if isinstance(c, ast.Call)
       for k in c.keywords if k.arg == "width" and k.value.value > 375]
(ok if _ve else fallo)("la sonda VE un ancho fijo de 600 (el fallo de v393)")
(ok if not _malos else fallo)("0 anchos fijos que se salgan de 375 px", _malos)

# ── 7 ────────────────────────────────────────────────────────────────────────
print("")
print("7. La barra superior cabe en UNA fila en el movil (medido: 112 -> 44 px)")
# ⚠️ MEDIDO en la app real con sesion de campo a 375x812, no leido: las 4 columnas
# se apilaban en TRES bandas y el titulo empezaba en y=196 — el 24% del telefono
# gastado en chrome antes de ver nada.
(ok if 'key="cpxtop"' in SRC_H else fallo)("la barra va en un contenedor con KEY")
# ⚠️ Anclado a la key y NO a `:first-of-type`, que depende del ORDEN del documento
# y se rompe en silencio si otra pantalla pinta una fila antes (v304/v332).
(ok if ".st-key-cpxtop" in SRC_H else fallo)("el CSS ancla a esa key")
(ok if ":first-of-type" not in SRC_H else fallo)("y NO al orden del documento")
(ok if "@media (max-width:640px)" in SRC_H else fallo)("acotado a pantallas estrechas")
# ⚠️ El suelo de 44 px NO es decoracion: sin el los botones quedaban en 26 px de
# ancho —bajo el minimo de 36 de v326/v327— y el movil es donde peor se pulsa.
(ok if "min-width:44px" in SRC_H else fallo)("con suelo de 44 px por boton (v326/v327)")

print("")
if fallos:
    print("HAY FALLOS: %d" % len(fallos))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
