# -*- coding: utf-8 -*-
"""v636 · DAILY FALSE CAR CHECKLIST (02/11/2026, con la foto del formato de CI Liftworx delante).

Decisiones del usuario: se marca al crear la obra (pregunta obligatoria, también desde cotización); se
exige desde que el false car está montado hasta que se retira; uno por obra y día, lo hace el primero y
los demás lo firman; ✓ o X, sin respuesta por defecto y con X las observaciones son obligatorias; una X
abre alarma y la pantalla dice que no se use; avisa, no bloquea; si faltan los dos, primero el Pre-Start.
Y además, también para el Pre-Start: en el Handover, y una lista de oficina con los días sin registro.

Lo que protege, SIN la hoja real (hojas, Drive y alarmas sustituidos; el módulo, el PDF y las pantallas, REALES):
  (a) el formato: los 18 puntos con su texto literal, y un PDF de verdad con ✓ y X (un cuadro negro no vale);
  (b) quién lo necesita y qué días: lo dicen el plan sellado y lo MARCADO, no el calendario;
  (c) guardar: todo respondido, X con observaciones, uno al día, el campo solo hoy, UNA alarma;
  (d) firmar después: anexo, sin rehacer el documento firmado;
  (e) los días sin registro, por obra y día, hasta ayer;
  (f) el Handover: siguen siendo trece, más el del false car solo si lo lleva;
  (g) la hoja: en el lote, se borra con la obra, y borrar no la crea;
  (h) las pantallas, con clics: el alta, el formato, la sección Pre-Start y los avisos en su orden.
"""
import ast
import datetime as dt
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
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"}

from pypdf import PdfReader                                       # noqa: E402
from streamlit.testing.v1 import AppTest                          # noqa: E402

from core import alerts, chat_agent as CA, clock, drive_store as DS, falsecar as FC   # noqa: E402
from core import falsecar_pdf as FP, handover as HO, hojas as H, prestart as PS       # noqa: E402
from core import prestart_pdf as PP, projects as P, projects_ui as PU                 # noqa: E402
from core import stage_progress as SP, stages as S, timeclock as TC                   # noqa: E402

n_ok, fallos = 0, []


def chk(q, cond, det=""):
    global n_ok
    if cond:
        n_ok += 1
        print("   ok   %s" % q)
    else:
        fallos.append(q)
        print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def leer(rel):
    with open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def funcion(fuente, nombre):
    arbol = ast.parse(fuente)
    return next((ast.get_source_segment(fuente, n) for n in ast.walk(arbol)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), "")


class HojaFalsa:
    def __init__(self, cab):
        self.cab, self.filas, self.falla = list(cab), [], False

    def get_all_records(self, **k):
        return [dict(zip(self.cab, f + [""] * (len(self.cab) - len(f)))) for f in self.filas]

    def append_row(self, fila, value_input_option=None):
        if self.falla:
            raise RuntimeError("sin red")
        assert value_input_option == "RAW" and len(fila) == len(self.cab), fila
        self.filas.append([str(x) for x in fila])

    def update_cell(self, f, c, v):
        self.filas[f - 2][c - 1] = str(v)

    def delete_rows(self, n):
        del self.filas[n - 2]


HOY = dt.date(2026, 11, 2)
clock.today = lambda *a: HOY
clock.now = lambda *a: dt.datetime(2026, 11, 2, 7, 15)

_ALARMAS, _DOCS, _SUBIDOS, _BORRADOS, _QUITADOS, _CRED, _PS = [], [], {}, [], [], {}, []
_W = HojaFalsa(FC.HEADERS)
FC._ws = lambda: _W
FC._records = lambda: _W.get_all_records()
FC._invalidate = lambda: None
H.siguiente_id_libre = lambda pref, n, propia=None, ancho=4: "%s%04d" % (pref, n + 1)
DS.is_available = lambda: True


def _sube(pid, nombre, datos, mime="application/pdf"):
    _id = "DRV-%d" % (len(_SUBIDOS) + 1)
    _SUBIDOS[_id] = datos
    return _id


DS.upload = _sube
DS.download = lambda i: _SUBIDOS[i]
DS.delete = lambda i: _BORRADOS.append(i) or True
P.add_document = lambda *a, **k: _DOCS.append(a) or (True, "")
P.delete_document_record = lambda pid, did: _QUITADOS.append((pid, did)) or (True, "")
alerts.report_problem = lambda *a: _ALARMAS.append(a) or (True, "AL-1")
SP.creditos = lambda pid, etapa=None: _CRED.get(pid, [])
PS._records = lambda: _PS


def obra(pid="PRJ-1", fc=True, tipo="Installation"):
    return {"ID": pid, "Name": "Obra " + pid, "Group": "cliente1",
            "StagePlanJSON": P.plan_nuevo(tipo, S.FALSE_CAR if fc else ())}


def credito(act, pct=100, dia="2026-10-20"):
    return {"Activity": act, "Pct": str(pct), "WorkDate": dia, "Updated": dia + " 10:00:00"}


def todo_bien():
    return {k: {"res": FC.PASA, "nota": ""} for k, _x in FC.CHECKS}


def datos(**k):
    return {"grupo": "cliente1", "proyecto_id": "PRJ-1", "proyecto_nombre": "Obra PRJ-1", "fecha": HOY,
            "hora": "07:15", "resultados": todo_bien(), "nombre": "Field Test", "iniciales": "FT",
            "firma": None, "usuario": "campo000", "gestor": False, **k}


# ═════════════════════════════════════════════════════════════════
sec("1. El catálogo: las tres actividades y la pregunta")
_cond = [c["nombre"] for c in S.condicionales()]
chk("las tres existen en el catálogo como condicionales", all(a in _cond for a in S.FALSE_CAR), _cond)
chk("instalación lo admite, también Ripout + Installation",
    S.admite_false_car("Installation") and S.admite_false_car("Ripout + Installation"))
chk("⚠️ un Ripout no", not S.admite_false_car("Ripout") and not S.admite_false_car(""))
chk("⚠️ no es un grupo excluyente: un alta por programa no se para", "false_car" not in S.EXCLUYENTES
    and S.falta_por_decidir("Installation", ()) == [])
_nombres = lambda pl: [a["nombre"] for e in pl for a in e["actividades"]]    # noqa: E731
_con = _nombres(S.plan_de("Installation", S.FALSE_CAR))
_sin = _nombres(S.plan_de("Installation", ()))
chk("con Yes, el plan lleva las tres", all(a in _con for a in S.FALSE_CAR), len(_con))
chk("con No, ninguna", not any(a in _sin for a in S.FALSE_CAR))
_pl = lambda c: sum(a["peso_en_obra"] for e in S.plan_de("Installation", c) for a in e["actividades"])   # noqa: E731
chk("⚠️ el plan sigue sumando 100, con y sin él", abs(_pl(S.FALSE_CAR) - 100) < 0.5 and abs(_pl(()) - 100) < 0.5, (_pl(S.FALSE_CAR), _pl(())))

sec("2. El formato, literal")
chk("18 puntos, numerados en orden", [k for k, _x in FC.CHECKS] == ["fc%02d" % i for i in range(1, 19)])
_T = dict(FC.CHECKS)
chk("el 1, literal", _T["fc01"] == "Check whether the steel wire rope is securely fixed.")
chk("el 9, con sus DOS frases", _T["fc09"] == "Run 3-5 times without load and check whether the hoist travels up and down correctly\n"
    "Check whether there is any abnormal noises, odor, or overheating in the hoist.")
chk("el 14, literal", _T["fc14"] == "Whether the manual descent is normal (Brake Release).")
chk("el 18, literal", _T["fc18"] == "A safety lock with power outage protection, manually locking the safety lock, the platform should not be able to operate.")
chk("título y subtítulo del papel", FC.TITULO == "Daily False Car Checklist"
    and FC.SUBTITULO == "Daily inspections are to be carried out according to the following schedule.")
chk("⚠️ ✓ si pasa y X si no (decisión del usuario)", FC.SIMBOLO == {"pass": "✓", "fail": "X"})

