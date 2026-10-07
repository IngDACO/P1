# -*- coding: utf-8 -*-
"""v542 · EL SURVEY SE LIMPIA DE VERDAD (A) — y no mezcla obras (B).

A. ⚠️ Todo lo que REEMPLAZA la matriz del Survey sin cambiar el nº de paradas («Duplicate
survey», «Clear everything and start over», «Load matrix (.xlsx)» y «Rebuild the project in
the Survey») dejaba encima las celdas tecleadas: el `data_editor` con clave y filas fijas se
identifica por la clave y la FORMA de los datos «para que las ediciones sobrevivan a cambios
de valores» (código de Streamlit 1.64), así que re-aplicaba lo tecleado sobre la matriz nueva.
Y «Clear everything» BORRABA los parámetros y la configuración con los campos en pantalla: el
servidor quedaba a cero pero el navegador no se enteraba (trampa nº31) y los devolvía.
→ La matriz lleva una clave con generación (`estado_vivo.tabla_nueva`) y «empezar de cero»
ASIGNA los valores de partida.

Lo que protege, EJECUTANDO la pantalla real del Survey y mirando lo que recibe el navegador
(`proto.set_value` de cada campo, `proto.id` de la matriz), con sondas validadas.
"""
import ast
import io
import json
import os
import sys

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


from streamlit.testing.v1 import AppTest                          # noqa: E402

GUION = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
import pandas as pd
from core import estado_vivo, plan_ui, survey_ui as S
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
plan_ui.P.is_configured = lambda: True
plan_ui._proyecto_fichado = lambda a: None
# ⚠️ Los guiones comparten proceso: lo que se sustituye se repone SIEMPRE (v534).
if not hasattr(estado_vivo, "_tabla_nueva_real"):
    estado_vivo._tabla_nueva_real = estado_vivo.tabla_nueva
estado_vivo.tabla_nueva = ((lambda h: None) if st.session_state.get("sin_tabla_nueva")
                           else estado_vivo._tabla_nueva_real)
S.init_state()
estado_vivo.pasada()
_m = st.session_state.pop("sembrar_matriz", None)
if _m:                     # lo que deja una matriz tecleada (su contenido vive en survey_df)
    st.session_state["survey_df"] = pd.DataFrame(_m)
if st.session_state.pop("reset_viejo", False):     # el «empezar de cero» de v541: BORRA
    for _k in [k for k in list(st.session_state.keys())
               if k.startswith("inp_") or k.startswith("cfg_")]:
        st.session_state.pop(_k, None)
