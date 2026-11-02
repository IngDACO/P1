# -*- coding: utf-8 -*-
"""v623 · RECORRIDO DEL CAMPO: PRE-START (01/11/2026, «Dale con todo incluido lo recomendado»).

  (1) ⚠️ Los datos pasaban de una obra a otra: respuestas, notas, ubicación y firmas, con el botón activo
      (medido: se generaba el de la B sin tocar nada) → el formulario es de una obra y una generación;
  (2) ⚠️ un near miss sin descripción, y una alarma que fallaba en silencio;
  (3) ⚠️ la fecha se podía cambiar → el campo, siempre hoy; la oficina, hacia atrás;
  (4) ⚠️ firmar tarde: sin login, «anexo añadido» aunque fallara, y un documento muerto en «Files»;
  (5) ⚠️ el historial bajaba todos los PDF al abrir la pantalla;
  (6)-(7) la charla hecha se dice arriba, y el resultado no se va al primer toque;
  (8) «Do it now» lleva a la obra de la que habla; (9) fechas DD/MM/YYYY y cifras activas;
  (10) texto escapado y traducible; (11) menos alto en el móvil; (12) el PDF lleva su número.
⚠️ Lo aprendido en v620: nada de estado preparado a mano. Se cambia de obra y se genera con clics.
Sin red ni hoja real.
"""
import datetime
import inspect
import io
import json
import os
import re
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": "field",
                            "grupo": "cliente1"}
from core import clock, prestart as PS                            # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


HOY = datetime.date(2026, 11, 1)
AYER = HOY - datetime.timedelta(days=1)
clock.today = lambda *a: HOY
clock.now = lambda *a: datetime.datetime(2026, 11, 1, 7, 0)


class Hoja:
    def __init__(self, filas=None):
        self.filas, self.altas, self.celdas = filas or [], [], []

    def get_all_records(self, **k):
        return self.filas

    def append_row(self, fila, **k):
        self.altas.append(fila)

    def update_cell(self, r, c, v):
        self.celdas.append((r, c, v))


BASE = {"grupo": "cliente1", "proyecto_id": "PRJ-1", "proyecto_nombre": "Obra A", "fecha": HOY, "hora": "07:00",
        "location": "Calle A", "facilitador": "installer CI 1", "activities_notes": "", "s1": {"permisos": "YES"},
        "near_miss": "NO", "near_miss_desc": "", "s3": {"cages": "YES"}, "general_notes": "",
        "attendees": [{"name": "installer CI 1", "initial": "IC", "sig": None}], "creado_por": "installer"}


def monta(filas=None):
    h = Hoja(filas)
    PS._ws = lambda: h
    PS._records = lambda: h.filas
    PS._invalidate = lambda: None
    PS._next_id = lambda recs: "PS-0009"
    return h


from core import drive_store, projects as P                       # noqa: E402

sec("1. ⚠️ El motor")
h = monta()
r = PS.submit({**BASE, "near_miss": "YES"})
chk("⚠️ un near miss sin descripción no se registra", not r["ok"] and "Describe" in r["error"] and not h.altas, r)
r = PS.submit({**BASE, "fecha": AYER, "gestor": False})
chk("⚠️ el campo no registra otro día", not r["ok"] and "today" in r["error"] and not h.altas, r)
r = PS.submit({**BASE, "fecha": HOY + datetime.timedelta(days=1), "gestor": False})
chk("…ni un día futuro", not r["ok"], r)
_ayer_fila = {"ID": "PS-0001", "ProjectID": "PRJ-1", "Date": AYER.isoformat(), "FacilitatedBy": "Otro"}
h = monta([_ayer_fila])
r = PS.submit({**BASE, "fecha": AYER})
chk("la oficina tampoco repite el de OTRO día (el aviso miraba solo hoy)", not r["ok"] and r["ya_hay"] == "PS-0001", r)
h = monta()
PS._ws = lambda: None
_llamado = []
import core.prestart_pdf as PDF                                    # noqa: E402
_real_pdf = PDF.generate_prestart_pdf
PDF.generate_prestart_pdf = lambda d: _llamado.append(d) or b"%PDF"
drive_store.is_available = lambda: False
r = PS.submit(BASE)
chk("⚠️ sin hoja no se genera el PDF: no queda un archivo sin registro", not r["ok"] and not _llamado, r)
h = monta()
r = PS.submit(BASE)
chk("el PDF recibe su número", r["ok"] and _llamado and _llamado[-1].get("id") == "PS-0009", r)
PDF.generate_prestart_pdf = _real_pdf
_pdf = PDF.generate_prestart_pdf({**BASE, "id": "PS-0009"})
from pypdf import PdfReader                                        # noqa: E402
chk("⚠️ …y se LEE en el documento", "PS-0009" in PdfReader(io.BytesIO(_pdf)).pages[0].extract_text())

