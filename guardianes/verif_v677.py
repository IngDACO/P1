# -*- coding: utf-8 -*-
"""v677 · Ausencias y fichaje (ciclo 3, mejoras 2/3).

H9  Finance → Hours → «Add a missed day»: la oficina añade un día que alguien trabajó sin fichar nada (la jornada y su
    entrada de obra, CERRADAS, y la corrección aprobada con el motivo), sin pisar otra jornada ni pasar de 16 h, y
    avisando si ese día ya está en una colilla. Time fixes lo enseña como «Added day · 07:00 → 15:30 · +8.50 h».
H2  Planning → Absences → «Register an absence for someone»: con las reglas del campo, nace aprobada, va al tablero y
    se le dice a la persona; y el saldo de ausencias en la ficha de la persona, con el botón que abre ese formulario.
H12 la vista previa de «My absences» dice el solape y no deja enviar (prometía «17 left after this»).
H1  los estados de las ausencias con mayúscula.
H7  fichar en una obra que aún no ha empezado, o en pausa, lo dice (sin bloquear).
H8  la barra lateral dice dónde y desde cuándo.

Nada sale a la red ni escribe: funciones reales con sustitutos y hojas de mentira; AppTest de las pantallas.
"""
import ast
import io
import os
import sys
from datetime import date, datetime

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:900]))
    if not cond:
        FALLOS.append(nombre)


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
from core import timeclock as TC                                           # noqa: E402
from core import correcciones as CO                                        # noqa: E402
from core import correcciones_ui as CUI                                    # noqa: E402
from core import ausencias as AU                                           # noqa: E402
from core import ausencias_ui as AUI                                       # noqa: E402
from core import projects as P                                             # noqa: E402

# los originales (trampa 48: los guiones de AppTest dejan sus sustitutos puestos en ESTE proceso)
_ORIG = dict(get_ws=TC._get_worksheet, now=TC._now, inv=TC._invalidate_records, reg=CO.registrar, apr=CO.aprobar,
             nqc=CO.nomina_que_cubre, aj=TC.anadir_jornada)


class WS:
    """Una hoja de fichaje de mentira: lee lo que se le da y apunta lo que se le pide escribir."""
    def __init__(self, filas=None):
        self.filas, self.escrito = list(filas or []), []

    def get_all_records(self, **k):
        return [dict(f) for f in self.filas]

    def append_rows(self, filas, value_input_option=None):
        self.escrito.append((filas, value_input_option))

    def append_row(self, fila, value_input_option=None):
        self.escrito.append(([fila], value_input_option))


def _f(usr, nom, tipo, ci, co, pid=""):
    return {"Name": nom, "PIN": "", "Project": "Torre" if pid else "", "Location": "", "Clock In": ci, "Clock Out": co,
            "Hours": "", "Status": "CERRADO" if co else "ABIERTO", "Group": "G", "Type": tipo, "User": usr,
            "ProjectID": pid}


E, S = datetime(2026, 11, 13, 7, 0), datetime(2026, 11, 13, 15, 30)

# ═════════════════════════════════════════════════════════════════════════════
print("1. H9 · la regla de un día añadido (`problema_jornada`)")
_d = _sustituir(TC, _now=lambda: "2026-11-16 10:00:00")
try:
    _reg = [_f("ana", "Ana", TC.TIPO_GENERAL, "2026-11-13 14:00:00", "2026-11-13 18:00:00"),
            _f("ana", "Ana", TC.TIPO_PROYECTO, "2026-11-12 07:00:00", "2026-11-12 15:00:00", "PRJ-1"),
            _f("beto", "Beto", TC.TIPO_GENERAL, "2026-11-13 07:00:00", "2026-11-13 15:30:00")]
    _ok = TC.problema_jornada(_reg, "ana", "Ana", "G", datetime(2026, 11, 12, 16, 0), datetime(2026, 11, 12, 20, 0))
    _ch = TC.problema_jornada(_reg, "ana", "Ana", "G", E, S)
    _chp = TC.problema_jornada(_reg, "ana", "Ana", "G", datetime(2026, 11, 12, 6, 0), datetime(2026, 11, 12, 6, 0))
    _ob = TC.problema_jornada([_reg[1]], "ana", "Ana", "G", datetime(2026, 11, 12, 6, 0), datetime(2026, 11, 12, 9, 0))
    _ob_sin = TC.problema_jornada([_reg[1]], "ana", "Ana", "G", datetime(2026, 11, 12, 6, 0),
                                  datetime(2026, 11, 12, 9, 0), con_obra=False)
    _fut = TC.problema_jornada([], "ana", "Ana", "G", datetime(2026, 11, 16, 7, 0), datetime(2026, 11, 16, 15, 30))
    _lar = TC.problema_jornada([], "ana", "Ana", "G", datetime(2026, 11, 12, 5, 0), datetime(2026, 11, 12, 23, 0))
    _otro = TC.problema_jornada(_reg, "beto", "Beto", "G", datetime(2026, 11, 12, 7, 0), datetime(2026, 11, 12, 15, 0))
