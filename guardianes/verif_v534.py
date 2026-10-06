# -*- coding: utf-8 -*-
"""v534 · LO QUE DESTAPÓ TERMINAR DE CERRAR EN PRODUCCIÓN (Survey real, Rieles, Fichaje).

1. ⚠️ LO TECLEADO SE PERDÍA AL SALIR DE LA HERRAMIENTA. Survey con 23 parámetros y una matriz
   de 3 pisos a mano (30/09/2026): un clic en «Rails» y otro de vuelta en «Survey», y los 23
   estaban a 0,00, las paradas a 2 y la matriz cortada a 2 filas. Streamlit borra el valor de
   un widget en cuanto una pasada no lo pinta; `survey_ui` reasignaba sus claves, pero DENTRO
   de su pantalla — en las pasadas de otra sección no corría.
   → `core/estado_vivo.pasada()`, desde `app.py`, en CADA pasada. Para las 5 herramientas.
   ⚠️ Y releyendo el arreglo antes de desplegar: ese borrado protegía, sin querer, de otra
   cosa. `plan_ui.aplicar` solo rellena lo VACÍO, así que conservando sin más, quien calcula
   Rieles en la obra A, ficha en la B y vuelve, se quedaba con el LFKK de A bajo el nombre de
   B. Lo conservado es de UNA obra: al VOLVER con otra, se olvida (como antes).
   ⚠️ Y «reabrir un cálculo» tumbaba la pantalla: la foto de las entradas incluía el BOTÓN.
2. Dibujos con el texto CORTADO por el borde: el título de Belting con 1-2 ascensores, la
   leyenda de Rieles con 1. Medidos con la fuente real (Arial), que da el mismo corte que se
   vio en producción (el «)» final de la leyenda).
3. El cronómetro del fichaje salía cortado por la derecha en una columna estrecha.
4. El VALOR de las métricas se cortaba con «…» («+0.0…» por «+0.0 mm»).
5. Tres restos en español («1 fuera», «Matriz: 3 niveles», «Piso 1», «Elevador 1»).
6. La matriz del Survey, con SEIS decimales («76.000000»).

Lo que protege, EJECUTANDO:
  (a) ⚠️ el caso de producción, con clics: teclear, irse a otra página dos pasadas y volver.
      Con `mantener()` el valor sigue; SIN él se pierde (la sonda ve el fallo);
  (b) un botón y una tabla editable con la clave «de la familia» no se tocan (si se
      reasignaran, Streamlit lanzaría una excepción al crearlos);
  (c) app.py llama a `pasada()` en el cuerpo del script, tras el login y antes de la shell;
  (c2) ⚠️ la pantalla REAL de Rieles con dos obras: misma obra → se conserva; al volver con
      otra → manda el plano de la nueva (y SIN el olvido se queda el de la vieja: la sonda
      ve el peligro); cambiar de obra sin salir no borra nada; lo cargado a propósito se
      respeta; reabrir un cálculo guardado CON el botón dentro ya no revienta;
  (d) ⚠️ TODA entrada de las 5 herramientas está en la lista, y NINGÚN botón/tabla/subida;
  (e) 91 dibujos sin textos fuera del viewBox ni pisados (la sonda ve los dos casos malos);
  (f) la pantalla REAL de Rieles: rótulos en inglés, claves intactas, y calcula;
  (g) el cronómetro, las métricas, los restos de idioma y los decimales.
"""
import ast
import datetime
import html
import io
import json
import os
import re
import sys
import tokenize

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
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


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


