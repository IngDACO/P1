"""Nóminas y colillas de pago (cuentas por pagar a usuarios) — Fase 3 financiera.

Hoja `Nominas`, una fila por usuario×periodo. La base = horas de jornada del
periodo (fichaje) × `TarifaHora`. Los conceptos (devengos/deducciones/aportes)
se precargan con lo de ley del grupo (retención de impuesto, superannuation) y
son EDITABLES: agregar/quitar según se requiera.

  Neto a pagar     = Base + Σ(devengo) − Σ(deducción)
  Costo empleador  = Base + Σ(devengo) + Σ(aporte)   (informativo; el aporte, p.ej.
                     super, no se le descuenta al usuario)

⚠️ NO es un motor fiscal certificado: la retención y el super se precargan con
un % configurable por grupo (default AU) y son editables; el usuario valida los
números. (Ver la nota del módulo financiero en memoria.)
"""
import json
import logging

import streamlit as st

from core import auth, clock, timeclock

logger = logging.getLogger(__name__)

NOMINAS_SHEET = "Nominas"
NOMINAS_HEADERS = [
    "ID", "Grupo", "Usuario", "Nombre", "PeriodoDesde", "PeriodoHasta",
    "Horas", "TarifaHora", "Base", "ConceptosJSON", "Neto",
    "FechaPago", "Estado", "Nota", "CreadoPor", "Creado",
]
_NCOL = {h: i + 1 for i, h in enumerate(NOMINAS_HEADERS)}
TIPOS = ["devengo", "deduccion", "aporte"]


def is_configured() -> bool:
    return timeclock._secrets_present()


def _num(v, d=0.0) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return d


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def conceptos_de(f: dict) -> list:
    try:
        return json.loads(f.get("ConceptosJSON", "") or "[]")
    except Exception:
        return []


def neto(base, conceptos) -> float:
    tot = _num(base)
    for c in conceptos or []:
        t = str(c.get("tipo", "")).lower()
        if t == "devengo":
            tot += _num(c.get("monto"))
        elif t == "deduccion":
            tot -= _num(c.get("monto"))
    return round(tot, 2)


def costo_empleador(base, conceptos) -> float:
    tot = _num(base)
    for c in conceptos or []:
        t = str(c.get("tipo", "")).lower()
        if t in ("devengo", "aporte"):
            tot += _num(c.get("monto"))
    return round(tot, 2)


