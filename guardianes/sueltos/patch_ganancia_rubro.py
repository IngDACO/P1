"""v360 — la ganancia deja de ser un % y pasa a ser un IMPORTE por rubro.

Decisiones del usuario:
1. La ganancia sobre el trabajador se mide **por hora**.
2. Se define **por proyecto** (cada obra dice cuánto quiere ganar con cada persona).
3. Los materiales cargados en obra (recibos) se facturan **a costo**, sin recargo.

## El modelo

    ingreso  = Σ_persona( horas × (tarifa_costo + ganancia_hora) )  +  materiales
    ganancia = Σ_persona( horas × ganancia_hora )

El **porcentaje deja de ser la entrada** y pasa a ser consecuencia: se sigue calculando
para mostrarlo (y para no romper las pantallas que lo enseñan), pero ya no se teclea.
Es lo mismo que se hizo en la cotización en v355, extendido al proyecto.

## ⚠️ Respaldo: ninguna obra cambia de cifra en silencio

Las 6 obras existentes tienen `MargenMO` (20-30%) y ninguna tiene todavía ganancia por
hora. Cambiar en frío les desplomaría el ingreso estimado —y con él lo pendiente de
facturar— sin que nadie lo pidiera. Así que **si el proyecto no tiene
`GananciaHoraJSON`, se sigue usando el modelo viejo**, y `project_revenue` devuelve
`modelo` para que la pantalla diga cuál está aplicando.

Se guarda en `Proyectos.GananciaHoraJSON` = {"usuario": $/h}: una columna, sin hoja
nueva ni llamada extra (misma solución que ParamsJSON/LineasJSON).
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) projects: la columna + sus accesores ─────────────────────
p = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\projects.py")
s = p.read_text(encoding="utf-8")
if "GananciaHoraJSON" not in s:
    s = s.replace('    "Tipo",\n]',
                  '    "Tipo",\n'
                  '    # v360: {usuario: ganancia $/h} de ESTE proyecto. La ganancia deja de ser\n'
                  '    # un % y pasa a ser un IMPORTE por rubro. VACÍO = sigue el modelo viejo\n'
                  '    # (MargenMO), para que ninguna obra cambie de cifra sin pedirlo.\n'
                  '    "GananciaHoraJSON",\n]', 1)
    assert "GananciaHoraJSON" in s, "no se pudo añadir la columna a PROJECTS_HEADERS"
    s += '''

# ── Ganancia por trabajador y hora (v360) ────────────────────────
def ganancia_hora(pid: str, prj: dict = None) -> dict:
    """{usuario: ganancia $/h} de este proyecto. {} si aún usa el modelo viejo."""
    if prj is None:
        prj = get_project(pid) or {}
    try:
        d = json.loads(str(prj.get("GananciaHoraJSON", "") or "{}"))
        return {str(k): _num(v) for k, v in d.items() if _num(v) != 0}
    except Exception as e:
        logger.warning("projects: GananciaHoraJSON inválido en %s: %s", pid, e)
        return {}


def set_ganancia_hora(pid: str, mapa: dict) -> tuple:
    """Fija cuánto se quiere ganar por hora con cada persona en ESTE proyecto.

    ⚠️ Un mapa vacío devuelve el proyecto al modelo viejo (`MargenMO`), que es una
    vuelta atrás legítima: si te equivocaste al migrarlo, puedes deshacerlo.
    """
    limpio = {str(k): round(_num(v), 2) for k, v in (mapa or {}).items() if _num(v) > 0}
    return update_project(pid, {"GananciaHoraJSON": json.dumps(limpio, ensure_ascii=False)})
'''
    p.write_text(s, encoding="utf-8")
    print("✓ projects: GananciaHoraJSON + ganancia_hora / set_ganancia_hora")

# ── 2) finance: el ingreso, por rubro ───────────────────────────
f = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\finance.py")
s = f.read_text(encoding="utf-8")

VIEJO = '''    mo  = E.labor_cost(pid, grupo)
    mat = E.project_expenses(pid)["total"]
    m   = project_margin(pid, grupo, prj)
    mo_fact = round(mo * (1 + m / 100.0), 2)
    costo   = round(mo + mat, 2)
    ingreso = round(mo_fact + mat, 2)
    return {"costo_mo": round(mo, 2), "materiales": round(mat, 2), "costo": costo,
            "margen_pct": m, "mo_facturable": mo_fact, "ingreso": ingreso,
            "ganancia": round(ingreso - costo, 2)}'''

NUEVO = '''    from core import projects as P
    mat = E.project_expenses(pid)["total"]        # los materiales van a COSTO (v360)
    gh  = P.ganancia_hora(pid, prj)

    if gh:
        # ── v360: ganancia por RUBRO. El trabajador es un rubro: cada persona
        # aporta `horas × su ganancia/hora` en ESTA obra. El % ya no se teclea:
        # se deriva para poder mostrarlo.
        lb = E.labor_breakdown(pid, grupo)
        mo, gan_mo, detalle = 0.0, 0.0, []
        for it in lb.get("items", []):
            u, h, c = str(it.get("usuario", "")), _num(it.get("horas")), _num(it.get("costo"))
            g = _num(gh.get(u))
            mo += c
            gan_mo += h * g
            detalle.append({"usuario": u, "horas": round(h, 2), "costo": round(c, 2),
                            "ganancia_hora": g, "ganancia": round(h * g, 2)})
        mo, gan_mo = round(mo, 2), round(gan_mo, 2)
        costo   = round(mo + mat, 2)
        ingreso = round(costo + gan_mo, 2)
        return {"costo_mo": mo, "materiales": mat, "costo": costo,
                # el % pasa a ser CONSECUENCIA, no entrada
                "margen_pct": round(100.0 * gan_mo / mo, 2) if mo > 0 else 0.0,
                "mo_facturable": round(mo + gan_mo, 2), "ingreso": ingreso,
                "ganancia": gan_mo, "modelo": "rubro", "por_persona": detalle,
                # gente con horas y SIN ganancia puesta: su trabajo se facturaría a
                # costo y nadie lo notaría hasta ver el total (patrón v346)
                "sin_ganancia": [d["usuario"] for d in detalle
                                 if d["ganancia_hora"] <= 0 and d["horas"] > 0]}

    # ── Modelo viejo (respaldo): % sobre la mano de obra ──────────
    # ⚠️ Se conserva para que las obras anteriores a v360 NO cambien de cifra sin
    # que nadie lo pida. En cuanto se le ponga ganancia/hora, esa obra pasa al nuevo.
    mo  = E.labor_cost(pid, grupo)
    m   = project_margin(pid, grupo, prj)
    mo_fact = round(mo * (1 + m / 100.0), 2)
    costo   = round(mo + mat, 2)
    ingreso = round(mo_fact + mat, 2)
    return {"costo_mo": round(mo, 2), "materiales": round(mat, 2), "costo": costo,
            "margen_pct": m, "mo_facturable": mo_fact, "ingreso": ingreso,
            "ganancia": round(ingreso - costo, 2), "modelo": "margen",
            "por_persona": [], "sin_ganancia": []}'''

assert VIEJO in s, "ancla de project_revenue no encontrada"
s = s.replace(VIEJO, NUEVO)
f.write_text(s, encoding="utf-8")
print("✓ finance.project_revenue: ganancia por rubro, con el modelo viejo de respaldo")
