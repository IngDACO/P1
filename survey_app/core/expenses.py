"""
Gastos / compras por proyecto → control de costos (compras + mano de obra).

- Recibos por proyecto (foto/PDF a Drive + valor + categoría). Los cargan admin,
  campo y conductor.
- Costo de mano de obra = Σ (horas de cada persona en el proyecto × su tarifa/hora,
  `auth.TarifaHora`). Costo total = compras + mano de obra.
- Presupuesto por proyecto (`Proyectos.Presupuesto`) → % consumido + alerta al pasarse.
- Reporte del grupo con desglose por categoría + export CSV (para contabilidad).

Hoja `Gastos`.
"""
import logging
from datetime import datetime

import streamlit as st

from core import timeclock

logger = logging.getLogger(__name__)

SHEET   = "Gastos"
HEADERS = ["ID", "ProyectoID", "Grupo", "Fecha", "Categoria", "Proveedor",
           "Descripcion", "Valor", "DriveID", "Archivo", "CreadoPor", "Creado"]
CATEGORIAS = ["Materiales", "Herramientas", "Transporte", "Combustible",
              "Subcontrato", "Alquiler", "Otros"]
_FOLDER = "COPEX Recibos"


def is_configured() -> bool:
    return timeclock._secrets_present()


def _num(v) -> float:
    try:
        return float(str(v).replace(",", ".").replace("$", "").strip() or 0)
    except Exception:
        return 0.0


def _ws():
    if not timeclock._secrets_present():
        return None
    try:
        return timeclock.get_sheet(SHEET, tuple(HEADERS))
    except Exception as e:
        logger.warning("expenses: no se pudo abrir la hoja: %s", e)
        return None


@st.cache_data(ttl=30, show_spinner=False)
def _records() -> list:
    w = _ws()
    if w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception:
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


# ── Lecturas ─────────────────────────────────────────────────────
def list_for(pid) -> list:
    return [r for r in _records() if str(r.get("ProyectoID", "")) == str(pid)]


def project_expenses(pid) -> dict:
    """{total, por_categoria{cat:val}, items[]} de las compras del proyecto."""
    items = list_for(pid)
    total = sum(_num(r.get("Valor")) for r in items)
    por = {}
    for r in items:
        c = str(r.get("Categoria", "")) or "Otros"
        por[c] = por.get(c, 0.0) + _num(r.get("Valor"))
    return {"total": round(total, 2), "por_categoria": {k: round(v, 2) for k, v in por.items()},
            "items": items}


def _mismo_proyecto(fila, pid: str, nombre: str) -> bool:
    """¿Este fichaje pertenece al proyecto? **Por ID (v145), nombre de respaldo.**

    Delega en `timeclock.es_del_proyecto` para que el costo de mano de obra y las
    horas del proyecto usen exactamente el mismo criterio y no puedan divergir.
    """
    return timeclock.es_del_proyecto(fila, pid, nombre)


def _horas_de(r) -> float:
    """Horas de una fila de fichaje; las sesiones ABIERTAS cuentan lo transcurrido."""
    if str(r.get("Estado", "")).strip().upper() == "ABIERTO":
        return round(timeclock.elapsed_seconds(r.get("Clock In")) / 3600.0, 2)
    return _num(r.get("Horas"))


def labor_breakdown(pid, grupo) -> dict:
    """Mano de obra POR PERSONA. `labor_cost` solo devolvia el total, asi que
    **quien consumia las horas era invisible** aunque el dato estuviera ahi.

    Devuelve {items:[{usuario,horas,tarifa,costo}], total, horas, sin_tarifa[]}.
    `sin_tarifa` = gente con horas y tarifa 0: su trabajo suma 0 al costo, y sin
    avisar parece que el proyecto no cuesta mano de obra.
    """
    from core import projects as P
    from core import auth
    prj = P.get_project(pid)
    if not prj:
        return {"items": [], "total": 0.0, "horas": 0.0, "sin_tarifa": []}

    nombre = str(prj.get("Nombre", ""))
    rates  = auth.rate_map(grupo)
    acc    = {}
    for r in P._fichaje_records():
        if not _mismo_proyecto(r, pid, nombre):
            continue
        if str(r.get("Grupo", "")) != str(grupo):
            continue
        h = _horas_de(r)
        if h <= 0:
            continue
        clave = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        acc.setdefault(clave, 0.0)
        acc[clave] += h

    items, sin_tarifa = [], []
    for u, h in acc.items():
        tar = rates.get(u, 0.0)
        items.append({"usuario": u, "horas": round(h, 2), "tarifa": tar,
                      "costo": round(h * tar, 2)})
        if tar <= 0:
            sin_tarifa.append(u)
    items.sort(key=lambda x: (-x["costo"], -x["horas"]))
    return {"items": items,
            "total": round(sum(x["costo"] for x in items), 2),
            "horas": round(sum(x["horas"] for x in items), 2),
            "sin_tarifa": sin_tarifa}


