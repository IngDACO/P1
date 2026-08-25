"""
Pre-Start diario (Daily Pre-Start) — registro de la charla de seguridad antes de
empezar en obra, por proyecto. Basado en el formato de CI Liftworx.

Flujo al enviar: genera el PDF (marca = nombre del grupo) → lo archiva en la carpeta
del proyecto en Drive + lo registra como documento → guarda una fila en la hoja
`PreStarts` → si hay Near Miss/Hazard, abre una alarma del proyecto.

Nombre de archivo: `ddmmyyyy AB CD EF.pdf` (fecha + iniciales de los asistentes).
"""
import io
import json
import logging

import streamlit as st

from core import timeclock
from core import clock
from core.num import parse_date as _parse_date

logger = logging.getLogger(__name__)

SHEET   = "PreStarts"
HEADERS = ["ID", "ProyectoID", "Grupo", "Fecha", "Hora", "Location", "Facilitador",
           "ActividadesNotas", "NearMiss", "NearMissDesc", "S1JSON", "S3JSON",
           "NotasGenerales", "Asistentes", "Archivo", "DriveID", "CreadoPor", "Creado"]

# Sección 1 — YES/NO
CHECKS_S1 = [
    ("permisos",        "Permisos obtenidos y revisados por cambios desde su emisión"),
    ("toolbox",         "Notas del toolbox del builder revisadas y discutidas"),
    ("subcontratistas", "Coordinación con subcontratistas y otros oficios en obra"),
    ("preop",           "Chequeos/inspecciones pre-operacionales diarios hechos o asignados"),
]
# Sección 3 — Shaft Protection: NO/YES/N/A
CHECKS_S3 = [
    ("cages",        "Landing cages íntegras (fijas, seguras, sin huecos inaceptables)"),
    ("landings",     "Landings libres de escombros y herramientas que puedan caer al hueco"),
    ("penetrations", "Penetraciones del hueco adecuadamente cubiertas"),
]
OPTS_YN  = ["YES", "NO"]
OPTS_YNA = ["YES", "NO", "N/A"]



def _libro_de(_hoja) -> str:
    """El id del libro que le toca a esta hoja AHORA (v378).

    Va como primer argumento del lector cacheado para que la clave distinga
    inquilinos. No se usa dentro: `hojas.registros` resuelve el libro por su
    cuenta; aquí solo hace falta que el VALOR entre en la clave.
    """
    try:
        from core import timeclock
        return timeclock.sheet_id_para(_hoja)
    except Exception:
        return ""

