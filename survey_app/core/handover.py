# -*- coding: utf-8 -*-
"""Expediente de entrega: qué tiene la obra y qué le falta para poder entregarse (v506).

## Qué es, y sobre todo qué NO es

⚠️ **Esto NO certifica nada.** No es un certificado AS1735 ni sustituye al del certificador,
al eléctrico ni al *Safe-to-Operate*. Decir lo contrario sería mentir y además peligroso:
esos documentos los emiten terceros y la app no puede fabricarlos.

Lo que SÍ es: el **expediente del instalador** — lo que la empresa tiene que conservar
cinco años, reunido en un sitio, **más la lista de lo que falta, con nombre**.

## De dónde sale la lista

De los trece documentos que el estándar técnico de lifts del Departamento de Educación de
NSW exige en *practical completion* (ítems a–m de «Lift Documentation and Support»). Se
eligió una lista REAL de un cliente real del mercado de arranque en vez de inventarla: un
expediente con una lista inventada no sirve para lo único que tiene que servir.

De esos trece, la app puede **evidenciar cinco** con datos que ya tiene. Los otros ocho los
emite un tercero: se reportan como pendientes hasta que alguien suba el documento.

## Lo que hace único a este expediente

No es juntar PDFs — eso lo hace cualquiera. Es **cruzar** el registro técnico con el de
personas y el de fechas, que es algo que solo puede hacer quien hace el cálculo:

    «Ana firmó el pre-start del 15/08, pero su ticket venció el 12/08.»
    «La actividad 4 se cerró sin que exista verificación de plomada.»

Un competidor no puede sacar eso aunque junte los mismos archivos, porque no tiene el
registro técnico de la instalación.

## Módulo HOJA

No importa nada de `core` y no toca Sheets: recibe un **contexto** ya reunido y devuelve el
estado. Así se puede ejercitar de verdad (importar no ejecuta, v378) y la pantalla que lo
usa queda libre de decidir nada.
"""
from datetime import date

# ── Origen de cada ítem ──────────────────────────────────────────
COPEX = "copex"            # la app lo evidencia con lo que ya guarda
TERCERO = "third_party"    # lo emite otro: hasta que se suba, falta

# ── Estado de un ítem ────────────────────────────────────────────
OK = "ok"                  # está, y se puede demostrar
FALTA = "missing"          # no está
PARCIAL = "partial"        # está a medias, y se dice en qué