def labor_cost(pid, grupo) -> float:
    """Costo de mano de obra = Σ (horas de cada persona en el proyecto × su tarifa/hora)."""
    return labor_breakdown(pid, grupo)["total"]


def cost_projection(pid, grupo) -> dict:
    """Cuanto va a costar el proyecto AL TERMINAR, al ritmo de gasto actual.

    ⚠️ Es la pregunta que la pestaña no respondia. La barra de presupuesto solo
    se ponia roja al pasarse, o sea **cuando ya no se puede hacer nada**. Si
    llevas el 60% del presupuesto con el 30% de avance, se sabe hoy.

    proyectado = costo_actual / (avance/100).  Devuelve None si avance = 0.
    """
    from core import projects as P
    c   = project_cost(pid, grupo)
    av  = _num(P.get_project(pid).get("Avance"))
    out = dict(c)
    out["avance"] = av
    if av <= 0 or c["total"] <= 0:
        out.update({"proyectado": None, "desvio": None, "pct_proj": None,
                    "por_punto": None})
        return out
    proy = round(c["total"] * 100.0 / av, 2)
    pres = c["presupuesto"]
    out.update({
        "proyectado": proy,
        "desvio":   round(proy - pres, 2) if pres > 0 else None,
        "pct_proj": round(100 * proy / pres) if pres > 0 else None,
        "por_punto": round(c["total"] / av, 2),      # costo por punto de avance
    })
    return out


def spend_curve(pid, grupo) -> dict:
    """Costo ACUMULADO por fecha (compras + mano de obra), para la curva de gasto.

    Las compras traen su Fecha y cada fichaje aporta horas×tarifa en el dia de su
    Clock In, asi que la curva sale de datos que ya existian.
    """
    from core import projects as P
    from core import auth
    prj = P.get_project(pid)
    if not prj:
        return {}
    nombre = str(prj.get("Nombre", ""))
    rates  = auth.rate_map(grupo)

    dia = {}                                   # fecha "YYYY-MM-DD" -> {compras, mo}
    for r in list_for(pid):
        f = str(r.get("Fecha", ""))[:10]
        if f:
            dia.setdefault(f, {"compras": 0.0, "mo": 0.0})
            dia[f]["compras"] += _num(r.get("Valor"))
    for r in P._fichaje_records():
        if not _mismo_proyecto(r, pid, nombre):
            continue
        if str(r.get("Grupo", "")) != str(grupo):
            continue
        h = _horas_de(r)
        f = str(r.get("Clock In", ""))[:10]
        if h <= 0 or not f:
            continue
        clave = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        dia.setdefault(f, {"compras": 0.0, "mo": 0.0})
        dia[f]["mo"] += h * rates.get(clave, 0.0)

    if not dia:
        return {}
    fechas = sorted(dia)
    acc_c = acc_m = 0.0
    compras, mo, total = [], [], []
    for f in fechas:
        acc_c += dia[f]["compras"]
        acc_m += dia[f]["mo"]
        compras.append(round(acc_c, 2))
        mo.append(round(acc_m, 2))
        total.append(round(acc_c + acc_m, 2))
    return {"fechas": fechas, "compras": compras, "mano_obra": mo, "total": total,
            "presupuesto": _num(prj.get("Presupuesto"))}



def project_cost(pid, grupo) -> dict:
    """{compras, mano_obra, total, presupuesto, pct, over}."""
    from core import projects as P
    compras = project_expenses(pid)["total"]
    mo = labor_cost(pid, grupo)
    total = round(compras + mo, 2)
    pres = _num(P.get_project(pid).get("Presupuesto"))
    pct = round(100 * total / pres) if pres > 0 else None
    return {"compras": compras, "mano_obra": mo, "total": total,
            "presupuesto": pres, "pct": pct, "over": bool(pres > 0 and total > pres)}


@st.cache_data(ttl=60, show_spinner=False)
def over_budget(grupo) -> list:
    """Proyectos del grupo sobre presupuesto (para el radar del admin)."""
    from core import projects as P
    out = []
    for p in P.list_projects(grupo=grupo):
        if str(p.get("Estado", "")) in ("Completado", "Cancelado"):
            continue
        c = project_cost(p.get("ID"), grupo)
        if c["over"]:
            out.append({"id": p.get("ID"), "nombre": p.get("Nombre"),
                        "total": c["total"], "presupuesto": c["presupuesto"], "pct": c["pct"]})
    return out


