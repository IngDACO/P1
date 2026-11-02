# -*- coding: utf-8 -*-
"""Daily False Car Checklist (v636): el formato diario de las obras con false car.

Decisiones del usuario (02/11/2026), con la foto del formato de CI Liftworx delante:
  · Se digitaliza «tal y como se ve»: los 18 puntos con su texto literal.
  · Se marca al CREAR la obra (`stages.FALSE_CAR`); las ya creadas cuentan como que no tienen.
  · Se exige desde que el false car está MONTADO hasta que se retira: lo dicen las actividades
    marcadas, no el calendario (`periodo`).
  · Uno por obra y día: lo hace el primero que llega y los demás lo firman, como el Pre-Start.
  · Cada punto ✓ o X, sin respuesta por defecto, y con X las observaciones son obligatorias.
  · Con una X se abre una alarma a la oficina y la pantalla dice que no se use.
  · Igual que el Pre-Start, avisa y no bloquea.

## ⚠️ El texto de los puntos es el del FORMATO, y es un documento de seguridad
No se corrige ni se traduce al guardar: se guarda la CLAVE (`fc09`), como el Pre-Start, y el texto
se lee de `CHECKS`. Cambiarlo cambiaría lo que dice un registro ya firmado.
"""
import datetime as _dt
import io
import json
import logging

import streamlit as st

from core import clock, columnas, timeclock
from core.i18n import d, t
from core.num import num as _num, parse_date as _parse_date

logger = logging.getLogger(__name__)

SHEET = "FalseCarChecks"
# ⚠️ Regla v363: columnas NUEVAS siempre al FINAL.
HEADERS = ["ID", "ProjectID", "Group", "Date", "Time", "ResultsJSON", "Failed", "Signers",
           "File", "DriveID", "CreatedBy", "Created"]
_COL = {h: i + 1 for i, h in enumerate(HEADERS)}

PASA, FALLA = "pass", "fail"
SIMBOLO = {PASA: "✓", FALLA: "X"}
HACER, FIRMAR = "do", "sign"          # lo que a una persona le toca hoy (`pendiente_hoy`)

TITULO = "Daily False Car Checklist"
SUBTITULO = "Daily inspections are to be carried out according to the following schedule."
CHECKS = [
    ("fc01", "Check whether the steel wire rope is securely fixed."),
    ("fc02", "Check whether there are any missing, abnormal wear, corrosion, component "
             "deformation, cracks, or desoldering in all parts of the equipment."),
    ("fc03", "Check all parts, especially the telescopic and movable parts, are not loose, "
             "abnormal or misaligned."),
    ("fc04", "Check whether the hoist and safety lock are securely installed."),
    ("fc05", "Check whether the cables are not flattened, damaged, and if the joints are "
             "securely connected."),
    ("fc06", "Check whether the safety gear roller/pull rod can reset properly."),
    ("fc07", "Check whether the trigger can open and operate normally."),
    ("fc08", "Check whether the gap between the guide shoe and the guide rail is correct."),
    ("fc09", "Run 3-5 times without load and check whether the hoist travels up and down correctly\n"
             "Check whether there is any abnormal noises, odor, or overheating in the hoist."),
    ("fc10", "Manually lock the safety lock, and check whether the safety lock can lock the "
             "platform when descending."),
    ("fc11", "Manually lower the trigger handle and check whether the safety gear can lock the "
             "platform."),
    ("fc12", "Check if platform shaking amplitude is too large."),
    ("fc13", "Anti-derailment switch function is normal."),
    ("fc14", "Whether the manual descent is normal (Brake Release)."),
    ("fc15", "Check all the functions on the pendant work correctly."),
    ("fc16", "Press the rope spring and check that the platform cannot continue to move upwards."),
    ("fc17", "Check whether the unlocking and locking functions of the safety lock are normal."),
    ("fc18", "A safety lock with power outage protection, manually locking the safety lock, the "
             "platform should not be able to operate."),
]
_NUMERO = {k: i for i, (k, _x) in enumerate(CHECKS, 1)}
_TEXTO = dict(CHECKS)