sec("3. Quién lo necesita y qué días")
chk("⚠️ la obra creada con Yes lo tiene", FC.tiene(obra()))
chk("creada con No, no", not FC.tiene(obra(fc=False)))
chk("⚠️ una obra ya creada, sin plan: como si no tuviera (decisión del usuario)", not FC.tiene({"ID": "PRJ-9"}) and not FC.tiene({}))
chk("plan ilegible: no revienta", not FC.tiene({"StagePlanJSON": "{x"}))
_CRED["PRJ-1"] = []
chk("⚠️ sin montar, no se exige", not FC.activo(obra()))
_CRED["PRJ-1"] = [credito(S.FC_MONTAR, 50)]
chk("⚠️ a medio montar, tampoco", not FC.activo(obra()))
_CRED["PRJ-1"] = [credito(S.FC_MONTAR)]
chk("⚠️ montado al 100 %, sí", FC.activo(obra()))
chk("...desde el día de trabajo que se marcó", FC.periodo(obra()) == (dt.date(2026, 10, 20), None), FC.periodo(obra()))
chk("el día anterior al montaje, no", not FC.activo(obra(), dt.date(2026, 10, 19)))
chk("ese mismo día, sí", FC.activo(obra(), dt.date(2026, 10, 20)))
_CRED["PRJ-1"] = [credito(S.FC_MONTAR, 0)]
chk("⚠️ si se desmarca el montaje (Pct 0), deja de exigirse", not FC.activo(obra()))
_CRED["PRJ-1"] = [credito(S.FC_MONTAR), credito(S.FC_RETIRAR, 100, "2026-10-30")]
chk("⚠️ retirado, ya no", not FC.activo(obra()))
chk("hasta el día anterior a retirarlo, sí", FC.activo(obra(), dt.date(2026, 10, 29)))
chk("el día de la retirada, no", not FC.activo(obra(), dt.date(2026, 10, 30)))
_CRED["PRJ-1"] = [credito(S.FC_MONTAR), credito(S.FC_RETIRAR, 40, "2026-10-30")]
chk("retirada a medias: se sigue exigiendo", FC.activo(obra()))
_CRED["PRJ-2"] = [credito(S.FC_MONTAR)]
chk("⚠️ el Sky lock no cuenta como montado", (lambda: (_CRED.__setitem__("PRJ-2", [credito(S.FC_LOCK)]), not FC.activo(obra("PRJ-2")))[1])())
chk("con No no se exige aunque alguien marque la actividad", not FC.activo(obra(fc=False)))

sec("4. Lo que exige el formato")
_r = todo_bien()
chk("todo respondido y bien: nada que pedir", FC.valida(_r) == "")
chk("⚠️ nada respondido: los 18", "18" in FC.valida({}), FC.valida({}))
_r2 = todo_bien()
_r2["fc07"] = {"res": None, "nota": ""}
chk("⚠️ uno sin responder: no pasa", "1" in FC.valida(_r2) and FC.valida(_r2) != "", FC.valida(_r2))
_r3 = todo_bien()
_r3["fc05"] = {"res": FC.FALLA, "nota": "   "}
chk("⚠️ X sin observaciones: no pasa, y dice cuál", "5" in FC.valida(_r3), FC.valida(_r3))
_r3["fc05"]["nota"] = "cable pisado"
chk("con observaciones, sí", FC.valida(_r3) == "")

sec("5. ⚠️ Guardar, con el PDF de verdad")
_ALARMAS.clear()
r1 = FC.submit(datos())
_f = _W.filas[0] if _W.filas else []
chk("guarda con ID FC-0001", r1["ok"] and r1["id"] == "FC-0001", r1)
chk("con obra, grupo, fecha y hora", _f[:5] == ["FC-0001", "PRJ-1", "cliente1", "2026-11-02", "07:15"], _f[:5])
chk("sin alarma si todo pasa", _ALARMAS == [] and r1["fallos"] == [] and _f[FC.HEADERS.index("Failed")] == "")
chk("⚠️ la firma no va a la hoja, solo QUE firmó", json.loads(_f[FC.HEADERS.index("Signers")])[0] == {"name": "Field Test", "initial": "FT", "firmado": False, "hora": "07:15", "usuario": "campo000"}, _f[7])
chk("se archiva en Files con su tipo", _DOCS and _DOCS[-1][2] == "falsecar" and _DOCS[-1][0] == "PRJ-1", _DOCS)
chk("el nombre del fichero lo distingue del Pre-Start", r1["filename"] == "02112026 False Car FT.pdf", r1["filename"])
_rd = PdfReader(io.BytesIO(_SUBIDOS[r1["drive_id"]]))
_txt = _rd.pages[0].extract_text()
chk("⚠️ el PDF, en UNA página como el papel", len(_rd.pages) == 1, len(_rd.pages))
chk("con todos los rótulos del papel", all(x in _txt for x in ("Daily False Car Checklist", "Inspection items", "Inspection results", "Remarks",
    "Name of person conducting daily check", "Signature", "Date of Daily Check", "02/11/2026")), _txt[:300])
chk("la marca es la empresa, con la obra y el número", "cliente1" in _txt and "Obra PRJ-1" in _txt and "FC-0001" in _txt)
chk("⚠️ los 18 ✓, como carácter (con el byte, reportlab pinta un cuadro negro)", _txt.count("\u2713") == 18 and "\u25a0" not in _txt, _txt.count("\u2713"))
_e = len(_W.filas)
r2 = FC.submit(datos())
chk("⚠️ uno por obra y día: el segundo no se guarda", not r2["ok"] and len(_W.filas) == _e and "already" in r2["error"], r2["error"])
_ayer = HOY - dt.timedelta(days=1)
r3 = FC.submit(datos(fecha=_ayer))
chk("⚠️ el campo no puede registrar otro día", not r3["ok"] and "today" in r3["error"] and len(_W.filas) == _e, r3["error"])
r4 = FC.submit(datos(fecha=_ayer, gestor=True))
chk("la oficina sí se pone al día, con ese día", r4["ok"] and _W.filas[-1][3] == "2026-11-01", r4)
_mal = todo_bien()
_mal["fc05"] = {"res": FC.FALLA, "nota": "cable pisado"}
_mal["fc12"] = {"res": FC.FALLA, "nota": "tiembla"}
_ALARMAS.clear()
r5 = FC.submit(datos(proyecto_id="PRJ-3", proyecto_nombre="Obra 3", resultados=_mal))
chk("⚠️ con X, se guarda igual", r5["ok"] and r5["fallos"] == [5, 12], r5)
chk("⚠️ UNA sola alarma, no una por punto", len(_ALARMAS) == 1 and r5["alarma"] is True, _ALARMAS)
chk("con la obra, el grupo y quién", _ALARMAS and _ALARMAS[0][0] == "PRJ-3" and _ALARMAS[0][1] == "cliente1" and _ALARMAS[0][3] == "campo000", _ALARMAS)
chk("...y dice QUÉ puntos y por qué", _ALARMAS and "5 (cable pisado)" in _ALARMAS[0][2] and "12 (tiembla)" in _ALARMAS[0][2], _ALARMAS)
chk("la hoja guarda cuáles fallaron", _W.filas[-1][FC.HEADERS.index("Failed")] == "5,12")
_t5 = PdfReader(io.BytesIO(_SUBIDOS[r5["drive_id"]])).pages[0].extract_text()
chk("⚠️ el PDF pone las X y la observación", "cable pisado" in _t5 and _t5.count("\u2713") == 16
    and len(re.findall(r"(?m)^\s*X\s*$", _t5)) == 2, (_t5.count("\u2713"), re.findall(r"(?m)^\s*X\s*$", _t5)))
