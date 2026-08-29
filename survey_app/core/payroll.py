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
from core.num import col_letter as _col_letter, num as _num, parse_date as _parse_date

logger = logging.getLogger(__name__)

NOMINAS_SHEET = "Nominas"
NOMINAS_HEADERS = [
    "ID", "Grupo", "Usuario", "Nombre", "PeriodoDesde", "PeriodoHasta",
    "Horas", "TarifaHora", "Base", "ConceptosJSON", "Neto",
    "FechaPago", "Estado", "Nota", "CreadoPor", "Creado",
]
_NCOL = {h: i + 1 for i, h in enumerate(NOMINAS_HEADERS)}
TIPOS = ["devengo", "deduccion", "aporte"]



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


# ── Worksheet + lecturas ─────────────────────────────────────────
def _ws():
    if not timeclock._secrets_present():
        return None, "Google Sheets no está configurado."
    try:
        return timeclock.get_sheet(NOMINAS_SHEET, tuple(NOMINAS_HEADERS)), None
    except Exception as e:
        logger.warning("payroll: no se pudo abrir la hoja: %s", e)
        return None, f"No se pudo abrir la hoja {NOMINAS_SHEET}: {e}"


@st.cache_data(ttl=120, show_spinner=False)
def _records_cached(libro: str):
    """Registros de NOMINAS_SHEET (por lote, v339)."""
    from core import hojas          # perezoso: evita el ciclo con timeclock
    return hojas.registros(NOMINAS_SHEET, NOMINAS_HEADERS) or []