@st.cache_data(ttl=60, show_spinner=False)
def group_expenses(grupo) -> dict:
    """Costos de todos los proyectos del grupo + desglose por categoría."""
    from core import projects as P
    proys, por_cat, filas = P.list_projects(grupo=grupo), {}, []
    for p in proys:
        c = project_cost(p.get("ID"), grupo)
        filas.append({"id": p.get("ID"), "nombre": p.get("Nombre"),
                      "compras": c["compras"], "mano_obra": c["mano_obra"],
                      "total": c["total"], "presupuesto": c["presupuesto"], "pct": c["pct"]})
    for r in _records():
        if str(r.get("Grupo", "")) == str(grupo):
            cat = str(r.get("Categoria", "")) or "Otros"
            por_cat[cat] = por_cat.get(cat, 0.0) + _num(r.get("Valor"))
    return {"proyectos": filas, "por_categoria": {k: round(v, 2) for k, v in por_cat.items()}}


# ── Escrituras ───────────────────────────────────────────────────
def _next_id(recs) -> str:
    mx = 0
    for r in recs:
        i = str(r.get("ID", ""))
        if i.startswith("G-"):
            try:
                mx = max(mx, int(i.split("-")[1]))
            except Exception:
                pass
    return f"G-{mx + 1:05d}"


def upload_receipt(pid, filename, data, mime="application/octet-stream") -> str:
    try:
        from core import drive_store
        if not drive_store.is_available():
            return ""
        safe = f"{pid}_{filename}".replace("/", "-").replace(" ", "_")
        return drive_store.upload_to(drive_store.folder(_FOLDER), safe, data, mime)
    except Exception as e:
        logger.warning("expenses.upload_receipt: %s", e)
        return ""


def add(pid, grupo, valor, categoria="Materiales", proveedor="", descripcion="",
        drive_id="", archivo="", creado_por="", fecha="") -> tuple:
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    if _num(valor) <= 0:
        return False, "El valor del recibo debe ser mayor que 0."
    try:
        gid = _next_id(w.get_all_records(numericise_ignore=["all"]))
        w.append_row([gid, str(pid), str(grupo),
                      str(fecha or datetime.now().strftime("%Y-%m-%d")),
                      str(categoria), str(proveedor), str(descripcion),
                      str(_num(valor)), str(drive_id), str(archivo), str(creado_por),
                      datetime.now().strftime("%Y-%m-%d %H:%M")],
                     value_input_option="RAW")
    except Exception as e:
        return False, f"Error guardando: {e}"
    _invalidate()
    return True, f"Recibo agregado ({_num(valor):.2f})."


def delete(gid) -> tuple:
    w = _ws()
    if w is None:
        return False, "Google Sheets no está configurado."
    try:
        recs = w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        return False, f"Error leyendo: {e}"
    for i, r in enumerate(recs):
        if str(r.get("ID", "")) == str(gid):
            did = str(r.get("DriveID", "")).strip()
            if did:
                try:
                    from core import drive_store
                    drive_store.delete(did)
                except Exception:
                    pass
            try:
                w.delete_rows(i + 2)
            except Exception as e:
                return False, f"Error: {e}"
            _invalidate()
            return True, "Recibo eliminado."
    return False, "Recibo no encontrado."


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _money(v) -> str:
    """$1.2k / $340 — etiquetas cortas para que quepan en los ejes."""
    v = float(v or 0)
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.1f}k"
    return f"${v:.0f}"