def _f(v):
    """Una fecha desde texto ISO, o None. No lanza: una celda a mano trae de todo."""
    if isinstance(v, date):
        return v
    try:
        y, m, d = str(v).strip()[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


# ═════════════════════════════════════════════════════════════════
# Los trece ítems (a–m del estándar de NSW DoE)
# ═════════════════════════════════════════════════════════════════
ITEMS = [
    # ── Los cinco que la app evidencia ──
    {"clave": "check_sheets", "letra": "a", "fuente": COPEX,
     "nombre": "Project specification check sheets",
     "nota": "Positioning solution and cuts recorded from the survey"},
    {"clave": "commissioning", "letra": "c", "fuente": COPEX,
     "nombre": "Commissioning records",
     "nota": "Real start and finish dates per activity"},
    {"clave": "as_built", "letra": "f", "fuente": COPEX,
     "nombre": "As-built record (dimensional)",
     "nota": "Survey matrix, positioning and plumb verification"},
    {"clave": "risk", "letra": "j", "fuente": COPEX,
     "nombre": "Hazard and risk assessment",
     "nota": "Signed daily pre-starts for the job"},
    {"clave": "installer_certs", "letra": "l", "fuente": COPEX,
     "nombre": "Installer's statutory certificates",
     "nota": "Credentials of everyone who worked, valid on the days they worked"},

    # ── Los ocho de terceros ──
    {"clave": "om_manuals", "letra": "b", "fuente": TERCERO,
     "nombre": "Operation and Maintenance manuals"},
    {"clave": "manufacturer", "letra": "d", "fuente": TERCERO,
     "nombre": "Product manufacturer information"},
    {"clave": "schematics", "letra": "e", "fuente": TERCERO,
     "nombre": "System schematics"},
    {"clave": "wiring", "letra": "g", "fuente": TERCERO,
     "nombre": "Electrical and wiring diagrams"},
    {"clave": "functional", "letra": "h", "fuente": TERCERO,
     "nombre": "Lift functionality and operation description"},
    {"clave": "plant_reg", "letra": "i", "fuente": TERCERO,
     "nombre": "Plant registration documentation"},
    {"clave": "workcover", "letra": "k", "fuente": TERCERO,
     "nombre": "WorkCover registration"},
    {"clave": "safe_to_operate", "letra": "m", "fuente": TERCERO,
     "nombre": "Safe-to-Operate certification"},
]

CLAVES = [i["clave"] for i in ITEMS]
_POR_CLAVE = {i["clave"]: i for i in ITEMS}


# ═════════════════════════════════════════════════════════════════
# El estado de cada ítem
# ═════════════════════════════════════════════════════════════════
def _ev_check_sheets(ctx):
    if ctx.get("params") and ctx.get("matrix"):
        return OK, "Survey solution recorded"
    if ctx.get("params"):
        return PARCIAL, "Parameters recorded, no solution matrix"
    return FALTA, "No survey recorded on this job"


def _ev_commissioning(ctx):
    acts = ctx.get("acts") or []
    if not acts:
        return FALTA, "No activities recorded"
    cerradas = [a for a in acts if _f(a.get("ActualEndDate"))]
    if len(cerradas) == len(acts):
        return OK, "%d of %d activities closed with a real date" % (len(cerradas), len(acts))
    if cerradas:
        return PARCIAL, "%d of %d activities closed with a real date" % (len(cerradas), len(acts))
    return FALTA, "No activity has a real finish date"


def _ev_as_built(ctx):
    if not ctx.get("matrix"):
        return FALTA, "No survey matrix on this job"
    if ctx.get("plumb_ok"):
        return OK, "Matrix and plumb verification present"
    return PARCIAL, "Matrix present, no plumb verification"


def _ev_risk(ctx):
    n = len(ctx.get("prestarts") or [])
    if n:
        return OK, "%d pre-start%s on file" % (n, "" if n == 1 else "s")
    return FALTA, "No pre-start recorded for this job"


def _ev_installer_certs(ctx):
    """⚠️ No basta con que la persona TENGA un certificado: tiene que estar vigente el
    día que trabajó. Un ticket que venció a mitad de obra es exactamente lo que una
    auditoría busca, y es un cruce que solo se puede hacer teniendo las dos cosas."""
    trabajaron = ctx.get("trabajaron") or {}      # {login: ultima fecha trabajada}
    if not trabajaron:
        return FALTA, "Nobody recorded as having worked on this job"
    creds = ctx.get("credenciales") or {}         # {login: [fecha de vencimiento|None]}
    sin, vencidos = [], []
    for u, ultimo in trabajaron.items():
        mios = creds.get(u) or []
        if not mios:
            sin.append(u)
            continue
        _d = _f(ultimo)
        if _d and all((_v is not None and _f(_v) and _f(_v) < _d) for _v in mios):
            vencidos.append(u)
    if sin or vencidos:
        _p = []
        if sin:
            _p.append("no certificate: %s" % ", ".join(sorted(sin)))
        if vencidos:
            _p.append("expired before their last day: %s" % ", ".join(sorted(vencidos)))
        return (FALTA if sin else PARCIAL), " · ".join(_p)
    return OK, "%d worker%s with a valid certificate" % (
        len(trabajaron), "" if len(trabajaron) == 1 else "s")


_EVIDENCIA = {
    "check_sheets": _ev_check_sheets,
    "commissioning": _ev_commissioning,
    "as_built": _ev_as_built,
    "risk": _ev_risk,
    "installer_certs": _ev_installer_certs,
}


def estado(ctx) -> list:
    """`[{clave, letra, nombre, fuente, estado, detalle, doc}]`, en el orden de ITEMS.

    `ctx` reúne lo que la pantalla ya sabe de la obra:
      params, matrix   – el survey guardado (ParamsJSON / MatrixJSON)
      plumb_ok         – si hay verificación de plomada
      acts             – actividades, con sus fechas reales
      prestarts        – pre-starts de la obra
      trabajaron       – {login: última fecha trabajada}
      credenciales     – {login: [vencimiento, …]}
      docs             – documentos subidos: {clave del ítem: nombre del fichero}

    ⚠️ Un ítem de TERCERO nunca sale OK por cálculo: solo si hay un documento subido
    contra él. La app no puede afirmar que existe el certificado eléctrico.
    """
    docs = ctx.get("docs") or {}
    out = []
    for it in ITEMS:
        _doc = docs.get(it["clave"])
        if it["fuente"] == TERCERO:
            _e = (OK, "Uploaded: %s" % _doc) if _doc else (FALTA, "Not uploaded yet")
        else:
            _e = _EVIDENCIA[it["clave"]](ctx)
            if _doc:                       # un documento subido refuerza, nunca degrada
                _e = (OK, "%s · uploaded: %s" % (_e[1], _doc))
        out.append({**it, "estado": _e[0], "detalle": _e[1], "doc": _doc})
    return out


def resumen(filas) -> dict:
    """Cuántos hay de cada estado, y si la obra se puede entregar sin huecos."""
    _c = {OK: 0, PARCIAL: 0, FALTA: 0}
    for f in filas:
        _c[f["estado"]] = _c.get(f["estado"], 0) + 1
    return {"ok": _c[OK], "parcial": _c[PARCIAL], "falta": _c[FALTA],
            "total": len(filas), "completo": _c[FALTA] == 0 and _c[PARCIAL] == 0}


# ═════════════════════════════════════════════════════════════════
# Los cruces: lo que nadie más puede decir
# ═════════════════════════════════════════════════════════════════
def incoherencias(ctx) -> list:
    """Contradicciones entre el registro técnico, el de personas y el de fechas.

    No es «falta un documento» —eso lo dice `estado`— sino «estos dos datos que SÍ
    tenemos no pueden ser los dos ciertos». Es lo que convierte el expediente en una
    comprobación y no en una carpeta.
    """
    out = []

    # 1) firmó con el ticket vencido
    creds = ctx.get("credenciales") or {}
    for p in (ctx.get("prestarts") or []):
        _d = _f(p.get("Date"))
        for u in (p.get("Attendees") or []):
            # ⚠️ Un invitado o subcontratista viene con el login VACÍO: esta empresa no
            # tiene tickets suyos y reclamárselos sería un falso rojo. Hoy además se
            # salvaba por accidente —nadie tiene credenciales bajo la clave ""—, y una
            # sola fila con el usuario en blanco habría empezado a acusar a todo el
            # mundo. Se dice explícitamente en vez de depender de la casualidad.
            if not str(u).strip():
                continue
            _v = [_f(x) for x in (creds.get(u) or []) if _f(x)]
            if _d and _v and max(_v) < _d:
                out.append({"tipo": "cert_vencido",
                            "texto": "%s signed the pre-start of %s, but their certificate "
                                     "expired on %s" % (u, _d.strftime("%d/%m/%Y"),
                                                        max(_v).strftime("%d/%m/%Y"))})

    # 2) obra cerrada sin verificación de plomada
    acts = ctx.get("acts") or []
    if acts and all(_f(a.get("ActualEndDate")) for a in acts) and not ctx.get("plumb_ok"):
        out.append({"tipo": "sin_plomada",
                    "texto": "Every activity is closed, but there is no plumb verification "
                             "on record for this job"})

    # 3) trabajó gente que no aparece asignada a la obra
    _asig = set(ctx.get("asignados") or [])
    if _asig:
        _extra = sorted(set(ctx.get("trabajaron") or {}) - _asig)
        if _extra:
            out.append({"tipo": "no_asignado",
                        "texto": "Hours were booked to this job by people not assigned to "
                                 "it: %s" % ", ".join(_extra)})

    # 4) actividad cerrada antes de empezar
    for a in acts:
        _i, _fin = _f(a.get("ActualStartDate")), _f(a.get("ActualEndDate"))
        if _i and _fin and _fin < _i:
            out.append({"tipo": "fechas_invertidas",
                        "texto": "Activity %s finished (%s) before it started (%s)"
                                 % (a.get("Order", "?"), _fin.strftime("%d/%m/%Y"),
                                    _i.strftime("%d/%m/%Y"))})
    return out