_o = alerts.report_problem
alerts.report_problem = lambda *a: (False, "sin red")
r6 = FC.submit(datos(proyecto_id="PRJ-4", resultados=_mal))
alerts.report_problem = lambda *a: (_ for _ in ()).throw(RuntimeError("x"))
r7 = FC.submit(datos(proyecto_id="PRJ-5", resultados=_mal))
alerts.report_problem = _o
chk("⚠️ si la alarma falla, se dice (`alarma` False), y el registro queda", r6["ok"] and r6["alarma"] is False and r7["ok"] and r7["alarma"] is False, (r6["alarma"], r7["alarma"]))
# ⚠️ En una obra SIN checklist hoy: en la PRJ-1 el rechazo salía por «ya lo tiene», y no probaba nada
_e = len(_W.filas)
_ALARMAS.clear()
_x = FC.submit(datos(proyecto_id="PRJ-50", resultados={}))
chk("⚠️ el motor también rechaza lo incompleto", not _x["ok"] and "18" in _x["error"] and len(_W.filas) == _e, _x)
_m2 = todo_bien()
_m2["fc03"] = {"res": FC.FALLA, "nota": "  "}
_x = FC.submit(datos(proyecto_id="PRJ-50", resultados=_m2))
chk("⚠️ ...y una X sin observaciones: ni fila ni alarma", not _x["ok"] and "3" in _x["error"] and len(_W.filas) == _e and _ALARMAS == [], _x)
_od = DS.upload
DS.upload = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("drive caído"))
r8 = FC.submit(datos(proyecto_id="PRJ-6"))
DS.upload = _od
chk("sin Drive se registra igual, y lo dice (drive_id vacío)", r8["ok"] and r8["drive_id"] == "", r8)
_W.falla = True
r9 = FC.submit(datos(proyecto_id="PRJ-7"))
_W.falla = False
chk("sin hoja, dice que no guardó", not r9["ok"] and r9["error"], r9)
chk("⚠️ dos checks en la misma fila no repiten ID", len({f[0] for f in _W.filas}) == len(_W.filas))

sec("6. ⚠️ Firmar después: anexo, sin tocar lo firmado")
FC._ws = lambda: _W
d0 = FC.del_dia("PRJ-1", HOY)
chk("se lee el de hoy", d0["id"] == "FC-0001" and d0["firmas"] == ["Field Test"] and len(d0["puntos"]) == 18, d0)
chk("el primero no tiene nada que firmar", FC.pendiente_de_firma("PRJ-1", "cliente1", "Field Test", "campo000") == {})
chk("⚠️ a quien llega le falta", FC.pendiente_de_firma("PRJ-1", "cliente1", "Helper One", "helper1").get("id") == "FC-0001")
chk("⚠️ un homónimo con OTRO login también (manda el login, v418)", FC.pendiente_de_firma("PRJ-1", "cliente1", "Field Test", "otro").get("id") == "FC-0001")
chk("sin persona, nada", FC.pendiente_de_firma("PRJ-1", "cliente1", "", "") == {})
chk("en otra obra, nada", FC.pendiente_de_firma("PRJ-99", "cliente1", "Helper One", "helper1") == {})
_viejo = d0["drive_id"]
_QUITADOS.clear()
_BORRADOS.clear()
rf = FC.firmar("FC-0001", "cliente1", "Helper One", "HO", None, "helper1")
_nuevo = FC.del_dia("PRJ-1", HOY)
chk("firma, y dice que se archivó", rf["ok"] and rf["archivado"], rf)
chk("ya consta, con su login", _nuevo["firmas"] == ["Field Test", "Helper One"] and "helper1" in _nuevo["firmas_usuarios"], _nuevo["firmas"])
chk("ya no le falta", FC.pendiente_de_firma("PRJ-1", "cliente1", "Helper One", "helper1") == {})
_pg = PdfReader(io.BytesIO(_SUBIDOS[_nuevo["drive_id"]]))
chk("⚠️ el PDF nuevo es el original + una hoja", len(_pg.pages) == 2, len(_pg.pages))
_an = _pg.pages[1].extract_text()
chk("⚠️ el anexo habla del checklist, no del Pre-Start", "people who signed after this check" in _an and "False car" in _an and "Pre-Start" not in _an, _an[:300])
chk("con el nombre, la fecha y la hora", "Helper One" in _an and "02/11/2026" in _an and "FC-0001" in _an)
chk("⚠️ la primera página no cambia", _pg.pages[0].extract_text() == PdfReader(io.BytesIO(_SUBIDOS[_viejo])).pages[0].extract_text())
chk("el PDF viejo se quita después", _BORRADOS == [_viejo] and _QUITADOS == [("PRJ-1", _viejo)], (_BORRADOS, _QUITADOS))
chk("firmar sin nombre, no", not FC.firmar("FC-0001", "cliente1", "  ")["ok"])
chk("un ID que no existe, no", not FC.firmar("FC-9999", "cliente1", "X")["ok"])
_od = DS.download
DS.download = lambda i: (_ for _ in ()).throw(RuntimeError("x"))
_id2 = next(f[0] for f in _W.filas if f[1] == "PRJ-3")
rg = FC.firmar(_id2, "cliente1", "Otro", "O", None, "otro")
DS.download = _od
chk("⚠️ si el PDF no se puede rehacer, la firma consta y lo dice", rg["ok"] and rg["archivado"] is False, rg)
# ── v637 · un doble toque ──
_e = len(_SUBIDOS)
_antes = list(_W.filas)
rd = FC.firmar("FC-0001", "cliente1", "Helper One", "HO", None, "helper1")
_n2 = FC.del_dia("PRJ-1", HOY)
chk("⚠️ un doble toque no firma dos veces ni añade otro anexo", rd["ok"] and _n2["firmas"].count("Helper One") == 1 and len(_SUBIDOS) == _e, (rd, _n2["firmas"]))
chk("...y a quien tocó le dice que sí", rd["archivado"] is True)
rd = FC.firmar("FC-0001", "cliente1", "Helper One", "HO", None, "helper2")
chk("⚠️ un homónimo con OTRO login sí firma", rd["ok"] and FC.del_dia("PRJ-1", HOY)["firmas"].count("Helper One") == 2)
rd = FC.firmar("FC-0001", "cliente1", "field test", "x", None, "")
chk("sin login, se compara el nombre (aquí, entre todos)", rd["ok"] and FC.del_dia("PRJ-1", HOY)["firmas"].count("Field Test") == 1 and len(FC.del_dia("PRJ-1", HOY)["firmas"]) == 3, FC.del_dia("PRJ-1", HOY)["firmas"])
chk("`ya_firmo` con el login manda", PS.ya_firmo([{"name": "A B", "usuario": "ab"}], "A B", "otro") is False and PS.ya_firmo([{"name": "A B", "usuario": "ab"}], "Z", "AB") is True)
chk("...y un invitado sin login casa por nombre", PS.ya_firmo([{"name": "José  Pérez"}], "jose perez", "login") is True)
chk("una lista rara no revienta", PS.ya_firmo(["x", None], "A", "a") is False and PS.ya_firmo(None, "A") is False)
_Wp = HojaFalsa(PS.HEADERS)
_Wp.filas = [["PS-1", "PRJ-1", "cliente1", "2026-11-02", "07:00", "", "", "", "NO", "", "{}", "{}", "",
              json.dumps([{"name": "Field Test", "usuario": "campo000"}]), "a.pdf", "", "campo000", ""]]
_opw, _opi = PS._ws, PS._invalidate
PS._ws, PS._invalidate = (lambda: _Wp), (lambda: None)
_e = len(_SUBIDOS)
r1p = PS.firmar("PS-1", "cliente1", "Helper One", "HO", None, "helper1")
_sub1 = len(_SUBIDOS)
r2p = PS.firmar("PS-1", "cliente1", "Helper One", "HO", None, "helper1")
_lista = json.loads(_Wp.filas[0][PS.HEADERS.index("Attendees")])
chk("⚠️ el Pre-Start tampoco firma dos veces", r1p["ok"] and r2p["ok"] and len(_lista) == 2 and _sub1 == _e + 1 and len(_SUBIDOS) == _sub1, (_lista, _sub1, len(_SUBIDOS)))
PS._ws, PS._invalidate = _opw, _opi
_pa = PP.generate_anexo_firmas_pdf({"marca": "g", "ps_id": "PS-1", "fecha": "2026-11-02", "proyecto": "PRJ-1", "location": "L", "firmas": []})
_ta = PdfReader(io.BytesIO(_pa)).pages[0].extract_text()
chk("el anexo del Pre-Start sigue diciendo lo suyo", "people who joined after the briefing" in _ta and "original Pre-Start" in _ta
    and re.search(r"Pre-Start\s+PS-1", _ta) is not None, _ta[:200])