def _cadenas(f):
    """Las cadenas del fuente, SIN comentarios (trampa nº2: grep ≠ uso)."""
    # ⚠️ Por NOMBRE, no por número: los tipos de token cambian entre versiones de Python
    # (con `>= 60` entraban los comentarios, que en 3.14 son el 65, y daba un rojo falso).
    tipos = {tokenize.STRING} | {getattr(tokenize, n) for n in ("FSTRING_MIDDLE",)
                                 if hasattr(tokenize, n)}
    out = []
    with io.open(os.path.join(RAIZ, f), "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in tipos:
                out.append(tok.string)
    return out


from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import estado_vivo as EV                                # noqa: E402

# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Lo tecleado en una herramienta sobrevive a salir de ella")

GUION = r'''
import sys
sys.path.insert(0, r"%s")
import pandas as pd
import streamlit as st
from core import estado_vivo
if st.session_state.get("vivo"):
    estado_vivo.pasada()
pg = st.session_state.get("pg", "survey")
if pg == "survey":
    st.number_input("BS", key="inp_BS")
    st.number_input("NS", min_value=2, max_value=50, step=1, key="ns")
    st.radio("Omega", ["R", "L"], key="cfg_omega_side")
elif pg == "rieles":
    st.number_input("LFKK", value=float(st.session_state.get("rc_lfkk", 0.0)), key="rc_lfkk")
    st.number_input("n", min_value=1, step=1, value=int(st.session_state.get("rc_n", 1)),
                    key="rc_n")
    st.number_input("HGPR 1", key="belt_hgpr_0")
    st.data_editor(pd.DataFrame({"a": [1.0]}), key="rc_L_editor")
    if st.button("calc", key="rc_calc1"):
        st.session_state["pulsado"] = True
st.markdown("E=%%r" %% ({k: st.session_state.get(k) for k in
                       ("inp_BS", "ns", "cfg_omega_side", "rc_lfkk", "rc_n", "belt_hgpr_0")},))
''' % RAIZ


def _vuelta(vivo):
    """Teclea en dos herramientas, se va a una página vacía dos pasadas y vuelve."""
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["vivo"] = vivo
    at.run()
    at.number_input(key="inp_BS").set_value(1326.0)
    at.number_input(key="ns").set_value(3)
    at.radio(key="cfg_omega_side").set_value("L")
    at.run()
    at.session_state["pg"] = "rieles"
    at.run()
    at.number_input(key="rc_lfkk").set_value(1200.0)
    at.number_input(key="rc_n").set_value(4)
    at.number_input(key="belt_hgpr_0").set_value(120.5)
    at.run()
    at.button(key="rc_calc1").click().run()
    _exc_boton = [e.value for e in at.exception]
    _pulsado = at.session_state["pulsado"] if "pulsado" in at.session_state else False
    at.session_state["pg"] = "otra"
    at.run()
    at.run()
    at.session_state["pg"] = "survey"
    at.run()
    _s = (at.number_input(key="inp_BS").value, at.number_input(key="ns").value,
          at.radio(key="cfg_omega_side").value)
    at.session_state["pg"] = "rieles"
    at.run()
    _r = (at.number_input(key="rc_lfkk").value, at.number_input(key="rc_n").value,
          at.number_input(key="belt_hgpr_0").value)
    return _s, _r, _exc_boton + [e.value for e in at.exception], _pulsado


_s, _r, _exc, _puls = _vuelta(True)
chk("⚠️ el caso de producción: tras salir y volver, el Survey conserva parámetro, paradas y "
    "configuración", _s == (1326.0, 3, "L"), _s)
chk("...y las otras herramientas también (Rieles con `value=`, el HGPR numerado de Belting)",
    _r == (1200.0, 4, 120.5), _r)
chk("⚠️ el botón y la tabla editable con la clave «de la familia» NO se tocan: ninguna "
    "excepción, y el botón sigue funcionando", not _exc and _puls is True, (_exc, _puls))
_s0, _r0, _exc0, _ = _vuelta(False)
chk("la sonda VE el fallo: SIN `pasada()` todo vuelve a su valor por defecto (trampa nº12)",
    _s0 == (0.0, 2, "R") and _r0 == (0.0, 1, 0.0), (_s0, _r0))

# ── app.py lo llama en cada pasada, tras el login y antes de la shell ──
_tapp = ast.parse(_fuente("app.py"))
_pos = {}
for _i, _n in enumerate(_tapp.body):
    _src = ast.unparse(_n)
    if isinstance(_n, ast.If) and "render_login()" in ast.unparse(_n.test):
        _pos["login"] = _i
    if isinstance(_n, ast.Expr) and _src.endswith("_estado_vivo.pasada()"):
        _pos.setdefault("mantener", _i)
    if isinstance(_n, ast.Expr) and "render_topbar(" in _src:
        _pos["shell"] = _i
chk("⚠️ app.py llama a `pasada()` en el CUERPO del script (no dentro de un `if`): corre en "
    "todas las pasadas, sea cual sea la sección", "mantener" in _pos, _pos)
chk("...después del login (en la pantalla de entrada no se conserva nada) y antes de la shell",
    "mantener" in _pos and _pos.get("login", 9e9) < _pos["mantener"] < _pos.get("shell", -1),
    _pos)
_tsv = ast.parse(_fuente("core/survey_ui.py"))
_rst = next(n for n in ast.walk(_tsv) if isinstance(n, ast.FunctionDef)
            and n.name == "render_survey_tab")
_bucles = [n for n in _rst.body[:6] if isinstance(n, ast.For)
           and "session_state[_k] = st.session_state[_k]" in ast.unparse(n)]
chk("`survey_ui` usa la MISMA lista (ya no tiene su copia del bucle)",
    not _bucles and "estado_vivo.mantener()" in ast.unparse(_rst.body[0]), len(_bucles))

# ── La lista: todas las entradas, ningún botón ──
_ENTRADA = {"number_input", "radio", "text_input", "text_area", "slider", "checkbox"}
_PROHIBIDO = {"button", "data_editor", "download_button", "file_uploader",
              "form_submit_button"}
_MODS = ("core/plumb_ui.py", "core/rail_cut_ui.py", "core/buffer_cut_ui.py",
         "core/belting_ui.py")


def _claves(f):
    """(método, clave o prefijo constante, es_prefijo) de cada widget con `key=`."""
    out = []
    for n in ast.walk(ast.parse(_fuente(f))):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        for kw in n.keywords:
            if kw.arg != "key":
                continue
            v = kw.value
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                out.append((n.func.attr, v.value, False))
            elif isinstance(v, ast.JoinedStr) and v.values \
                    and isinstance(v.values[0], ast.Constant):
                out.append((n.func.attr, str(v.values[0].value), True))
    return out


_sin, _de_mas, _vistas = [], [], 0
for _f in _MODS:
    for _met, _k, _pref in _claves(_f):
        _dentro = (_k.startswith(EV.PREFIJOS) if _pref else EV.es_entrada(_k))
        if _met in _ENTRADA:
            _vistas += 1
            if not _dentro:
                _sin.append((_f, _met, _k))
        elif _met in _PROHIBIDO and (_dentro or EV.es_entrada(_k)):
            _de_mas.append((_f, _met, _k))
chk("se leyeron las entradas de las cuatro herramientas (no es un paso en vacío)",
    _vistas >= 20, _vistas)
chk("⚠️ TODA entrada de Plomada, Rieles, Buffers y Belting está en la lista (una nueva sin "
    "apuntar se pierde al salir)", not _sin, _sin)
chk("⚠️ NINGÚN botón, tabla editable ni subida está en la lista (reasignarlos lanza una "
    "excepción)", not _de_mas, _de_mas)
_ksv = _claves("core/survey_ui.py")
_sv_in = [(m, k) for m, k, p in _ksv if m in _ENTRADA
          and (k in ("inp_", "ns") or k.startswith("cfg_"))]
chk("el Survey: parámetros, paradas y configuración están en la lista — y son SUYOS (se "
    "olvidan con su obra)",
    len(_sv_in) >= 8 and all(EV.de_herramienta("sv", k + ("X" if k == "inp_" else ""))
                             for _m, k in _sv_in),
    [x for x in _sv_in if not EV.de_herramienta("sv", x[1] + ("X" if x[1] == "inp_" else ""))])
chk("⚠️ la FASE del Survey no se conserva: al volver se abre en «Survey data», que es donde "
    "se mira con qué obra se vuelve", not EV.es_entrada("survey_fase"))
_de_nadie = [k for k in EV.CLAVES if not any(EV.de_herramienta(h, k) for h in EV.HERRAMIENTAS)]
chk("toda clave conservada es de una herramienta (salvo la identidad del informe)",
    sorted(_de_nadie) == ["cliente", "ingeniero", "proyecto", "ubicacion"], _de_nadie)
chk("la obra elegida en cada herramienta se conserva, y no es una entrada que se olvide",
    EV.es_entrada("pl_prj_rc") and not EV.de_herramienta("rc", "pl_prj_rc"))
_sv_mal = [(m, k) for m, k, p in _ksv if m in _PROHIBIDO and EV.es_entrada(k)]
chk("...y ninguno de sus botones o tablas", not _sv_mal, _sv_mal)
chk("⚠️ la solución activa y los pisos siguen con clave POR CÁLCULO y fuera de la lista (v530)",
    not EV.es_entrada("sol_activa_3") and not EV.es_entrada("diag_pisos_3")
    and any(k == "sol_activa_" and p for _m, k, p in _ksv))
chk("una clave cualquiera de la app no se toca", not EV.es_entrada("auth")
    and not EV.es_entrada("_admin_sec") and not EV.es_entrada("rc_calc1")
    and not EV.es_entrada("rc_L_editor"))

# ═════════════════════════════════════════════════════════════════
sec("1b. ⚠️ Lo conservado es de UNA obra (la pantalla REAL de Rieles, con dos obras)")
GUION_O = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import estado_vivo, plan_ui, plan_store, plan_data, tool_save_ui, rail_cut_ui as R
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
PLANOS = {"PRJ-A": {"lfkk": 1111.0, "lfgk": 911.0}, "PRJ-B": {"lfkk": 2222.0, "lfgk": 922.0}}
plan_ui.P.is_configured = lambda: True
_o = st.session_state.get("obra", "")
plan_ui._proyecto_fichado = lambda a: ({"ID": _o, "Name": _o} if _o else None)
plan_data.del_proyecto = lambda pid: dict(PLANOS.get(pid, {}))
plan_data.resumen = lambda d: "plano"
plan_store.selector = lambda *a, **k: None
R.render_guardar = lambda **k: st.markdown("SNAP=%%r" %% (sorted(tool_save_ui._snapshot("rieles")),))
R.tool_pdf = lambda *a, **k: b""
# ⚠️ Los guiones de AppTest corren en ESTE proceso y comparten los módulos: lo que uno
# sustituye se queda puesto para el siguiente. La batería lo cazó — el guion «sin olvido»
# dejaba `al_pintar` anulado y el de reabrir pasaba en vacío. Se repone SIEMPRE.
if not hasattr(estado_vivo, "_al_pintar_real"):
    estado_vivo._al_pintar_real = estado_vivo.al_pintar
estado_vivo.al_pintar = ((lambda h, o: False) if st.session_state.get("sin_olvido")
                         else estado_vivo._al_pintar_real)
if st.session_state.pop("reabrir", None):
    st.session_state[tool_save_ui._PENDIENTE] = {
        "herramienta": "rieles", "id": "CAL-7",
        "valores": {"rc_lfkk": 1200.0, "rc_n2500": 5, "rc_calc1": False, "rc_pdf_name": None,
                    "rc_L_df": {"__df__": [{"Elevador": "Lift 1", "L (mm)": 21000.0}]}}}
estado_vivo.pasada()
if st.session_state.get("pg", "rieles") == "rieles":
    R.render_rail_cut_tab()
st.markdown("V=%%r" %% ((st.session_state.get("rc_lfkk"), st.session_state.get("rc_n2500")),))
''' % RAIZ


def _v(at):
    return next(m.value for m in at.markdown if m.value.startswith("V="))


def _fuera_y_vuelve(at, obra=None):
    at.session_state["pg"] = "otra"
    at.run()
    at.run()
    if obra is not None:
        at.session_state["obra"] = obra
    at.session_state["pg"] = "rieles"
    at.run()
    return _v(at)


at = AppTest.from_string(GUION_O, default_timeout=90)
at.session_state["obra"] = "PRJ-A"
at.run()
chk("la pantalla de Rieles se pinta con la obra A y toma el LFKK de SU plano",
    not at.exception and _v(at) == "V=(1111.0, 0)", (_v(at), [e.value for e in at.exception][:1]))
at.number_input(key="rc_n2500").set_value(3).run()
chk("⚠️ misma obra: tras salir y volver, lo tecleado y lo del plano siguen",
    _fuera_y_vuelve(at) == "V=(1111.0, 3)", _v(at))
chk("⚠️ al volver con OTRA obra manda el plano de la nueva (2222, no el 1111 de la vieja) y "
    "lo tecleado para la vieja se olvida", _fuera_y_vuelve(at, "PRJ-B") == "V=(2222.0, 0)", _v(at))
at.number_input(key="rc_n2500").set_value(4).run()
at.session_state["obra"] = "PRJ-A"
at.run()
# ⚠️ v535 · Actualizada con su razón (v385): v534 afirmaba que cambiar de obra SIN salir
# no borraba nada — y así Rieles seguía con el LFKK de la obra anterior bajo el nombre de la
# nueva (el campo cambia de obra con el fichaje del menú lateral sin dejar la herramienta).
# Desde v535 manda el plano de la obra nueva y lo tecleado para la vieja se olvida; solo el
# Survey conserva lo medido a mano («Duplicate for the next lift»), lo comprueba verif_v535.
chk("cambiar de obra SIN salir de la herramienta: manda el plano de la nueva (1111, no el "
    "2222 de la anterior) y lo tecleado para la anterior se olvida (v535)",
    _v(at) == "V=(1111.0, 0)", _v(at))
at.number_input(key="rc_n2500").set_value(6).run()
chk("...y lo que se teclea después se conserva al salir y volver con esa misma obra",
    _fuera_y_vuelve(at) == "V=(1111.0, 6)", _v(at))

at = AppTest.from_string(GUION_O, default_timeout=90)
at.session_state["obra"] = "PRJ-A"
at.session_state["sin_olvido"] = True
at.run()
chk("la sonda VE el peligro: conservando SIN mirar la obra, al volver con la B se queda el "
    "LFKK de la A (trampa nº12)", _fuera_y_vuelve(at, "PRJ-B") == "V=(1111.0, 0)", _v(at))

# ── Reabrir un cálculo guardado: se respeta, y el botón guardado ya no revienta ──
at = AppTest.from_string(GUION_O, default_timeout=90)
at.session_state["obra"] = "PRJ-A"
at.run()
at.session_state["pg"] = "otra"
at.run()
at.run()
at.session_state["obra"] = "PRJ-B"
at.session_state["reabrir"] = True
at.session_state["pg"] = "rieles"
at.run()
chk("⚠️ reabrir un cálculo guardado que trae el BOTÓN dentro ya no tumba la pantalla",
    not at.exception, [str(e.value)[:90] for e in at.exception][:1])
chk("⚠️ ...y lo reabierto se respeta aunque la herramienta vuelva con otra obra",
    _v(at) == "V=(1200.0, 5)", _v(at))
# El control de ese «se respeta»: sin nada que reabrir, en la MISMA situación se olvida.
at = AppTest.from_string(GUION_O, default_timeout=90)
at.session_state["obra"] = "PRJ-A"
at.run()
at.number_input(key="rc_n2500").set_value(5).run()
chk("...(control) sin reabrir nada, en esa misma situación SÍ se olvida: el respeto es de lo "
    "reabierto, no de que el olvido esté apagado", _fuera_y_vuelve(at, "PRJ-B") == "V=(2222.0, 0)",
    _v(at))
at.session_state["obra"] = "PRJ-A"
at.session_state["pg"] = "otra"
at.run()
at.run()
at.session_state["reabrir"] = True
at.session_state["pg"] = "rieles"
at.run()
at.button(key="rc_calc1").click().run()
_snap = next((m.value for m in at.markdown if m.value.startswith("SNAP=")), "")
chk("la foto de las entradas que se guarda con un cálculo ya no incluye el botón ni el "
    "nombre del PDF, y sí las entradas y la tabla",
    "rc_calc1" not in _snap and "rc_pdf_name" not in _snap and "'rc_lfkk'" in _snap
    and "'rc_L_df'" in _snap, _snap)

# ── Las cinco herramientas preguntan la obra ANTES de crear sus entradas ──
_tarde = {}
for _f, _h in (("core/survey_ui.py", "sv"), ("core/plumb_ui.py", "plb"),
               ("core/rail_cut_ui.py", "rc"), ("core/buffer_cut_ui.py", "bc"),
               ("core/belting_ui.py", "belt")):
    _t = ast.parse(_fuente(_f))
    _sel = [n.lineno for n in ast.walk(_t) if isinstance(n, ast.Call)
            and ast.unparse(n.func) == "plan_ui.selector_proyecto"
            and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == _h]
    _wid = [n.lineno for n in ast.walk(_t) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr in _ENTRADA
            and any(kw.arg == "key" and (
                (isinstance(kw.value, ast.Constant) and EV.de_herramienta(_h, kw.value.value))
                or (isinstance(kw.value, ast.JoinedStr) and kw.value.values
                    and isinstance(kw.value.values[0], ast.Constant)
                    and EV.de_herramienta(_h, str(kw.value.values[0].value) + "X")))
                    for kw in n.keywords)]
    if len(_sel) != 1 or not _wid or _sel[0] > min(_wid):
        _tarde[_f] = (_sel, sorted(_wid)[:2])
chk("⚠️ las cinco herramientas preguntan su obra ANTES de crear su primera entrada (después "
    "ya no se puede olvidar nada: Streamlit no deja tocar un widget creado)", not _tarde, _tarde)
_tpl = ast.parse(_fuente("core/plan_ui.py"))
_fsel = next(n for n in _tpl.body if isinstance(n, ast.FunctionDef)
             and n.name == "selector_proyecto")
chk("`selector_proyecto` avisa de la obra en TODOS sus caminos (un solo `return`, tras "
    "`al_pintar`)", sum(isinstance(n, ast.Return) for n in ast.walk(_fsel)) == 1
    and "estado_vivo.al_pintar(key" in ast.unparse(_fsel))
chk("«Rebuild the project in the Survey» marca lo que carga para que se respete",
    "_ev.respetar('sv')" in ast.unparse(ast.parse(_fuente("core/projects_ui.py"))))

# ═════════════════════════════════════════════════════════════════
sec("2. Los dibujos: ningún texto fuera del borde ni pisando a otro (fuente real)")
_ARIAL = {False: r"C:\Windows\Fonts\arial.ttf", True: r"C:\Windows\Fonts\arialbd.ttf"}
_F = {}
try:
    from PIL import ImageFont
    for _b, _p in _ARIAL.items():
        _F[_b] = ImageFont.truetype(_p, 100)
except Exception as e:                                            # sin fuente no se mide
    _F = {}
    fallo("hay con qué medir: Arial y PIL (sin ellos esta sección no probaría nada)", e)

_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)


def _textos(svg):
    out = []
    for attrs, cuerpo in _RE.findall(svg):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
        if "transform" in a:
            continue
        try:
            x, y, fs = float(a.get("x", 0)), float(a.get("y", 0)), float(a.get("font-size", 10))
        except ValueError:
            continue
        tx = html.unescape(re.sub(r"<[^>]+>", "", cuerpo)).strip()
        if not tx:
            continue
        w = _F[a.get("font-weight") == "bold"].getlength(tx) * fs / 100.0
        anc = a.get("text-anchor", "start")
        x0 = x - w if anc == "end" else (x - w / 2 if anc == "middle" else x)
        out.append((x0, x0 + w, y, fs, tx))
    return out


def fuera(svg, margen=1.0):
    """Textos que se salen del viewBox por la izquierda o la derecha."""
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not m:
        return [("SIN VIEWBOX",)]
    vw = float(m.group(1))
    return [(tx[:36], round(a), round(b), int(vw)) for a, b, y, fs, tx in _textos(svg)
            if a < -margen or b > vw + margen]


def pisados(svg, margen=1.0):
    ts = _textos(svg)
    out = []
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            a, b = ts[i], ts[j]
            if abs(a[2] - b[2]) < min(a[3], b[3]) * 0.7 \
                    and min(a[1], b[1]) - max(a[0], b[0]) > margen:
                out.append((round(a[2]), a[4][:26], b[4][:26]))
    return out


if _F:
    from core import belting, buffer_cut, diagrams, plumb, rail_cut, schedule, survey_calc
    import fixture_survey as FS

    # La sonda, contra lo que se VIO en producción: la leyenda de Rieles en una línea perdía
    # el «)» final en un dibujo de 470 de ancho.
    _vieja = ('<svg viewBox="0 0 470 366"><text x="164" y="348" font-size="8">adds to the 1st '
              'rail · the cut goes on the BOTTOM rail (same signed value as the table)</text>'
              '</svg>')
    chk("⚠️ la sonda VE el corte visto en producción (la leyenda vieja de Rieles se sale por "
        "3 px: el «)» que faltaba)", len(fuera(_vieja)) == 1 and fuera(_vieja)[0][2] in (472, 473, 474),
        fuera(_vieja))
    chk("...y no acusa a un texto que cabe",
        fuera('<svg viewBox="0 0 470 366"><text x="18" y="20" font-size="8">cabe</text></svg>') == [])
    chk("la sonda VE dos textos pisados, y no dos separados",
        len(pisados('<svg viewBox="0 0 470 9"><text x="10" y="5" font-size="8">una frase bastante '
                    'larga</text><text x="60" y="5" font-size="8">otra encima</text></svg>')) == 1
        and pisados('<svg viewBox="0 0 470 9"><text x="10" y="5" font-size="8">a</text>'
                    '<text x="200" y="5" font-size="8">b</text></svg>') == [])

    _OBRAS = ("", "ZZ PRUEBA v519 — Tower B lift 2",
              "Westfield Parramatta Stage 2 — Tower B, passenger lift 3")
    _H = [100, 130, 120, 95, 110, 105]
    casos = {}
    for n in range(1, 7):
        for _io, _pr in enumerate(_OBRAS):
            _s = " obra%d" % _io
            casos["buffers n=%d%s" % (n, _s)] = buffer_cut.buffer_cut_svg(
                buffer_cut.compute_buffer_cut(120, _H[:n]), proyecto=_pr)
            casos["belting n=%d%s" % (n, _s)] = belting.belting_svg(
                belting.compute_belting(85, 14045, _H[:n]), proyecto=_pr)
            casos["rieles caso 1 n=%d%s" % (n, _s)] = rail_cut.rail_cut_svg(
                rail_cut.compute_case1(1200, 900, 2, 3, [21000 + 100 * k for k in range(n)]),
                caso=1, n2500=2, n5000=3, proyecto=_pr)
            casos["rieles caso 2 n=%d%s" % (n, _s)] = rail_cut.rail_cut_svg(
                {"elevadores": rail_cut.compute_case2(
                    1200, 900, [{"RZ": 300, "RO": 320, "RF": 250, "RB": 260}] * n, "encima")},
                caso=2, proyecto=_pr)
    _rc = survey_calc.recalcular(FS.PARAMS, FS.MATRIZ)
    chk("el survey de prueba se calcula (si no, los dibujos del Survey no se medirían)",
        bool(_rc) and bool(_rc.get("best")) and bool(_rc.get("plumb")))
    if _rc and _rc.get("best"):
        _ap, _lim, _best, _lm, _pl = (_rc["all_params"], _rc["limits"], _rc["best"],
                                      _rc["lim_map"], _rc["plumb"])
        for _io, _pr in enumerate(_OBRAS):
            _s = " obra%d" % _io
            casos["plomada planta" + _s] = plumb.plumb_svg(_pl, proyecto=_pr)
            casos["plomada iso" + _s] = plumb.plumb_iso_svg(_pl, proyecto=_pr)
            casos["plomada detalle" + _s] = plumb.plumb_detail_svg(_pl, proyecto=_pr)
            casos["plomada ficha" + _s] = plumb.plumb_card_svg(_pl, proyecto=_pr)
            casos["iso del hueco" + _s] = diagrams.shaft_iso_svg(
                _ap, _lim, _best, len(_best["matrix"]), _lm, proyecto=_pr)
        for _i, _row in enumerate(_best["matrix"]):
            casos["planta piso %d" % _i] = diagrams.floor_plan_svg(
                _ap, _lim, _row, _i, _lm, False, "R", _i == len(_best["matrix"]) - 1)
        casos["cronograma"] = schedule.schedule_svg(
            schedule.build_schedule(3, datetime.date(2026, 9, 30)))
    _vacios = [k for k, s in casos.items() if len(_textos(s)) < 3]
    chk("se midieron %d dibujos y todos traen texto (no es un paso en vacío)" % len(casos),
        len(casos) >= 90 and not _vacios, (len(casos), _vacios[:4]))
    _fu = {k: fuera(s) for k, s in casos.items() if fuera(s)}
    chk("⚠️ ningún texto se sale del dibujo (Buffers, Belting y Rieles de 1 a 6; plomada, "
        "plantas, isométricas y cronograma; sin obra, con nombre corto y con nombre largo)",
        not _fu, dict(list(_fu.items())[:3]))
    _pi = {k: pisados(s) for k, s in casos.items() if pisados(s)}
    chk("⚠️ ...y ninguno pisa a otro (el nombre de la obra incluido)", not _pi,
        dict(list(_pi.items())[:3]))
    _b1 = belting.belting_svg(belting.compute_belting(85, 14045, [100]))
    _vw = float(re.search(r'viewBox="0 0 ([\d.]+)', _b1).group(1))
    _marco = re.search(r'<rect x="([\d.]+)" y="58" width="([\d.]+)"', _b1)
    chk("Belting con 1 ascensor: el dibujo es tan ancho como su título (470, no 198)",
        _vw >= 470, _vw)
    chk("...y la columna queda centrada, no pegada a la izquierda",
        bool(_marco) and abs((float(_marco.group(1)) + 75) - _vw / 2) < 1.0,
        _marco.groups() if _marco else None)
    _b6 = belting.belting_svg(belting.compute_belting(85, 14045, _H))
    chk("con 6 ascensores el dibujo no cambia de tamaño (948)",
        'viewBox="0 0 948 300"' in _b6, _b6[:60])

# ═════════════════════════════════════════════════════════════════
sec("3. La pantalla REAL de Rieles: rótulos en inglés, claves intactas, y calcula")
GUION_R = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import plan_ui, plan_store, tool_save_ui, rail_cut_ui as R
plan_ui.selector_proyecto = lambda *a, **k: (None, {})
plan_store.selector = lambda *a, **k: None
tool_save_ui.aplicar_restauracion = lambda h: ""
R.render_guardar = lambda **k: None
R.tool_pdf = lambda *a, **k: b""
if "rc_n" not in st.session_state:
    st.session_state["rc_n"] = 2
R.render_rail_cut_tab()
st.markdown("RES=%%r" %% (bool(st.session_state.get("rc_res")),))
''' % RAIZ
at = AppTest.from_string(GUION_R, default_timeout=90)
at.run()
chk("la pantalla de Rieles se pinta sin excepción", not at.exception,
    [e.value for e in at.exception][:1])
_ed = list(at.dataframe)
_v1 = list(_ed[0].value["Elevador"]) if _ed and "Elevador" in _ed[0].value.columns else None
chk("⚠️ Caso 1: las filas dicen «Lift 1», «Lift 2» (antes «Elevador 1») — y la columna sigue "
    "llamándose igual", _v1 == ["Lift 1", "Lift 2"], _v1)
_C2 = "Case 2 — last installed (the top one)"
at.radio(key="rc_caso").set_value(_C2).run()
_ed = list(at.dataframe)
_cols = list(_ed[0].value.columns) if _ed else []
chk("⚠️ Caso 2: las CLAVES de la tabla no cambian (se leen de vuelta al calcular)",
    _cols == ["Riel", "Elevador 1", "Elevador 2"], _cols)
_cfg = json.loads(_ed[0].proto.columns or "{}") if _ed else {}
chk("...y su cabecera se pinta en inglés: «Lift 1», «Lift 2»",
    (_cfg.get("Elevador 1") or {}).get("label") == "Lift 1"
    and (_cfg.get("Elevador 2") or {}).get("label") == "Lift 2", _cfg)
at.button(key="rc_calc2").click().run()
chk("con la etiqueta cambiada, «Calculate cuts (Case 2)» sigue leyendo sus columnas y calcula",
    not at.exception and "RES=True" in [m.value for m in at.markdown],
    ([e.value for e in at.exception][:1], [m.value for m in at.markdown][-1:]))

# ═════════════════════════════════════════════════════════════════
sec("4. El cronómetro, las métricas, los restos de idioma y los decimales")
import streamlit as st                                            # noqa: E402

from core import theme, timeclock                                 # noqa: E402
from core import timeclock_ui as TU                               # noqa: E402

_cap = []
_oi, _oe = st.iframe, timeclock.elapsed_seconds
st.iframe = lambda h, height=None, **k: _cap.append((h, height))
timeclock.elapsed_seconds = lambda s: 3725
try:
    TU._chronometer("2026-09-30 10:00:00", "On this project", "#1e8449", "chrono_prj")
    TU._chrono_mini("2026-09-30 10:00:00", "Workday", "#1a3a5c", "sb")
finally:
    st.iframe, timeclock.elapsed_seconds = _oi, _oe
_h, _alto = _cap[0] if _cap else ("", None)
chk("el cronómetro grande se pinta (se capturó su HTML)", len(_cap) == 2 and "chrono_prj" in _h)
chk("⚠️ si no caben en una línea, el reloj BAJA en vez de cortarse (`flex-wrap`), y ni el "
    "rótulo ni el reloj se parten", "flex-wrap:wrap" in _h and _h.count("white-space:nowrap") == 2,
    _h[:200])
chk("...sin los márgenes del documento, para que las dos líneas quepan en los mismos 52 px",
    _h.startswith('<body style="margin:0">') and _alto == 52, (_h[:40], _alto))
chk("...el recorte sin barra de v532 sigue dentro del <body>, y el reloj sigue contando",
    _h.startswith('<body style="margin:0"><style>html,body{overflow:hidden}</style>')
    and "setInterval" in _h and "var e=3725;" in _h, _h[:90])
chk("el cronómetro del menú lateral no cambia (44 px)", _cap[1][1] == 44 and "sb" in _cap[1][0])

_css = theme._CSS
_m = re.search(r'\[data-testid="stMetricValue"\] \[data-testid="stMarkdownContainer"\],\s*'
               r'\[data-testid="stMetricValue"\] \[data-testid="stMarkdownContainer"\] p \{(.*?)\}',
               _css, re.S)
_regla = _m.group(1) if _m else ""
chk("⚠️ el VALOR de una métrica parte en dos líneas en vez de cortarse con «…» (el recorte lo "
    "pone el contenedor de markdown de DENTRO: medido en producción)",
    bool(_m) and "white-space: normal !important" in _regla
    and "overflow: visible !important" in _regla and "text-overflow: clip !important" in _regla,
    _regla)
chk("...y la regla de la ETIQUETA (v335) sigue en su sitio",
    '[data-testid="stMetricLabel"] p {' in _css and _css.count("white-space: normal !important") >= 2)

# ── Restos en español ──
_ssv = " ".join(_cadenas("core/survey_ui.py"))
chk("⚠️ el desplegable de soluciones dice «N out of limit» (antes «N fuera»)",
    '"{n} out of limit"' in _ssv and " fuera" not in _ssv, "")
chk("⚠️ el resumen de entradas dice «Matrix: N levels» (antes «Matriz: N niveles»)",
    "Matrix: {n} levels" in _ssv and "niveles" not in _ssv and "Matriz:" not in _ssv, "")
chk("⚠️ el selector de pisos dice «Floor N» (antes «Piso N»)",
    '"Floor {n}"' in _ssv and "Piso " not in _ssv, "")
_spl = " ".join(_cadenas("core/plumb_ui.py"))
chk("Plomada: las filas de la tabla de BSR dicen «Lift N»",
    '"Lift {n}"' in _spl and "Elevador {" not in _spl, "")
from core import i18n                                             # noqa: E402
chk("las frases nuevas salen bien formadas de `t()`",
    i18n.t("{n} out of limit", n=1) == "1 out of limit"
    and i18n.t("Floor {n}", n=2) == "Floor 2" and i18n.t("Lift {n}", n=3) == "Lift 3"
    and i18n.t(":green[:material/check_circle:] Matrix: {n} levels", n=3).endswith("Matrix: 3 levels"))

# ── Seis decimales ──
_mal = []
_n_st = 0
for _n in ast.walk(_tsv):
    if isinstance(_n, ast.Call) and ast.unparse(_n.func) == "st.dataframe" and _n.args:
        _a0 = ast.unparse(_n.args[0])
        if ".style." in _a0:
            _n_st += 1
            if not _a0.endswith(".format(precision=1)"):
                _mal.append(_a0[:60])
chk("las tres tablas coloreadas del Survey se encontraron", _n_st == 3, _n_st)
chk("⚠️ las tres fijan UN decimal (sin `format`, un Styler manda «76.000000»)", not _mal, _mal)
import pyarrow as pa                                              # noqa: E402

GUION_S = '''
import pandas as pd
import streamlit as st
df = pd.DataFrame({"WR": [76.0, 82.5], "n": [1, 2], "Status": ["a", "b"]})
f = lambda d: pd.DataFrame("", index=d.index, columns=d.columns)
st.dataframe(df.style.apply(f, axis=None))
st.dataframe(df.style.apply(f, axis=None).format(precision=1))
'''
at = AppTest.from_string(GUION_S, default_timeout=60)
at.run()


def _pintado(el):
    dv = el.proto.arrow_data.styler.display_values
    return pa.ipc.open_stream(io.BytesIO(dv)).read_all().to_pandas().to_dict("list") if dv else {}


_dfs = list(at.dataframe)
_sin_f = _pintado(_dfs[0]) if len(_dfs) == 2 else {}
_con_f = _pintado(_dfs[1]) if len(_dfs) == 2 else {}
chk("la sonda VE el fallo: sin `format`, lo que viaja al navegador es «76.000000»",
    _sin_f.get("WR") == ["76.000000", "82.500000"], _sin_f)
chk("⚠️ con `format(precision=1)` viaja «76.0» y «82.5»; los enteros y el texto, intactos",
    _con_f.get("WR") == ["76.0", "82.5"] and _con_f.get("n") == ["1", "2"]
    and _con_f.get("Status") == ["a", "b"], _con_f)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
