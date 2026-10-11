# -*- coding: utf-8 -*-
"""v559 · PROJECTS → LA FICHA DE UNA OBRA (Status / Data / Costs / Files), acción por acción.

Recorrido en producción (11/10/2026, cuenta admin, 1024 px, PRJ-0015). Lo arreglado («Dale»):
  1. ⚠️ Files: «Delete» borraba de DRIVE con un clic, sin preguntar ni decir nada → pregunta,
     y el borrado se ejecuta antes de pintar la lista (acción diferida, trampa 37); la tabla
     nace con otra clave (la selección es un número de fila).
  2. ⚠️ Data: los asignados y los certificados se guardan con «Save changes», mucho más
     abajo, y nada lo decía → aviso «Not saved yet» cuando difieren de lo guardado.
  3. Status: el cronograma se dibujaba a 1280 y se encogía a 650 (texto ~4 px) → tres
     lienzos (700/1000/1280) y una media query DENTRO del recuadro elige; la cifra larga de
     una tarjeta ya no se parte («09/11/202» / «6»).
  4. Logins → NOMBRES en Status, Data (asignados, avisos, historial), Costs, Files y partes.
  5. Fechas DD/MM/YYYY (fechas de Data, pedidos, historial, partes, gráfico de gasto).
  6. Data: inicio antes que fin; «— automatic —» en vez de «Choose an option»; el avance 0
     ya no sale «(empty)» en el historial.
  7. Costs: marcas del eje sin repetirse, leyenda solo de lo dibujado, «$» en la tabla,
     las 5 tarjetas en una fila, sin el segundo botón de facturar, botones a Data y Users,
     sin «(decision from v360)», «Presup.»/«Fin»/«llega» en inglés.
  8. Files: «Survey matrix» / «Admin report»; el selector de archivo se vacía al subir.
  9. Plurales: «1 log · 1 day covered», «(tomorrow)», «created with 1 activity».

Funciones con sus dependencias sustituidas (ninguna hoja se toca) + un ensayo SOLO LECTURA
con la ficha real de PRJ-0015 (la obra de prueba que se queda a propósito).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
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


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def kw(call, nombre):
    for k in call.keywords:
        if k.arg == nombre:
            return k.value
    return None


def es_llamada(n, attr):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == attr)


def sin_comentarios_constantes(arbol):
    """Todas las cadenas constantes del árbol (lo que se puede pintar)."""
    return [n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant)
            and isinstance(n.value, str)]


# ══════════════════════════════════════════════════════════════════════════════
print("0. Estático")
PUS = fuente(os.path.join("core", "projects_ui.py"))
ARB = ast.parse(PUS)
FN = {n.name: n for n in ast.walk(ARB) if isinstance(n, ast.FunctionDef)}
_cad = sin_comentarios_constantes(ARB)
for _malo in ("(decision from v360)", "Set it in :material/edit: Details",
              "It is set in :material/build: Users", "Informe admin", "Matriz survey",
              " · llega "):
    chk("ya no se pinta «%s»" % _malo, not any(_malo in s for s in _cad))
# ⚠️ Delete NO borra en el clic: solo apunta. El borrado vive en `_archivos_section`.
_acc = FN["_acciones_archivo"]
_lentos = {"delete", "delete_document_record"}
_en_acc = sorted({c.func.attr for c in ast.walk(_acc) if isinstance(c, ast.Call)
                  and isinstance(c.func, ast.Attribute)} & _lentos)
chk("⚠️ `_acciones_archivo` ya no borra nada (solo apunta y pregunta)", not _en_acc, _en_acc)
_ar = ast.unparse(FN["_archivos_section"])
chk("…el borrado se ejecuta en `_archivos_section` ANTES de pintar la tabla",
    0 <= _ar.find("delete_document_record(") < _ar.find("st.dataframe("))
_dfk = [ast.unparse(kw(n, "key")) for n in ast.walk(FN["_archivos_section"])
        if es_llamada(n, "dataframe") and kw(n, "key") is not None]
chk("…y la CLAVE de la tabla lleva la generación (cambia tras borrar)",
    len(_dfk) == 1 and "arch_tbl_" in _dfk[0] and "_arch_gen_" in _dfk[0], _dfk)
# ⚠️ `ast.unparse` escribe las cadenas con comillas SIMPLES (la 1ª vuelta buscaba dobles).
_eg = ast.unparse(FN["_editor_ganancia_hora"])
chk("ganancia: se GUARDA por el login (columna «Usuario»), no por el nombre",
    "_ed.iloc[i]['Usuario']" in _eg and "str(_ed.iloc[i]['Persona'])" not in _eg)
_cs = ast.unparse(FN["_costos_section"])
chk("Costs: las tarjetas con base de 110 px (las 5 en una fila)",
    "cpx-kpis-cst" in _cs and "110px" in _cs)
chk("Status: «(tomorrow)» y «(today)» para el próximo hito",
    "(tomorrow)." in _es_src if (_es_src := ast.unparse(FN["_estado_section"])) else False)
chk("alta: «created with 1 activity» (no «1 activities»)",
    "1 activity" in ast.unparse(FN["_nuevo_proyecto_form"]))
_sd = ast.unparse(FN["_subir_documento"])
chk("el selector de archivo se vacía al subir (generación)", "_updoc_gen_" in _sd
    and "_ug + 1" in _sd)
# Fechas DD/MM/YYYY en la ficha y en los pedidos
_dis = [n for f in ("_detalle_proyecto", "_ordenes_section") for n in ast.walk(FN[f])
        if es_llamada(n, "date_input")]
chk("se localizan las fechas de Data y de pedidos (3)", len(_dis) == 3, len(_dis))
chk("⚠️ todas en DD/MM/YYYY",
    all(isinstance(kw(n, "format"), ast.Constant) and kw(n, "format").value == "DD/MM/YYYY"
        for n in _dis), [ast.unparse(kw(n, "format")) if kw(n, "format") else None for n in _dis])
_dp = ast.unparse(FN["_detalle_proyecto"])
chk("el inicio va a la izquierda (e1) y el fin a la derecha (e2)",
    "f_ini = e1.date_input" in _dp and "f_fin = e2.date_input" in _dp)
# El cronograma: tres lienzos
_es = ast.unparse(FN["_estado_section"])
chk("⚠️ el cronograma se dibuja en 3 lienzos (700/1000/1280) con media query",
    all(f"({w}," in _es for w in (700, 1000, 1280)) and "@media" in _es and "vw=w" in _es)
# ⚠️ Sobre las CADENAS del código, no sobre el fuente: la 1ª versión de este chequeo
# leía el fichero entero y se puso roja con el comentario que explica el cambio (trampa 2).
_cad_ex = sin_comentarios_constantes(ast.parse(fuente(os.path.join("core", "expenses.py"))))
chk("el gráfico de gasto ya no dice «Presup.» ni «Fin»",
    not any("Presup." in s or s.startswith("Fin ") or ">Fin " in s for s in _cad_ex))

from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import projects_ui as PU, expenses as E, handover as H           # noqa: E402

# ══════════════════════════════════════════════════════════════════════════════
print("\n1. Tarjetas, gráfico de gasto, expediente")
_c = PU._kpi_card("Projected finish", "09/11/2026")
chk("⚠️ cifra larga (10) a 21 px: no se parte", "font-size:21px" in _c, _c[:160])
chk("cifra media (7) a 21 px", "font-size:21px" in PU._kpi_card("Cost", "$27,883"))
chk("cifra muy larga (11, «13 d behind») a 18 px", "font-size:18px" in PU._kpi_card("Situation", "13 d behind"))
chk("cifra corta, tamaño del tema", "font-size" not in PU._kpi_card("Cost", "$2"))
_cur = {"fechas": ["2026-09-30", "2026-10-06", "2026-10-09"], "mano_obra": [0, 1.2, 1.8],
        "total": [0, 1.2, 1.8], "presupuesto": 0}
_svg = E.spend_svg(_cur, None, "Obra")
import re                                                                   # noqa: E402
_ticks = re.findall(r'text-anchor="end" font-size="8" fill="#667080">([^<]+)<', _svg)
chk("se leen 5 marcas del eje", len(_ticks) == 5, _ticks)
chk("⚠️ las marcas no se repiten (antes «$0 $1 $1 $2 $2 $2»)", len(set(_ticks)) == 5, _ticks)
chk("subtítulo en DD/MM/YYYY", "30/09/2026 → 09/10/2026" in _svg)
chk("sin presupuesto ni proyección, ni «Budget» ni «Finish» en el dibujo",
    "Budget" not in _svg and "Finish" not in _svg)
_svg2 = E.spend_svg(dict(_cur, presupuesto=5), 4.0, "Obra")
chk("con presupuesto y proyección: «Budget» y «Finish» (en inglés)",
    ">Budget $5<" in _svg2 and ">Finish $4<" in _svg2)
_ctx = {"trabajaron": {"admin2": "2026-10-09"}, "credenciales": {}, "asignados": ["c0"],
        "nombres": {"admin2": "Bobo"}}
_det = {f["clave"]: f["detalle"] for f in H.estado(_ctx)}
chk("⚠️ expediente: «no certificate: Bobo» (no el login)",
    "no certificate: Bobo" in _det.get("installer_certs", ""), _det.get("installer_certs"))
chk("…y «not assigned to it: Bobo»",
    any("not assigned to it: Bobo" in x["texto"] for x in H.incoherencias(_ctx)))
chk("sin nombres, el login de siempre (módulo HOJA)",
    "no certificate: admin2" in {f["clave"]: f["detalle"]
                                for f in H.estado(dict(_ctx, nombres={}))}["installer_certs"])

def b(at, k):
    x = [y for y in at.button if y.key == k]
    return x[0] if x else None


# ⚠️ El ensayo REAL va ANTES de los guiones que sustituyen funciones: AppTest corre en
# el MISMO proceso y lo sustituido se queda sustituido (lección de v534, repetida en
# v558 y aquí en la 1ª vuelta: `E.labor_breakdown` falso tumbó Costs con KeyError).
# ══════════════════════════════════════════════════════════════════════════════
print("\n2. Ensayo SOLO LECTURA con la ficha real de PRJ-0015")
GUION_REAL = r'''
import streamlit as st
from core import projects_ui as PU
st.session_state.setdefault("auth", {"usuario": "Admin2", "rol": "administrator", "grupo": "cliente1"})
PU._detalle_proyecto("PRJ-0015", "cliente1")
'''
at = AppTest.from_string(GUION_REAL, default_timeout=240)
at.run()


def sec(at, s):
    [x for x in at.radio if x.key == "cpxseg_prj_sec"][0].set_value(s)
    at.run()


chk("Status: sin excepción", not at.exception, [e.value for e in at.exception][:1])
_dfs = [d.value for d in at.dataframe if "Persona" in list(d.value.columns)]
chk("Status: «Who has worked here» tiene filas (PRJ-0015 tiene horas)", bool(_dfs) and len(_dfs[0]) > 0)
chk("⚠️ Status: …y ningún login en ella", _dfs and not ({"Admin2", "campo000"} & set(_dfs[0]["Persona"])),
    list(_dfs[0]["Persona"]) if _dfs else "")
sec(at, "✏️ Datos")
chk("Data: sin excepción", not at.exception, [e.value for e in at.exception][:1])
_ms = [m for m in at.multiselect if m.key == "asig_PRJ-0015"]
chk("Data: se localiza el selector de asignados", bool(_ms))
# ⚠️ Añadido tras la batería (escapó «los asignados vuelven a salir por login»): las
# OPCIONES que se pintan son nombres; el valor guardado sigue siendo el login.
chk("Data: el selector de asignados enseña NOMBRES (campo000 → su nombre)",
    _ms and "campo000" in _ms[0].value and "campo000" not in _ms[0].options,
    (_ms[0].value, _ms[0].options[:4]) if _ms else "")
chk("Data: con lo guardado, solo la nota (sin «Not saved yet»)",
    not any("Not saved yet" in w.value for w in at.warning)
    and any("saved with **Save changes**" in c.value for c in at.caption))
_sm = [s for s in at.selectbox if "Manual status" in str(s.label)]
chk("Data: estado manual vacío = «— automatic (from the progress) —»",
    _sm and "— automatic (from the progress) —" in _sm[0].options, _sm[0].options if _sm else "")
_avs = " | ".join([w.value for w in at.warning] + [i.value for i in at.info])
chk("Data: el aviso de contacto con NOMBRE («helper leader CI 1», no el login)",
    "helper leader CI 1" in _avs, _avs[:300])
import re as _re                                                            # noqa: E402
chk("Data: «until» en DD/MM/YYYY (no ISO)",
    bool(_re.search(r"until \d\d/\d\d/\d{4}", _avs)) and not _re.search(r"until 20\d\d-", _avs),
    _avs[:300])
if _ms:
    _ms[0].set_value(_ms[0].value[:1])
    at.run()
    chk("⚠️ Data: quitar a alguien avisa «Not saved yet» (nada se escribe: no se pulsa Save)",
        any("Not saved yet" in w.value for w in at.warning))
sec(at, "💰 Costos")
chk("Costs: sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("Costs: ⚠️ sin el segundo botón de facturar", b(at, "fac_atajo_PRJ-0015") is None)
_mdc = " | ".join(m.value for m in at.markdown)
chk("Costs: con algo pendiente NO dice «Everything invoiced» (lo dice la cabecera)",
    "Not invoiced" in _mdc and "Everything invoiced" not in _mdc)
_cpc = " | ".join(c.value for c in at.caption)
chk("Costs: sin presupuesto, la leyenda no habla de la línea del presupuesto",
    "Cumulative cost day by day." in _cpc and "budget" not in _cpc.split("Cumulative cost")[1][:200])
_lab = [d for d in at.dataframe if "Rate/h" in list(d.value.columns)]
# ⚠️ Columna POR columna (tras la batería: con el «$» solo en una, la otra pasaba).
import json as _json                                                       # noqa: E402
_cols = _json.loads(_lab[0].proto.columns) if _lab else {}
chk("Costs: la tabla de mano de obra con «$» en Rate/h Y en Cost",
    all((_cols.get(c) or {}).get("type_config", {}).get("format") == "$%,.2f"
        or (_cols.get(c) or {}).get("format") == "$%,.2f" for c in ("Rate/h", "Costo")),
    {c: _cols.get(c) for c in ("Rate/h", "Costo")})
_bd = b(at, "cst_ir_datos_PRJ-0015")
chk("Costs: «Set the budget in Data» (PRJ-0015 no tiene presupuesto)", _bd is not None)
if _bd:
    _bd.click()
    at.run()
    chk("…que abre la pestaña Data",
        [x for x in at.radio if x.key == "cpxseg_prj_sec"][0].value == "✏️ Datos")
sec(at, "💰 Costos")
_bu = b(at, "cst_ir_users_PRJ-0015")
chk("Costs: «Go to Users» (hay horas sin tarifa)", _bu is not None)
if _bu:
    _bu.click()
    at.run()
    chk("…que lleva a Planning → Users",
        "_admin_nav_pending" in at.session_state
        and tuple(at.session_state["_admin_nav_pending"]) == ("planificacion", "👷 Usuarios"))
sec(at, "📎 Archivos")
chk("Files: sin excepción", not at.exception, [e.value for e in at.exception][:1])
_mdf = " | ".join(m.value for m in at.markdown)
chk("Files: el expediente con NOMBRES («no certificate:» sin «Admin2»)",
    "no certificate:" in _mdf and "Admin2" not in _mdf.split("no certificate:")[1][:120],
    _mdf.split("no certificate:")[1][:120] if "no certificate:" in _mdf else "")

# ══════════════════════════════════════════════════════════════════════════════
print("\n3. Files: borrar pregunta, y borra una vez confirmado")
GUION_FILES = r'''
import streamlit as st
from core import projects_ui as PU, projects as P, drive_store as D, toolruns, auth
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
st.session_state.setdefault("_LOG", [])
LOG = st.session_state["_LOG"]
D.is_configured = lambda: True
D.delete = lambda did: LOG.append(("drive", did))
D.download = lambda did: b"x"
toolruns.is_configured = lambda: False
auth.list_users = lambda *a, **k: [{"User": "ana", "Name": "Ana Ruiz"}]
DOCS = [{"ProjectID": "P1", "Name": "plano.pdf", "Type": "plano", "DriveID": "D1",
         "UploadedBy": "ana", "Date": "2026-10-08 05:54:00"}]
P.list_documents = lambda pid: list(DOCS)
P.delete_document_record = lambda pid, did: (LOG.append(("hoja", did)) or (True, "Document deleted."))
PU._archivos_section("P1")
# la fila elegida, pintada a mano (AppTest no selecciona filas de un st.dataframe)
PU._acciones_archivo("P1", {"did": "D1", "nombre": "plano.pdf", "doc": DOCS[0], "run": None}, True)
'''




def log(at):
    return list(at.session_state["_LOG"])


def flashes(at):
    return list(at.session_state["_flash_cola"]) if "_flash_cola" in at.session_state else []


at = AppTest.from_string(GUION_FILES, default_timeout=60)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0].value if at.dataframe else None
chk("«Uploaded by» con el NOMBRE (Ana Ruiz, no «ana»)",
    _df is not None and list(_df["Uploaded by"]) == ["Ana Ruiz"],
    list(_df["Uploaded by"]) if _df is not None else "")
b(at, "arch_del_P1_D1").click()
at.run()
chk("⚠️ el clic en «Delete» NO borra nada", log(at) == [], log(at))
chk("…pregunta («Delete «plano.pdf»?… cannot be recovered»)",
    any("Delete «plano.pdf»?" in w.value and "cannot be" in w.value for w in at.warning))
b(at, "arch_delno_P1_D1").click()
at.run()
chk("«Keep it» lo deja y vuelve el botón", log(at) == [] and b(at, "arch_del_P1_D1") is not None)
b(at, "arch_del_P1_D1").click()
at.run()
b(at, "arch_delok_P1_D1").click()
at.run()
chk("⚠️ confirmado: se borra de Drive y de la hoja", log(at) == [("drive", "D1"), ("hoja", "D1")],
    log(at))
chk("…dice que se borró (flash)", any("deleted" in str(x) for x in flashes(at)), flashes(at))
chk("…y la tabla nace con otra clave", "_arch_gen_P1" in at.session_state
    and at.session_state["_arch_gen_P1"] == 1)

# ══════════════════════════════════════════════════════════════════════════════
print("\n4. Historial, equipo, ganancia, partes")
GUION_VAR = r'''
import streamlit as st
from core import projects_ui as PU, auditoria, auth, expenses as E, theme, daily_log_ui as DLU
st.session_state.setdefault("auth", {"usuario": "jefa", "rol": "administrator", "grupo": "G"})
auth.list_users = lambda *a, **k: [{"User": "campo000", "Name": "Hugo"},
                                   {"User": "Admin2", "Name": "Bobo"}]
auditoria.historial = lambda **k: [
    {"Date": "2026-10-09 10:52:39", "User": "Admin2",
     "cambios": {"FieldAssigned": ("campo000", "campo000;Admin2")}},
    {"Date": "2026-09-30 18:16:36", "User": "campo000",
     "cambios": {"Progress": ("2.0", 0)}}]
PU._historial_section("P1")
E.is_configured = lambda: True
E.labor_breakdown = lambda pid, g: {"items": [{"usuario": "Admin2", "horas": 0.04},
                                              {"usuario": "campo000", "horas": 0.14}],
                                    "horas": 0.18}
PU._equipo_proyecto("P1", "G")
PU._editor_ganancia_hora("P1", [{"usuario": "campo000", "horas": 2, "tarifa": 40}], {}, theme)
DLU._linea({"Author": "campo000", "Date": "2026-09-26", "Created": "2026-09-29 16:35:28",
            "Text": "hola", "ID": "L1"}, False, "t")
st.caption(DLU._cuantos(1, 1) + " | " + DLU._cuantos(3, 2))
'''
at = AppTest.from_string(GUION_VAR, default_timeout=60)
at.run()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_md = " | ".join(m.value for m in at.markdown)
chk("historial: fecha DD/MM/YYYY HH:MM y quién por su nombre («09/10/2026 10:52** · Bobo»)",
    "**09/10/2026 10:52** · Bobo" in _md, _md[:300])
chk("historial: la plantilla en NOMBRES («Hugo → … Hugo, Bobo»)",
    ">Hugo</span> → <b>Hugo, Bobo</b>" in _md)
chk("⚠️ historial: el avance 0 es «0», no «(empty)»", "→ <b>0</b>" in _md and "(empty)" not in _md)
_dfs = [d.value for d in at.dataframe]
chk("«Who has worked here» con nombres (Bobo, Hugo)",
    any("Persona" in d.columns and list(d["Persona"]) == ["Bobo", "Hugo"] for d in _dfs))
_ed = [d for d in at.dataframe if "Usuario" in list(d.value.columns)
       and "Ganancia/h" in list(d.value.columns)]
chk("ganancia: se ve el NOMBRE y el login va OCULTO (con él se guarda)",
    _ed and list(_ed[0].value["Persona"]) == ["Hugo"]
    and '"Usuario": {"hidden": true' in str(_ed[0].proto.columns))
_cap = " | ".join(c.value for c in at.caption)
chk("sin «(decision from v360)»", "v360" not in _cap)
chk("⚠️ partes: «26/09/2026 · Hugo · 29/09/2026 16:35»",
    "26/09/2026 · Hugo · 29/09/2026 16:35" in _md, [m for m in _md.split(" | ") if "Hugo" in m][:2])
chk("partes: «1 log · 1 day covered» y «3 logs · 2 days covered»",
    "1 log · 1 day covered | 3 logs · 2 days covered" in _cap)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")
