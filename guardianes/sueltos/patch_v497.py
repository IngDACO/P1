# -*- coding: utf-8 -*-
"""v497 · el emparejado dice POR QUÉ, y se puede aplicar de una vez."""
import io
import os

os.chdir("C:/Users/diego/P1/survey_app")


def rep(p, old, new):
    s = io.open(p, encoding="utf-8").read()
    assert s.count(old) == 1, (p, s.count(old), old[:70])
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new))


# ── 1 · xero_nomina: la propuesta, con su motivo ──
VIEJA = '''def propuesta(usuarios: list, empleados: list) -> dict:
    """{usuario: EmployeeID} que se PROPONE: primero por email, luego por nombre.

    ⚠️ Solo parejas ÚNICAS: si dos empleados de Xero comparten email o nombre (o dos
    usuarios de COPEX apuntan al mismo), no se propone nada. Adivinar ahí pagaría las
    horas de una persona a otra; es mejor que el administrador lo elija.
    """
    por_email, por_nombre = {}, {}
    for e in empleados:
        if _cf(e.get("Email")):
            por_email.setdefault(_cf(e.get("Email")), []).append(e["EmployeeID"])
        por_nombre.setdefault(_cf(nombre_empleado(e)), []).append(e["EmployeeID"])
    out = {}
    for u in usuarios:
        login = str(u.get("User", ""))
        cand = por_email.get(_cf(u.get("Email"))) if _cf(u.get("Email")) else None
        if (not cand or len(cand) != 1) and _cf(u.get("Name")):
            cand = por_nombre.get(_cf(u.get("Name")))
        if cand and len(cand) == 1:
            out[login] = cand[0]
    repetidos = {v for v in out.values() if list(out.values()).count(v) > 1}
    return {k: v for k, v in out.items() if v not in repetidos}
'''

NUEVA = '''def propuesta_detallada(usuarios: list, empleados: list) -> dict:
    """{usuario: {"id", "por", "motivo"}} — la pareja propuesta y POR QUÉ (v497).

    `por` = "email" | "nombre" cuando hay pareja. Si no la hay, `motivo` dice cuál de
    los cinco casos es, para que el administrador sepa qué arreglar en vez de mirar un
    «— not in Xero —» mudo: el dato que falta suele estar en COPEX (un correo), no en Xero.

    ⚠️ Solo parejas ÚNICAS: si dos empleados de Xero comparten email o nombre (o dos
    usuarios de COPEX apuntan al mismo), no se propone nada. Adivinar ahí pagaría las
    horas de una persona a otra; es mejor que el administrador lo elija.
    """
    por_email, por_nombre = {}, {}
    for e in empleados:
        if _cf(e.get("Email")):
            por_email.setdefault(_cf(e.get("Email")), []).append(e["EmployeeID"])
        por_nombre.setdefault(_cf(nombre_empleado(e)), []).append(e["EmployeeID"])
    out = {}
    for u in usuarios:
        login = str(u.get("User", ""))
        email, nombre = _cf(u.get("Email")), _cf(u.get("Name"))
        cand = por_email.get(email) if email else None
        if cand and len(cand) == 1:
            out[login] = {"id": cand[0], "por": "email", "motivo": ""}
            continue
        ambiguo_email = bool(cand and len(cand) > 1)
        cand2 = por_nombre.get(nombre) if nombre else None
        if cand2 and len(cand2) == 1:
            out[login] = {"id": cand2[0], "por": "nombre", "motivo": ""}
            continue
        if ambiguo_email:
            motivo = "email_repetido"          # dos empleados de Xero con ese correo
        elif cand2 and len(cand2) > 1:
            motivo = "nombre_repetido"         # dos empleados de Xero se llaman igual
        elif not email:
            motivo = "sin_email"               # en COPEX no tiene correo: es lo que falta
        else:
            motivo = "no_esta"                 # su correo y su nombre no están en Xero
        out[login] = {"id": "", "por": "", "motivo": motivo}
    # ⚠️ Dos personas de COPEX que caen en el MISMO empleado: ninguna se propone.
    ids = [v["id"] for v in out.values() if v["id"]]
    repetidos = {i for i in ids if ids.count(i) > 1}
    for v in out.values():
        if v["id"] in repetidos:
            v.update({"id": "", "por": "", "motivo": "mismo_empleado"})
    return out


def propuesta(usuarios: list, empleados: list) -> dict:
    """{usuario: EmployeeID} que se PROPONE. DELEGA en `propuesta_detallada` (v497):
    una sola definición de cómo se empareja (v323)."""
    return {k: v["id"] for k, v in propuesta_detallada(usuarios, empleados).items() if v["id"]}
'''
rep("core/xero_nomina.py", VIEJA, NUEVA)