sec("7. Días trabajados, por obra")
_fich = [
    {"Group": "cliente1", "Type": "project", "ProjectID": "PRJ-1", "Project": "A", "User": "u1", "Clock In": "2026-10-30 07:00:00", "Clock Out": "2026-10-30 15:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "cliente1", "Type": "project", "ProjectID": "PRJ-1", "Project": "A", "User": "u2", "Clock In": "2026-10-30 08:00:00", "Clock Out": "2026-10-30 12:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "cliente1", "Type": "general", "ProjectID": "PRJ-1", "Project": "", "User": "u3", "Clock In": "2026-10-29 07:00:00", "Clock Out": "2026-10-29 15:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "cliente1", "Type": "project", "ProjectID": "", "Project": "Sin ID", "User": "u4", "Clock In": "2026-10-29 07:00:00", "Clock Out": "2026-10-29 15:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "otro", "Type": "project", "ProjectID": "PRJ-1", "Project": "A", "User": "u5", "Clock In": "2026-10-28 07:00:00", "Clock Out": "2026-10-28 15:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "cliente1", "Type": "project", "ProjectID": "PRJ-2", "Project": "B", "User": "u1", "Clock In": "2026-10-27 22:00:00", "Clock Out": "2026-10-28 02:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "cliente1", "Type": "project", "ProjectID": "PRJ-2", "Project": "B", "User": "u1", "Clock In": "2026-09-01 07:00:00", "Clock Out": "2026-09-01 15:00:00", "Status": "CERRADO", "Hours": "8"},
    {"Group": "cliente1", "Type": "project", "ProjectID": "PRJ-1", "Project": "A", "User": "u1", "Clock In": "2026-11-02 07:00:00", "Clock Out": "2026-11-02 09:00:00", "Status": "CERRADO", "Hours": "8"},
]
_oc = (TC._cached_records, TC.mapa_nombres, TC._nombre_actual)
TC._cached_records = lambda: _fich
TC.mapa_nombres = lambda g="": {}
TC._nombre_actual = lambda p, n: "Nombre " + p
_d30 = dt.date(2026, 10, 3)
_od = TC.obras_por_dia("cliente1", _d30, dt.date(2026, 11, 1))
chk("una entrada por obra y día, con quién", _od[(dt.date(2026, 10, 30), "PRJ-1")]["usuarios"] == {"u1", "u2"}, _od)
chk("con el nombre vigente", _od[(dt.date(2026, 10, 30), "PRJ-1")]["nombre"] == "Nombre PRJ-1")
chk("⚠️ la jornada general no es una obra", (dt.date(2026, 10, 29), "PRJ-1") not in _od)
chk("⚠️ sin ID no hay obra a la que pedirle nada", not any(not k[1] for k in _od))
chk("otro grupo no entra", (dt.date(2026, 10, 28), "PRJ-1") not in _od)
chk("⚠️ un turno de noche cuenta en los dos días", (dt.date(2026, 10, 27), "PRJ-2") in _od and (dt.date(2026, 10, 28), "PRJ-2") in _od, sorted(_od))
chk("fuera del rango, no", (dt.date(2026, 9, 1), "PRJ-2") not in _od and (HOY, "PRJ-1") not in _od)
chk("sin límites, todo", (dt.date(2026, 9, 1), "PRJ-2") in TC.obras_por_dia("cliente1"))

_og = P.get_project
_PR = {"PRJ-1": obra("PRJ-1"), "PRJ-2": obra("PRJ-2", fc=False)}
P.get_project = lambda p: _PR.get(p, {})
_CRED["PRJ-1"] = [credito(S.FC_MONTAR, 100, "2026-10-29")]
_PS.clear()
_W2 = HojaFalsa(FC.HEADERS)
FC._records = lambda: _W2.get_all_records()
_L = FC.dias_sin_registro("cliente1", hoy=HOY)
chk("el más reciente primero", [(x["fecha"], x["pid"]) for x in _L] == [(dt.date(2026, 10, 30), "PRJ-1"), (dt.date(2026, 10, 28), "PRJ-2"), (dt.date(2026, 10, 27), "PRJ-2")], _L)
chk("⚠️ HOY no sale: puede estar aún por hacer", not any(x["fecha"] == HOY for x in _L))
chk("⚠️ en la obra con false car montado faltan los dos, con la charla primero", _L[0]["falta"] == ["prestart", "falsecar"], _L[0])
chk("⚠️ en la obra sin false car, solo el Pre-Start", _L[1]["falta"] == ["prestart"], _L[1])
chk("con quién y el nombre de la obra", _L[0]["usuarios"] == ["u1", "u2"] and _L[0]["nombre"] == "Nombre PRJ-1", _L[0])
_PS.append({"ProjectID": "PRJ-1", "Date": "2026-10-30"})
_L = FC.dias_sin_registro("cliente1", hoy=HOY)
chk("con su Pre-Start, solo falta el checklist", _L[0]["falta"] == ["falsecar"], _L[0])
_W2.filas.append(["FC-1", "PRJ-1", "cliente1", "2026-10-30"])
_L = FC.dias_sin_registro("cliente1", hoy=HOY)
chk("⚠️ con los dos, ese día desaparece", not any(x["pid"] == "PRJ-1" for x in _L), _L)
_W2.filas.clear()
_CRED["PRJ-1"] = [credito(S.FC_MONTAR, 100, "2026-10-31")]
_L = FC.dias_sin_registro("cliente1", hoy=HOY)
chk("⚠️ antes de montarlo no se exige", not any(x["pid"] == "PRJ-1" for x in _L), _L)
_CRED["PRJ-1"] = [credito(S.FC_MONTAR, 100, "2026-10-29"), credito(S.FC_RETIRAR, 100, "2026-10-30")]
chk("⚠️ el día de retirarlo tampoco", not any(x["pid"] == "PRJ-1" for x in FC.dias_sin_registro("cliente1", hoy=HOY)))
_PS.clear()
chk("el filtro por obra", all(x["pid"] == "PRJ-2" for x in FC.dias_sin_registro("cliente1", pid="PRJ-2", hoy=HOY)))
chk("sin límite, también lo de hace dos meses (el expediente)", any(x["fecha"] == dt.date(2026, 9, 1) for x in FC.dias_sin_registro("cliente1", dias=None, hoy=HOY)))
chk("con 30 días, no", not any(x["fecha"] == dt.date(2026, 9, 1) for x in FC.dias_sin_registro("cliente1", hoy=HOY)))
TC._cached_records, TC.mapa_nombres, TC._nombre_actual = _oc
FC._records = lambda: _W.get_all_records()

sec("8. El Handover")
chk("⚠️ el estándar siguen siendo trece", len(HO.ITEMS) == 13 and "false_car" not in HO.CLAVES)
_c = lambda **k: {"prestarts": [{"Date": "2026-10-01"}], **k}                # noqa: E731
_fi = lambda c: next(f for f in HO.estado(c) if f["clave"] == "risk")        # noqa: E731
_fc = lambda c: next((f for f in HO.estado(c) if f["clave"] == "false_car"), None)  # noqa: E731
chk("sin false car, trece filas", len(HO.estado(_c())) == 13 and _fc(_c()) is None)
chk("con él, catorce", len(HO.estado(_c(false_car=True))) == 14)
chk("Pre-Start: como siempre si no falta ninguno", _fi(_c())["estado"] == HO.OK and _fi(_c(sin_prestart=[]))["estado"] == HO.OK)
_p = _fi(_c(sin_prestart=[1, 2]))
chk("⚠️ con días sin él, PARCIAL, y dice cuántos", _p["estado"] == HO.PARCIAL and "2 days worked with none" in _p["detalle"], _p)
chk("sin ninguno, sigue en falta", _fi({"sin_prestart": [1]})["estado"] == HO.FALTA)
chk("false car: al día", _fc(_c(false_car=True, checks_fc=[1, 2]))["estado"] == HO.OK)
_p = _fc(_c(false_car=True, checks_fc=[1], sin_falsecar=[1]))
chk("⚠️ con días sin él, PARCIAL", _p["estado"] == HO.PARCIAL and "1 day worked with none" in _p["detalle"], _p)
chk("sin ninguno y con días, en falta", _fc(_c(false_car=True, sin_falsecar=[1]))["estado"] == HO.FALTA)
chk("⚠️ sin montar aún no acusa de nada", _fc(_c(false_car=True))["estado"] == HO.PARCIAL and "not marked as installed" in _fc(_c(false_car=True))["detalle"])
_h = leer("core/handover_ui.py")
chk("la pantalla le pasa los datos, también de Pre-Start", all(x in _h for x in ('"sin_prestart": sin_ps', '"false_car": false_car', '"checks_fc": checks_fc', '"sin_falsecar": sin_fc')))
chk("el rótulo no dice trece si son catorce", 'thirteen items, plus the false car' in _h)