finally:
    _d()
chk("sin nada que pisar: nada que decir", _ok == "", _ok)
chk("pisa su jornada de 14:00 a 18:00 → lo dice con las horas", "overlaps the workday entry from 14:00 to 18:00" in _ch, _ch)
chk("la salida antes (o igual) que la entrada → no", "end must be after the start" in _chp, _chp)
chk("pisa una entrada de OBRA suya → lo dice (y sin obra, no le afecta)", "overlaps the project entry" in _ob and _ob_sin == "",
    (_ob, _ob_sin))
chk("lo que aún no ha pasado (hoy a las 15:30, con las 10:00) → no", "hasn't come yet" in _fut, _fut)
chk("más de 16 h → no", "can't be longer than 16 h" in _lar and "18.00 h" in _lar, _lar)
chk("lo de OTRA persona no cuenta (beto el 12)", _otro == "", _otro)

print("2. H9 · `anadir_jornada` escribe las DOS filas cerradas en una escritura")
ws = WS([_f("ana", "Ana", TC.TIPO_GENERAL, "2026-11-12 07:00:00", "2026-11-12 15:00:00")])
_d = _sustituir(TC, _get_worksheet=lambda: (ws, None), _now=lambda: "2026-11-16 10:00:00", _invalidate_records=lambda: None)
try:
    _r1 = TC.anadir_jornada("G", "ana", "Ana", E, S, "Torre", "PRJ-1")
    _esc1 = list(ws.escrito)
    ws.escrito.clear()
    _r2 = TC.anadir_jornada("G", "ana", "Ana", datetime(2026, 11, 12, 8, 0), datetime(2026, 11, 12, 9, 0), "Torre", "PRJ-1")
    _esc2 = list(ws.escrito)
    _r3 = TC.anadir_jornada("G", "ana", "Ana", E, S)
    _esc3 = list(ws.escrito)
finally:
    _d()
_filas = _esc1[0][0] if _esc1 else []
chk("devuelve las horas (8.5)", _r1 == (True, 8.5), _r1)
chk("UNA escritura, en crudo, con dos filas del ancho de HEADERS",
    len(_esc1) == 1 and _esc1[0][1] == "RAW" and len(_filas) == 2 and all(len(f) == len(TC.HEADERS) for f in _filas), _esc1)
if len(_filas) == 2:
    _g, _p = (dict(zip(TC.HEADERS, f)) for f in _filas)
    chk("la jornada: cerrada, 07:00 → 15:30, 8.5 h, general, de ana, sin obra",
        (_g["Status"], _g["Clock In"], _g["Clock Out"], _g["Hours"], _g["Type"], _g["User"], _g["ProjectID"], _g["Group"])
        == ("CERRADO", "2026-11-13 07:00:00", "2026-11-13 15:30:00", "8.5", TC.TIPO_GENERAL, "ana", "", "G"), _g)
    chk("la entrada de obra: las mismas horas, con el nombre y el ID de la obra",
        (_p["Status"], _p["Clock In"], _p["Clock Out"], _p["Hours"], _p["Type"], _p["Project"], _p["ProjectID"])
        == ("CERRADO", "2026-11-13 07:00:00", "2026-11-13 15:30:00", "8.5", TC.TIPO_PROYECTO, "Torre", "PRJ-1"), _p)
chk("pisando su jornada del 12 → se niega y NO escribe", _r2[0] is False and "overlaps" in str(_r2[1]) and _esc2 == [],
    (_r2, _esc2))
chk("sin obra: solo la jornada", _r3[0] is True and len(_esc3) == 1 and len(_esc3[0][0]) == 1, _esc3)

print("3. H9 · `anadir_dia_oficina`: el rastro aprobado, el motivo y la colilla")
_AP, _RG = [], []
_d = [_sustituir(TC, anadir_jornada=lambda *a, **k: (True, 8.5)),
      _sustituir(CO, registrar=lambda *a, **k: (_RG.append((a, k)), (True, "COR-0099"))[1],
                 aprobar=lambda cid, rev, nota="": (_AP.append((cid, rev, nota)), (True, "ok"))[1],
                 nomina_que_cubre=lambda g, u, f: "NOM-0007")]
try:
    _sin = CO.anadir_dia_oficina("G", "ana", "Ana", E, S, "Torre", "PRJ-1", "bobo", "   ")
    _n_sin = len(_RG)                   # ⚠️ lo apuntado tras la llamada SIN motivo, antes de la otra
    _con = CO.anadir_dia_oficina("G", "ana", "Ana", E, S, "Torre", "PRJ-1", "bobo", "Forgot to clock in")
finally:
    for x in _d:
        x()
