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


def labor_cost(pid, grupo) -> float:
    """Costo de mano de obra = Σ (horas de cada persona en el proyecto × su tarifa/hora)."""
    from core import projects as P
    from core import auth
    prj = P.get_project(pid)
    if not prj:
        return 0.0
    nombre_proy = str(prj.get("Nombre", ""))
    rates = auth.rate_map(grupo)
    total = 0.0
    for r in P._fichaje_records():
        if str(r.get("Proyecto", "")) != nombre_proy or str(r.get("Grupo", "")) != str(grupo):
            continue
        estado = str(r.get("Estado", "")).strip().upper()
        h = (round(timeclock.elapsed_seconds(r.get("Clock In")) / 3600.0, 2)
             if estado == "ABIERTO" else _num(r.get("Horas")))
        if h <= 0:
            continue
        # Tarifa por USUARIO; filas antiguas (sin Usuario) caen al Nombre.
        clave = str(r.get("Usuario", "")).strip() or str(r.get("Nombre", "")).strip()
        total += h * rates.get(clave, 0.0)
    return round(total, 2)


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