S.render_survey_tab("field", "g")
''' % RAIZ

MATRIZ = {c: [101.0, 102.0] for c in ("WR", "FR", "OR", "WL", "FL", "OL")}


def corre(at):
    at.run()
    if at.exception:
        raise SystemExit("EXCEPCION: %s" % [e.value for e in at.exception][:2])
    return at


def matriz(at):
    return next(df for df in at.dataframe if "WR" in list(df.value.columns))


def nuevo(**flags):
    at = AppTest.from_string(GUION, default_timeout=120)
    for k, v in flags.items():
        at.session_state[k] = v
    corre(at)
    at.number_input(key="inp_BS").set_value(1597.0)
    corre(at)
    at.number_input(key="inp_BSR").set_value(1330.0)
    corre(at)
    at.radio(key="cfg_omega_side").set_value("L")
    corre(at)
    at.session_state["sembrar_matriz"] = MATRIZ
    corre(at)
    return at


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ «Clear everything and start over» limpia también en el navegador")
at = nuevo()
m0 = matriz(at)
chk("de partida: BS 1597, BSR 1330, Omega L y la matriz con 101/102",
    at.number_input(key="inp_BS").value == 1597.0 and at.radio(key="cfg_omega_side").value == "L"
    and list(m0.value["WR"]) == [101.0, 102.0], list(m0.value["WR"]))
id0 = m0.proto.id
at.button(key="btn_reset_survey").click()
corre(at)
_v = {k: (at.number_input(key=k).value, at.number_input(key=k).proto.set_value)
      for k in ("inp_BS", "inp_BSR")}
chk("⚠️ los parámetros vuelven a 0 Y el navegador lo recibe (`set_value`)",
    _v == {"inp_BS": (0.0, True), "inp_BSR": (0.0, True)}, _v)
_r = at.radio(key="cfg_omega_side")
chk("...y la configuración a su valor de partida, también en el navegador",
    _r.value == "R" and _r.proto.set_value is True, (_r.value, _r.proto.set_value))
m1 = matriz(at)
chk("⚠️ la matriz vuelve a ceros y es una tabla NUEVA para el navegador (otra identidad: lo "
    "tecleado no se re-aplica)", list(m1.value["WR"]) == [0.0, 0.0] and m1.proto.id != id0,
    (list(m1.value["WR"]), m1.proto.id == id0))

at = nuevo()
at.session_state["reset_viejo"] = True
corre(at)
_sv = at.number_input(key="inp_BS").proto.set_value
chk("la sonda VE el fallo: borrando (lo de v541) el navegador NO recibe nada (set_value False)",
    at.number_input(key="inp_BS").value == 0.0 and _sv is False, _sv)

# ═════════════════════════════════════════════════════════════════
sec("2. «Duplicate survey» e importar un Excel: matriz nueva")
at = nuevo()
id0 = matriz(at).proto.id
at.button(key="btn_dup_survey").click()
corre(at)
m1 = matriz(at)
chk("Duplicate: la matriz a ceros en una tabla NUEVA, y los parámetros se quedan (es su "
    "propósito)", list(m1.value["WR"]) == [0.0, 0.0] and m1.proto.id != id0
    and at.number_input(key="inp_BS").value == 1597.0,
    (list(m1.value["WR"]), m1.proto.id == id0, at.number_input(key="inp_BS").value))

at = nuevo(sin_tabla_nueva=True)
id0 = matriz(at).proto.id
at.button(key="btn_dup_survey").click()
corre(at)
chk("la sonda VE el fallo: sin `tabla_nueva`, Duplicate deja la MISMA tabla (el navegador "
    "re-aplicaría lo tecleado)", matriz(at).proto.id == id0)

at = nuevo()
id0 = matriz(at).proto.id
import pandas as pd                                                # noqa: E402

at.session_state["_import_pending"] = {
    "ns": 2, "params": {}, "cfg": {}, "todo": False,
    "df": pd.DataFrame({c: [7.0, 8.0] for c in ("WR", "FR", "OR", "WL", "FL", "OL")})}
corre(at)
m1 = matriz(at)
chk("importar un Excel: la matriz importada (7/8) en una tabla NUEVA",
    list(m1.value["WR"]) == [7.0, 8.0] and m1.proto.id != id0,
    (list(m1.value["WR"]), m1.proto.id == id0))

# ═════════════════════════════════════════════════════════════════
sec("3. Quien reemplaza la matriz estrena tabla")
_ts = ast.parse(_fuente("core/survey_ui.py"))
_editor = [ast.unparse(k.value) for n in ast.walk(_ts) if isinstance(n, ast.Call)
           and ast.unparse(n.func).endswith("data_editor") for k in n.keywords if k.arg == "key"]
chk("la matriz del Survey usa la clave con generación",
    "estado_vivo.clave_tabla('sv', 'survey_editor')" in _editor, _editor)
_pu = ast.unparse(ast.parse(_fuente("core/projects_ui.py")))
_blq = _pu.split("_ev.respetar('sv', pid)")[1][:1500] if "_ev.respetar('sv', pid)" in _pu else ""
chk("«Rebuild the project in the Survey» estrena matriz al cargar la de la obra",
    "st.session_state['survey_df'] = pd.DataFrame(matriz)" in _blq
    and "_ev.tabla_nueva('sv')" in _blq, _blq[:200])

# ═════════════════════════════════════════════════════════════════
# B. NO SE MEZCLA INFORMACIÓN DE PROYECTOS (decisión del usuario)
GUION_B = r'''
import sys, json
sys.path.insert(0, r"%s")
import streamlit as st
import pandas as pd
from core import estado_vivo, plan_ui, plan_data, survey_ui as S
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
PLANOS = {"PRJ-A": {"params": {"BS": 1326.0}, "ns": 3},
          "PRJ-B": {"params": {"BS": 1500.0}, "ns": 5}}