def _records():
    """Envoltorio: resuelve el libro y delega en la versión cacheada (v378).

    ⚠️ El id del libro va en la CLAVE de caché. Sin él, `st.cache_data` —que se
    comparte por PROCESO— servía al segundo cliente lo que dejó memoizado el
    primero: una fuga de datos entre inquilinos, no un problema de rendimiento.
    """
    return _records_cached(_libro_de(NOMINAS_SHEET))
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
    Devuelve {creadas, omitidas, sin_tarifa: [nombres]}.

    ⚠️ v346 — SIN TARIFA NO SE GENERA (decisión del usuario). Antes se creaba igual con
    base $0: una colilla de $0 por trabajo hecho es un documento EQUIVOCADO, y se
    quedaba ahí (en la hoja real había una, `NOM-0002`: 8,69 h de trabajo → $0, emitida
    antes de que esa persona tuviera tarifa). Ahora se salta y se devuelve el NOMBRE
    para poder arreglarlo. **Es reversible**: al ponerle la tarifa y volver a generar el
    mismo periodo entra sin duplicar, porque no dejó fila que active el salto de
    duplicados. Al resto del equipo no le afecta: su nómina se genera igual.
    """
    w, err = _ws()
    if err:
        return {"error": err}
    d_iso, h_iso = str(desde), str(hasta)
    horas = timeclock.horas_por_usuario_rango(grupo, desde, hasta)
    rates = auth.rate_map(grupo)
    # ⚠️ v347: las ANULADAS no bloquean. Antes se contaban como existentes, así que
    # **no había forma de reemitir el periodo de nadie**: anulabas la nómina mal hecha
    # y al regenerar decía «omitidas: 1» y no creaba nada. Si se puede deshacer, tiene
    # que poder rehacerse (el principio de v340 con lo archivado). La fila anulada se
    # queda como rastro de lo que se corrigió; `list_nominas` la oculta por defecto y
    # ni `resumen` ni el `costo_nomina` del P&L la cuentan, así que no se duplica nada.
    existentes = {(str(f.get("Usuario", "")), str(f.get("PeriodoDesde", "")), str(f.get("PeriodoHasta", "")))
                  for f in list_nominas(grupo)}

    # ⚠️ v364: el salto de duplicados de arriba compara la TERNA EXACTA, así que un
    # periodo que SOLAPA con otro ya emitido pasaba sin que nada avisara — y esas horas
    # se pagan DOS VECES. No es hipotético: salió con datos reales cuando dos personas
    # generaron nóminas a la vez (quincenas 20/07-02/08 y 03/08-16/08 contra un
    # 21/07-19/08); a `campo1` se le pagaron 567 h habiendo trabajado 354.
    # La conciliación de v313 lo detectaba («sin explicar −$36.035»), pero DESPUÉS de
    # emitir: aquí se corta antes.
    _d, _h = _parse_date(d_iso), _parse_date(h_iso)
    solapes = {}
    if _d and _h:
        for f in list_nominas(grupo):            # ya excluye las anuladas (v347)
            fd, fh = _parse_date(f.get("PeriodoDesde")), _parse_date(f.get("PeriodoHasta"))
            if not fd or not fh:
                continue                          # sin fechas legibles no se puede afirmar
            if str(f.get("PeriodoDesde", "")) == d_iso and str(f.get("PeriodoHasta", "")) == h_iso:
                continue                          # el duplicado EXACTO ya lo trata `existentes`
            if fd <= _h and _d <= fh:             # intersección de intervalos cerrados
                solapes.setdefault(str(f.get("Usuario", "")), []).append(
                    {"id": str(f.get("ID", "")), "desde": str(f.get("PeriodoDesde", "")),
                     "hasta": str(f.get("PeriodoHasta", "")),
                     "nombre": str(f.get("Nombre", "") or f.get("Usuario", ""))})

    # ⚠️ v430: las AUSENCIAS PAGADAS. La base sale de las horas FICHADAS, y quien está
    # de vacaciones o de baja no ficha: sin esto, aprobarle unas vacaciones a alguien
    # significaba pagarle $0 esa quincena — y si estuvo fuera el periodo ENTERO, ni
    # siquiera aparecía en `horas`, así que **no se le generaba nómina en absoluto**.
    # Por eso las claves se unen abajo en vez de recorrer solo lo fichado.
    aus = {}
    try:
        from core import ausencias as AU
        aus = AU.horas_pagadas_grupo(grupo, desde, hasta)
    except Exception as e:
        # Best-effort: un fallo leyendo ausencias no puede impedir pagar lo trabajado.
        logger.warning("payroll.generar: no se pudieron leer las ausencias: %s", e)

    # v432: días en que la ausencia se recortó porque además se fichó. Se informan
    # para que el ajuste NO sea silencioso (ver `ausencias.horas_pagadas_grupo`).
    recortes = []
    for _k, _v in (aus or {}).items():
        for _r in _v.get("recortados", []):
            recortes.append({"nombre": _v.get("nombre") or _k, "usuario": _k,
                             "fecha": str(_r["fecha"]), "fichadas": _r["fichadas"],
                             "pagadas": _r["pagadas"]})

    rows, creadas, omitidas, sin_tarifa, solapadas = [], 0, 0, [], []
    base_num = _max_num()
    for clave in sorted(set(horas) | set(aus)):
        info = horas.get(clave) or {
            "horas": 0.0,
            "nombre": str((aus.get(clave) or {}).get("nombre") or clave)}
        if (clave, d_iso, h_iso) in existentes:
            omitidas += 1
            continue
        if clave in solapes:
            # ⚠️ NO se emite: pagar dos veces las mismas horas es un error de dinero y
            # es MUY difícil de ver después (la colilla individual sale correcta; solo
            # el total del periodo delata). Se nombra el periodo que estorba para que
            # se pueda anular o cambiar el rango.
            for s in solapes[clave]:
                solapadas.append({"nombre": s["nombre"], "usuario": clave,
                                  "id": s["id"], "desde": s["desde"], "hasta": s["hasta"]})
            continue
        tarifa = _num(rates.get(clave, 0))
        if tarifa <= 0:
            # ⚠️ v346: se SALTA, no se crea con $0 (ver el docstring).
            sin_tarifa.append((str(info.get("nombre") or clave), clave))
            continue
        base = round(_num(info["horas"]) * tarifa, 2)
        conceptos = []

        # ⚠️ v430: la ausencia pagada va como DEVENGO, **no sumada a `Base`**. `Base` y
        # la columna `Horas` son «lo trabajado», y es contra eso que `conciliacion_mo`
        # (v313) contrasta la jornada fichada: meterlo dentro haría que cada vacación
        # aprobada apareciera como un descuadre («sin explicar») que no existe.
        _a = aus.get(clave) or {}
        _ah = _num(_a.get("horas"))
        monto_aus = round(_ah * tarifa, 2) if _ah > 0 else 0.0
        if monto_aus > 0:
            from core import ausencias as _AU
            conceptos.append({
                "concepto": (_AU.etiqueta_ausencias(_a.get("por_tipo"))
                             or "Ausencia pagada") + f" — {_ah:g} h",
                "tipo": "devengo", "monto": monto_aus, "origen": "ausencia"})

        # ⚠️ La retención y el aporte se calculan sobre base + ausencia pagada: un día
        # de vacaciones es salario ordinario, y dejarlo fuera lo pagaría sin impuesto
        # ni superannuation. Los dos porcentajes siguen siendo editables después.
        bruto = round(base + monto_aus, 2)
        if ret_pct > 0:
            # ⚠️ v436: el texto se GUARDA en `ConceptosJSON`, así que esto solo afecta a
            # las nóminas NUEVAS; las ya emitidas conservan el suyo en español (son
            # datos históricos). Nadie compara este texto — se comparan `tipo` y
            # `origen`, que siguen igual.
            conceptos.append({"concepto": "Income tax withheld (PAYG)",
                              "tipo": "deduccion", "monto": round(bruto * ret_pct / 100.0, 2)})
        if super_pct > 0:
            conceptos.append({"concepto": "Superannuation",
                              "tipo": "aporte", "monto": round(bruto * super_pct / 100.0, 2)})
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
    # ⚠️ v348: desempatar HOMÓNIMOS. En producción salió `['Bobo', 'fijiofgjei',
    # 'fijiofgjei']`: dos personas distintas con el mismo nombre, en el aviso que
    # justamente te dice a quién ponerle la tarifa. El login solo se añade cuando el
    # nombre se repite, para no ensuciar el caso normal (regla de v151/v306/v319).
    _veces = {}
    for nom, _ in sin_tarifa:
        _veces[nom] = _veces.get(nom, 0) + 1
    st_txt = [f"{nom} ({clave})" if _veces[nom] > 1 else nom for nom, clave in sin_tarifa]
    return {"creadas": creadas, "omitidas": omitidas, "sin_tarifa": st_txt,
            "solapadas": solapadas, "recortes": recortes}


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