sec("2. ⚠️ Firmar tarde")
_F = {"ID": "PS-0009", "ProjectID": "PRJ-1", "Date": HOY.isoformat(), "Attendees": "[]", "DriveID": "VIEJO",
      "File": "a.pdf", "Location": "", "FacilitatedBy": "x"}
h = monta([dict(_F)])
_rec, _bor = [], []
drive_store.is_available = lambda: True
drive_store.download = lambda d: _pdf
drive_store.upload = lambda *a, **k: "NUEVO"
drive_store.delete = lambda d: _bor.append(d)
P.add_document = lambda *a, **k: None
P.delete_document_record = lambda pid, did: _rec.append((pid, did)) or (True, "")
r = PS.firmar("PS-0009", "cliente1", "Mei Chen", "MC", None, "mei1")
_asist = json.loads(next(c[2] for c in h.celdas if str(c[2]).startswith("[")))
chk("⚠️ la firma tardía guarda el LOGIN", _asist[-1].get("usuario") == "mei1", _asist)
chk("⚠️ con dos «Mei Chen», la que no firmó sigue pendiente",
    bool(PS.pendiente_de_firma("PRJ-1", "cliente1", "Mei Chen", "mei2")) if not h.filas.__setitem__(0, {**_F, "Attendees": json.dumps(_asist)}) else False)
chk("…y la que firmó, no", not PS.pendiente_de_firma("PRJ-1", "cliente1", "Mei Chen", "mei1"))
chk("dice que quedó archivado", r["ok"] and r["archivado"] is True, r)
chk("⚠️ la línea del documento viejo se va (quedaba muerta en «Files»)", _rec == [("PRJ-1", "VIEJO")], _rec)
chk("…y su archivo", _bor == ["VIEJO"], _bor)
h = monta([dict(_F)])
drive_store.is_available = lambda: False
r = PS.firmar("PS-0009", "cliente1", "Mei Chen", "MC", None, "mei1")
chk("⚠️ sin archivar lo dice: la firma consta pero el PDF no", r["ok"] and r["archivado"] is False, r)

from streamlit.testing.v1 import AppTest                           # noqa: E402

GUION = r'''
import sys, json
from datetime import date, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import prestart as PS, prestart_ui as U, clock, timeclock as T, flash, auth, drive_store
E = st.session_state["_esc"]
st.session_state["auth"] = {"usuario": "installer", "nombre": "installer CI 1", "rol": E.get("rol", "field"), "grupo": "cliente1"}
clock.today = lambda *a: date(2026, 11, 1)
clock.now = lambda *a: datetime(2026, 11, 1, 7, 0)
PS.is_configured = lambda: True
_F = E["filas"]
PS._records = lambda: _F
U._projects_for = lambda *a: E["obras"]
T.open_sessions = lambda *a, **k: {T.TIPO_GENERAL: None, T.TIPO_PROYECTO: None}
T.proyectos_por_usuario_dia = lambda *a: {}
auth.list_users = lambda **k: [{"User": "installer", "Name": "installer CI 1"}]
auth.etiqueta_usuarios = lambda u: {"installer": "installer CI 1"}
def _bajar(d):
    st.session_state["_bajados"] = st.session_state.get("_bajados", 0) + 1
    return b"x"
drive_store.download = _bajar
def _sub(d):
    st.session_state["_enviado"] = {k: (str(v) if k == "fecha" else v) for k, v in d.items() if k != "attendees"}
    _F.append({"ID": "PS-0009", "ProjectID": d["proyecto_id"], "Date": str(d["fecha"]), "Time": "07:00", "FacilitatedBy": d["facilitador"],
               "Attendees": json.dumps([{"name": "installer CI 1", "usuario": "installer"}]), "S1JSON": "{}", "S3JSON": "{}", "DriveID": "D1", "File": "a.pdf"})
    return {"ok": True, "id": "PS-0009", "pdf": b"x", "filename": "01112026 IC.pdf", "drive_id": "D1", "alarma": E.get("alarma", False),
            "alarma_checks": False, "checks_no": [], "error": ""}
PS.submit = _sub
U._canvas_disponible = lambda: None
flash.mostrar()
U.render_prestart_tab()
'''
_OBRAS = [{"ID": "PRJ-1", "Name": "Obra A", "Group": "cliente1", "Location": "Calle A", "FieldAssigned": "installer"},
          {"ID": "PRJ-2", "Name": "Obra B", "Group": "cliente1", "Location": "Calle B", "FieldAssigned": "installer"}]