chk("sin motivo, no se añade nada", _sin[0] is False and "why" in _sin[1].lower() and _n_sin == 0, (_sin, _n_sin))
# registrar(grupo, usuario, nombre, tipo, proyecto, campo, valor_anterior, valor_nuevo, motivo=)
_a = _RG[0][0] if _RG else ()
chk("la corrección: jornada, «Added day», sin valor anterior, «entrada → salida», con la obra y el motivo",
    len(_a) == 8 and _a[:3] == ("G", "ana", "Ana") and _a[3] == TC.TIPO_GENERAL and _a[4] == "Torre"
    and _a[5] == CO.CAMPO_DIA and _a[6] == "" and _a[7] == "2026-11-13 07:00:00 → 2026-11-13 15:30:00"
    and _RG[0][1].get("motivo") == "Forgot to clock in", _RG)
chk("…y la aprueba quien lo hizo, con el motivo de nota", _AP == [("COR-0099", "bobo", "Forgot to clock in")], _AP)
chk("el aviso dice a quién, cuándo, cuánto y dónde", _con[0] is True and
    _con[1] == "Day added for Ana: 13/11/2026, 07:00 → 15:30 · 8.50 h on Torre.", _con)
chk("…y devuelve la colilla que ya cubre ese día", _con[2] == "NOM-0007", _con)
chk("`ventana` lee las dos horas de vuelta",
    CO.ventana({"Field": CO.CAMPO_DIA, "NewValue": "2026-11-13 07:00:00 → 2026-11-13 15:30:00"})
    == ("2026-11-13 07:00:00", "2026-11-13 15:30:00") and CO.ventana({"Field": CO.CAMPO_IN, "NewValue": "x"}) == ("", ""))

print("4. H9 · Time fixes lo enseña como un día añadido")
_RD = {"ID": "COR-0099", "Group": "G", "User": "ana", "Name": "Ana", "Type": TC.TIPO_GENERAL, "Project": "Torre",
       "Field": CO.CAMPO_DIA, "OldValue": "", "NewValue": "2026-11-13 07:00:00 → 2026-11-13 15:30:00",
       "Status": CO.APROBADA, "ReviewedBy": "bobo", "ReviewedDate": "2026-11-16 10:00:00", "Created": "2026-11-16 10:00:00"}
chk("las horas: +8.50 h worked", CUI._dif_horas(_RD) == "+8.50 h worked", CUI._dif_horas(_RD))
chk("lo que cambió: 07:00 → 15:30 (y una corrección normal, como siempre)", CUI._horas_txt(_RD) == "07:00 → 15:30"
    and CUI._horas_txt({"Field": CO.CAMPO_IN, "OldValue": "2026-11-13 07:10:00", "NewValue": "2026-11-13 07:00:00"})
    == "07:10 → 07:00", CUI._horas_txt(_RD))
chk("el día: Fri 13/11/2026", CUI._dia(_RD) == "Fri 13/11/2026", CUI._dia(_RD))
chk("«Revert» no habla de una sesión abierta", "added a missed day" in CUI.no_se_puede(_RD, "revertir", []),
    CUI.no_se_puede(_RD, "revertir", []))
