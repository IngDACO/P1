"""
Radar del grupo para el agente/administrador: reúne los hechos relevantes del
cliente (grupo) al que pertenece el admin — sin IA. Dos salidas:

- `group_digest(grupo)`  → dict con lo PENDIENTE/novedades (retrasos, alarmas,
  vencimientos, near miss, sin asignar, contacto de campo faltante, panorama).
- `group_snapshot_text(grupo)` → listado compacto del portafolio, como contexto
  en vivo para que el agente responda preguntas, recomiende y redacte.
"""
import logging

import streamlit as st

from core import projects as P
from core import alerts
from core import auth
from core import prestart
from core import clock
from core.num import parse_date as _parse_date

logger = logging.getLogger(__name__)

_DONE = ("Completado", "Cancelado")


def _base(grupo) -> dict:
    proys = P.list_projects(grupo=grupo)
    return {
        "proys":   proys,
        "activos": [p for p in proys if str(p.get("Estado", "")) not in _DONE],
        "delays":  P.delays_for(proys),
        "horas":   P.project_hours_bulk(grupo),
        "alarmas": alerts.open_counts_all() if alerts.is_configured() else {},
    }


@st.cache_data(ttl=120, show_spinner=False)
def group_digest(grupo) -> dict:
    b = _base(grupo)
    proys, activos, delays, horas, alarmas = (b["proys"], b["activos"], b["delays"],
                                              b["horas"], b["alarmas"])
    name = {str(p.get("ID", "")): p.get("Nombre", "") for p in proys}
    hoy = clock.today()

    retrasos = sorted(
        [{"id": pid, "nombre": name.get(pid, pid), "dias": round(d)} for pid, d in delays.items()],
        key=lambda x: -x["dias"])

    al = [{"id": str(p.get("ID", "")), "nombre": p.get("Nombre", ""),
           "n": alarmas.get(str(p.get("ID", "")), 0)}
          for p in activos if alarmas.get(str(p.get("ID", "")), 0)]

    por_vencer, vencidos = [], []
    for p in activos:
        ff = _parse_date(p.get("FechaFinEst"))
        if not ff:
            continue
        dd = (ff - hoy).days
        item = {"id": str(p.get("ID", "")), "nombre": p.get("Nombre", ""),
                "fin": ff.strftime("%Y-%m-%d"), "dias": dd}
        if dd < 0:
            vencidos.append(item)
        elif dd <= 7:
            por_vencer.append(item)

    near = []
    for p in proys:
        try:
            for ps in prestart.list_prestarts(p.get("ID")):
                if str(ps.get("NearMiss", "")).upper() == "YES":
                    fd = _parse_date(ps.get("Fecha"))
                    if fd and (hoy - fd).days <= 7:
                        near.append({"proyecto": p.get("Nombre", ""), "fecha": ps.get("Fecha", ""),
                                     "desc": ps.get("NearMissDesc", "")})
        except Exception:
            pass

    campo_sin = []
    for u in auth.list_users(grupo):
        if str(u.get("Rol", "")).lower() != "campo":
            continue
        if not (str(u.get("Email", "")).strip() and str(u.get("TelegramChatID", "")).strip()):
            campo_sin.append(u.get("Usuario", ""))

    sin_asig = [{"id": str(p.get("ID", "")), "nombre": p.get("Nombre", "")}
                for p in activos
                if not [x for x in str(p.get("CampoAsignados", "")).split(";") if x.strip()]]

    # Credenciales por vencer/vencidas del grupo
    cred_venc = []
    try:
        from core import credentials
        if credentials.is_configured():
            cred_venc = credentials.expiring(grupo)
    except Exception:
        pass

    # Proyectos sobre presupuesto
    sobre_pres = []
    try:
        from core import expenses
        if expenses.is_configured():
            sobre_pres = expenses.over_budget(grupo)
    except Exception:
        pass

    avances = [P._num(p.get("Avance")) for p in proys]
    return {
        "grupo": grupo,
        "n_total": len(proys), "n_activos": len(activos),
        "avance_prom": round(sum(avances) / len(avances)) if avances else 0,
        "horas": round(sum(horas.get(str(p.get("ID", "")), 0.0) for p in proys)),
        "retrasos": retrasos, "alarmas": al,
        "por_vencer": sorted(por_vencer, key=lambda x: x["dias"]),
        "vencidos": sorted(vencidos, key=lambda x: x["dias"]),
        "near_miss": near, "campo_sin_contacto": campo_sin, "sin_asignar": sin_asig,
        "cred_venc": cred_venc, "sobre_presupuesto": sobre_pres,
    }


_PENDING_KEYS = ("retrasos", "alarmas", "por_vencer", "vencidos",
                 "near_miss", "campo_sin_contacto", "sin_asignar", "cred_venc",
                 "sobre_presupuesto")


def has_pending(d) -> bool:
    return any(d.get(k) for k in _PENDING_KEYS)