def pinta(filas=None, **esc):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_esc"] = {"filas": filas if filas is not None else [], "obras": _OBRAS, **esc}
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def radio(at, trozo):
    return next(r for r in at.radio if trozo in r.key)


def boton(at, trozo):
    return next((b for b in at.button if trozo in b.key), None)


def responde(at, nm="NO"):
    for r in at.radio:
        if "_s1_" in r.key or "_s3_" in r.key:
            r.set_value("YES")
    radio(at, "ps_nm_").set_value(nm)
    return at


sec("3. ⚠️ Cambiar de obra (con clics)")
at = pinta()
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
responde(at)
next(a for a in at.text_area if "ps_act_" in a.key).set_value("Notas de la A")
at.run()
chk("en la A, todo respondido: se puede generar", boton(at, "ps_submit").disabled is False)
at.selectbox(key="ps_proy").set_value("Obra B (PRJ-2)").run()
chk("⚠️ en la B las respuestas están VACÍAS", all(r.value is None for r in at.radio if "_s1_" in r.key or "_s3_" in r.key or "ps_nm_" in r.key),
    [(r.key, r.value) for r in at.radio])
chk("⚠️ las notas de la A no pasan", next(a for a in at.text_area if "ps_act_" in a.key).value == "")
chk("⚠️ la ubicación es la de la B (se quedaba la de la A)", next(i for i in at.text_input if "ps_loc_" in i.key).value == "Calle B")
chk("⚠️ y NO se puede generar sin responder", boton(at, "ps_submit").disabled is True)
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
# Streamlit descarta lo que deja de pintarse: quien vuelve, revisa otra vez. En un registro de
# seguridad es lo que se quiere, y queda dicho aquí para que nadie lo «arregle».
chk("al volver a la A también empieza de cero: se revisa otra vez", radio(at, "_s1_").value is None)
_kk = [k for x in (list(at.radio) + list(at.text_area) + list(at.text_input)) for k in [x.key] if k and k != "ps_proy"]
chk("toda clave del formulario lleva la obra", all("PRJ-" in k for k in _kk), [k for k in _kk if "PRJ-" not in k])
_src = open(os.path.join(RAIZ, "core", "prestart_ui.py"), encoding="utf-8").read()
chk("⚠️ …y la firma también", 'st_canvas(key=f"ps_firma_{kp}_{_k}"' in _src and 'st_canvas(key=f"ps_firma_tarde_{_pid}"' in _src)