# ── 2 · xero_ui: el resumen, los motivos y el botón de aplicar ──
ANCLA = '''    guardado = XN.emparejado(grupo, tenant_id)
    propuesto = XN.propuesta(usuarios, d["empleados"])
'''
NUEVO = '''    guardado = XN.emparejado(grupo, tenant_id)
    detalle = XN.propuesta_detallada(usuarios, d["empleados"])
    propuesto = {k: v["id"] for k, v in detalle.items() if v["id"]}
'''
rep("core/xero_ui.py", ANCLA, NUEVO)

ANCLA2 = '''        st.caption(t("Proposed by email, then by name. Check them and save once; people "
                     "not in Xero Payroll stay «not in Xero»."))
        elegidos = {}
'''
NUEVO2 = '''        st.caption(t("Proposed by email, then by name. Check them and save once; people "
                     "not in Xero Payroll stay «not in Xero»."))
        _n_email = sum(1 for lg, v in detalle.items() if v["por"] == "email" and lg not in guardado)
        _n_nombre = sum(1 for lg, v in detalle.items() if v["por"] == "nombre" and lg not in guardado)
        _sin = {lg: v["motivo"] for lg, v in detalle.items() if not v["id"] and lg not in guardado}
        if _n_email or _n_nombre:
            st.caption(t("Matched for you: {a} by email · {b} by name. Check and save.",
                         a=_n_email, b=_n_nombre))
        if _sin:
            # ⚠️ Un «— not in Xero —» mudo manda a mirar Xero, y lo que casi siempre falta
            # está en COPEX (el correo de esa persona). Se dice cuál es el caso de cada uno.
            _MOT = {
                "sin_email": t("has no email in COPEX: add it and it will match itself"),
                "no_esta": t("their email and name are not in Xero Payroll"),
                "email_repetido": t("two Xero employees share that email"),
                "nombre_repetido": t("two Xero employees have that name"),
                "mismo_empleado": t("two people here point to the same Xero employee"),
            }
            st.caption(t("Not matched ({n}): ", n=len(_sin)) + " · ".join(
                f"{_md(etq_u.get(lg, lg))} — {_MOT.get(m, m)}" for lg, m in _sin.items()))
        # ⚠️ Rellenar las claves de los desplegables va ANTES de instanciarlos (regla v111):
        # por eso el botón deja una bandera y el relleno ocurre en la pasada siguiente.
        if st.session_state.pop("_xn_aplicar_propuesta", False):
            _ya = {st.session_state.get(f"xn_emp_{str(u.get('User', ''))}") for u in usuarios}
            for u in usuarios:
                lg = str(u.get("User", ""))
                pid = propuesto.get(lg, "")
                # solo donde no hay nada elegido: no se pisa lo que el administrador puso
                if pid and not st.session_state.get(f"xn_emp_{lg}") and pid not in _ya:
                    st.session_state[f"xn_emp_{lg}"] = pid
                    _ya.add(pid)
        elegidos = {}
'''
rep("core/xero_ui.py", ANCLA2, NUEVO2)

ANCLA3 = '''        if st.button(t(":material/save: Save matches"), key="xn_guardar",
                     disabled=bool(repetidos)):'''
NUEVO3 = '''        if propuesto and st.button(t(":material/auto_fix_high: Fill in the {n} proposed "
                                    "matches", n=len(propuesto)), key="xn_aplicar"):
            st.session_state["_xn_aplicar_propuesta"] = True
            st.rerun()
        if st.button(t(":material/save: Save matches"), key="xn_guardar",
                     disabled=bool(repetidos)):'''
rep("core/xero_ui.py", ANCLA3, NUEVO3)
print("v497 parcheado")