sec("9. La hoja")
chk("⚠️ en el LOTE (lector sin cabeceras: fuera, vacía para siempre)", FC.SHEET in H.HOJAS_LECTURA)
chk("columnas: las del registro, sin imagen de firma", FC.HEADERS == ["ID", "ProjectID", "Group", "Date", "Time", "ResultsJSON", "Failed", "Signers", "File", "DriveID", "CreatedBy", "Created"])
_cuenta = []
_wb = HojaFalsa(FC.HEADERS)
_wb.filas = [["FC-1", "PRJ-1"], ["FC-2", "PRJ-2"], ["FC-3", "PRJ-1"]]
FC._ws, FC._records = (lambda: _cuenta.append(1) or _wb), (lambda: _wb.get_all_records())
chk("borrar la obra quita sus checklists", FC.borrar_de_obra("PRJ-1") == 2 and [f[0] for f in _wb.filas] == ["FC-2"], _wb.filas)
_cuenta.clear()
chk("⚠️ una obra sin checklists no toca (ni crea) la hoja", FC.borrar_de_obra("PRJ-8") == 0 and _cuenta == [])
FC._ws, FC._records = (lambda: _W), (lambda: _W.get_all_records())
_p = leer("core/projects.py")
chk("`delete_project` lo llama", "_FC.borrar_de_obra(pid)" in funcion(_p, "delete_project"))
chk("⚠️ y el aviso de antes de borrar lo cuenta", '("False car checks", _FC.SHEET, "ProjectID")' in funcion(_p, "datos_asociados"))
chk("Files: etiqueta, orden, y el campo lo ve", PU._TIPO_LABEL.get("falsecar") == "False car" and "falsecar" in PU._TIPO_ORDER and "falsecar" in PU._CAMPO_VER)
_g = CA.SYSTEM_PROMPT if hasattr(CA, "SYSTEM_PROMPT") else leer("core/chat_agent.py")
chk("el asistente lo conoce", "Daily False Car Checklist" in _g and "Days worked with no record" in _g)

# ═════════════════════════════════════════════════════════════════
sec("10. La pregunta al crear la obra (con clics)")
GUION_ALTA = r'''
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import projects_ui as PU
tipo = st.session_state["_tipo"]
p = PU._pregunta_etapas(tipo, "k")
st.session_state["_pend"] = [x["clave"] for x in p]
st.session_state["_cond"] = list(PU._cond_elegidas("k"))
'''


def alta(tipo):
    at = AppTest.from_string(GUION_ALTA, default_timeout=60)
    at.session_state["_tipo"] = tipo
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


at = alta("Installation")
_rfc = next((r for r in at.radio if r.key == "np_fc_k"), None)
chk("⚠️ en una instalación se pregunta", _rfc is not None and _rfc.label == "False car?" and _rfc.options == ["Yes", "No"], [r.key for r in at.radio])
chk("⚠️ sin preselección", _rfc.value is None)
chk("⚠️ sin responder, no se puede crear", at.session_state["_pend"] == ["false_car"], at.session_state["_pend"])
_rfc.set_value(True).run()
chk("Yes: nada pendiente", at.session_state["_pend"] == [])
chk("⚠️ Yes añade las tres al plan", set(at.session_state["_cond"]) == set(S.FALSE_CAR), at.session_state["_cond"])
next(r for r in at.radio if r.key == "np_fc_k").set_value(False).run()
chk("No: nada pendiente y ninguna actividad", at.session_state["_pend"] == [] and at.session_state["_cond"] == [])
at = alta("Ripout + Installation")
chk("con desmontaje, las DOS preguntas", {r.key for r in at.radio} == {"np_demol_k", "np_fc_k"}, [r.key for r in at.radio])
chk("...y las dos pendientes", set(at.session_state["_pend"]) == {"demolicion", "false_car"}, at.session_state["_pend"])
at = alta("Ripout")
chk("⚠️ en un Ripout no se pregunta", not any(r.key == "np_fc_k" for r in at.radio) and "false_car" not in at.session_state["_pend"])
_u = leer("core/projects_ui.py")
_q = leer("core/quotes_ui.py")
chk("el alta y la cotización pasan por la misma pregunta", "_pendientes = _pregunta_etapas(_tipo, key)" in _u and "_PU._pregunta_etapas(tipo, _kalta)" in _q and "condicionales=_PU._cond_elegidas(_kalta)" in _q)

sec("11. La pantalla del checklist (con clics)")
GUION = r'''
import sys, json
from datetime import date, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import clock, falsecar as FC, falsecar_ui as U, flash, prestart_ui as PU, stages as S, projects as P, stage_progress as SP
E = st.session_state["_esc"]
clock.today = lambda *a: date(2026, 11, 2)
clock.now = lambda *a: datetime(2026, 11, 2, 7, 15)
SP.creditos = lambda pid, etapa=None: E.get("cred", [{"Activity": S.FC_MONTAR, "Pct": "100", "WorkDate": "2026-10-20"}])
FC._records = lambda: E["filas"]
def _sub(d):
    st.session_state["_enviado"] = {"fecha": str(d["fecha"]), "res": d["resultados"], "gestor": d["gestor"], "ini": d["iniciales"], "pid": d["proyecto_id"]}
    return {"ok": True, "id": "FC-0007", "pdf": b"x", "filename": "a.pdf", "drive_id": "D1", "fallos": E.get("fallos", []), "alarma": E.get("alarma", True), "error": ""}
FC.submit = _sub
def _fir(*a):
    st.session_state["_firmado"] = a
    return {"ok": True, "archivado": True, "error": ""}
FC.firmar = _fir
PU._canvas_disponible = (lambda: (lambda **k: None)) if E.get("lienzo") else (lambda: None)
flash.mostrar()
_o = {"ID": "PRJ-1", "Name": "Obra A", "Group": "cliente1", "StagePlanJSON": P.plan_nuevo("Installation", S.FALSE_CAR)}
U.render(_o, "cliente1", E.get("rol", "field"), "campo000", "Field Test", E.get("dia"))
'''


def pinta(**esc):
    at = AppTest.from_string(GUION, default_timeout=60)
    at.session_state["_esc"] = {"filas": [], **esc}
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def rad(at):
    return [r for r in at.radio if r.key.startswith("fc_res_")]


def btn(at, trozo):
    return next((b for b in at.button if trozo in b.key), None)


def fila_hecha(firmas=None, fallos=None):
    return {"ID": "FC-0005", "ProjectID": "PRJ-1", "Date": "2026-11-02", "Time": "07:00",
            "ResultsJSON": json.dumps({k: {"res": "fail" if (fallos and n in fallos) else "pass", "nota": "mal" if (fallos and n in fallos) else ""}
                                       for n, (k, _x) in enumerate(FC.CHECKS, 1)}),
            "Signers": json.dumps(firmas or [{"name": "Field Test", "usuario": "campo000"}]), "DriveID": "D1", "File": "a.pdf"}


at = pinta()
chk("⚠️ los 18 puntos, sin respuesta por defecto", len(rad(at)) == 18 and all(r.value is None for r in rad(at)), len(rad(at)))
chk("✓ y X", rad(at)[0].options == ["✓", "X"], rad(at)[0].options)
chk("⚠️ el campo no elige fecha", not any("fc_fecha" in str(d.key) for d in at.date_input))
chk("⚠️ sin responder no se puede enviar", btn(at, "fc_submit").disabled is True)
chk("toda clave lleva la obra y el día", all("PRJ-1_2026-11-02" in r.key for r in rad(at)), rad(at)[0].key)
for r in rad(at):
    r.set_value("pass")