sec("4. ⚠️ Generar")
at = pinta()
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
responde(at).run()
next(i for i in at.text_input if "ps_att_ini" in i.key).set_value("IC")
at.run()
boton(at, "ps_submit").click().run()
chk("se envió con la fecha de hoy, aunque nadie pueda elegirla", at.session_state["_enviado"]["fecha"] == "2026-11-01", at.session_state["_enviado"])
chk("⚠️ y como campo", at.session_state["_enviado"]["gestor"] is False)
chk("el aviso de éxito", any("PS-0009" in s.value for s in at.success), [s.value for s in at.success])
chk("⚠️ con la charla hecha, el formulario se oculta", not any("_s1_" in r.key for r in at.radio), [r.key for r in at.radio])
at.run()
chk("⚠️ el resultado NO se va al siguiente toque", any("PS-0009" in s.value for s in at.success), [s.value for s in at.success])
chk("la casilla de la segunda charla está", any("ps_forzar_" in c.key for c in at.checkbox))
next(c for c in at.checkbox if "ps_forzar_" in c.key).check().run()
chk("⚠️ el formulario de una segunda charla nace VACÍO", all(r.value is None for r in at.radio if "_s1_" in r.key), [(r.key, r.value) for r in at.radio])
at.selectbox(key="ps_proy").set_value("Obra B (PRJ-2)").run()
chk("en otra obra no sale el resultado de la A", not any("PS-0009" in s.value for s in at.success))
# ⚠️ La generación solo se nota cuando el formulario SIGUE a la vista (al ocultarse, Streamlit ya lo
# vacía): la oficina que registra una charla de otro día. Lo destapó romper_v623.
at = pinta(rol="administrator")
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
next(d for d in at.date_input if "ps_fecha_" in d.key).set_value(AYER)
at.run()
responde(at).run()
next(i for i in at.text_input if "ps_att_ini" in i.key).set_value("IC")
at.run()
boton(at, "ps_submit").click().run()
chk("la oficina registró la de ayer", at.session_state["_enviado"]["fecha"] == AYER.isoformat(), at.session_state["_enviado"])
chk("⚠️ el formulario sigue a la vista y nace VACÍO: otra charla no hereda esta",
    any("_s1_" in r.key for r in at.radio) and all(r.value is None for r in at.radio if "_s1_" in r.key),
    [(r.key, r.value) for r in at.radio])
at = pinta(alarma=False)
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
responde(at, nm="YES").run()
chk("⚠️ YES sin descripción no deja generar", boton(at, "ps_submit").disabled is True)
chk("…y dice qué falta", any("describe the near miss" in c.value for c in at.caption), [c.value[:90] for c in at.caption])
next(a for a in at.text_area if "ps_nmdesc_" in a.key).set_value("Tablón suelto en el nivel 4")
at.run()
next(i for i in at.text_input if "ps_att_ini" in i.key).set_value("IC")
at.run()
boton(at, "ps_submit").click().run()
chk("⚠️ si la alarma falla, se dice (era silencioso)", any("could NOT be opened" in e.value for e in at.error), [e.value for e in at.error])

sec("5. ⚠️ La fecha")
at = pinta()
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
_d = next(d for d in at.date_input if "ps_fecha_" in d.key)
chk("⚠️ el campo no puede cambiarla", _d.disabled is True and str(_d.value) == "2026-11-01", (_d.disabled, _d.value))
at = pinta(rol="administrator")
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
_d = next(d for d in at.date_input if "ps_fecha_" in d.key)
chk("la oficina sí", _d.disabled is False)
chk("⚠️ pero no a un día futuro", "max_value=hoy" in _src)

sec("6. La charla de hoy ya está")
_HECHA = [{"ID": "PS-0007", "ProjectID": "PRJ-1", "Date": "2026-11-01", "Time": "06:30", "FacilitatedBy": "Ana <b>*x*</b>",
           "Attendees": json.dumps([{"name": "installer CI 1", "usuario": "installer"}]), "S1JSON": "{}", "S3JSON": "{}",
           "DriveID": "D7", "File": "h.pdf"}]
at = pinta(list(_HECHA))
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
_t = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
chk("⚠️ se dice arriba, sin formulario", "already on it" in _t and not any("_s1_" in r.key for r in at.radio), _t[:200])
chk("con su número y quién", "PS-0007" in _t and r"\*x\*" in _t, _t[:300])
chk("⚠️ abrir la pantalla no baja ningún PDF", "_bajados" not in at.session_state, at.session_state["_bajados"] if "_bajados" in at.session_state else 0)