plan_ui.P.is_configured = lambda: True
plan_ui._proyecto_fichado = lambda a: ({"ID": st.session_state["obra"],
                                        "Name": st.session_state["obra"]}
                                       if st.session_state.get("obra") else None)
plan_data.del_proyecto = lambda pid: json.loads(json.dumps(PLANOS.get(pid, {})))
plan_data.resumen = lambda d: "plano"
S.projects_data.head_installers_label = lambda *a, **k: "Ing"
if not hasattr(estado_vivo, "_cambio_de_obra_real"):
    estado_vivo._cambio_de_obra_real = estado_vivo.cambio_de_obra
estado_vivo.cambio_de_obra = ((lambda h: False) if st.session_state.get("sin_cambio")
                              else estado_vivo._cambio_de_obra_real)
S.init_state()
estado_vivo.pasada()
# El fichaje del menú lateral: cambia la obra y corta la pasada con st.rerun() (v541).
for etq, o in (("cerrar", ""), ("fichar A", "PRJ-A"), ("fichar B", "PRJ-B")):
    if st.button(etq, key="sb_" + etq):
        st.session_state["obra"] = o
        st.rerun()
_m = st.session_state.pop("sembrar_matriz", None)
if _m:
    st.session_state["survey_df"] = pd.DataFrame(_m)