at.run()
next(i for i in at.text_input if i.key.startswith("fc_ini_")).set_value("FT")
at.run()
chk("todo ✓: se puede enviar", btn(at, "fc_submit").disabled is False)
rad(at)[4].set_value("fail").run()
chk("⚠️ una X sin observaciones lo impide", btn(at, "fc_submit").disabled is True and any("5" in c.value for c in at.caption if "Still to complete" in c.value), [c.value for c in at.caption][:3])
next(i for i in at.text_input if i.key.endswith("_fc05")).set_value("cable pisado").run()
chk("con observaciones, sí", btn(at, "fc_submit").disabled is False)
btn(at, "fc_submit").click().run()
_e = at.session_state["_enviado"]
chk("envía los 18, con la X y su nota", len(_e["res"]) == 18 and _e["res"]["fc05"] == {"res": "fail", "nota": "cable pisado"} and _e["res"]["fc01"]["res"] == "pass", _e["res"]["fc05"])
chk("con la fecha de hoy y como campo", _e["fecha"] == "2026-11-02" and _e["gestor"] is False, _e)

at = pinta(fallos=[5, 12])
for r in rad(at):
    r.set_value("pass")
at.run()
next(i for i in at.text_input if i.key.startswith("fc_ini_")).set_value("FT")
at.run()
btn(at, "fc_submit").click().run()
chk("el aviso de guardado", any("FC-0007" in s.value for s in at.success), [s.value for s in at.success])
chk("⚠️ con X, dice que NO se use, y cuáles", any("Do not use the false car" in e.value and "5, 12" in e.value for e in at.error), [e.value for e in at.error])
chk("...y que se avisó a la oficina", any("administrator has been notified" in w.value for w in at.warning), [w.value for w in at.warning])
chk("⚠️ el formulario nace vacío (otra generación)", all(r.value is None for r in rad(at)) if rad(at) else True)
at.run()
chk("el resultado no se va al siguiente toque", any("FC-0007" in s.value for s in at.success))

at = pinta(alarma=False, fallos=[5])
for r in rad(at):
    r.set_value("pass")
at.run()
next(i for i in at.text_input if i.key.startswith("fc_ini_")).set_value("FT")
at.run()
btn(at, "fc_submit").click().run()
chk("⚠️ si la alarma no se abrió, lo dice", any("could NOT be opened" in e.value for e in at.error), [e.value for e in at.error])

at = pinta(cred=[])
chk("⚠️ sin montar: lo explica y no hay formulario", not rad(at) and any("Install sky climber" in i.value for i in at.info), [i.value for i in at.info])
at = pinta(cred=[{"Activity": S.FC_MONTAR, "Pct": "100", "WorkDate": "2026-10-20"}, {"Activity": S.FC_RETIRAR, "Pct": "100", "WorkDate": "2026-10-30"}])
chk("retirado: tampoco", not rad(at))

at = pinta(filas=[fila_hecha()])
chk("⚠️ hecho y firmado por mí: lo dice, sin formulario", not rad(at) and any("you are already on it" in m.value for m in at.markdown), [m.value for m in at.markdown][:4])
at = pinta(filas=[fila_hecha(fallos=[3])])
chk("⚠️ con una X de esta mañana, lo avisa a quien abre la pantalla", any("Do not use the false car" in e.value and "3" in e.value for e in at.error), [e.value for e in at.error])
at = pinta(filas=[fila_hecha(firmas=[{"name": "Otro", "usuario": "otro"}])])
chk("⚠️ hecho por otro: se firma, no se rehace", not rad(at) and btn(at, "fc_tarde_ok") is not None)
next(i for i in at.text_input if i.key.startswith("fc_tarde_ini")).set_value("FT")
at.run()
btn(at, "fc_tarde_ok").click().run()
chk("firma con mi nombre y login", at.session_state["_firmado"][:4] == ("FC-0005", "cliente1", "Field Test", "FT") and at.session_state["_firmado"][5] == "campo000", at.session_state["_firmado"])
at = pinta(filas=[fila_hecha(fallos=[3], firmas=[{"name": "Otro", "usuario": "otro"}])])
chk("⚠️ también avisa a quien va a firmar", any("Do not use" in e.value for e in at.error))

at = pinta(rol="administrator")
_di = next((d for d in at.date_input if "fc_fecha" in d.key), None)
chk("la oficina elige la fecha, y hoy es el tope", _di is not None and _di.value == dt.date(2026, 11, 2) and _di.max == dt.date(2026, 11, 2), _di)
at = pinta(rol="administrator", dia=dt.date(2026, 10, 25))
_di = next((d for d in at.date_input if "fc_fecha" in d.key), None)
chk("⚠️ con un día pedido, abre en ese día", _di.value == dt.date(2026, 10, 25), _di.value)
chk("...y el formulario es de ese día", "2026-10-25" in rad(at)[0].key, rad(at)[0].key)
at.run()
chk("⚠️ y sigue en él al tocar otra cosa", next(d for d in at.date_input if "fc_fecha" in d.key).value == dt.date(2026, 10, 25))
for r in rad(at):
    r.set_value("pass")
at.run()
next(i for i in at.text_input if i.key.startswith("fc_ini_")).set_value("FT")
at.run()
btn(at, "fc_submit").click().run()
chk("⚠️ se registra ese día, como oficina", at.session_state["_enviado"]["fecha"] == "2026-10-25" and at.session_state["_enviado"]["gestor"] is True, at.session_state["_enviado"]["fecha"])

sec("12. Dentro de la sección Pre-Start (con clics)")
GUION_PS = r'''
import sys
from datetime import date, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import clock, falsecar as FC, falsecar_ui as FU, flash, prestart as PS, prestart_ui as U, projects as P, stages as S, stage_progress as SP, timeclock as T, auth
E = st.session_state["_esc"]
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": E.get("rol", "field"), "grupo": "cliente1"}
clock.today = lambda *a: date(2026, 11, 2)
clock.now = lambda *a: datetime(2026, 11, 2, 7, 15)
PS.is_configured = lambda: True
PS._records = lambda: E.get("ps", [])
FC._records = lambda: []
U._projects_for = lambda *a: E["obras"]
T.open_sessions = lambda *a, **k: {T.TIPO_GENERAL: None, T.TIPO_PROYECTO: None}
SP.creditos = lambda pid, etapa=None: [{"Activity": S.FC_MONTAR, "Pct": "100", "WorkDate": "2026-10-20"}]
auth.list_users = lambda *a, **k: [{"User": "campo000", "Name": "Field Test"}]
auth.etiqueta_usuarios = lambda u: {"campo000": "Field Test"}
FC.dias_sin_registro = lambda g, **k: E.get("faltan", [])
U._canvas_disponible = lambda: None
flash.mostrar()
for k, v in E.get("pendiente", {}).items():
    st.session_state.setdefault(k, v) if not st.session_state.get("_ya") else None
st.session_state["_ya"] = True
U.render_prestart_tab()
'''
_OBRAS = [{**obra("PRJ-1"), "Name": "Con FC"}, {**obra("PRJ-2", fc=False), "Name": "Sin FC"}]


def pinta_ps(**esc):
    at = AppTest.from_string(GUION_PS, default_timeout=60)
    at.session_state["_esc"] = {"obras": _OBRAS, **esc}
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