def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378): va en la CLAVE de caché."""
    try:
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""


def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    """⚠️ `get_sheet` CREA la hoja si falta: solo lo usan las escrituras."""
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("falsecar: no se pudo abrir %s: %s", SHEET, e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """⚠️ SIN cabeceras, y por eso va en `hojas.HOJAS_LECTURA`: fuera del lote leería vacío para
    siempre (v461/v507/v514/v610)."""
    from core import hojas
    return hojas.registros(SHEET) or []


def _records():
    return _records_cached(_libro_de(SHEET))


def _invalidate():
    from core import hojas
    hojas.invalidar(SHEET)
    try:
        _records_cached.clear()
    except Exception as e:
        logger.warning("falsecar._invalidate: %s", e)


# ═════════════════════════════════════════════════════════════════
# ¿Esta obra lo necesita, y desde cuándo?
# ═════════════════════════════════════════════════════════════════
def tiene(prj) -> bool:
    """¿La obra se creó con false car? Lo dice su plan sellado (v512): una obra anterior no lo
    lleva y cuenta como que no tiene (decisión del usuario). Sin una marca aparte que pueda
    contradecir al plan."""
    from core import projects as P
    from core import stages as S
    return S.FC_MONTAR in (P.plan_etapas(prj or {}).get("condicionales") or ())


def periodo(prj) -> tuple:
    """`(desde, hasta)`: el día en que quedó montado y el día en que se retiró, o None.

    ⚠️ Lo dice lo MARCADO y entero (100%), con su día de trabajo (v525): «Install sky climber» a
    medias todavía no es una máquina que se pueda usar."""
    from core import stage_progress as SP
    from core import stages as S
    desde = hasta = None
    for r in SP.creditos(str((prj or {}).get("ID", ""))):
        if _num(r.get("Pct")) < 100:
            continue
        _a = str(r.get("Activity", ""))
        if _a == S.FC_MONTAR:
            desde = _parse_date(SP._fecha_de(r))
        elif _a == S.FC_RETIRAR:
            hasta = _parse_date(SP._fecha_de(r))
    return desde, hasta


def _dentro(per, dia) -> bool:
    """¿Ese día cae en el periodo? El de la retirada ya no: se está desmontando, no usando."""
    desde, hasta = per
    return bool(desde) and desde <= dia and not (hasta and hasta <= dia)


def activo(prj, dia=None) -> bool:
    """¿Ese día había que hacer el checklist? Desde que está montado hasta que se retira."""
    if not tiene(prj):
        return False
    return _dentro(periodo(prj), dia or clock.today((prj or {}).get("Group")))


# ═════════════════════════════════════════════════════════════════
# Lecturas
# ═════════════════════════════════════════════════════════════════
def leer(r) -> dict:
    """Una fila, legible: los 18 puntos en orden, quién firmó y lo que falló."""
    try:
        _res = json.loads(r.get("ResultsJSON", "") or "{}") or {}
    except Exception:
        _res = {}
    try:
        _fir = json.loads(r.get("Signers", "") or "[]") or []
    except Exception:
        _fir = []
    puntos = [{"n": _NUMERO[k], "clave": k, "texto": x,
               "res": str((_res.get(k) or {}).get("res", "")),
               "nota": str((_res.get(k) or {}).get("nota", ""))} for k, x in CHECKS]
    return {"id": str(r.get("ID", "")), "fecha": str(r.get("Date", "")), "hora": str(r.get("Time", "")),
            "pid": str(r.get("ProjectID", "")), "puntos": puntos,
            "fallos": [p for p in puntos if p["res"] == FALLA],
            "firmas": [str(a.get("name", "")).strip() for a in _fir if a.get("name")],
            "firmas_usuarios": [str(a.get("usuario", "")).strip() for a in _fir
                                if str(a.get("usuario", "") or "").strip()],
            "firmas_sin_login": [str(a.get("name", "")).strip() for a in _fir if a.get("name")
                                 and not str(a.get("usuario", "") or "").strip()],
            "archivo": str(r.get("File", "")), "drive_id": str(r.get("DriveID", ""))}


def de_obra(pid) -> list:
    """Los checklists de una obra, el más reciente primero."""
    return sorted([r for r in _records() if str(r.get("ProjectID", "")).strip() == str(pid).strip()],
                  key=lambda r: (str(r.get("Date", "")), str(r.get("ID", ""))), reverse=True)


def del_dia(pid, dia) -> dict:
    """El checklist de esa obra ese día, leído, o {}."""
    filas = [r for r in _records() if str(r.get("ProjectID", "")).strip() == str(pid).strip()
             and _parse_date(r.get("Date")) == dia]
    return leer(filas[-1]) if filas else {}


def hecho_hoy(pid, grupo: str = "") -> bool:
    """¿Esa obra tiene el de HOY? Por obra y día, no por persona, como el Pre-Start (v374)."""
    return bool(del_dia(pid, clock.today(grupo)))


def _norm(s) -> str:
    from core.prestart import _norm_nombre
    return _norm_nombre(s)


def pendiente_de_firma(pid, grupo: str = "", persona: str = "", usuario: str = "") -> dict:
    """El de HOY que a esa persona le falta firmar, o {}: el mismo criterio que el Pre-Start. El
    login manda sobre el nombre, que puede repetirse (v418)."""
    reg = del_dia(pid, clock.today(grupo))
    quien, quien_u = _norm(persona), str(usuario or "").strip().lower()
    if not reg or not (quien or quien_u):
        return {}
    if quien_u and quien_u in {u.lower() for u in reg["firmas_usuarios"]}:
        return {}
    _nombres = reg["firmas_sin_login"] if quien_u else reg["firmas"]
    if quien and quien in {_norm(a) for a in _nombres}:
        return {}
    return reg


def pendiente_hoy(prj, grupo, persona: str = "", usuario: str = "") -> str:
    """Lo que a esa persona le toca HOY con el checklist de esa obra: `HACER`, `FIRMAR` o "". Una
    sola definición para el diálogo, la banda y el menú lateral."""
    if not activo(prj, clock.today(grupo)):
        return ""
    pid = str((prj or {}).get("ID", ""))
    if not hecho_hoy(pid, grupo):
        return HACER
    return FIRMAR if pendiente_de_firma(pid, grupo, persona, usuario) else ""


def dias_sin_registro(grupo, dias=30, pid=None, hoy=None) -> list:
    """Los días que hubo gente fichada en una obra y falta su Pre-Start o su checklist.

    ⚠️ Hasta AYER: el de hoy puede estar aún por hacer, y para eso están los avisos. Cuenta por obra
    y día, como los propios documentos. `dias=None`: desde siempre (el expediente de entrega).
    Devuelve `[{fecha, pid, nombre, usuarios, falta}]`, lo más reciente primero, con `falta`
    entre `prestart` y `falsecar`."""
    from core import prestart as PS
    from core import projects as P
    hoy = hoy or clock.today(grupo)
    ayer = hoy - _dt.timedelta(days=1)
    desde = None if dias is None else hoy - _dt.timedelta(days=int(dias))
    obras = timeclock.obras_por_dia(grupo, desde, ayer)
    con_ps = {(str(r.get("ProjectID", "")).strip(), _parse_date(r.get("Date"))) for r in PS._records()}
    con_fc = {(str(r.get("ProjectID", "")).strip(), _parse_date(r.get("Date"))) for r in _records()}
    _per, out = {}, []
    for (dia, p), info in obras.items():
        if pid and str(p) != str(pid):
            continue
        falta = [] if (p, dia) in con_ps else ["prestart"]
        if p not in _per:                  # una vez por obra: 30 días no son 30 consultas
            _prj = P.get_project(p) or {}
            _per[p] = periodo(_prj) if tiene(_prj) else (None, None)
        if (p, dia) not in con_fc and _dentro(_per[p], dia):
            falta.append("falsecar")
        if falta:
            out.append({"fecha": dia, "pid": p, "nombre": info["nombre"],
                        "usuarios": sorted(info["usuarios"]), "falta": falta})
    return sorted(out, key=lambda x: (x["fecha"], x["nombre"]), reverse=True)


# ═════════════════════════════════════════════════════════════════
# Escrituras — ⚠️ leen FRESCO para decidir dónde escribir (v323)
# ═════════════════════════════════════════════════════════════════
def _next_id(recs) -> str:
    mx = 0
    for r in recs:
        _v = str(r.get("ID", ""))
        if _v.startswith("FC-"):
            mx = max(mx, int(_num(_v[3:]) or 0))
    from core import hojas
    try:
        return hojas.siguiente_id_libre("FC-", mx, propia=SHEET)
    except Exception as e:                       # nunca impedir registrarlo
        logger.warning("falsecar._next_id: %s", e)
        return "FC-%04d" % (mx + 1)


def filename_for(fecha, iniciales="") -> str:
    """`ddmmyyyy False Car AB.pdf`: como el Pre-Start, y se distingue de él en Files."""
    _f = fecha.strftime("%d%m%Y") if hasattr(fecha, "strftime") else clock.now().strftime("%d%m%Y")
    _i = str(iniciales or "").strip().upper()
    return "%s False Car%s.pdf" % (_f, (" " + _i) if _i else "")


def valida(resultados) -> str:
    """Lo que le falta al formulario, o "". ⚠️ En el motor, no solo en la pantalla: una X sin
    observaciones abriría una alarma que no dice nada (v623)."""
    _res = resultados or {}
    _sin = [_NUMERO[k] for k, _x in CHECKS if (_res.get(k) or {}).get("res") not in (PASA, FALLA)]
    if _sin:
        return t("Answer every item: {n} still to answer.", n=len(_sin))
    _nota = [str(_NUMERO[k]) for k, _x in CHECKS if _res[k]["res"] == FALLA
             and not str(_res[k].get("nota", "")).strip()]
    if _nota:
        return t("Write the remarks of the items marked X: {n}.", n=", ".join(_nota))
    return ""


def submit(data: dict) -> dict:
    """Genera el PDF, lo archiva y guarda el checklist; con alguna X, abre la alarma.
    `{ok, id, pdf, filename, drive_id, fallos, alarma, error}`."""
    res = {"ok": False, "id": "", "pdf": None, "filename": "", "drive_id": "", "fallos": [],
           "alarma": False, "error": ""}
    pid, grupo = str(data.get("proyecto_id", "")).strip(), str(data.get("grupo", "")).strip()
    _hoy = clock.today(grupo)
    _f = data.get("fecha")
    dia = _f if hasattr(_f, "year") else _hoy
    resultados = data.get("resultados") or {}
    _err = valida(resultados)
    if _err:
        res["error"] = _err
        return res
    # ⚠️ El campo registra el de HOY, como el Pre-Start (v623): la oficina sí puede ponerse al día.
    if not data.get("gestor") and dia != _hoy:
        res["error"] = t("The checklist can only be recorded for today.")
        return res
    w = _ws()
    if w is None:
        res["error"] = t("Could not open the false car sheet.")
        return res
    try:
        recs = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))
    except Exception as e:
        res["error"] = f"{t('Could not record the checklist')}: {e}"
        return res
    # Uno por obra y día: el segundo que llega lo firma, no lo rehace.
    if any(str(r.get("ProjectID", "")).strip() == pid and _parse_date(r.get("Date")) == dia
           for r in recs):
        res["error"] = t("This job already has the checklist for that day.")
        return res
    cid = _next_id(recs)
    nombre, iniciales = str(data.get("nombre", "")), str(data.get("iniciales", ""))
    usuario = str(data.get("usuario", ""))
    hora = str(data.get("hora", "") or clock.now(grupo).strftime("%H:%M"))
    fallos = [_NUMERO[k] for k, _x in CHECKS if resultados[k]["res"] == FALLA]
    res["fallos"] = fallos

    try:
        from core import falsecar_pdf
        pdf = falsecar_pdf.generate_pdf({**data, "id": cid, "fecha": dia, "hora": hora})
    except Exception as e:
        res["error"] = f"{t('Could not generate the PDF')}: {e}"
        return res
    fname = filename_for(dia, iniciales)
    res["pdf"], res["filename"] = pdf, fname

    drive_id = ""
    try:
        from core import drive_store
        from core import projects
        if pid and drive_store.is_available():
            drive_id = drive_store.upload(pid, fname, pdf, "application/pdf")
            projects.add_document(pid, fname, "falsecar", drive_id, usuario)
    except Exception as e:
        logger.warning("falsecar: archivado en Drive falló: %s", e)
    res["drive_id"] = drive_id

    _firma = {"name": nombre, "initial": iniciales, "firmado": bool(data.get("firma")), "hora": hora}
    if usuario:
        _firma["usuario"] = usuario
    try:
        # ⚠️ La firma va solo al PDF, como en el Pre-Start (v383): en la hoja, QUE firmó.
        w.append_row([cid, pid, grupo, dia.strftime("%Y-%m-%d"), hora,
                      json.dumps(resultados, ensure_ascii=False),
                      ",".join(str(n) for n in fallos),
                      json.dumps([_firma], ensure_ascii=False), fname, drive_id, usuario,
                      clock.now(grupo).strftime("%Y-%m-%d %H:%M")], value_input_option="RAW")
    except Exception as e:
        res["error"] = f"{t('Could not record the checklist')}: {e}"
        return res
    _invalidate()
    res["ok"], res["id"] = True, cid

    # ⚠️ UNA alarma con todos los puntos, no una por punto: `report_problem` también avisa (v373).
    if fallos:
        try:
            from core import alerts
            _txt = " · ".join("%d (%s)" % (n, str(resultados[k]["nota"]).strip())
                              for k, n in _NUMERO.items() if n in fallos)
            ok, _x = alerts.report_problem(
                pid, grupo, "False car check with %d item(s) marked X: %s" % (len(fallos), _txt),
                usuario, data.get("proyecto_nombre", ""))
            res["alarma"] = bool(ok)
        except Exception as e:
            logger.warning("falsecar: no se pudo crear la alarma: %s", e)
    return res


def firmar(cid: str, grupo: str, nombre: str, iniciales: str = "", firma_png=None,
           usuario: str = "") -> dict:
    """Añade la firma de quien llega después, en una hoja de anexo, como el Pre-Start (v403): el
    documento firmado no se reescribe. `{ok, error, archivado}`."""
    res = {"ok": False, "error": "", "archivado": False}
    cid = str(cid or "").strip()
    if not cid or not str(nombre or "").strip():
        res["error"] = t("The checklist or the signer name is missing.")
        return res
    w = _ws()
    if w is None:
        res["error"] = t("Could not open the false car sheet.")
        return res
    filas = columnas.canonizar(w.get_all_records(numericise_ignore=["all"]))   # FRESCO (v323)
    idx = next((i for i, r in enumerate(filas) if str(r.get("ID", "")).strip() == cid), -1)
    if idx < 0:
        res["error"] = t("Checklist not found.")
        return res
    fila = filas[idx]
    hora = clock.now(grupo).strftime("%H:%M")
    pid, drive_id = str(fila.get("ProjectID", "")), str(fila.get("DriveID", "") or "")

    # El PDF nuevo ANTES de tocar la fila, y el viejo se borra DESPUÉS (lección de v343).
    nuevo_id = ""
    try:
        from core import drive_store
        from core import prestart_pdf
        from core import projects
        anexo = prestart_pdf.generate_anexo_firmas_pdf({
            "marca": grupo, "ps_id": cid, "fecha": str(fila.get("Date", "")), "proyecto": pid,
            "location": "", "etiqueta": d("False car"),
            "titulo": d("SIGNATURE ADDENDUM — people who signed after this check"),
            "sub": d("These people arrived after this daily check and signed it on arrival."),
            "nota": d("This addendum does not modify the original checklist: it is attached to "
                      "it. Each signature keeps the time it was taken."),
            "firmas": [{"name": nombre, "initial": iniciales, "sig": firma_png, "hora": hora}]})
        if drive_id and drive_store.is_available():
            from pypdf import PdfReader, PdfWriter
            wr = PdfWriter()
            for _b in (drive_store.download(drive_id), anexo):
                for p in PdfReader(io.BytesIO(_b)).pages:
                    wr.add_page(p)
            out = io.BytesIO()
            wr.write(out)
            fname = str(fila.get("File", "")) or f"{cid}.pdf"
            nuevo_id = drive_store.upload(pid, fname, out.getvalue(), "application/pdf")
            projects.add_document(pid, fname, "falsecar", nuevo_id, usuario or nombre)
    except Exception as e:                                        # noqa: BLE001
        logger.warning("falsecar.firmar: no se pudo rehacer el PDF: %s", e)

    try:
        asist = json.loads(fila.get("Signers", "") or "[]")
    except Exception:
        asist = []
    _nuevo = {"name": str(nombre), "initial": str(iniciales or ""), "firmado": bool(firma_png),
              "hora": hora, "tarde": True}
    if str(usuario or "").strip():
        _nuevo["usuario"] = str(usuario).strip()
    asist.append(_nuevo)
    try:
        w.update_cell(idx + 2, _COL["Signers"], json.dumps(asist, ensure_ascii=False))
        if nuevo_id:
            w.update_cell(idx + 2, _COL["DriveID"], nuevo_id)
    except Exception as e:                                        # noqa: BLE001
        res["error"] = f"{t('Could not save the signature')}: {e}"
        return res
    _invalidate()

    if nuevo_id and drive_id and nuevo_id != drive_id:            # ya no hace falta (best-effort)
        try:
            from core import drive_store
            from core import projects
            projects.delete_document_record(pid, drive_id)
            drive_store.delete(drive_id)
        except Exception as e:                                    # noqa: BLE001
            logger.warning("falsecar.firmar: no se pudo borrar el PDF anterior: %s", e)
    res["ok"], res["archivado"] = True, bool(nuevo_id)
    return res


def borrar_de_obra(pid) -> int:
    """Al borrar la OBRA (`projects.delete_project`), como los partes y las tareas: vive en otra
    hoja y quedaría apuntando a nada. ⚠️ Solo si los hay: `_ws` CREA la hoja."""
    if not any(str(r.get("ProjectID", "")).strip() == str(pid) for r in _records()):
        return 0
    w = _ws()
    if w is None:
        return 0
    filas = [i + 2 for i, r in enumerate(columnas.canonizar(w.get_all_records(numericise_ignore=["all"])))
             if str(r.get("ProjectID", "")).strip() == str(pid)]
    for f in sorted(filas, reverse=True):         # de abajo arriba: borrar desplaza lo de debajo
        w.delete_rows(f)
    if filas:
        _invalidate()
    return len(filas)