def spend_svg(curva: dict, proyectado=None, titulo: str = "") -> str:
    """Curva de gasto ACUMULADO: mano de obra + compras apiladas, contra el
    presupuesto y contra lo que costara al terminar al ritmo actual.

    Mismo lenguaje que el cronograma (v143). Sin <defs>/<marker> → compatible
    con Streamlit y svglib.
    """
    fechas = curva.get("fechas") or []
    if len(fechas) < 2:
        return ""

    mo, tot = curva["mano_obra"], curva["total"]
    pres    = float(curva.get("presupuesto") or 0)

    VW, ML, MR, MT, MB = 760, 74, 108, 50, 44
    VH = 300
    pw, ph = VW - ML - MR, VH - MT - MB

    techo = max(tot[-1], pres, float(proyectado or 0)) * 1.12 or 1.0
    n = len(fechas)

    def sx(i):   return ML + (i / max(1, n - 1)) * pw
    def sy(v):   return MT + ph - (float(v) / techo) * ph

    C_MO, C_CO, C_PRES, C_ROJO = "#2e6da4", "#BA7517", "#6b7280", "#c0392b"
    p = [f'<svg viewBox="0 0 {VW} {VH}" xmlns="http://www.w3.org/2000/svg" '
         f'style="width:100%;max-width:{VW}px;font-family:Arial,Helvetica,sans-serif;'
         f'display:block;margin:0 auto">',
         f'<rect x="0" y="0" width="{VW}" height="{VH}" fill="#ffffff"/>',
         f'<text x="18" y="24" font-size="13" fill="#1a3a5c" font-weight="bold">'
         f'GASTO ACUMULADO</text>',
         f'<text x="18" y="38" font-size="8.5" fill="#7a8699">'
         f'{_esc(titulo) + " · " if titulo else ""}{fechas[0]} → {fechas[-1]}'
         f' · {n} movimientos</text>']

    # rejilla horizontal
    for k in range(5):
        v  = techo * k / 4.0
        yy = sy(v)
        p.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{VW-MR}" y2="{yy:.1f}" '
                 f'stroke="{"#c3ccd8" if k == 0 else "#f0f2f6"}" stroke-width="1"/>')
        p.append(f'<text x="{ML-6}" y="{yy+3:.1f}" text-anchor="end" font-size="8" '
                 f'fill="#9aa7b8">{_money(v)}</text>')

    base = sy(0)
    # mano de obra (abajo) y compras encima: se ve el reparto, no solo el total
    p.append(f'<polygon points="{sx(0):.1f},{base:.1f} '
             + " ".join(f"{sx(i):.1f},{sy(mo[i]):.1f}" for i in range(n))
             + f' {sx(n-1):.1f},{base:.1f}" fill="{C_MO}" fill-opacity="0.30"/>')
    p.append(f'<polygon points="'
             + " ".join(f"{sx(i):.1f},{sy(mo[i]):.1f}" for i in range(n)) + " "
             + " ".join(f"{sx(i):.1f},{sy(tot[i]):.1f}" for i in range(n - 1, -1, -1))
             + f'" fill="{C_CO}" fill-opacity="0.30"/>')
    p.append('<polyline points="'
             + " ".join(f"{sx(i):.1f},{sy(tot[i]):.1f}" for i in range(n))
             + f'" fill="none" stroke="#1a3a5c" stroke-width="2.6"/>')
    p.append(f'<circle cx="{sx(n-1):.1f}" cy="{sy(tot[-1]):.1f}" r="4" fill="#ffffff" '
             f'stroke="#1a3a5c" stroke-width="2"/>')
    p.append(f'<text x="{sx(n-1)+8:.1f}" y="{sy(tot[-1])-6:.1f}" font-size="9.5" '
             f'fill="#1a3a5c" font-weight="bold">{_money(tot[-1])}</text>')

    # presupuesto
    if pres > 0:
        yy = sy(pres)
        p.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{VW-MR}" y2="{yy:.1f}" '
                 f'stroke="{C_PRES}" stroke-width="1.4" stroke-dasharray="6,4"/>')
        p.append(f'<text x="{VW-MR+5}" y="{yy+3:.1f}" font-size="8.5" fill="{C_PRES}" '
                 f'font-weight="bold">Presup. {_money(pres)}</text>')

    # a este ritmo terminas aqui
    if proyectado:
        yy    = sy(proyectado)
        tarde = pres > 0 and float(proyectado) > pres
        col   = C_ROJO if tarde else "#1e8449"
        p.append(f'<line x1="{sx(n-1):.1f}" y1="{sy(tot[-1]):.1f}" '
                 f'x2="{VW-MR:.1f}" y2="{yy:.1f}" stroke="{col}" stroke-width="1.6" '
                 f'stroke-dasharray="6,4" stroke-opacity="0.85"/>')
        p.append(f'<circle cx="{VW-MR:.1f}" cy="{yy:.1f}" r="3.5" fill="{col}"/>')
        p.append(f'<text x="{VW-MR+5}" y="{yy+3:.1f}" font-size="8.5" fill="{col}" '
                 f'font-weight="bold">Fin {_money(proyectado)}</text>')

    # eje de fechas (como mucho 6 etiquetas)
    paso = max(1, n // 6)
    for i in range(0, n, paso):
        p.append(f'<line x1="{sx(i):.1f}" y1="{base:.1f}" x2="{sx(i):.1f}" '
                 f'y2="{base+4:.1f}" stroke="#9aa7b8" stroke-width="1"/>')
        p.append(f'<text x="{sx(i):.1f}" y="{base+15:.1f}" text-anchor="middle" '
                 f'font-size="7.5" fill="#7a8699">{fechas[i][8:10]}/{fechas[i][5:7]}</text>')

    lgx = ML
    for et, col in (("Mano de obra", C_MO), ("Compras", C_CO)):
        p.append(f'<rect x="{lgx:.1f}" y="{VH-16}" width="13" height="7" fill="{col}" '
                 f'fill-opacity="0.45"/>')
        p.append(f'<text x="{lgx+18:.1f}" y="{VH-10}" font-size="8" fill="#7a8699">{et}</text>')
        lgx += 34 + len(et) * 5.4

    p.append("</svg>")
    return "".join(p)
