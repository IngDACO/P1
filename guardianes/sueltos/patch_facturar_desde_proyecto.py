"""v357 — atajo: facturar desde el propio proyecto.

Hoy, para facturar una obra: Finanzas → Facturas → Nueva → elegir cliente → volver a
buscar el proyecto. El atajo lo hace desde donde estás mirando la obra.

⚠️ Reutiliza el alta que YA existe (`_fac_nueva` + `fac_cli`, el mismo camino que usa
Contactos desde v259). No se construye un segundo creador de facturas: dos mecanismos
para lo mismo es exactamente lo que hubo que desmontar en v140 y v146.

⚠️ **No se fija `fac_scope` a mano.** La etiqueta del proyecto la calcula
`etiqueta_proyectos` sobre la lista de proyectos DE ESE CLIENTE, y lleva el ID detrás
solo si el nombre se repite (v306). Fijarla desde fuera implicaría recalcularla con otro
conjunto y podría no coincidir con ninguna opción del radio — que en Streamlit revienta.
Se pasa el **ID** en `_fac_prj_pending` y el formulario resuelve su propia etiqueta,
aplicándola ANTES de instanciar el widget (regla v111).
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) invoices_ui: consumir el pendiente antes de pintar el radio ──
u = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\invoices_ui.py")
s = u.read_text(encoding="utf-8")

VIEJO = '''    _scope = st.radio("Alcance", ["Todo el cliente"] + prj_names, horizontal=True, key="fac_scope")'''
NUEVO = '''    # v357: atajo desde el proyecto. Llega el ID y AQUÍ se resuelve su etiqueta, que es
    # donde se conoce el conjunto con el que se calculó (v306). Se aplica ANTES de
    # instanciar el radio: escribir la clave de un widget ya creado revienta (v111).
    _pend_pid = st.session_state.pop("_fac_prj_pending", None)
    if _pend_pid:
        _et = _lbl.get(str(_pend_pid))
        if _et in prj_names:
            st.session_state["fac_scope"] = _et
        elif _et:
            st.info(":material/info: Ese proyecto no es de este cliente; elige el alcance a mano.")
    _scope = st.radio("Alcance", ["Todo el cliente"] + prj_names, horizontal=True, key="fac_scope")'''
assert VIEJO in s, "ancla del radio no encontrada"
u.write_text(s.replace(VIEJO, NUEVO), encoding="utf-8")
print("✓ invoices_ui: consume `_fac_prj_pending` antes del radio")

# ── 2) projects_ui: el botón, en la pestaña de Costos ────────────
p = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")
s = p.read_text(encoding="utf-8")

ANCLA = '''    # ── Órdenes de compra: el dinero comprometido (v343) ──
    _ordenes_section(pid, grupo, editable=can_delete, key_prefix=key_prefix)'''
NUEVO2 = '''    # ── Facturar esta obra (atajo, v357) ─────────────────────────
    if can_delete:                      # solo gestión: el campo no factura
        _facturar_atajo(pid, grupo, prj_nombre=str(P.get_project(pid).get("Nombre", "")))

    # ── Órdenes de compra: el dinero comprometido (v343) ──
    _ordenes_section(pid, grupo, editable=can_delete, key_prefix=key_prefix)'''
assert ANCLA in s, "ancla de órdenes no encontrada"
s = s.replace(ANCLA, NUEVO2)

# la función, junto a _ordenes_section
ANCLA2 = '''def render_expenses(pid, grupo, can_delete=False, key_prefix="ex"):'''
NUEVO3 = '''def _facturar_atajo(pid, grupo, prj_nombre=""):
    """Facturar la obra desde la propia obra (v357).

    Reutiliza el alta de `invoices_ui` (no se duplica el creador de facturas) y le pasa
    el ID del proyecto; la etiqueta la resuelve allí. Muestra lo pendiente para que se
    sepa de antemano si hay algo que facturar.
    """
    try:
        from core import invoices as I
        from core import theme as _T
        pend = I.pendiente_de_facturar(pid, grupo)
        facturado = I.facturado_por_proyecto(grupo).get(str(pid), 0.0)
    except Exception:
        return
    if pend <= 0 and facturado <= 0:
        return                          # nada que facturar y nada facturado: no estorbar
    _c1, _c2 = st.columns([3, 2])
    with _c1:
        if pend > 0:
            st.markdown(":material/receipt: **Pendiente de facturar: "
                        + _T.dinero(pend, 0) + "**")
            st.caption("Ingreso estimado del proyecto menos lo ya facturado.")
        else:
            st.markdown(":material/check_circle: **Todo facturado** ("
                        + _T.dinero(facturado, 0) + ")")
    with _c2:
        if st.button(":material/receipt_long: Facturar esta obra", key="fac_atajo_" + str(pid),
                     use_container_width=True, type="primary" if pend > 0 else "secondary",
                     help="Abre la nueva factura con este cliente y este proyecto ya elegidos."):
            prj = P.get_project(pid) or {}
            st.session_state["_fac_nueva"] = True
            # el cliente se preselecciona por NOMBRE porque esa es la clave del selectbox
            _cli = str(prj.get("Cliente", "") or "")
            if _cli:
                st.session_state["fac_cli"] = _cli
            st.session_state["_fac_prj_pending"] = str(pid)
            st.session_state["_admin_nav_pending"] = ("finanzas", "🧾 Facturas")
            st.rerun()


def render_expenses(pid, grupo, can_delete=False, key_prefix="ex"):'''
assert ANCLA2 in s, "ancla de render_expenses no encontrada"
s = s.replace(ANCLA2, NUEVO3, 1)
p.write_text(s, encoding="utf-8")
print("✓ projects_ui: botón «Facturar esta obra» en 💰 Costos (solo gestión)")