S.render_survey_tab("field", "g")
''' % RAIZ


def b_nuevo(obra, filas, **flags):
    at = AppTest.from_string(GUION_B, default_timeout=120)
    at.session_state["obra"] = obra
    for k, v in flags.items():
        at.session_state[k] = v
    corre(at)
    at.number_input(key="inp_BSR").set_value(1330.0)
    corre(at)
    at.radio(key="cfg_omega_side").set_value("L")
    corre(at)
    at.session_state["sembrar_matriz"] = {c: [55.0] * filas
                                          for c in ("WR", "FR", "OR", "WL", "FL", "OL")}
    corre(at)
    return at


def b_estado(at):
    n = at.number_input
    return {"BS": n(key="inp_BS").value, "BSR": n(key="inp_BSR").value, "NS": n(key="ns").value,
            "omega": at.radio(key="cfg_omega_side").value,
            "matriz": list(matriz(at).value["WR"])}


def boton(at, etq):
    at.button(key="sb_" + etq).click()
    return corre(at)


sec("4. ⚠️ De una obra a OTRA: el Survey empieza de cero (también en el navegador)")
at = b_nuevo("PRJ-A", 3)
e0 = b_estado(at)
chk("de partida: obra A (BS 1326, 3 paradas de su plano), BSR 1330, Omega L y la matriz",
    e0 == {"BS": 1326.0, "BSR": 1330.0, "NS": 3, "omega": "L", "matriz": [55.0] * 3}, e0)
id0 = matriz(at).proto.id
boton(at, "fichar B")
e1 = b_estado(at)
chk("⚠️ ficha en la obra B: NADA de A — BSR a 0, Omega a su valor de partida, la matriz a "
    "ceros — y manda el plano de B (BS 1500, 5 paradas)",
    e1 == {"BS": 1500.0, "BSR": 0.0, "NS": 5, "omega": "R", "matriz": [0.0] * 5}, e1)
chk("...también en el navegador: BSR y Omega le llegan (`set_value`) y la matriz es otra tabla",
    at.number_input(key="inp_BSR").proto.set_value is True
    and at.radio(key="cfg_omega_side").proto.set_value is True and matriz(at).proto.id != id0)
chk("...el nº de paradas sigue siendo un ENTERO", type(at.number_input(key="ns").value) is int)
_cola = at.session_state["_flash_cola"] if "_flash_cola" in at.session_state else []
chk("...y se avisa de que empezó de cero, por `flash` (con otro nº de paradas la pasada se "
    "corta con `st.rerun()` y un `st.info` se perdía — lo cazó este guardián)",
    any("started from zero" in str(x[1]) for x in _cola), _cola)

at = b_nuevo("PRJ-A", 3, sin_cambio=True)
boton(at, "fichar B")
chk("la sonda VE el fallo: sin `cambio_de_obra`, lo medido en A (BSR 1330) pasa a B",
    at.number_input(key="inp_BSR").value == 1330.0, at.number_input(key="inp_BSR").value)

sec("5. Lo que NO es cambiar de proyecto")
at = b_nuevo("PRJ-A", 3)
boton(at, "cerrar")
e1 = b_estado(at)
boton(at, "fichar A")
e2 = b_estado(at)
chk("cerrar la jornada y volver a fichar en la MISMA obra: todo se queda (v541)",
    e1["BSR"] == 1330.0 and e2 == e0, (e1, e2))

at = b_nuevo("", 2)
boton(at, "fichar A")
e1 = b_estado(at)
chk("sin obra → A (tecleado antes de fichar): lo tecleado se queda (no viene de ningún "
    "proyecto) y manda el plano de A", e1["BSR"] == 1330.0 and e1["BS"] == 1326.0
    and e1["NS"] == 3 and e1["matriz"][:2] == [55.0, 55.0], e1)

sec("6. ⚠️ «Duplicate for the next lift»: lo adopta la siguiente obra")
at = b_nuevo("PRJ-A", 3)
at.button(key="btn_dup_survey").click()
corre(at)
e1 = b_estado(at)
chk("Duplicate: la matriz a ceros y los parámetros se quedan",
    e1["BSR"] == 1330.0 and e1["matriz"] == [0.0] * 3, e1)
corre(at)
chk("...sigue fichado en A: nada cambia (espera a la siguiente obra)",
    b_estado(at)["BSR"] == 1330.0, b_estado(at))
boton(at, "fichar B")
e2 = b_estado(at)
chk("⚠️ ficha en B (el siguiente ascensor): lo duplicado SE QUEDA (BSR 1330, Omega L) y manda "
    "el plano de B (BS 1500, 5 paradas)",
    e2["BSR"] == 1330.0 and e2["omega"] == "L" and e2["BS"] == 1500.0 and e2["NS"] == 5, e2)

sec("7. En el código: guardar en un proyecto y duplicar")
_ts = ast.parse(_fuente("core/survey_ui.py"))
_dup = _fuente("core/survey_ui.py").split('if st.session_state.pop("_dup_survey", False):')[1][:1500]
chk("Duplicate deja lo suyo para la siguiente obra y pone el selector del admin en «sin "
    "proyecto» ASIGNÁNDOLO (que el navegador lo vea)",
    'estado_vivo.adoptar_siguiente("sv")' in _dup
    and 'st.session_state["pl_prj_sv"] = plan_ui.SIN_PROYECTO' in _dup, _dup[:300])
_g = ast.unparse(_ts)
_tras = _g.split("projects_data.attach_survey(")[1] if "projects_data.attach_survey(" in _g else ""
_ok_rama = _tras.split("else:", 1)[1][:4000] if "else:" in _tras else ""
chk("⚠️ guardado el survey en su proyecto, empieza de cero (y vuelve a los datos, con el "
    "selector en «sin proyecto»)",
    "st.session_state['_reset_survey'] = True" in _ok_rama
    and "st.session_state['pl_prj_sv'] = plan_ui.SIN_PROYECTO" in _ok_rama
    and "st.rerun()" in _ok_rama, _ok_rama[-400:])
chk("...y sus mensajes van por `flash` (el `st.rerun()` se llevaría un `st.success`/`caption`)",
    "flash.exito(" in _ok_rama and "st.success(" not in _ok_rama
    and "st.caption(" not in _ok_rama, _ok_rama[:200])
_top = _g.split("def render_survey_tab")[1].split("_FASE_DATOS, _FASE_RES")[0]
chk("el aviso «proyecto actualizado» con «Open project ➜» está ARRIBA (sobrevive a la limpieza)",
    "_prj_creado" in _top and "ir_al_proyecto" in _top)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
