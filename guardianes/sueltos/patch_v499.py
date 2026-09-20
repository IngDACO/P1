# -*- coding: utf-8 -*-
"""v499 · las actividades se encadenan: columna, remapeo, cronograma y pantalla."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")


def rep(p, old, new):
    s = io.open(p, encoding="utf-8").read()
    assert s.count(old) == 1, (p, s.count(old), old[:70])
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))


# ── 1 · projects: la columna, AL FINAL (migra sola, v363) ──
rep("core/projects.py",
    '''ACTIVITIES_HEADERS = [
    "ProjectID", "Order", "Name", "DurationDays", "Weight", "Progress",
    "ActualStartDate", "ActualEndDate", "Note",
]''',
    '''ACTIVITIES_HEADERS = [
    "ProjectID", "Order", "Name", "DurationDays", "Weight", "Progress",
    "ActualStartDate", "ActualEndDate", "Note",
    # v499: detrás de qué va esta actividad («3;5-2»). ⚠️ AL FINAL: las filas se
    # escriben por POSICIÓN y colar una columna en medio guarda cada dato en la de al
    # lado (v363). Vacío = detrás de la anterior, que es lo que la app hacía hasta v498.
    "Predecessors",
]''')

# la fila de create_project y la de add_activity: un valor MÁS (v363)
rep("core/projects.py",
    '''        str(a.get("peso", a.get("Weight", 0))),
        "0", "", "", "",
    ] for i, a in enumerate(activities or [])]''',
    '''        str(a.get("peso", a.get("Weight", 0))),
        "0", "", "", "", str(a.get("pred", a.get("Predecessors", ""))),
    ] for i, a in enumerate(activities or [])]''')
rep("core/projects.py",
    '''    aws.append_row([pid, str(orden), str(nombre), str(int(_num(duracion) or 1)),
                    str(_num(peso)), "0", "", "", ""], value_input_option="RAW")''',
    '''    aws.append_row([pid, str(orden), str(nombre), str(int(_num(duracion) or 1)),
                    str(_num(peso)), "0", "", "", "", ""], value_input_option="RAW")''')

# ── 2 · guardar: la columna nueva + REMAPEAR al reordenar o borrar ──
rep("core/projects.py",
    '''    batch = []
    for e in edits:
        row = rowmap.get(str(e.get("orden0")))
        if row is None:
            continue
        for field in ("Name", "DurationDays", "Weight", "Order"):''',
    '''    # ⚠️ v499: si cambian los números de orden, «detrás de la 3» pasaría a apuntar a
    # OTRA actividad sin que nada avise. Se remapea con el mapa viejo→nuevo, y una
    # referencia a algo que ya no está se cae de la lista (`plan.remapear`).
    mapa = {int(_num(e.get("orden0"))): int(_num(e.get("Order", e.get("orden0"))))
            for e in edits if str(e.get("orden0", "")).strip() != ""}
    batch = []
    for e in edits:
        row = rowmap.get(str(e.get("orden0")))
        if row is None:
            continue
        if "Predecessors" in _ACOL:
            _p = e.get("Predecessors")
            if _p is None:                       # no se editó: se conserva y se remapea
                _p = next((r.get("Predecessors", "") for r in recs
                           if str(r.get("ProjectID", "")) == str(pid)
                           and str(r.get("Order", "")) == str(e.get("orden0"))), "")
            batch.append({"range": f"{_col_letter(_ACOL['Predecessors'])}{row}",
                          "values": [[plan.remapear(_p, mapa)]]})
        for field in ("Name", "DurationDays", "Weight", "Order"):''')

# delete_activity: las referencias a la borrada tienen que caerse
rep("core/projects.py",
    '''def delete_activity(pid, orden) -> tuple:
    """Elimina una actividad y recalcula el % del proyecto."""''',
    '''def limpiar_predecesoras(pid, orden_borrado) -> None:
    """Quita de las demás actividades la referencia a la que se acaba de borrar (v499).

    ⚠️ Si no, esa referencia apunta a un número que ya no existe: `plan.calcular` la
    ignoraría con aviso, pero la actividad quedaría empezando el día 0 — un plan que
    miente en silencio.
    """
    aws, err = _activities_ws()
    if err or "Predecessors" not in _ACOL:
        return
    try:
        recs = valores.canonizar(columnas.canonizar(
            aws.get_all_records(numericise_ignore=["all"])), PROJECTS_SHEET)
        batch = []
        for i, r in enumerate(recs):
            if str(r.get("ProjectID", "")) != str(pid):
                continue
            crudo = str(r.get("Predecessors", "") or "")
            if not crudo:
                continue
            mapa = {o: o for o, _l in plan.parse(crudo) if int(o) != int(_num(orden_borrado))}
            nuevo = plan.remapear(crudo, mapa)
            if nuevo != crudo:
                batch.append({"range": f"{_col_letter(_ACOL['Predecessors'])}{i + 2}",
                              "values": [[nuevo]]})
        if batch:
            aws.batch_update(batch, value_input_option="RAW")
            _invalidate()
    except Exception as e:
        logger.warning("projects.limpiar_predecesoras: %s", e)


def delete_activity(pid, orden) -> tuple:
    """Elimina una actividad y recalcula el % del proyecto."""''')

# ── 3 · el cronograma reconstruido pasa las predecesoras ──
rep("core/projects.py",
    '''    custom = [{"nombre":   a.get("Name", ""),
               "duracion": _num(a.get("DurationDays")) or 1.0,
               "peso":     _num(a.get("Weight"))} for a in acts]''',
    '''    custom = [{"nombre":   a.get("Name", ""),
               "duracion": _num(a.get("DurationDays")) or 1.0,
               "peso":     _num(a.get("Weight")),
               "orden":    _num(a.get("Order")) or (i + 1),
               "pred":     str(a.get("Predecessors", "") or "")}
              for i, a in enumerate(acts)]''')
print("projects.py listo")