sec("7. ⚠️ El historial")
_MUCHAS = [{"ID": "PS-%04d" % i, "ProjectID": "PRJ-1", "Date": "2026-10-%02d" % i, "Time": "07:00", "FacilitatedBy": "Ana",
            "NearMiss": "YES" if i == 3 else "NO", "NearMissDesc": "cae *algo* $5" if i == 3 else "", "ActivityNotes": "nota *a*",
            "Attendees": "[]", "S1JSON": json.dumps({"permisos": "NO" if i == 5 else "YES"}), "S3JSON": "{}", "DriveID": "D%d" % i, "File": "f.pdf"}
           for i in range(1, 14)]
at = pinta(list(_MUCHAS))
at.selectbox(key="ps_proy").set_value("Obra A (PRJ-1)").run()
chk("⚠️ 13 charlas con PDF: ninguna descarga al pintar", "_bajados" not in at.session_state,
    at.session_state["_bajados"] if "_bajados" in at.session_state else 0)
_e = [x for x in list(at.expander) + list(at.status) if "2026" in x.label]
chk("de entrada se ven 10", len(_e) == 10, len(_e))
chk("⚠️ las fechas en DD/MM/YYYY", all(re.search(r"\d\d/10/2026", x.label) for x in _e) and not any("2026-10" in x.label for x in _e), [x.label for x in _e][:2])
boton(at, "ps_hist_mas").click().run()
_e = [x for x in list(at.expander) + list(at.status) if "2026" in x.label]
chk("…y el resto, a un toque", len(_e) == 13, len(_e))
boton(at, "cpxkpi_ps_nm").click().run()
_e = [x for x in list(at.expander) + list(at.status) if "2026" in x.label]
chk("⚠️ «With near miss» filtra", len(_e) == 1 and "03/10/2026" in _e[0].label, [x.label for x in _e])
chk("⚠️ el texto escrito va escapado", any(r"cae \*algo\* \$5" in x.value for x in at.error), [x.value for x in at.error])
boton(at, "cpxkpi_ps_no").click().run()
_e = [x for x in list(at.expander) + list(at.status) if "2026" in x.label]
chk("«With NO checks» filtra", len(_e) == 1 and "05/10/2026" in _e[0].label, [x.label for x in _e])
boton(at, "cpxkpi_ps_todas").click().run()
_e = [x for x in list(at.expander) + list(at.status) if "2026" in x.label]
chk("«Recorded» vuelve a todas", len(_e) == 13, len(_e))

sec("8. Lo que queda escrito")
from core import timeclock_ui as TU                                # noqa: E402
_tc = open(os.path.join(RAIZ, "core", "timeclock_ui.py"), encoding="utf-8").read()
_hu = open(os.path.join(RAIZ, "core", "home_ui.py"), encoding="utf-8").read()
chk("⚠️ `_ir_a_prestart` deja pedida la obra", "_ps_proy_pending" in inspect.getsource(TU._ir_a_prestart))
chk("⚠️ nadie la llama sin decir qué obra", "_ir_a_prestart()" not in _tc + _hu, re.findall(r".{30}_ir_a_prestart\(\)", _tc + _hu))
# ⚠️ v636 · `_nom =`: el de la banda del false car es otro, y con la búsqueda vieja tapaba a este
chk("el banner escapa el nombre de la obra", "_nom = _html.escape(str(prj.get(" in _hu)
_s2 = re.sub(r'""".*?"""', "", _src, flags=re.S)
chk("ningún aviso armado con f-string sin `t()`", not re.search(r'st\.(success|warning|error|info)\(f"|flash\.\w+\(f"', _s2),
    re.findall(r'st\.\w+\(f"[^\n]{0,50}', _s2)[:3])
chk("la cabecera, 2 + 2 también en el móvil", 'theme.por_fila("cpx_ps_cab", 2)' in _src)
chk("lo pendiente, por sección", 'section 1: {n} to answer' in _src)
# (v624 · visto verificando v623: a 859 px con el menú, 17 px de la firma quedaban cortados)
chk("⚠️ la columna de la firma cabe el lienzo: [1, 2] en los dos sitios",
    _src.count("c1, c2 = st.columns([1, 2])") == 2 and "st.columns([2, 3])" not in _src)

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