at = pinta_ps()
at.selectbox(key="ps_proy").set_value("Sin FC (PRJ-2)").run()
chk("⚠️ en una obra sin false car nada cambia", not any(r.key.startswith("cpxseg_ps_doc") for r in at.radio))
at.selectbox(key="ps_proy").set_value("Con FC (PRJ-1)").run()
_rd = next((r for r in at.radio if r.key == "cpxseg_ps_doc_PRJ-1"), None)
chk("⚠️ en la que lo lleva se elige, y empieza por el Pre-Start", _rd is not None and _rd.value == "prestart" and _rd.options == ["Pre-Start", "False car"], _rd)
_rd.set_value("falsecar").run()
chk("⚠️ False car abre el checklist", any("Daily False Car Checklist" in m.value for m in at.markdown) and len([r for r in at.radio if r.key.startswith("fc_res_")]) == 18)
chk("...y ya no el formulario del Pre-Start", not any("_s1_" in r.key for r in at.radio))
chk("el campo no ve la lista de días", not any(e.label.startswith("Days worked") for e in list(at.expander) + list(at.status)))
at = pinta_ps(pendiente={"_ps_proy_pending": "PRJ-1", "_ps_doc_pending": "falsecar"})
chk("⚠️ el atajo de los avisos llega directo al checklist", at.selectbox(key="ps_proy").value == "Con FC (PRJ-1)" and any("Daily False Car Checklist" in m.value for m in at.markdown), at.selectbox(key="ps_proy").value)
chk("⚠️ el encargo no queda en la sesión para otra obra", "_ps_doc_pending" not in at.session_state and "_ps_dia_pending" not in at.session_state)
_falt = [{"fecha": dt.date(2026, 10, 30), "pid": "PRJ-1", "nombre": "Con FC", "usuarios": ["campo000"], "falta": ["prestart"]}]
at = pinta_ps(rol="administrator", faltan=_falt)
_ex = next((e for e in list(at.expander) + list(at.status) if e.label.startswith("Days worked")), None)
chk("⚠️ la oficina ve la lista, con cuántos", _ex is not None and "(1)" in _ex.label, [e.label for e in list(at.expander) + list(at.status)])
chk("con la tabla dentro", len(at.dataframe) >= 1)
chk("cerrada: no empuja la pantalla", _ex is not None and not _ex.proto.expanded if hasattr(_ex.proto, "expanded") else True)
at = pinta_ps(rol="administrator")
_ex = next((e for e in list(at.expander) + list(at.status) if e.label.startswith("Days worked")), None)
chk("sin nada pendiente lo dice", _ex is not None and "(0)" in _ex.label and any("Every day worked" in c.value for c in at.caption))
at = pinta_ps(rol="owner")
chk("⚠️ el propietario no tiene grupo: aquí no sale", not any(e.label.startswith("Days worked") for e in list(at.expander) + list(at.status)))
# Tocar la fila: AppTest no sabe tocar una tabla, así que se prueba lo que deja el toque
# ⚠️ Con MI firma en la de hoy: sin ella, lo que sale es «fírmala» y la tarjeta de hecho no aparece
at = pinta_ps(rol="administrator", ps=[{"ID": "PS-1", "ProjectID": "PRJ-2", "Date": "2026-11-02", "File": "a.pdf",
                                        "Attendees": json.dumps([{"name": "Field Test", "usuario": "campo000"}])}],
              pendiente={"_ps_proy_pending": "PRJ-2", "_ps_dia_pending": dt.date(2026, 10, 30)})
_fi = next((d for d in at.date_input if d.key.startswith("ps_fecha_")), None)
chk("⚠️ el día tocado llega al Pre-Start, aunque hoy ya esté hecho", _fi is not None and _fi.value == dt.date(2026, 10, 30), _fi.value if _fi else None)
at.run()
chk("⚠️ y sigue ahí al tocar otra cosa", next(d for d in at.date_input if d.key.startswith("ps_fecha_")).value == dt.date(2026, 10, 30))
at = pinta_ps(rol="administrator", pendiente={"_ps_proy_pending": "PRJ-1", "_ps_doc_pending": "falsecar", "_ps_dia_pending": dt.date(2026, 10, 30)})
_fi = next((d for d in at.date_input if "fc_fecha" in d.key), None)
chk("⚠️ y al checklist, con el suyo", _fi is not None and _fi.value == dt.date(2026, 10, 30), _fi)
_f = leer("core/falsecar_ui.py")
chk("⚠️ tocar la fila deja obra y día, y otra clave de tabla", all(x in _f for x in ('st.session_state["_ps_proy_pending"] = _x["pid"]', 'st.session_state["_ps_dia_pending"] = _x["fecha"]', 'key=f"ps_faltantes_{st.session_state.get(_gk, 0)}"')))
chk("⚠️ si faltan los dos, primero la charla", 'if _x["falta"] == ["falsecar"]:' in _f)

sec("13. Los avisos, en su orden")
GUION_AV = r'''
import sys
from datetime import date, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
from core import clock, falsecar as FC, flash, home_ui as HU, prestart as PS, projects as P, stages as S, stage_progress as SP, timeclock as T, timeclock_ui as U
E = st.session_state["_esc"]
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test", "rol": "field", "grupo": "cliente1"}
clock.today = lambda *a: date(2026, 11, 2)
clock.now = lambda *a: datetime(2026, 11, 2, 7, 15)
PS.hecho_hoy = lambda *a: E["ps_hecho"]
U._pend_firma_de = lambda *a: E.get("ps_firma", {})
PS.pendiente_de_firma = lambda *a, **k: E.get("ps_firma", {})
SP.creditos = lambda pid, etapa=None: E.get("cred", [{"Activity": S.FC_MONTAR, "Pct": "100", "WorkDate": "2026-10-20"}])
FC._records = lambda: E.get("fc", [])
P.get_project = lambda p: {"ID": p, "Name": "Obra", "Group": "cliente1", "StagePlanJSON": P.plan_nuevo("Installation", S.FALSE_CAR)}
T.is_configured = lambda: True
T.open_sessions = lambda *a, **k: {T.TIPO_PROYECTO: {"proyecto_id": "PRJ-1", "proyecto": "Obra <A>"}}
T.olvidos = lambda s: {}
if not st.session_state.get("_arm"):
    st.session_state["_arm"] = True
    U._armar_aviso_prestart("PRJ-1", "Obra <A>", "cliente1")
if E.get("banda"):
    st.session_state["_b_ps"] = HU._banda_prestart()
    if not st.session_state["_b_ps"]:
        HU._banda_falsecar()
if E.get("dialogos"):
    if not U.aviso_prestart_pendiente("cliente1"):
        U.aviso_falsecar_pendiente("cliente1")
if E.get("chip"):
    U._chip_falsecar("PRJ-1", "cliente1")
'''