# ── Worksheet + lecturas ─────────────────────────────────────────
def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(NOMINAS_SHEET, tuple(NOMINAS_HEADERS)), None
    except Exception as e:
        logger.warning("payroll: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {NOMINAS_SHEET}: {e}"


@st.cache_data(ttl=30, show_spinner=False)
def _records():
    w, err = _ws()
    if err or w is None:
        return []
    try:
        return w.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        logger.warning("payroll: lectura falló: %s", e)
        return []


def _invalidate():
    try:
        _records.clear()
    except Exception:
        pass


def list_nominas(grupo: str = None, usuario: str = None, incluir_anuladas: bool = False) -> list:
    out = []
    for r in _records():
        if grupo is not None and str(r.get("Grupo", "")) != str(grupo):
            continue
        if usuario is not None and str(r.get("Usuario", "")) != str(usuario):
            continue
        if not incluir_anuladas and str(r.get("Estado", "")).lower() == "anulada":
            continue
        out.append(r)
    return out


def get_nomina(nid: str) -> dict:
    for r in _records():
        if str(r.get("ID", "")) == str(nid):
            return r
    return {}


def resumen(grupo: str) -> dict:
    """{a_pagar (Σneto emitidas), pagado (Σneto pagadas), n}."""
    ap = pg = 0.0
    n = 0
    for f in list_nominas(grupo):
        n += 1
        if str(f.get("Estado", "")).lower() == "pagada":
            pg += _num(f.get("Neto"))
        else:
            ap += _num(f.get("Neto"))
    return {"a_pagar": round(ap, 2), "pagado": round(pg, 2), "n": n}


# ── Escrituras ───────────────────────────────────────────────────
def _max_num() -> int:
    mx = 0
    for r in _records():
        nid = str(r.get("ID", ""))
        if nid.startswith("NOM-"):
            try:
                mx = max(mx, int(nid.split("-")[1]))
            except Exception:
                pass
    return mx


def generar(grupo, desde, hasta, super_pct=0.0, ret_pct=0.0, creado_por="") -> dict:
    """Crea una nómina por usuario con horas en [desde, hasta]. (batch, 1 escritura).

    Precarga: retención (deducción = base×ret%) y superannuation (aporte = base×super%),
    ambos editables luego. Salta usuarios que YA tienen nómina de ese mismo periodo.
    Devuelve {creadas, omitidas, sin_tarifa}.
    """
    w, err = _ws()
    if err:
        return {"error": err}
    d_iso, h_iso = str(desde), str(hasta)
    horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta)
    rates = auth.rate_map(grupo)
    existentes = {(str(f.get("Usuario", "")), str(f.get("PeriodoDesde", "")), str(f.get("PeriodoHasta", "")))
                  for f in list_nominas(grupo, incluir_anuladas=True)}
    rows, creadas, omitidas, sin_tarifa = [], 0, 0, 0
    base_num = _max_num()
    for clave, info in sorted(horas.items()):
        if (clave, d_iso, h_iso) in existentes:
            omitidas += 1
            continue
        tarifa = _num(rates.get(clave, 0))
        if tarifa <= 0:
            sin_tarifa += 1
        base = round(_num(info["horas"]) * tarifa, 2)
        conceptos = []
        if ret_pct > 0:
            conceptos.append({"concepto": "Retención de impuesto (PAYG)",
                              "tipo": "deduccion", "monto": round(base * ret_pct / 100.0, 2)})
        if super_pct > 0:
            conceptos.append({"concepto": "Superannuation",
                              "tipo": "aporte", "monto": round(base * super_pct / 100.0, 2)})
        nt = neto(base, conceptos)
        base_num += 1
        rows.append([
            f"NOM-{base_num:04d}", grupo, clave, str(info["nombre"]), d_iso, h_iso,
            str(info["horas"]), str(tarifa), str(base),
            json.dumps(conceptos, ensure_ascii=False), str(nt),
            "", "emitida", "", str(creado_por or ""),
            clock.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])
        creadas += 1
    if rows:
        w.append_rows(rows, value_input_option="RAW")
        _invalidate()
    return {"creadas": creadas, "omitidas": omitidas, "sin_tarifa": sin_tarifa}


def _find_row(w, nid):
    for i, r in enumerate(w.get_all_records(numericise_ignore=["all"])):
        if str(r.get("ID", "")) == str(nid):
            return i + 2
    return None


def update_conceptos(nid: str, conceptos: list) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    f = get_nomina(nid)
    if not f:
        return False, "Nómina no encontrada."
    row = _find_row(w, nid)
    if row is None:
        return False, "Nómina no encontrada."
    nt = neto(f.get("Base"), conceptos)
    try:
        w.batch_update([
            {"range": f"{_col_letter(_NCOL['ConceptosJSON'])}{row}",
             "values": [[json.dumps(conceptos, ensure_ascii=False)]]},
            {"range": f"{_col_letter(_NCOL['Neto'])}{row}", "values": [[str(nt)]]},
        ], value_input_option="RAW")
    except Exception as e:
        return False, str(e)
    _invalidate()
    return True, "Nómina actualizada."


def marcar_pagada(nid: str, fecha="") -> tuple:
    w, err = _ws()
    if err:
        return False, err
    row = _find_row(w, nid)
    if row is None:
        return False, "Nómina no encontrada."
    try:
        w.batch_update([
            {"range": f"{_col_letter(_NCOL['Estado'])}{row}", "values": [["pagada"]]},
            {"range": f"{_col_letter(_NCOL['FechaPago'])}{row}",
             "values": [[str(fecha or clock.today().isoformat())]]},
        ], value_input_option="RAW")
    except Exception as e:
        return False, str(e)
    _invalidate()
    return True, "Nómina marcada como pagada."


def anular(nid: str) -> tuple:
    w, err = _ws()
    if err:
        return False, err
    row = _find_row(w, nid)
    if row is None:
        return False, "Nómina no encontrada."
    try:
        w.update_cell(row, _NCOL["Estado"], "anulada")
    except Exception as e:
        return False, str(e)
    _invalidate()
    return True, "Nómina anulada."