BAND = r'''
import streamlit as st
from core import correcciones as CO, correcciones_ui as CUI, auth
st.session_state.setdefault("auth", {"usuario": "bobo", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
R = {"ID": "COR-0099", "Group": "G", "User": "ana", "Name": "Ana", "Type": "general", "Project": "Torre",
     "Field": CO.CAMPO_DIA, "OldValue": "", "NewValue": "2026-11-13 07:00:00 → 2026-11-13 15:30:00",
     "Status": CO.APROBADA, "ReviewedBy": "bobo", "ReviewedDate": "2026-11-16 10:00:00", "Created": "2026-11-16 10:00:00"}
CO.is_configured = lambda: True
CO.list_group = lambda *a, **k: [dict(R)]
auth.list_users = lambda *a, **k: [{"User": "ana", "Name": "Ana"}, {"User": "bobo", "Name": "Bobo"}]
if st.session_state.get("_KPI"):
    st.session_state["_cor_kpi"] = "ok"
CUI.render_bandeja("G")
'''
at = AppTest.from_string(BAND, default_timeout=120)
at.run()
chk("la bandeja se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_df = at.dataframe[0].value if len(at.dataframe) else None
_fila = _df.iloc[0].to_dict() if _df is not None and len(_df) else {}
chk("el historial: «Added day», antes «—», ahora «07:00 → 15:30», «Approved» (con mayúscula, H1) y quién",
    (_fila.get("Campo"), _fila.get("Antes"), _fila.get("Ahora"), _fila.get("Estado"), _fila.get("Revisor"))
    == ("Added day", "—", "07:00 → 15:30", "Approved", "Bobo"), _fila)
at = AppTest.from_string(BAND, default_timeout=120)
at.session_state["_KPI"] = True
at.run()
_md = " ¦ ".join(m.value for m in at.markdown)
chk("la lista de «Approved»: «Ana · added day · Fri 13/11/2026 · 07:00 → 15:30»",
    "**Ana** · added day · Fri 13/11/2026 · 07:00 → 15:30" in _md, _md[:600])

print("5. H9 · la pantalla «Add a missed day» (AppTest)")
HORAS = r'''
import datetime as dt
import streamlit as st
from core import projects_ui as PU, projects as P, auth, timeclock as TC, clock, correcciones as CO
from core import correcciones_ui as CUI
clock.today = lambda *a, **k: dt.date(2026, 11, 16)
TC._now = lambda: "2026-11-16 10:00:00"
st.session_state.setdefault("auth", {"usuario": "bobo", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
USERS = [{"User": "ana", "Name": "Ana", "Role": "field", "Active": "SI", "Group": "G"},
         {"User": "bobo", "Name": "Bobo", "Role": "administrator", "Active": "SI", "Group": "G"},
         {"User": "old", "Name": "Old", "Role": "field", "Active": "NO", "Group": "G"}]
auth.list_users = lambda *a, **k: USERS
P.list_projects = lambda *a, **k: [{"ID": "PRJ-1", "Name": "Torre", "Status": "In progress", "Group": "G"},
                                   {"ID": "PRJ-A", "Name": "Vieja", "Status": "Archived", "Group": "G"}]
REG = ([{"Name": "Ana", "Clock In": "2026-11-13 08:00:00", "Clock Out": "2026-11-13 10:00:00", "Status": "CERRADO",
         "Group": "G", "Type": "general", "User": "ana"}] if st.session_state.get("_CHOCA") else [])
TC._cached_records = lambda: REG
CO.nomina_que_cubre = lambda g, u, f: "NOM-0009" if st.session_state.get("_NOM") else ""
st.session_state.setdefault("_LL", [])
st.session_state.setdefault("_AVI", [])
CO.anadir_dia_oficina = lambda *a: (st.session_state["_LL"].append(a), (True, "Day added for Ana.", "NOM-0009"))[1]
CUI.avisar_dia_anadido = lambda *a, **k: st.session_state["_AVI"].append(a)
PU.dia_olvidado_section("G")
'''


def _horas(**ss):
    at = AppTest.from_string(HORAS, default_timeout=120)
    for k, v in ss.items():
        at.session_state[k] = v
    at.run()
    return at


at = _horas()
chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_sb = {s.key: s for s in at.selectbox}
_ops_u = list(_sb["gh_dia_u_0"].options) if "gh_dia_u_0" in _sb else []
_ops_p = list(_sb["gh_dia_p_0"].options) if "gh_dia_p_0" in _sb else []
chk("la persona: las ACTIVAS del grupo, de campo y de oficina (no «Old»)", "Ana" in _ops_u and "Bobo" in _ops_u
    and "Old" not in _ops_u, _ops_u)
chk("la obra: con su ID, y no las archivadas", any("PRJ-1" in o for o in _ops_p) and not any("PRJ-A" in o for o in _ops_p),
    _ops_p)
_di = {d.key: d for d in at.date_input}
chk("el día propuesto: el último laborable (un lunes → el viernes 13/11)", _di.get("gh_dia_d_0") is not None
    and _di["gh_dia_d_0"].value == date(2026, 11, 13), [(k, d.value) for k, d in _di.items()])
_bt = {b.key: b for b in at.button}
chk("sin persona, obra y motivo, el botón no se puede pulsar", _bt.get("gh_dia_ok_0") is not None and _bt["gh_dia_ok_0"].disabled)
at.selectbox(key="gh_dia_u_0").select("Ana").run()
_cap = " ¦ ".join(c.value for c in at.caption)
chk("con la persona: «8.50 h on 13/11/2026 — the workday and the job»", "**8.50 h** on 13/11/2026" in _cap, _cap[:500])
at.selectbox(key="gh_dia_p_0").select(next(o for o in _ops_p if "PRJ-1" in o)).run()
at.text_input(key="gh_dia_m_0").input("Forgot to clock in").run()
_bt = {b.key: b for b in at.button}
chk("con todo puesto, sí", _bt.get("gh_dia_ok_0") is not None and not _bt["gh_dia_ok_0"].disabled)
_bt["gh_dia_ok_0"].click().run()
_ll = list(at.session_state["_LL"])
chk("«Add the day» llama a la oficina con la persona, las horas, la obra, quién y el motivo",
    len(_ll) == 1 and _ll[0][1:3] == ("ana", "Ana") and _ll[0][3] == E and _ll[0][4] == S
    and _ll[0][5:9] == ("Torre", "PRJ-1", "bobo", "Forgot to clock in"), _ll)
chk("…se le dice a la persona", len(list(at.session_state["_AVI"])) == 1, list(at.session_state["_AVI"]))
chk("…y los campos empiezan de cero (generación nueva)", at.session_state["_gh_dia_gen"] == 1)
at = _horas(_CHOCA=True)
at.selectbox(key="gh_dia_u_0").select("Ana").run()
# ⚠️ con obra y motivo puestos: sin ellos el botón ya está desactivado y esto pasaba en vacío (lo destapó la rotura)
at.selectbox(key="gh_dia_p_0").select(next(o for o in _ops_p if "PRJ-1" in o)).run()
at.text_input(key="gh_dia_m_0").input("Forgot to clock in").run()
_w = " ¦ ".join(w.value for w in at.warning)
chk("si pisa otra jornada suya, lo dice ANTES (la misma regla) y no deja añadir",
    "overlaps the workday entry from 08:00 to 10:00" in _w and at.button(key="gh_dia_ok_0").disabled, _w)
at = _horas(_NOM=True)
at.selectbox(key="gh_dia_u_0").select("Ana").run()
_w = " ¦ ".join(w.value for w in at.warning)
chk("si ese día ya está en una colilla, lo dice y manda a Payroll", "already in payslip **NOM-0009**" in _w
    and "Finance → Payroll" in _w, _w)
_n, _rg = funcion("core/projects_ui.py", "render_group_hours")
chk("está en Finance → Hours, debajo de las jornadas largas", "jornadas_largas_section(grupo)\n    dia_olvidado_section(grupo)" in _rg)

# ═════════════════════════════════════════════════════════════════════════════
print("6. H2 · una ausencia registrada por la oficina")


class WSA(WS):
    pass


wsa = WSA([])
_d = [_sustituir(AU, _ws=lambda: wsa, solapadas=lambda *a, **k: [], exceso=lambda *a, **k: 0,
                 _invalidate=lambda: None, _next_id=lambda recs: "AUS-0042")]
try:
    _o = AU.solicitar("G", "ana", "Ana", AU.VACACIONES, "2026-11-23", "2026-11-24", "Phone call", por_oficina="bobo")
    _fo = dict(zip(AU.HEADERS, wsa.escrito[-1][0][0])) if wsa.escrito else {}
    _c = AU.solicitar("G", "ana", "Ana", AU.VACACIONES, "2026-11-23", "2026-11-24")
    _fc = dict(zip(AU.HEADERS, wsa.escrito[-1][0][0])) if wsa.escrito else {}
finally:
    for x in _d:
        x()
chk("la de la oficina nace APROBADA, resuelta y creada por quien la registró", _o == (True, "AUS-0042")
    and (_fo.get("Status"), _fo.get("ResolvedBy"), _fo.get("CreatedBy"), _fo.get("User")) == (AU.APROBADA, "bobo", "bobo", "ana")
    and bool(_fo.get("ResolvedDate")), _fo)
chk("…la del campo, como siempre: pendiente y creada por la persona",
    (_fc.get("Status"), _fc.get("ResolvedBy"), _fc.get("CreatedBy")) == (AU.PENDIENTE, "", "ana"), _fc)
_SOL = [{"ID": "AUS-0007", "Type": AU.VACACIONES, "From": "2026-11-20", "To": "2026-11-20", "Status": AU.APROBADA}]
_d = _sustituir(AU, solapadas=lambda *a, **k: list(_SOL))
try:
    _ms = AU.msg_solape("G", "ana", "2026-11-19", "2026-11-20")
    _ps = AU.problema_solicitud("G", "ana", AU.VACACIONES, "2026-11-19", "2026-11-20")
finally:
    _d()
chk("`msg_solape`: la ausencia que pisa, con su ID, tipo y fechas", "There is already an absence overlapping those dates: "
    "AUS-0007 (Annual leave, 20/11/2026 → 20/11/2026, approved)" in _ms, _ms)
chk("…y el motor dice LO MISMO (una regla)", _ps == _ms, (_ps, _ms))
_SC, _AR, _NT = [], [], []
_LG = []
_d = [_sustituir(AU, solicitar=lambda *a, **k: (_SC.append((a, k)), (True, "AUS-0042"))[1],
                 # ⚠️ la recién creada se lee en SU grupo (`_de_grupo` → `list_group`), nunca por un ID global (v351)
                 list_group=lambda g, *a, **k: (_LG.append(g), [{"ID": "AUS-0042", "Type": AU.VACACIONES, "From": "2026-11-23",
                                                                 "To": "2026-11-24", "User": "ana"}])[1],
                 aplicar_al_roster=lambda r, quitar=False: (_AR.append(r.get("ID")), (True, 2))[1]),
      _sustituir(AUI, _avisar_registrada=lambda u, r, m="": _NT.append((u, r.get("ID"), m)))]
try:
    _ro = AUI.registrar_oficina("G", "ana", "Ana", AU.VACACIONES, date(2026, 11, 23), date(2026, 11, 24), "Phone", False, "bobo")
finally:
    for x in _d:
        x()
chk("registrar_oficina: con la regla del motor y `por_oficina`", _SC and _SC[0][1].get("por_oficina") == "bobo", _SC)
chk("…al tablero y a la persona, con la ausencia leída en SU grupo", _AR == ["AUS-0042"]
    and _NT == [("ana", "AUS-0042", "Phone")] and _LG and set(_LG) == {"G"}, (_AR, _NT, _LG))
chk("…y el aviso lo dice", _ro == (True, "Annual leave recorded and approved for Ana (AUS-0042). 2 day(s) marked in the planner."), _ro)

BANDA = r'''
import datetime as dt
import streamlit as st
from core import ausencias as AU, ausencias_ui as AUI, auth, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 16)
st.session_state.setdefault("auth", {"usuario": "bobo", "rol": "administrator", "grupo": "G", "nombre": "Bobo"})
AU.is_configured = lambda: True
for _n in ("list_group", "pendientes", "ausentes_en", "excesos_por_decidir"):
    setattr(AU, _n, lambda *a, **k: [])
USERS = [{"User": "ana", "Name": "Ana", "Role": "field", "Active": "SI", "Group": "G"},
         {"User": "old", "Name": "Old", "Role": "field", "Active": "NO", "Group": "G"}]
auth.list_users = lambda *a, **k: USERS
SOL = ([{"ID": "AUS-0007", "Type": "vacaciones", "From": "2026-11-16", "To": "2026-11-16", "Status": "approved"}]
       if st.session_state.get("_SOL") else [])
AU.solapadas = lambda *a, **k: list(SOL)
AU.saldo = lambda g, u, tp, ref=None: {"asignados": 20.0, "usados": 2.0, "restantes": 18.0, "pendientes": 0.0,
                                       "disponibles": 18.0, "ilimitado": tp == "libre", "periodo": None}
st.session_state.setdefault("_RO", [])
AUI.registrar_oficina = lambda *a: (st.session_state["_RO"].append(a), (True, "Recorded."))[1]
AUI.render_bandeja("G")
'''


def _banda(**ss):
    at = AppTest.from_string(BANDA, default_timeout=120)
    for k, v in ss.items():
        at.session_state[k] = v
    at.run()
    return at


at = _banda(_aus_of_pers_pending="ana")
chk("la bandeja se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
chk("viniendo de la ficha, la persona ya está elegida (y solo las activas)", at.selectbox(key="aus_of_u_0").value == "Ana"
    and "Old" not in list(at.selectbox(key="aus_of_u_0").options), list(at.selectbox(key="aus_of_u_0").options))
_cap = " ¦ ".join(c.value for c in at.caption)
chk("la vista previa: «This takes 1 day · 17 left after this»", "This takes **1 day** · 17 left after this" in _cap, _cap[:500])
at.button(key="aus_of_ok_0").click().run()
_ro = list(at.session_state["_RO"])
chk("«Register it (approved)» registra a ana con quien lo hace", len(_ro) == 1 and _ro[0][1] == "ana" and _ro[0][2] == "Ana"
    and _ro[0][-1] == "bobo", _ro)
at = _banda(_aus_of_pers_pending="ana", _SOL=True)
_w = " ¦ ".join(w.value for w in at.warning)
chk("con un solape, lo dice con la regla del motor y no deja registrar", "There is already an absence overlapping" in _w
    and at.button(key="aus_of_ok_0").disabled, _w)

print("7. H2 · el saldo en la ficha de la persona")
FICHA = r'''
import streamlit as st
from core import auth_ui as AUT, ausencias as AU
AU.is_configured = lambda: True
AU.saldo = lambda g, u, tp, ref=None: ({"asignados": 20.0, "usados": 1.0, "pendientes": 1.0, "disponibles": 18.0,
                                        "restantes": 19.0, "ilimitado": False, "periodo": None} if tp == "vacaciones" else
                                       {"asignados": 10.0, "usados": 0.0, "pendientes": 0.0, "disponibles": 10.0,
                                        "restantes": 10.0, "ilimitado": False, "periodo": None} if tp == "enfermedad" else
                                       {"asignados": 0.0, "usados": 3.0, "pendientes": 0.0, "disponibles": -3.0,
                                        "restantes": -3.0, "ilimitado": True, "periodo": None})
AUT._saldo_ausencias("G", "ana", "fk")
'''
at = AppTest.from_string(FICHA, default_timeout=60)
at.run()
_md = " ¦ ".join(m.value for m in at.markdown)
chk("dice el saldo de cada tipo (lo que queda, con lo pendiente)", "**Leave balance** · Annual leave: **18** of 20 left (1 pending)"
    " · Sick leave: **10** of 10 left · Day off: 3 used" in _md, _md)
at.button(key="fk_ausreg").click().run()
chk("«Register an absence» abre la bandeja con la persona elegida", at.session_state["_aus_of_pers_pending"] == "ana"
    and at.session_state["_admin_nav_pending"] == ("planificacion", "🌴 Ausencias"))
# ⚠️ la LLAMADA, no la línea `def _saldo_ausencias(grupo, sel, k):`, que también lo contiene (pasaba en vacío)
import re                                                                  # noqa: E402
chk("está en «Their work»", bool(re.search(r"^\s+_saldo_ausencias\(grupo, sel, k\)", src("core/auth_ui.py"), re.M)))

# ═════════════════════════════════════════════════════════════════════════════
print("8. H12 · la vista previa de «My absences» dice el solape · H1 · estados con mayúscula")
MIAS = r'''
import datetime as dt
import streamlit as st
from core import ausencias as AU, ausencias_ui as AUI, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 19)
st.session_state.setdefault("auth", {"usuario": "ana", "rol": "field", "grupo": "G", "nombre": "Ana"})
AU.is_configured = lambda: True
AU.list_group = lambda *a, **k: []
SOL = ([{"ID": "AUS-0007", "Type": "vacaciones", "From": "2026-11-19", "To": "2026-11-19", "Status": "approved"}]
       if st.session_state.get("_SOL") else [])
AU.solapadas = lambda *a, **k: list(SOL)
AU.saldo = lambda g, u, tp, ref=None: {"asignados": 20.0, "usados": 2.0, "restantes": 18.0, "pendientes": 0.0,
                                       "disponibles": 18.0, "ilimitado": tp == "libre", "periodo": None}
AUI.render_mis_ausencias()
'''
at = AppTest.from_string(MIAS, default_timeout=120)
at.session_state["_SOL"] = True
at.run()
chk("«My absences» se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_w = " ¦ ".join(w.value for w in at.warning)
_cap = " ¦ ".join(c.value for c in at.caption)
chk("con un solape: lo dice ANTES de enviar y no promete «left after this»",
    "There is already an absence overlapping those dates: AUS-0007" in _w and "left after this" not in _cap, (_w, _cap[:300]))
chk("…y no deja enviar", at.button(key="aus_enviar").disabled)
at = AppTest.from_string(MIAS, default_timeout=120)
at.run()
chk("sin solape, como siempre: «This takes … left after this» y se puede enviar",
    "left after this" in " ".join(c.value for c in at.caption) and not at.button(key="aus_enviar").disabled)
chk("H1 · los estados con mayúscula", (AUI._chip_estado(AU.PENDIENTE), AUI._chip_estado(AU.APROBADA),
                                     AUI._chip_estado(AU.RECHAZADA), AUI._chip_estado(AU.CANCELADA))
    == ("🟡 Pending", "🟢 Approved", "🔴 Rejected", "⚪ Cancelled"), AUI._chip_estado(AU.APROBADA))
chk("…y así salen en la línea de cada ausencia (bandeja, historial y «My absences»)",
    AUI._linea({"Type": AU.VACACIONES, "From": "2026-11-23", "To": "2026-11-24", "Days": "2", "Status": AU.APROBADA})
    .endswith("· 🟢 Approved"))

# ═════════════════════════════════════════════════════════════════════════════
print("9. H7 · fichar en una obra que aún no ha empezado, o en pausa · H8 · la barra lateral")
from core import timeclock_ui as TU                                        # noqa: E402
from core import clock as CK                                               # noqa: E402
_OB = {"PRJ-F": {"ID": "PRJ-F", "Status": "Planned", "StartDate": "2026-11-16"},
       "PRJ-H": {"ID": "PRJ-H", "Status": "On hold", "StartDate": "2026-10-01"},
       "PRJ-1": {"ID": "PRJ-1", "Status": "In progress", "StartDate": "2026-11-02"},
       "PRJ-0": {"ID": "PRJ-0", "Status": "Planned", "StartDate": "2026-11-15"}}
_d = [_sustituir(P, get_project=lambda pid: dict(_OB.get(pid, {}))), _sustituir(CK, today=lambda *a, **k: date(2026, 11, 15))]
try:
    _nf, _nh, _n1, _n0 = (TU.nota_obra(x, "G") for x in ("PRJ-F", "PRJ-H", "PRJ-1", "PRJ-0"))
finally:
    for x in _d:
        x()
chk("una que empieza mañana: «This job starts on Mon 16/11/2026»", "This job starts on Mon 16/11/2026" in _nf, _nf)
chk("una en pausa: «This job is on hold»", "This job is on hold" in _nh, _nh)
chk("una en marcha, o que empieza HOY: nada", _n1 == "" and _n0 == "", (_n1, _n0))
_n, _fi = funcion("core/timeclock_ui.py", "_fichar")
_n2, _rt = funcion("core/timeclock_ui.py", "render_timeclock_tab")
chk("se dice al fichar (lateral y pantalla: `_fichar`) y al cambiar de obra («Switch»)",
    "_nota = nota_obra(pid, grupo)" in _fi and "flash.aviso(_nota)" in _fi and "flash.aviso(nota_obra(_nuevo, grupo))" in _rt)
FICH = r'''
import datetime as dt
import streamlit as st
from core import timeclock_ui as TU, timeclock as TC, flash, projects as P, clock
clock.today = lambda *a, **k: dt.date(2026, 11, 15)
P.get_project = lambda pid: {"ID": pid, "Status": "Planned", "StartDate": "2026-11-16"}
TC.fichar_proyecto = lambda *a, **k: (True, "✅ Clocked in to C3 at 16:58.", False)
st.session_state.setdefault("_AVS", [])
flash.aviso = lambda m: st.session_state["_AVS"].append(m)
TU._armar_aviso_prestart = lambda *a, **k: None
if st.button("go", key="go"):
    TU._fichar("Bobo", "C3", "G", "bobo", "PRJ-44")
'''
at = AppTest.from_string(FICH, default_timeout=60)
at.run()
at.button(key="go").click().run()
chk("fichar en ella deja el aviso (sin bloquear: ficha igual)", any("This job starts on Mon 16/11/2026" in x
                                                                   for x in at.session_state["_AVS"]), list(at.session_state["_AVS"]))
LAT = r'''
import streamlit as st
from core import timeclock_ui as TU
TU._chrono_mini = lambda *a, **k: None
TU._chip_prestart = lambda *a, **k: None
TU._chip_falsecar = lambda *a, **k: None
GEN = {"clock_in": "2026-11-15 16:58:00"}
PRJ = ({"proyecto": "C3 — Harbour Lifts — Lift 3", "clock_in": "2026-11-15 16:58:00", "proyecto_id": "PRJ-0044"}
       if st.session_state.get("_PRJ", True) else None)
TU._sidebar_fichado("Bobo", "bobo", "G", GEN, PRJ)
'''
at = AppTest.from_string(LAT, default_timeout=60)
at.run()
_cap = " ¦ ".join(c.value for c in at.caption)
chk("H8 · fichado en una obra: «C3 — Harbour Lifts — Lift 3 · since 16:58»",
    "C3 — Harbour Lifts — Lift 3 · since 16:58" in _cap, _cap)
at = AppTest.from_string(LAT, default_timeout=60)
at.session_state["_PRJ"] = False
at.run()
chk("…y solo con la jornada: «Workday, no project · since 16:58»", "Workday, no project · since 16:58"
    in " ".join(c.value for c in at.caption))

# ═════════════════════════════════════════════════════════════════════════════
print("10. Lo visto verificando v676 en producción")
from core import roster as R                                               # noqa: E402
from core import roster_ui as RU                                           # noqa: E402
from core import flash as FL                                               # noqa: E402
_LV = {"items": [{"a": "LEAVE", "i": "07:00", "f": "15:30"}], "nota": "Sick leave · AUS-0009"}
_TR = {"items": [{"a": "PRJ-1", "i": "07:00", "f": "15:30"}], "nota": ""}
chk("una celda de AUSENCIA, con su nota, no abre el fin de semana (la semana del 30/11)",
    R.dias_con_datos({"ana": {"sab": dict(_LV), "dom": dict(_LV)}}) == R.DIAS)
chk("…una de trabajo, o una nota en un día vacío, sí", R.dias_con_datos({"ana": {"sab": dict(_TR)}}) == R.DIAS + ["sab"]
    and R.dias_con_datos({"ana": {"dom": {"items": [], "nota": "van"}}}) == R.DIAS + ["dom"])
chk("…y con la misma regla se puede cerrar la columna (`dia_tiene_datos`)",
    R.dia_tiene_datos({"ana": {"sab": dict(_LV)}, "beto": {"sab": dict(_TR)}}, "sab") == ["beto"])
_FE = []
_d = [_sustituir(R, limpiar_proyecto=lambda g, pid, usuarios=None, desde=None: 40),
      _sustituir(P, get_project=lambda pid: {"ID": pid, "Name": "C1 — Lift 1"}),
      _sustituir(CK, today=lambda *a, **k: date(2026, 11, 15)), _sustituir(FL, exito=lambda m: _FE.append(m))]
try:
    RU._liberar_cerrada("G", "PRJ-0039")
finally:
    for x in _d:
        x()
chk("liberar una obra cerrada lo dice con su NOMBRE: «C1 — Lift 1 (PRJ-0039): 40 day(s) freed…»",
    _FE == ["C1 — Lift 1 (PRJ-0039): 40 day(s) freed on the board from 16/11/2026."], _FE)
_n, _cc = funcion("core/roster_ui.py", "_confirmar_copia")
_n2, _lt = funcion("core/projects_ui.py", "_liberar_tablero_obra")
chk("«Not copied (the job is closed)» y la lista de cierre, también con el nombre",
    "{_np.get(pid) or pid} ({pid})" in _cc and 'p=f"{_nom} ({pid})" if _nom else pid' in _lt)

# devolver lo real (trampa 48)
TC._get_worksheet, TC._now, TC._invalidate_records = _ORIG["get_ws"], _ORIG["now"], _ORIG["inv"]
CO.registrar, CO.aprobar, CO.nomina_que_cubre, TC.anadir_jornada = _ORIG["reg"], _ORIG["apr"], _ORIG["nqc"], _ORIG["aj"]

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
if FALLOS:
    print("FALLOS:", FALLOS)
sys.exit(1 if FALLOS else 0)