def av(**esc):
    at = AppTest.from_string(GUION_AV, default_timeout=60)
    at.session_state["_esc"] = esc
    at.run()
    chk("se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
    return at


def _hay(at, clave):
    return any(b.key == clave for b in at.button)


at = av(ps_hecho=False, dialogos=True)
chk("⚠️ si faltan los dos, solo el diálogo del Pre-Start", _hay(at, "ps_dlg_ir") and not _hay(at, "fc_dlg_ir"), [b.key for b in at.button])
chk("el del checklist queda armado", (at.session_state["_fc_aviso"] or {}).get("pid") == "PRJ-1")
at.session_state["_esc"]["ps_hecho"] = True
at.run()
chk("⚠️ con la charla hecha, aparece el del checklist", _hay(at, "fc_dlg_ir") and not _hay(at, "ps_dlg_ir"), [b.key for b in at.button])
next(b for b in at.button if b.key == "fc_dlg_no").click().run()
chk("«Not now» no vuelve a salir en la sesión", not _hay(at, "fc_dlg_ir") and at.session_state["_fc_visto_PRJ-1"] is True)
at = av(ps_hecho=True, ps_firma={"id": "PS-1"}, dialogos=True)
chk("⚠️ si me falta firmar la charla, tampoco tapa el checklist", not _hay(at, "fc_dlg_ir"), [b.key for b in at.button])
at = av(ps_hecho=True, dialogos=True, cred=[])
chk("⚠️ sin montar, ningún aviso", not _hay(at, "fc_dlg_ir") and "_fc_aviso" not in at.session_state)
at = av(ps_hecho=True, dialogos=True, fc=[fila_hecha()])
chk("hecho y firmado por mí, ninguno", not _hay(at, "fc_dlg_ir"))
at = av(ps_hecho=True, dialogos=True, fc=[fila_hecha(firmas=[{"name": "Otro", "usuario": "otro"}])])
chk("⚠️ hecho por otro: el diálogo pide firmar", _hay(at, "fc_dlg_ir") and any("you have not" in m.value for m in at.markdown), [m.value for m in at.markdown])

at = av(ps_hecho=False, banda=True)
chk("⚠️ si faltan los dos, solo la banda del Pre-Start", _hay(at, "banda_ps_ir") and not _hay(at, "banda_fc_ir") and at.session_state["_b_ps"] is True, [b.key for b in at.button])
at = av(ps_hecho=True, ps_firma={"id": "PS-1"}, banda=True)
chk("firmar la charla también va primero", _hay(at, "banda_ps_firmar") and not _hay(at, "banda_fc_ir") and at.session_state["_b_ps"] is True)
at = av(ps_hecho=True, banda=True)
chk("⚠️ con la charla lista, la banda del checklist", _hay(at, "banda_fc_ir"), [b.key for b in at.button])
chk("⚠️ el nombre de la obra va escapado (un «<» se comería la banda)", any("Obra &lt;A&gt;" in m.value for m in at.markdown), [m.value for m in at.markdown])
at = av(ps_hecho=True, banda=True, fc=[fila_hecha(firmas=[{"name": "Otro", "usuario": "otro"}])])
chk("hecho por otro: la banda pide firmar", any("Sign today's false car check" in m.value for m in at.markdown))
at = av(ps_hecho=True, banda=True, fc=[fila_hecha()])
chk("hecho y firmado, ninguna", not _hay(at, "banda_fc_ir"))
at = av(ps_hecho=True, chip=True)
chk("⚠️ el menú lateral lo recuerda", _hay(at, "sb_fc_ir"))
at = av(ps_hecho=True, chip=True, fc=[fila_hecha(firmas=[{"name": "Otro", "usuario": "otro"}])])
chk("...o pide firmar", _hay(at, "sb_fc_firmar"))
at = av(ps_hecho=True, chip=True, fc=[fila_hecha()])
chk("...y calla si no hace falta", not _hay(at, "sb_fc_ir") and not _hay(at, "sb_fc_firmar"))
_a = leer("app.py")
chk("⚠️ `app.py` abre un solo diálogo por pasada", "if not aviso_prestart_pendiente(_GRUPO):\n        aviso_falsecar_pendiente(_GRUPO)" in _a)
_tu = leer("core/timeclock_ui.py")
chk("`aviso_prestart_pendiente` dice si abrió uno", funcion(_tu, "aviso_prestart_pendiente").count("return True") == 2)
chk("⚠️ `_ir_a_falsecar` lleva a la pestaña correcta", 'st.session_state["_ps_doc_pending"] = "falsecar"' in funcion(_tu, "_ir_a_falsecar"))
chk("⚠️ se avisa aunque la charla ya esté hecha (no va dentro de su `if`)", funcion(_tu, "_armar_aviso_prestart").index("_falsecar_toca") > funcion(_tu, "_armar_aviso_prestart").index("except Exception"))

sec("14. v637 · Lo visto verificando")
_pu = leer("core/prestart_ui.py")
_f = leer("core/falsecar_ui.py")
chk("⚠️ tocar la fila pide bajar", 'st.session_state["_bajar_cpx_ps_obra"] = True' in _f)
chk("⚠️ y el bloque de la obra baja", '_PU._bajar_a("cpx_ps_obra", "_bajar_cpx_ps_obra", bloque="start")' in _pu)
at = pinta_ps(pendiente={"_bajar_cpx_ps_obra": True})
chk("la marca se consume una vez y la shell no sube", "_bajar_cpx_ps_obra" not in at.session_state and at.session_state["_bajada_pedida"] is True)
_fo = funcion(_f, "_formulario")
chk("⚠️ los 18 puntos van en el bloque de la regla", _fo.index('with st.container(key="cpx_fc_puntos"):') < _fo.index("for n, (k, texto) in enumerate(FC.CHECKS, 1):"))
chk("con la regla pintada antes", _fo.index("st.markdown(_CSS_PUNTOS, unsafe_allow_html=True)") < _fo.index('with st.container(key="cpx_fc_puntos"):'))
chk("⚠️ en estrecho, ✓/X y Remarks en una fila", all(x in _f for x in ("@container (max-width:700px)", "nth-child(1)", "flex:0 0 96px", "flex:1 1 0")))
from PIL import Image                                             # noqa: E402
_b = io.BytesIO()
Image.new("RGB", (300, 90), "white").save(_b, "PNG")
_m = 72 / 25.4
_i1 = PP._celda_firma({"sig": _b.getvalue()}, PP._styles())
_i2 = PP._celda_firma({"sig": _b.getvalue()}, PP._styles(), ancho=60 * _m, alto=18 * _m)
chk("el Pre-Start conserva su medida", _i1._width <= 25 * _m + 0.1 or _i1.drawWidth <= 25 * _m + 0.1, (_i1.drawWidth, _i1._width))
chk("⚠️ la firma cabe más grande cuando se le da más caja", _i2.drawWidth >= 55 * _m, _i2.drawWidth)
chk("⚠️ y el checklist se la da", "ancho=60 * mm, alto=18 * mm" in leer("core/falsecar_pdf.py"))
_rp = FP.generate_pdf({"id": "FC-1", "grupo": "g", "proyecto_nombre": "O", "fecha": HOY, "hora": "07:00", "resultados": todo_bien(), "nombre": "N", "iniciales": "I", "firma": _b.getvalue()})
chk("con la firma grande sigue siendo UNA página", len(PdfReader(io.BytesIO(_rp)).pages) == 1)
at = pinta(rol="administrator")
for r in rad(at):
    r.set_value("pass")
at.run()
next(i for i in at.text_input if i.key.startswith("fc_ini_")).set_value("FT")
at.run()
btn(at, "fc_submit").click().run()
chk("el aviso sale en su día", any("FC-0007" in s.value for s in at.success), [s.value for s in at.success])
next(d for d in at.date_input if "fc_fecha" in d.key).set_value(dt.date(2026, 10, 25)).run()
chk("⚠️ con otro día elegido, el aviso no sale", not any("FC-0007" in s.value for s in at.success), [s.value for s in at.success])
chk("...y ahí está su formulario", len(rad(at)) == 18)
next(d for d in at.date_input if "fc_fecha" in d.key).set_value(dt.date(2026, 11, 2)).run()
chk("al volver a su día, vuelve", any("FC-0007" in s.value for s in at.success), [s.value for s in at.success])

sec("15. v638 · Mark all as passed (con clics)")
at = pinta()
_bt = btn(at, "fc_todo")
chk("⚠️ el botón está, y el formulario sigue naciendo vacío", _bt is not None and _bt.disabled is False and all(r.value is None for r in rad(at)))
chk("con su rótulo", "Mark all as passed" in _bt.label, _bt.label)
_bt.click().run()
chk("⚠️ marca ✓ los 18", all(r.value == "pass" for r in rad(at)), [r.value for r in rad(at)])
chk("⚠️ y le llega al NAVEGADOR (trampa 31: el valor se asigna)", all(r.proto.set_value for r in rad(at)), [r.proto.set_value for r in rad(at)][:3])
chk("⚠️ marcar no envía nada", "_enviado" not in at.session_state)
chk("hecho, se apaga sin desaparecer", btn(at, "fc_todo").disabled is True)
rad(at)[6].set_value("fail").run()
chk("⚠️ se puede cambiar cualquiera a X, y pide sus observaciones", btn(at, "fc_submit").disabled is True and any("7" in c.value for c in at.caption if "Still to complete" in c.value), [c.value for c in at.caption][:3])
at = pinta()
rad(at)[4].set_value("fail").run()
next(i for i in at.text_input if i.key.endswith("_fc05")).set_value("cable pisado").run()
rad(at)[9].set_value("pass").run()
btn(at, "fc_todo").click().run()
_v = {r.key[-4:]: r.value for r in rad(at)}
chk("⚠️ una X NO se pisa", _v["fc05"] == "fail", _v)
chk("...ni sus observaciones", next(i for i in at.text_input if i.key.endswith("_fc05")).value == "cable pisado")
chk("...y el resto queda en ✓", [k for k, x in _v.items() if x != "pass"] == ["fc05"], _v)
at = pinta()
btn(at, "fc_todo").click().run()
next(i for i in at.text_input if i.key.startswith("fc_ini_")).set_value("FT")
at.run()
btn(at, "fc_submit").click().run()
_e = at.session_state["_enviado"]
chk("se envían los 18 en ✓, como marcados uno a uno", len(_e["res"]) == 18 and all(x["res"] == "pass" for x in _e["res"].values()), _e["res"])
at = pinta(lienzo=True)
btn(at, "fc_todo").click().run()
chk("⚠️ la firma sigue siendo obligatoria", btn(at, "fc_submit").disabled is True and any("signature" in c.value for c in at.caption if "Still to complete" in c.value), [c.value for c in at.caption][:3])
_bk = funcion(leer("core/falsecar_ui.py"), "_formulario")
chk("el botón lleva obra, día y generación", 'key=f"fc_todo_{kp}"' in _bk and "args=(kp,)" in _bk)
chk("el asistente lo conoce", "Mark all as passed" in leer("core/chat_agent.py"))

print("\n=== verif_v636: %d OK, %d FALLOS ===" % (n_ok, len(fallos)))
for f in fallos:
    print("   -", f)
sys.exit(1 if fallos else 0)