def digest_text(d) -> str:
    """Hechos en texto (para el prompt del agente y como fallback sin IA)."""
    L = [f"Grupo {d['grupo']}: {d['n_activos']} proyecto(s) activo(s) de {d['n_total']}, "
         f"avance promedio {d['avance_prom']}%, {d['horas']} horas registradas."]
    if d["vencidos"]:
        L.append("VENCIDOS: " + "; ".join(f"{x['nombre']} (hace {abs(x['dias'])} d, fin {x['fin']})"
                                          for x in d["vencidos"]))
    if d["por_vencer"]:
        L.append("Por vencer (≤7 d): " + "; ".join(f"{x['nombre']} (en {x['dias']} d, {x['fin']})"
                                                    for x in d["por_vencer"]))
    if d["retrasos"]:
        L.append("En retraso (SPI): " + "; ".join(f"{x['nombre']} ({x['dias']} d)" for x in d["retrasos"]))
    if d["alarmas"]:
        L.append("Alarmas abiertas: " + "; ".join(f"{x['nombre']} ({x['n']})" for x in d["alarmas"]))
    if d["near_miss"]:
        L.append("Near miss recientes (≤7 d): "
                 + "; ".join(f"{x['proyecto']} ({x['fecha']}: {x['desc'] or 's/d'})" for x in d["near_miss"]))
    if d["sin_asignar"]:
        L.append("Sin campo asignado: " + "; ".join(x["nombre"] for x in d["sin_asignar"]))
    if d["campo_sin_contacto"]:
        L.append("Campo sin contacto completo (no se les puede notificar): "
                 + ", ".join(d["campo_sin_contacto"]))
    if d.get("cred_venc"):
        L.append("Credenciales por vencer/vencidas: "
                 + "; ".join(f"{c['usuario']} · {c['tipo']} "
                             f"({'VENCIDA' if c['dias'] < 0 else f'en {c['dias']} d'})"
                             for c in d["cred_venc"]))
    if d.get("sobre_presupuesto"):
        L.append("Sobre presupuesto: "
                 + "; ".join(f"{x['nombre']} ({x['pct']}%)" for x in d["sobre_presupuesto"]))
    if len(L) == 1:
        L.append("Sin pendientes urgentes.")
    return "\n".join(L)


@st.cache_data(ttl=120, show_spinner=False)
def grupos_fuera_del_maestro() -> list:
    """Grupos con libro propio (v359). Sus datos NO entran en este consolidado.

    ⚠️ Se expone para que la pantalla lo DIGA. Un resumen al que le faltan clientes sin
    avisar es peor que no tenerlo: el propietario tomaría decisiones sobre una foto
    incompleta creyéndola entera."""
    try:
        return auth.grupos_con_libro_propio()
    except Exception:
        return []


def owner_digest() -> list:
    """Resumen por grupo para el propietario: [{grupo, activos, avance, retrasos,
    alarmas, vencidos, cred_venc, sobre_presupuesto, pendientes}]."""
    out = []
    try:
        grupos = [g["Grupo"] for g in auth.list_groups()]
    except Exception:
        grupos = []
    for g in grupos:
        try:
            d = group_digest(g)
        except Exception:
            continue
        out.append({
            "grupo": g,
            "activos": d["n_activos"], "avance": d["avance_prom"],
            "retrasos": len(d["retrasos"]),
            "alarmas": sum(a["n"] for a in d["alarmas"]),
            "vencidos": len(d["vencidos"]),
            "cred_venc": len(d.get("cred_venc", [])),
            "sobre_presupuesto": len(d.get("sobre_presupuesto", [])),
            "pendientes": has_pending(d),
        })
    out.sort(key=lambda x: -(x["retrasos"] + x["alarmas"] + x["vencidos"]))
    return out


def group_snapshot_text(grupo, max_proys=30) -> str:
    """Listado compacto del portafolio del grupo (contexto en vivo para el agente)."""
    b = _base(grupo)
    proys, delays, horas, alarmas = b["proys"], b["delays"], b["horas"], b["alarmas"]
    if not proys:
        return f"El grupo {grupo} no tiene proyectos."
    lines = [f"## ESTADO EN VIVO DEL GRUPO {grupo} ({len(proys)} proyectos)"]
    for p in proys[:max_proys]:
        pid = str(p.get("ID", ""))
        campo = ", ".join([x for x in str(p.get("CampoAsignados", "")).split(";") if x.strip()]) or "sin asignar"
        extra = []
        d = delays.get(pid)
        if d:
            extra.append(f"retraso {round(d)} d")
        na = alarmas.get(pid, 0)
        if na:
            extra.append(f"{na} alarma(s)")
        lines.append(
            f"- [{pid}] {p.get('Nombre', '')} | {p.get('Estado', '')} | avance {P._num(p.get('Avance')):.0f}% "
            f"| fin est {p.get('FechaFinEst', '') or '—'} | campo: {campo} "
            f"| {horas.get(str(p.get('ID', '')), 0.0):.0f} h"
            + (" | " + ", ".join(extra) if extra else ""))
    us = []
    for u in auth.list_users(grupo):
        if str(u.get("Rol", "")).lower() == "campo":
            ok = str(u.get("Email", "")).strip() and str(u.get("TelegramChatID", "")).strip()
            us.append(f"{u.get('Usuario', '')}{'' if ok else ' (SIN contacto completo)'}")
    if us:
        lines.append("Usuarios de campo: " + ", ".join(us))
    return "\n".join(lines)
