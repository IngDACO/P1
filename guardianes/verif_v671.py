# -*- coding: utf-8 -*-
"""v671 · Nómina y horas (ciclo 2, mejoras 3/5).

H27 las jornadas CERRADAS de más de 16 h se señalan (Hours, Radar, nómina) y se arreglan con «Fix it»: la salida real
    de la jornada y de sus entradas de obra, con las correcciones apuntadas; la nómina deja fuera a esa persona.
H15 «Generate» propone el periodo siguiente al último generado, dice qué colilla tiene ya cada persona, y las horas
    fichadas después de generar se saldan (a la colilla sin pagar, o en una de ajuste si está pagada).
H25 la colilla dice el fondo de super de la persona, y avisa de lo que le falta (ABN, fondo).

Nada sale a la red ni escribe: funciones reales con sustitutos y hojas de mentira; AppTest de las pantallas.
"""
import ast
import io
import json
import os
import sys
from datetime import date, datetime, time

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


def src(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


def funcion(rel, nombre):
    s = src(rel)
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n, ast.get_source_segment(s, n) or ""
    return None, ""


def _sustituir(obj, **kw):
    viejo = {k: getattr(obj, k) for k in kw}
    for k, v in kw.items():
        setattr(obj, k, v)
    return lambda: [setattr(obj, k, v) for k, v in viejo.items()]


from streamlit.testing.v1 import AppTest                                   # noqa: E402
from core import timeclock as T                                            # noqa: E402
from core import correcciones as CO                                        # noqa: E402
from core import payroll as PR                                             # noqa: E402
from core import auth as A                                                 # noqa: E402

_ORIG = {"jornadas_largas": T.jornadas_largas, "recortar": T.recortar_jornada}
_CAB = list(T.HEADERS)


def _f(nombre, user, ini, fin, tipo, proyecto="", estado="CERRADO", grupo="G"):
    r = {h: "" for h in _CAB}
    r.update({"Name": nombre, "User": user, "Project": proyecto, "Clock In": ini, "Clock Out": fin,
              "Status": estado, "Group": grupo, "Type": tipo})
    if ini and fin:
        r["Hours"] = str(round((datetime.strptime(fin, T.FMT) - datetime.strptime(ini, T.FMT)).total_seconds() / 3600, 2))
    return r


# ═════════════════════════════════════════════════════════════════════════════
sec("1. Las jornadas imposibles (H27)")
_FILAS = [
    _f("hjg,ujgjg", "campo000", "2026-10-23 06:23:27", "2026-10-26 06:20:24", T.TIPO_GENERAL),
    _f("hjg,ujgjg", "campo000", "2026-10-23 06:23:28", "2026-10-26 06:20:24", T.TIPO_PROYECTO, "Parramatta"),
    _f("hjg,ujgjg", "campo000", "2026-10-22 06:26:29", "2026-10-22 20:07:28", T.TIPO_GENERAL),       # 13.68 h
    _f("Bobo", "admin2", "2026-11-04 06:30:00", "2026-11-04 14:30:00", T.TIPO_GENERAL),              # 8 h
    _f("Noche", "noche", "2026-11-02 23:00:00", "2026-11-04 01:00:00", T.TIPO_GENERAL),              # 26 h, 2 medianoches
    _f("Abierta", "ab", "2026-10-01 07:00:00", "", T.TIPO_GENERAL, estado="ABIERTO"),
    _f("Otra empresa", "x", "2026-10-01 07:00:00", "2026-10-05 07:00:00", T.TIPO_GENERAL, grupo="OTRA"),
]
_d = [_sustituir(T, _cached_records=lambda: [dict(r) for r in _FILAS], mapa_nombres=lambda g="": {})]
try:
    _lg = T.jornadas_largas("G")
    _lg_rango = T.jornadas_largas("G", desde=date(2026, 11, 1), hasta=date(2026, 11, 9))
finally:
    for x in _d:
        x()
_hs = [(j["nombre"], j["horas"]) for j in _lg]
chk("jornadas_largas: la de 71.95 h y la que cruza dos medianoches; ni la de 13.68 h, ni la de 8, ni la abierta, ni otra "
    "empresa", _hs == [("Noche", 26.0), ("hjg,ujgjg", 71.95)], _hs)
chk("…y con rango, solo las que lo tocan", [j["nombre"] for j in _lg_rango] == ["Noche"], _lg_rango)
chk("…con el login para corregirla", _lg[1]["cuenta"] == "campo000" and _lg[1]["entrada"] == "2026-10-23 06:23:27", _lg[1])


class _WST:
    """La hoja del fichaje, que APLICA lo que se escribe (corregir_fichaje lee lo de antes en la siguiente)."""
    def __init__(self, filas):
        self.filas = [dict(r) for r in filas]
        self.escritos = []

    def get_all_records(self, **k):
        return [dict(r) for r in self.filas]

    def batch_update(self, rangos, **k):
        for r in rangos:
            col, fila = r["range"][0], int(r["range"][1:])
            campo = {"E": "Clock In", "F": "Clock Out", "G": "Hours"}[col]
            self.filas[fila - 2][campo] = r["values"][0][0]
            self.escritos.append((fila, campo, r["values"][0][0]))


_w = _WST(_FILAS[:2])
_d = [_sustituir(T, _get_worksheet=lambda: (_w, None), _invalidate_records=lambda: None)]
try:
    _ok, _res = T.recortar_jornada("G", "campo000", "hjg,ujgjg", "2026-10-23 06:23:27", "2026-10-26 06:20:24",
                                   datetime(2026, 10, 23, 15, 0))
    _w2 = _WST(_FILAS[:2])
    _d.append(_sustituir(T, _get_worksheet=lambda: (_w2, None)))
    _okx, _resx = T.recortar_jornada("G", "campo000", "hjg,ujgjg", "2026-10-23 06:23:27", "2026-10-26 06:20:24",
                                     datetime(2026, 10, 27, 15, 0))
    _w3 = _WST([_FILAS[0], _f("hjg,ujgjg", "campo000", "2026-10-24 08:00:00", "2026-10-26 06:20:24",
                              T.TIPO_PROYECTO, "Late job")])
    _d.append(_sustituir(T, _get_worksheet=lambda: (_w3, None)))
    _oky, _resy = T.recortar_jornada("G", "campo000", "hjg,ujgjg", "2026-10-23 06:23:27", "2026-10-26 06:20:24",
                                     datetime(2026, 10, 23, 15, 0))
finally:
    for x in _d:
        x()
chk("recortar_jornada: la jornada y su entrada de obra terminan a las 15:00 del 23/10, con sus horas recalculadas",
    _ok and _w.filas[0]["Clock Out"] == "2026-10-23 15:00:00" and _w.filas[1]["Clock Out"] == "2026-10-23 15:00:00"
    and _w.filas[0]["Hours"] == "8.61", (_ok, _res, _w.filas))
chk("…PRIMERO la entrada de obra y después la jornada (si no, la obra quedaría fuera de su jornada)",
    [e[0] for e in _w.escritos if e[1] == "Clock Out"] == [3, 2], _w.escritos)
chk("…y devuelve lo cambiado (para el rastro)", _res.get("jornada") == ("2026-10-26 06:20:24", "2026-10-23 15:00:00")
    and _res.get("obras") == [("Parramatta", "2026-10-26 06:20:24", "2026-10-23 15:00:00")], _res)
chk("una salida POSTERIOR a la registrada se niega sin escribir", not _okx and not _w2.escritos, _resx)
chk("una entrada de obra que empieza DESPUÉS de la hora nueva se dice, sin escribir nada",
    not _oky and "Late job" in _resy and not _w3.escritos, _resy)

_reg, _apr = [], []
_d = [_sustituir(T, recortar_jornada=lambda *a, **k: (True, {"jornada": ("2026-10-26 06:20:24", "2026-10-23 15:00:00"),
                                                             "obras": [("Parramatta", "2026-10-26 06:20:24",
                                                                        "2026-10-23 15:00:00")]})),
      _sustituir(CO, registrar=lambda *a, **k: (_reg.append((a, k)), (True, f"COR-{len(_reg)}"))[1],
                 aprobar=lambda cid, revisor, nota="": (_apr.append((cid, revisor, nota)), (True, "ok"))[1])]
try:
    _okc, _msgc = CO.recortar_jornada_oficina("G", "campo000", "hjg,ujgjg", "2026-10-23 06:23:27", "2026-10-26 06:20:24",
                                              datetime(2026, 10, 23, 15, 0), "admin2", "left site at 15:00")
finally:
    for x in _d:
        x()
chk("la oficina deja apuntadas DOS correcciones (obra y jornada) con la hora vieja y la nueva, y aprobadas por ella",
    _okc and len(_reg) == 2 and _reg[0][0][3] == T.TIPO_PROYECTO and _reg[1][0][3] == T.TIPO_GENERAL
    and _reg[1][0][6] == "2026-10-26 06:20:24" and _reg[1][0][7] == "2026-10-23 15:00:00"
    and [a[1] for a in _apr] == ["admin2", "admin2"] and "23/10/2026 15:00" in _msgc, (_reg, _apr, _msgc))

# ═════════════════════════════════════════════════════════════════════════════
sec("2. «Fix it» en Hours y el Radar (AppTest)")
HORAS = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, timeclock as T, correcciones as CO, flash
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
st.session_state.setdefault("_LL", [])
T.jornadas_largas = lambda g, **k: [{"usuario": "campo000", "cuenta": "campo000", "nombre": "hjg,ujgjg",
    "entrada": "2026-10-23 06:23:27", "salida": "2026-10-26 06:20:24", "horas": 71.95}]
CO.recortar_jornada_oficina = lambda *a: (st.session_state["_LL"].append(a), (True, "Workday fixed."))[1]
flash.mostrar()
PU.jornadas_largas_section("G")
'''
at = AppTest.from_string(HORAS, default_timeout=90)
at.run()
chk("la sección se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("dice cuántas, de más de 16 h, y por qué importa",
    any("1 closed workday(s) of more than 16 h" in e.value and "payroll leaves those people out" in e.value
        for e in at.error), [e.value for e in at.error])
_md = " ".join(m.value for m in at.markdown)
chk("…cada una con su persona, entrada → salida (DD/MM/YYYY) y horas",
    "hjg,ujgjg" in _md and "23/10/2026 06:23 → 26/10/2026 06:20" in _md and "71.95 h" in _md, _md[:300])
at.button(key="gh_fix_0").click().run()
_di = [x for x in at.date_input if x.key == "gh_fixd_0"]
_ti = [x for x in at.time_input if x.key == "gh_fixt_0"]
chk("«Fix it» propone el día de la entrada y 8 h después (14:23)", _di and _di[0].value == date(2026, 10, 23)
    and _ti and _ti[0].value == time(14, 23), (_di and _di[0].value, _ti and _ti[0].value))
_ti[0].set_value(time(15, 0))
at.button(key="gh_fixok_0").click().run()
_ll = list(at.session_state["_LL"]) if "_LL" in at.session_state else []
chk("«Apply the real end» corrige con la hora puesta, quien lo hace y la jornada exacta",
    _ll and _ll[0][1] == "campo000" and _ll[0][3] == "2026-10-23 06:23:27" and _ll[0][4] == "2026-10-26 06:20:24"
    and _ll[0][5] == datetime(2026, 10, 23, 15, 0) and _ll[0][6] == "admin2", _ll)

RADAR = r'''
import streamlit as st
from core import roster_ui as RU
RU._radar_largas("G", [{"nombre": "hjg,ujgjg", "entrada": "2026-10-23 06:23:27", "horas": 71.95}])
'''
at = AppTest.from_string(RADAR, default_timeout=60)
at.run()
_b = [b for b in at.button if b.key == "radar_lg_0"]
chk("el Radar las lista («hjg,ujgjg · 23/10/2026 · 71.95 h»)", _b and "23/10/2026 · 71.95 h" in str(_b[0].label),
    [str(b.label) for b in at.button])
_b[0].click().run()
chk("…y una línea lleva a Hours", at.session_state["_admin_nav_pending"] == ("finanzas", "⏱ Horas"))
_n, _rp = funcion("core/roster_ui.py", "_radar_personal")
_s_ru = src("core/roster_ui.py")
# v676 · detrás de las jornadas largas suman las obras cerradas (H4 del ciclo 3): la forma del final cambió
chk("…y cuentan en el Radar (su cifra y su «nada que ver»)", "+ len(_lg) + len({pid" in _rp and "_radar_largas(grupo, _lg)" in _rp
    and "+ len(_jornadas_largas(grupo))" in _s_ru)
_n, _gh = funcion("core/projects_ui.py", "render_group_hours")
chk("Hours la pinta antes de la tabla (sea cual sea el periodo)",
    "jornadas_largas_section(grupo)" in _gh and _gh.find("jornadas_largas_section(grupo)") < _gh.find("if not data:"))

# ═════════════════════════════════════════════════════════════════════════════
sec("3. La nómina (H27, H15)")


class _WSP:
    def __init__(self):
        self.filas, self.lotes = [], []

    def append_rows(self, rows, **k):
        self.filas.extend(rows)

    def batch_update(self, rangos, **k):
        self.lotes.append(rangos)


_wp = _WSP()
from core import ausencias as AU                                           # noqa: E402
_d = [_sustituir(PR, _ws=lambda: (_wp, None), list_nominas=lambda g, **k: [], _max_num=lambda: 0,
                 _ids_nuevos=lambda mx, n: [f"NOM-{9000 + i}" for i in range(n)]),
      _sustituir(T, horas_por_usuario_rango=lambda g, d, h, **k: {"campo000": {"nombre": "hjg,ujgjg", "horas": 188.92},
                                                                    "admin2": {"nombre": "Bobo", "horas": 8.0}},
                 jornadas_abiertas=lambda g, d, h: {},
                 jornadas_largas=lambda g, **k: [{"usuario": "campo000", "nombre": "hjg,ujgjg", "horas": 71.95,
                                                  "entrada": "2026-10-23 06:23:27"}]),
      _sustituir(A, rate_map=lambda g: {"campo000": 55.0, "admin2": 45.0}),
      _sustituir(AU, horas_pagadas_grupo=lambda g, d, h: {})]
try:
    _r = PR.generar("G", "2026-10-20", "2026-10-26", 11.5, 0.0, "admin2")
finally:
    for x in _d:
        x()
chk("H27 · generar deja FUERA a quien tiene una jornada de más de 16 h, y lo dice («hjg,ujgjg (71.95 h, 23/10)»)",
    _r["creadas"] == 1 and _r.get("largas") == ["hjg,ujgjg (71.95 h, 23/10)"] and len(_wp.filas) == 1
    and _wp.filas[0][2] == "admin2", (_r, _wp.filas))

_NOMS = [{"ID": "NOM-0001", "Group": "G", "User": "admin2", "Name": "Bobo", "PeriodFrom": "2026-11-03",
          "PeriodTo": "2026-11-09", "Hours": "0.19", "HourlyRate": "45", "Base": "8.55",
          "ConceptsJSON": json.dumps([{"concepto": "Superannuation", "tipo": "aporte", "monto": 0.98}]),
          "Net": "8.55", "Status": "pagada"},
         {"ID": "NOM-0002", "Group": "G", "User": "campo000", "Name": "hjg,ujgjg", "PeriodFrom": "2026-11-03",
          "PeriodTo": "2026-11-09", "Hours": "8.0", "HourlyRate": "55", "Base": "440",
          "ConceptsJSON": json.dumps([{"concepto": "Superannuation", "tipo": "aporte", "monto": 50.6},
                                      {"concepto": "Income tax withheld (PAYG)", "tipo": "deduccion", "monto": 88.0}]),
          "Net": "352", "Status": "emitida"},
         {"ID": "NOM-0003", "Group": "G", "User": "x", "Name": "X", "PeriodFrom": "2026-10-27",
          "PeriodTo": "2026-11-02", "Hours": "5", "HourlyRate": "40", "Base": "200", "ConceptsJSON": "[]",
          "Net": "200", "Status": "pagada"},
         # Y: su colilla y una de AJUSTE del mismo periodo (2 + 3 h) cubren sus 5 h: nada pendiente
         {"ID": "NOM-0005", "Group": "G", "User": "y", "Name": "Y", "PeriodFrom": "2026-10-27",
          "PeriodTo": "2026-11-02", "Hours": "2", "HourlyRate": "40", "Base": "80", "ConceptsJSON": "[]",
          "Net": "80", "Status": "pagada"},
         {"ID": "NOM-0006", "Group": "G", "User": "y", "Name": "Y", "PeriodFrom": "2026-10-27",
          "PeriodTo": "2026-11-02", "Hours": "3", "HourlyRate": "40", "Base": "120", "ConceptsJSON": "[]",
          "Net": "120", "Status": "emitida"}]
_d = [_sustituir(PR, list_nominas=lambda g=None, **k: [dict(n) for n in _NOMS]),
      _sustituir(T, horas_por_usuario_rango=lambda g, d, h, **k: (
          {"admin2": {"horas": 0.32}, "campo000": {"horas": 8.23}} if d == "2026-11-03" else {"x": {"horas": 5}, "y": {"horas": 5}}))]
try:
    _ult = PR.ultimo_hasta("G")
    _hsp = PR.horas_sin_pagar("G")
finally:
    for x in _d:
        x()
chk("H15 · ultimo_hasta: hasta el 09/11", _ult == date(2026, 11, 9), _ult)
_hs2 = {x["nid"]: (x["dif"], x["pagada"]) for x in _hsp}
chk("H15 · horas_sin_pagar: Bobo +0.13 h (su colilla, pagada) y hjg +0.23 h (sin pagar); X e Y (con su ajuste), nada",
    _hs2 == {"NOM-0001": (0.13, True), "NOM-0002": (0.23, False)}, _hsp)

_ws2 = _WSP()
_d = [_sustituir(PR, get_nomina=lambda nid: dict(next(n for n in _NOMS if n["ID"] == nid)),
                 _ws=lambda: (_ws2, None), _find_row=lambda w, nid: 3, _invalidate=lambda: None, _max_num=lambda: 3,
                 _ids_nuevos=lambda mx, n: ["NOM-0004"])]
try:
    _s2 = PR.saldar_horas("NOM-0002", 0.23, "admin2")
    _s1 = PR.saldar_horas("NOM-0001", 0.13, "admin2")
finally:
    for x in _d:
        x()
_e2 = {r["range"]: r["values"][0][0] for lote in _ws2.lotes for r in lote}
from core.num import col_letter as _cl                                     # noqa: E402
_con2 = json.loads(_e2.get(f"{_cl(PR._NCOL['ConceptsJSON'])}3", "[]"))
chk("H15 · a la colilla SIN pagar se le suman: 8.23 h, base $452.65, super y PAYG al mismo % (11.5 y 20)",
    _s2[0] and _e2.get(f"{_cl(PR._NCOL['Hours'])}3") == "8.23" and _e2.get(f"{_cl(PR._NCOL['Base'])}3") == "452.65"
    and {c["concepto"]: c["monto"] for c in _con2} == {"Superannuation": 52.05, "Income tax withheld (PAYG)": 90.53}
    and _e2.get(f"{_cl(PR._NCOL['Net'])}3") == "362.12", (_s2, _e2))
_aj = _ws2.filas[0] if _ws2.filas else []
chk("H15 · a la PAGADA, una colilla de ajuste del mismo periodo: 0.13 h × $45 = $5.85, con su super",
    _s1[0] and _aj[0] == "NOM-0004" and _aj[4:6] == ["2026-11-03", "2026-11-09"] and _aj[6] == "0.13"
    and _aj[8] == "5.85" and "Adjustment to NOM-0001" in _aj[13]
    and json.loads(_aj[9]) == [{"concepto": "Superannuation", "tipo": "aporte", "monto": 0.67}], (_s1, _aj))

GEN = r'''
import datetime as dt
import streamlit as st
from core import payroll_ui as PUI, payroll as PR, timeclock as T, auth, clock, flash
from core import ausencias as AU
clock.today = lambda *a, **k: dt.date(2026, 11, 10)
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
PR.is_configured = lambda: True
PR.list_nominas = lambda g=None, **k: [{"ID": "NOM-0001", "User": "admin2", "Name": "Bobo", "PeriodFrom": "2026-11-03",
    "PeriodTo": "2026-11-09", "Hours": "0.19", "Status": "pagada"}]
PR.horas_sin_pagar = lambda g: [{"nid": "NOM-0001", "usuario": "admin2", "nombre": "Bobo", "desde": "2026-11-03",
    "hasta": "2026-11-09", "en_colilla": 0.19, "ahora": 0.32, "dif": 0.13, "pagada": True, "tarifa": 45.0}]
T.horas_por_usuario_rango = lambda g, d, h, **k: {"admin2": {"nombre": "Bobo", "horas": 0.32}}
T.jornadas_abiertas = lambda g, d, h: {}
T.jornadas_largas = lambda g, **k: [{"usuario": "campo000", "nombre": "hjg,ujgjg", "horas": 71.95,
    "entrada": "2026-10-23 06:23:27"}]
auth.rate_map = lambda g: {"admin2": 45.0}
auth.group_num_setting = lambda g, k, d: d
# ⚠️ sustituida: el clic de «Settle» llega a `_accion_pendiente`, y la real ESCRIBIRÍA en la hoja
st.session_state.setdefault("_LL", [])
PR.saldar_horas = lambda nid, h, quien="": (st.session_state["_LL"].append(("saldar", nid, h)), (True, "ok"))[1]
AU.excesos_por_decidir = lambda *a, **k: []
st.session_state.setdefault("_nom_gen", True)
flash.mostrar()
PUI.render_nominas("G")
'''
at = AppTest.from_string(GEN, default_timeout=90)
at.run()
chk("«Generate payroll» se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_dd = {x.key: x.value for x in at.date_input}
chk("H15 · propone el periodo SIGUIENTE al generado: 10/11 → 16/11",
    _dd.get("nom_desde_Semanal") == date(2026, 11, 10) and _dd.get("nom_hasta_Semanal") == date(2026, 11, 16), _dd)
chk("…y dice hasta dónde está generada", any("Payroll is generated up to 09/11/2026" in c.value for c in at.caption),
    [c.value for c in at.caption])
chk("H27 · avisa de la jornada de más de 16 h del periodo, con salida a Hours",
    any("Workday of more than 16 h to fix first" in e.value and "71.95 h" in e.value for e in at.error)
    and "nom_gen_ir_horas" in {b.key for b in at.button}, [e.value for e in at.error])
at.date_input(key="nom_desde_Semanal").set_value(date(2026, 11, 3)).run()
at.date_input(key="nom_hasta_Semanal").set_value(date(2026, 11, 9)).run()
_df = at.dataframe[0].value if at.dataframe else None
chk("H15 · con el periodo ya generado, la vista previa dice «already on NOM-0001 (0.19 h)»",
    _df is not None and "already on NOM-0001 (0.19 h)" in list(_df["Nota"]), None if _df is None else list(_df["Nota"]))
_bs = {b.key: str(b.label) for b in at.button}
chk("…y ofrece la colilla de ajuste de las +0.13 h (estaba pagada)",
    "Adjustment payslip (+0.13 h)" in _bs.get("nom_gen_saldar_0", ""), _bs)
at.button(key="nom_gen_saldar_0").click().run()
chk("…y al pulsarlo salda ESA colilla con esas horas (por la acción diferida)",
    ("saldar", "NOM-0001", 0.13) in list(at.session_state["_LL"]), list(at.session_state["_LL"]))
_n, _ap = funcion("core/payroll_ui.py", "_accion_pendiente")
chk("la acción diferida llama a saldar_horas", 'elif _acc.get("accion") == "saldar":' in _ap
    and 'payroll.saldar_horas(_acc.get("nid", ""), _acc.get("horas", 0), _creado_por())' in _ap)
_n, _rn = funcion("core/payroll_ui.py", "render_nominas")
chk("la lista de nóminas también avisa de las horas sin pagar", 'horas_sin_pagar_section(grupo, "nom_lst")' in _rn)
_n, _gn = funcion("core/payroll_ui.py", "_generar")
chk("al generar, el aviso de quién quedó fuera por una jornada de más de 16 h", 'if res.get("largas"):' in _gn)

# ═════════════════════════════════════════════════════════════════════════════
sec("4. La colilla (H25)")
chk("Login lleva la columna SuperFund, al final", A.LOGIN_HEADERS[-1] == "SuperFund")
_n, _fu = funcion("core/auth_ui.py", "_ficha_usuario")
chk("…y se pone en la ficha de la persona", 'auth.set_login_setting(sel, "SuperFund", _sf)' in _fu)
from core import payslip_pdf as PP                                         # noqa: E402
from core import contable as CB                                            # noqa: E402
_d = [_sustituir(A, get_user=lambda u: {"User": "admin2", "Name": "Bobo", "SuperFund": "AustralianSuper · member 123"}
                 if u == "admin2" else {}),
      _sustituir(CB, identidad=lambda g: {"abn": "", "legal": "", "plazo": 14})]
try:
    _fs = (PP.fondo_super({"User": "admin2"}), PP.fondo_super({"User": "nadie"}))
    _pdf = PP.generate_payslip_pdf(_NOMS[0], "G")
finally:
    for x in _d:
        x()
chk("fondo_super lee el de la persona", _fs == ("AustralianSuper · member 123", ""), _fs)
from pypdf import PdfReader                                                # noqa: E402
_tx = " ".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(_pdf)).pages)
chk("el PDF dice «Super fund: AustralianSuper · member 123»", "Super fund: AustralianSuper" in _tx, _tx[-300:])
_n, _de = funcion("core/payroll_ui.py", "_detalle")
chk("el detalle avisa, junto al PDF, de lo que le falta (ABN, fondo)", "This payslip is missing {x}." in _de
    and "payslip_pdf.fondo_super(f)" in _de and "the company's ABN" in _de)
DET = r'''
import json
import streamlit as st
from core import payroll_ui as PUI, payroll as PR, auth, contable, flash
st.session_state.setdefault("auth", {"usuario": "admin2", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
_N = {"ID": "NOM-0001", "Group": "G", "User": "admin2", "Name": "Bobo", "PeriodFrom": "2026-11-03",
      "PeriodTo": "2026-11-09", "Hours": "0.19", "HourlyRate": "45", "Base": "8.55",
      "ConceptsJSON": json.dumps([{"concepto": "Superannuation", "tipo": "aporte", "monto": 0.98}]),
      "Net": "8.55", "Status": "emitida"}
PR.is_configured = lambda: True
PR.get_nomina = lambda nid: dict(_N)
PR.list_nominas = lambda g=None, **k: [dict(_N)]
contable.identidad = lambda g: {"abn": st.session_state.get("_ABN", ""), "legal": "X", "plazo": 14}
auth.get_user = lambda u: {"User": u, "Name": "Bobo", "SuperFund": st.session_state.get("_SF", "")}
st.session_state.setdefault("_nom_open", "NOM-0001")
flash.mostrar()
PUI.render_nominas("G")
'''
at = AppTest.from_string(DET, default_timeout=90)
at.run()
_cap = " ".join(c.value for c in at.caption)
chk("el detalle de una colilla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("…y sin ABN ni fondo, lo DICE junto al PDF (los dos)", "This payslip is missing" in _cap
    and "the company's ABN" in _cap and "super fund" in _cap, _cap[:400])
at = AppTest.from_string(DET, default_timeout=90)
at.session_state["_ABN"] = "12 345 678 901"
at.session_state["_SF"] = "AustralianSuper"
at.run()
chk("…y con los dos puestos, no avisa", "This payslip is missing" not in " ".join(c.value for c in at.caption))

T.jornadas_largas, T.recortar_jornada = _ORIG["jornadas_largas"], _ORIG["recortar"]
print("\n" + ("TODO OK" if not FALLOS else f"{len(FALLOS)} FALLO(S): {FALLOS}"))
sys.exit(1 if FALLOS else 0)
