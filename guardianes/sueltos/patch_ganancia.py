"""La «ganancia real» a mitad de obra no es ganancia: es que aún no has gastado.

Con el proyecto al 0% y $900 de costo, `ingreso − costo` daba $3.499 contra $893
cotizados, en verde. Técnicamente cierto, historia falsa. Se sustituye por la
PROYECCIÓN al ritmo actual, que es el patrón que v144 estableció para el presupuesto.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) core/quotes.py: proyectar el costo y la ganancia ──────────
q = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes.py")
s = q.read_text(encoding="utf-8")

VIEJO = '''    return {
        "proyecto_id": pid, "proyecto": str(prj.get("Nombre", "")),
        "avance": _num(prj.get("Avance")),
        "horas": _dif(t["horas"], horas_real),
        "costo": _dif(t["costo"], real["total"]),
        # el ingreso es fijo: es lo que el cliente aceptó pagar
        "ingreso": t["subtotal"],
        "ganancia": _dif(t["ganancia"], t["subtotal"] - real["total"]),
    }'''

NUEVO = '''    av = _num(prj.get("Avance"))
    # ⚠️ A mitad de obra, `ingreso − costo` NO es la ganancia: es lo que todavía no has
    # gastado. Con el proyecto al 0% y $900 de costo daba $3.499 «de ganancia» contra
    # $893 cotizados, en verde — un número cierto que cuenta una historia falsa (la
    # familia de v320 y v324). Lo que sí es accionable es la PROYECCIÓN al ritmo
    # actual, igual que `expenses.cost_projection` hace con el presupuesto (v144).
    costo_proy = round(real["total"] * 100.0 / av, 2) if av > 0 and real["total"] > 0 else None
    gan_proy = round(t["subtotal"] - costo_proy, 2) if costo_proy is not None else None
    return {
        "proyecto_id": pid, "proyecto": str(prj.get("Nombre", "")),
        "avance": av,
        "terminado": av >= 100,
        "horas": _dif(t["horas"], horas_real),
        "costo": _dif(t["costo"], real["total"]),
        # el ingreso es fijo: es lo que el cliente aceptó pagar
        "ingreso": t["subtotal"],
        "ganancia_cotizada": t["ganancia"],
        # ⚠️ None mientras no haya avance o costo: sin base, proyectar es inventar.
        "costo_proyectado": costo_proy,
        "ganancia_proyectada": gan_proy,
        # solo tiene sentido llamarla «real» cuando la obra terminó
        "ganancia_real": round(t["subtotal"] - real["total"], 2) if av >= 100 else None,
    }'''

assert VIEJO in s, "ancla no encontrada en quotes.py"
q.write_text(s.replace(VIEJO, NUEVO), encoding="utf-8")
print("✓ quotes.comparacion proyecta en vez de mentir")

# ── 2) core/quotes_ui.py: la tarjeta correspondiente ─────────────
u = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes_ui.py")
s = u.read_text(encoding="utf-8")

VIEJO_UI = '''    # ⚠️ En la GANANCIA el sentido se invierte: subir es BUENO (el mismo cuidado que en
    # v341 con los costos, pero al revés). Se arma aparte para no pintarla en rojo.
    g = comp["ganancia"]
    _cg = T.VERDE if g["dif"] >= 0 else T.ROJO
    T.kpi_row([
        _tarj("Horas", comp["horas"], "h"),
        _tarj("Costo", comp["costo"]),
        ("Ingreso", T.dinero(comp["ingreso"], 0), "lo que aceptó el cliente"),
        ("Ganancia real", T.dinero(g["real"], 0),
         "cotizaste " + T.dinero(g["cotizado"], 0), _cg),
    ])'''

NUEVO_UI = '''    # ⚠️ La GANANCIA no se compara «real vs cotizada» a mitad de obra: hasta terminar,
    # lo no gastado parece ganancia. Se muestra la PROYECCIÓN al ritmo actual (v144) y
    # solo se llama «real» cuando el proyecto está al 100%.
    _gc = comp["ganancia_cotizada"]
    if comp["terminado"]:
        _g, _etq, _pie = comp["ganancia_real"], "Ganancia real", "obra terminada"
    elif comp["ganancia_proyectada"] is not None:
        _g, _etq = comp["ganancia_proyectada"], "Ganancia proyectada"
        _pie = "al ritmo actual · cotizaste " + T.dinero(_gc, 0)
    else:
        _g, _etq, _pie = None, "Ganancia proyectada", "aún no hay avance ni costo"
    _cg = T.VERDE if (_g is not None and _g >= _gc) else (T.ROJO if _g is not None else None)
    T.kpi_row([
        _tarj("Horas", comp["horas"], "h"),
        _tarj("Costo", comp["costo"]),
        ("Ingreso", T.dinero(comp["ingreso"], 0), "lo que aceptó el cliente"),
        (_etq, T.dinero(_g, 0) if _g is not None else "—", _pie, _cg),
    ])
    if comp["costo_proyectado"] is not None:
        st.caption(":material/trending_up: Al ritmo actual la obra costará "
                   + T.dinero(comp["costo_proyectado"], 0) + " contra los "
                   + T.dinero(comp["costo"]["cotizado"], 0) + " cotizados.")'''

assert VIEJO_UI in s, "ancla no encontrada en quotes_ui.py"
u.write_text(s.replace(VIEJO_UI, NUEVO_UI), encoding="utf-8")
print("✓ la tarjeta ya no llama «real» a lo que no lo es")