def is_configured() -> bool:
    return timeclock._secrets_present()


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("prestart: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str) -> list:
    """Registros de SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(SHEET, HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(SHEET))
def _invalidate():
    # ⚠️ v339: además de la caché propia hay que tirar el LOTE compartido
    # (`hojas._lote`). Si no, tras escribir, el dato seguiría saliendo del lote
    # cacheado hasta 120 s y parecería que no se guardó.
    from core import hojas
    hojas.invalidar()
    try:
        _records_cached.clear()
    except Exception:
        pass


_LABELS = {k: v for k, v in CHECKS_S1} | {k: v for k, v in CHECKS_S3}


def leer(r) -> dict:
    """Descompone una fila de pre-start en algo legible (v158).

    ⚠️ S1JSON/S3JSON/Asistentes se escribían desde v97 y **nadie los leía**: el
    historial solo mostraba fecha/facilitador/near-miss. Un check en **NO** es
    una alerta de seguridad y quedaba invisible sin abrir el PDF.

    Devuelve {checks:[{label,estado}], n_no, asistentes:[...], near_miss, ...}.
    """
    import json as _json

    def _parse(col):
        try:
            return _json.loads(r.get(col, "") or "{}")
        except Exception:
            return {}

    s1, s3 = _parse("S1JSON"), _parse("S3JSON")
    checks = []
    for k, v in list(s1.items()) + list(s3.items()):
        checks.append({"label": _LABELS.get(k, k), "estado": str(v).upper()})
    n_no = sum(1 for c in checks if c["estado"] == "NO")

    try:
        asist = _json.loads(r.get("Asistentes", "") or "[]")
    except Exception:
        asist = []

    return {
        "id": r.get("ID", ""), "fecha": r.get("Fecha", ""), "hora": r.get("Hora", ""),
        "facilitador": r.get("Facilitador", ""), "location": r.get("Location", ""),
        "near_miss": str(r.get("NearMiss", "")).upper() == "YES",
        "near_miss_desc": r.get("NearMissDesc", ""),
        "checks": checks, "n_no": n_no,
        "act_notes": r.get("ActividadesNotas", ""), "gen_notes": r.get("NotasGenerales", ""),
        "asistentes": [str(a.get("name", "")).strip() for a in asist if a.get("name")],
        "archivo": r.get("Archivo", ""), "drive_id": r.get("DriveID", ""),
    }


def list_prestarts(pid) -> list:
    """Pre-starts de un proyecto, más recientes primero."""
    out = [r for r in _records() if str(r.get("ProyectoID", "")) == str(pid)]
    return list(reversed(out))


def hecho_hoy(pid, grupo: str = "") -> bool:
    """¿La obra tiene ya el Pre-Start de HOY? (v374)

    ⚠️ Por OBRA y DÍA, **no por persona**: el Pre-Start es la charla de seguridad del
    SITIO —una por obra y día, con sus asistentes—, así que si el facilitador ya la
    hizo, al resto de la cuadrilla no hay nada que recordarle. Decisión del usuario.

    Sale de `_records()`, que ya está cacheado y viaja en el lote de v339:
    **0 llamadas nuevas** a Sheets aunque se consulte en cada pasada.
    """
    pid = str(pid or "").strip()
    if not pid:
        return False
    hoy = clock.today(grupo)
    for r in _records():
        if str(r.get("ProyectoID", "")).strip() != pid:
            continue
        # ⚠️ Se PARSEA la fecha en vez de comparar el texto: `submit` la escribe en
        # ISO, pero una fila vieja o tocada a mano puede traer `20/08/2026` y una
        # comparación de cadenas diría «no hecho» con el Pre-Start delante — el
        # mismo fallo que v323 destapó en las facturas que se caían del P&L.
        if _parse_date(r.get("Fecha")) == hoy:
            return True
    return False


def _norm_nombre(s) -> str:
    """Nombre comparable: sin acentos, sin dobles espacios y sin may/min.

    ⚠️ Los asistentes se TECLEAN, así que comparar en crudo dejaría fuera a
    «José Pérez» frente a «jose perez». Vive aquí y no en `num.py` porque es una
    regla de este dominio, no de números; si algún día hace falta en otro sitio, se
    sube a un módulo común en vez de copiarse (la lección de los cinco `_num`, v323).
    """
    import unicodedata
    t = unicodedata.normalize("NFKD", str(s or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.lower().split())


def pendiente_de_firma(pid, grupo: str = "", persona: str = "") -> dict:
    """El Pre-Start de HOY de esa obra que a `persona` le falta por firmar, o {}.

    ⚠️ Complementa a `hecho_hoy`, no lo sustituye: aquel responde «¿hay que HACER la
    charla?» (por obra y día) y este «¿tengo que FIRMARLA yo?». Son dos preguntas
    distintas y confundirlas fue el hueco de v374: en cuanto el facilitador emitía el
    Pre-Start, quien fichaba después no recibía ningún aviso y **acababa trabajando en
    esa obra sin constar en el documento de seguridad**.

    Devuelve {} si no hay Pre-Start hoy (entonces manda `hecho_hoy`: hay que hacerlo)
    o si la persona ya está entre los asistentes.
    """
    pid = str(pid or "").strip()
    quien = _norm_nombre(persona)
    if not pid or not quien:
        return {}
    hoy = clock.today(grupo)
    # ⚠️ v406: se miran TODAS las charlas del día, no la primera. Nada impide dos
    # Pre-Starts de la misma obra el mismo día (dos turnos, dos cuadrillas… o un
    # duplicado), y mirando solo la primera fila pasaba esto: quien firmaba la
    # SEGUNDA seguía viendo «te falta firmar» por la primera, para siempre. Salió al
    # sembrar sin querer un segundo Pre-Start en una obra que ya tenía el suyo.
    candidatos = [r for r in _records()
                  if str(r.get("ProyectoID", "")).strip() == pid
                  and _parse_date(r.get("Fecha")) == hoy]
    if not candidatos:
        return {}
    for r in candidatos:
        d = leer(r)
        # ⚠️ `leer` devuelve los asistentes ya como texto legible; se comparan
        # normalizados. Si el nombre no casa se pedirá firmar otra vez, que es el
        # fallo tolerable: el intolerable es no pedirlo nunca.
        if quien in {_norm_nombre(a) for a in d.get("asistentes", [])}:
            return {}                      # firmó ALGUNA de las de hoy: no se insiste
    # ⚠️ Si hay varias y no firmó ninguna, se ofrece la ÚLTIMA: las filas se añaden al
    # final, así que es la charla más reciente — la que con más probabilidad es la suya.
    # No se puede saber cuál le tocaba, así que se dice cuántas hay (`otras`) en vez de
    # elegir en silencio.
    r = candidatos[-1]
    d = leer(r)
    return {"id": str(r.get("ID", "")), "fecha": str(r.get("Fecha", "")),
            "facilitador": str(r.get("Facilitador", "")),
            "location": str(r.get("Location", "")),
            "drive_id": str(r.get("DriveID", "")),
            "archivo": str(r.get("Archivo", "")),
            "asistentes": d.get("asistentes", []),
            "otras": len(candidatos) - 1}


def firmar(ps_id: str, grupo: str, nombre: str, iniciales: str = "",
           firma_png=None, usuario: str = "") -> dict:
    """Añade la firma de quien llegó después AL Pre-Start ya emitido (v403).

    Devuelve {ok, error, pdf, drive_id}. El PDF resultante es el original **más una
    hoja de anexo**: ver `prestart_pdf.generate_anexo_firmas_pdf` para por qué no se
    regenera el documento entero.
    """
    res = {"ok": False, "error": "", "pdf": None, "drive_id": ""}
    ps_id = str(ps_id or "").strip()
    if not ps_id or not str(nombre or "").strip():
        res["error"] = "Falta el Pre-Start o el nombre de quien firma."
        return res

    w = _ws()
    if w is None:
        res["error"] = "No se pudo abrir la hoja de pre-starts."
        return res
    # ⚠️ FRESCO, no de la caché: esto decide en qué FILA se escribe (regla v323).
    filas = w.get_all_records(numericise_ignore=["all"])
    idx = next((i for i, r in enumerate(filas) if str(r.get("ID", "")).strip() == ps_id), -1)
    if idx < 0:
        res["error"] = f"No se encontró el Pre-Start {ps_id}."
        return res
    fila = filas[idx]
    hora = clock.now(grupo).strftime("%H:%M")

    # 1) el anexo, y el PDF final = original + anexo (pypdf, ya es dependencia)
    nuevo_pdf, drive_id = None, str(fila.get("DriveID", "") or "")
    try:
        from core import drive_store
        from core import prestart_pdf
        anexo = prestart_pdf.generate_anexo_firmas_pdf({
            "marca": grupo, "ps_id": ps_id, "fecha": str(fila.get("Fecha", "")),
            "proyecto": str(fila.get("ProyectoID", "")),
            "location": str(fila.get("Location", "")),
            "firmas": [{"name": nombre, "initial": iniciales,
                        "sig": firma_png, "hora": hora}]})
        if drive_id and drive_store.is_available():
            from pypdf import PdfReader, PdfWriter
            orig = drive_store.download(drive_id)
            wr = PdfWriter()
            for p in PdfReader(io.BytesIO(orig)).pages:
                wr.add_page(p)
            for p in PdfReader(io.BytesIO(anexo)).pages:
                wr.add_page(p)
            out = io.BytesIO()
            wr.write(out)
            nuevo_pdf = out.getvalue()
        else:
            nuevo_pdf = anexo          # sin Drive, al menos queda el anexo suelto
    except Exception as e:                                        # noqa: BLE001
        logger.warning("prestart.firmar: no se pudo componer el PDF: %s", e)
    res["pdf"] = nuevo_pdf

    # 2) subir el PDF nuevo ANTES de tocar la fila, y borrar el viejo DESPUÉS
    #    ⚠️ El orden importa (lección de v343): si se borrara primero y algo fallara,
    #    el Pre-Start se quedaría sin documento. Así, en el peor caso hay un archivo
    #    de más — visible y recuperable — en vez de uno de menos.
    nuevo_id = ""
    try:
        from core import drive_store
        from core import projects
        pid = str(fila.get("ProyectoID", ""))
        fname = str(fila.get("Archivo", "")) or f"{ps_id}.pdf"
        if nuevo_pdf and pid and drive_store.is_available():
            nuevo_id = drive_store.upload(pid, fname, nuevo_pdf, "application/pdf")
            projects.add_document(pid, fname, "prestart", nuevo_id, usuario or nombre)
    except Exception as e:                                        # noqa: BLE001
        logger.warning("prestart.firmar: no se pudo archivar el PDF: %s", e)

    # 3) la fila: el asistente se AÑADE a los que ya estaban
    try:
        asist = json.loads(fila.get("Asistentes", "") or "[]")
    except Exception:
        asist = []
    asist.append({"name": str(nombre), "initial": str(iniciales or ""),
                  "firmado": bool(firma_png), "hora": hora, "tarde": True})
    try:
        col_a = HEADERS.index("Asistentes") + 1
        w.update_cell(idx + 2, col_a, json.dumps(asist, ensure_ascii=False))
        if nuevo_id:
            w.update_cell(idx + 2, HEADERS.index("DriveID") + 1, nuevo_id)
        _invalidate()
    except Exception as e:                                        # noqa: BLE001
        res["error"] = f"No se pudo guardar la firma: {e}"
        return res

    # 4) ya con la fila apuntando al nuevo, el viejo sobra (best-effort)
    if nuevo_id and drive_id and nuevo_id != drive_id:
        try:
            from core import drive_store
            drive_store.delete(drive_id)
        except Exception as e:                                    # noqa: BLE001
            logger.warning("prestart.firmar: no se pudo borrar el PDF anterior: %s", e)

    res["ok"] = True
    res["drive_id"] = nuevo_id or drive_id
    return res


def _next_id(recs) -> str:
    mx = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("PS-"):
            try:
                mx = max(mx, int(i.split("-")[1]))
            except Exception:
                pass
    return f"PS-{mx + 1:04d}"


def _asistentes_para_hoja(attendees) -> list:
    """Los asistentes SIN la firma, para guardar en la hoja (v383).

    ⚠️ Decisión del usuario: la firma dibujada va **solo al PDF**, que es el
    documento que vale y ya se archiva en Drive. Aquí se quita a propósito por dos
    razones, y las dos rompen de verdad:
      · `json.dumps` no serializa `bytes` → el registro entero fallaría;
      · una celda de Sheets admite 50.000 caracteres y seis firmas en base64
        rondan los 40.000: se quedaría sin margen y empezaría a fallar en silencio.
    """
    out = []
    for a in (attendees or []):
        out.append({"name": str(a.get("name", "")),
                    "initial": str(a.get("initial", "")),
                    # rastro de QUE firmó, sin la imagen
                    "firmado": bool(a.get("sig"))})
    return out


def filename_for(data) -> str:
    """`ddmmyyyy AB CD EF.pdf` — fecha + iniciales de los asistentes."""
    f = data.get("fecha")
    ddmmyyyy = f.strftime("%d%m%Y") if hasattr(f, "strftime") else clock.now().strftime("%d%m%Y")
    inis = [str(a.get("initial", "")).strip().upper() for a in data.get("attendees", [])
            if str(a.get("initial", "")).strip()]
    tail = (" " + " ".join(inis)) if inis else ""
    return f"{ddmmyyyy}{tail}.pdf"


def submit(data: dict) -> dict:
    """Genera el PDF, lo archiva en Drive + hoja y abre alarma si hay near miss
    o algún check en NO (v373).
    Devuelve {ok, id, pdf, filename, drive_id, alarma, alarma_checks, checks_no, error}."""
    res = {"ok": False, "id": "", "pdf": None, "filename": "", "drive_id": "",
           "alarma": False, "alarma_checks": False, "checks_no": [], "error": ""}

    # 1) PDF
    try:
        from core import prestart_pdf
        pdf = prestart_pdf.generate_prestart_pdf(data)
    except Exception as e:
        res["error"] = f"No se pudo generar el PDF: {e}"
        return res
    fname = filename_for(data)
    res["pdf"] = pdf
    res["filename"] = fname

    pid   = str(data.get("proyecto_id", ""))
    grupo = str(data.get("grupo", ""))
    creado_por = str(data.get("creado_por", ""))

    # 2) Archivar en Drive + documento del proyecto (best-effort)
    drive_id = ""
    try:
        from core import drive_store
        from core import projects
        if pid and drive_store.is_available():
            drive_id = drive_store.upload(pid, fname, pdf, "application/pdf")
            projects.add_document(pid, fname, "prestart", drive_id, creado_por)
    except Exception as e:
        logger.warning("prestart: archivado en Drive falló: %s", e)
    res["drive_id"] = drive_id

    # 3) Registro en la hoja
    w = _ws()
    if w is None:
        res["error"] = "No se pudo abrir la hoja de pre-starts."
        return res
    try:
        f = data.get("fecha")
        fecha_s = f.strftime("%Y-%m-%d") if hasattr(f, "strftime") else str(f)
        aid = _next_id(w.get_all_records(numericise_ignore=["all"]))
        w.append_row([
            aid, pid, grupo, fecha_s, str(data.get("hora", "")),
            str(data.get("location", "")), str(data.get("facilitador", "")),
            str(data.get("activities_notes", "")),
            str(data.get("near_miss", "NO")), str(data.get("near_miss_desc", "")),
            json.dumps(data.get("s1", {}), ensure_ascii=False),
            json.dumps(data.get("s3", {}), ensure_ascii=False),
            str(data.get("general_notes", "")),
            json.dumps(_asistentes_para_hoja(data.get("attendees")), ensure_ascii=False),
            fname, drive_id, creado_por, clock.now().strftime("%Y-%m-%d %H:%M"),
        ], value_input_option="RAW")
    except Exception as e:
        res["error"] = f"No se pudo registrar el pre-start: {e}"
        return res
    _invalidate()
    res["ok"] = True
    res["id"] = aid

    # 4) Alarma si hay near miss / hazard
    if str(data.get("near_miss", "")).upper() == "YES":
        try:
            from core import alerts
            msg = "Near Miss/Hazard reportado en el Pre-Start"
            if data.get("near_miss_desc"):
                msg += f": {data['near_miss_desc']}"
            ok, _ = alerts.report_problem(pid, grupo, msg, creado_por,
                                          data.get("proyecto_nombre", ""))
            res["alarma"] = bool(ok)
        except Exception as e:
            logger.warning("prestart: no se pudo crear la alarma: %s", e)

    # 5) Alarma si algún check quedó en NO (v373, decisión del usuario)
    #
    # Hasta v372 SOLO el near miss abría alarma: un check en NO se veía con su
    # semáforo rojo en la ficha del pre-start y no salía de ahí — un control de
    # seguridad sin cumplir que solo conocía quien abriera ese registro. Es un
    # riesgo de obra, y el mecanismo para escalarlo ya existía desde v88.
    #
    # ⚠️ UNA alarma con todos los checks, no una por check: `report_problem`
    #    escribe Y notifica por Telegram/email, así que N checks serían N avisos
    #    por un solo formulario. Y va SEPARADA de la del near miss porque son dos
    #    cosas distintas: un near miss es un suceso, un check en NO es un control
    #    que falta poner — se resuelven por separado.
    # ⚠️ Solo cuenta "NO": el "N/A" de la sección 3 es una respuesta legítima
    #    (no aplica), y un check sin responder no puede llegar (la UI no deja
    #    generar el pre-start hasta que están todos, v158).
    checks = {**(data.get("s1") or {}), **(data.get("s3") or {})}
    no_ok = [_LABELS.get(k, k) for k, v in checks.items()
             if str(v).strip().upper() == "NO"]
    res["checks_no"] = no_ok
    if no_ok:
        try:
            from core import alerts
            msg = (f"Pre-Start con {len(no_ok)} control(es) en NO: "
                   + " · ".join(no_ok))
            ok, _ = alerts.report_problem(pid, grupo, msg, creado_por,
                                          data.get("proyecto_nombre", ""))
            res["alarma_checks"] = bool(ok)
        except Exception as e:
            logger.warning("prestart: no se pudo crear la alarma de checks: %s", e)

    return res
