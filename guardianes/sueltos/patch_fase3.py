"""Inserta la fase 3 (aceptar → proyecto, y cotizado vs real) en quotes_ui.py."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\quotes_ui.py")
s = p.read_text(encoding="utf-8")

VIEJO = '''    if est == Q.ACEPTADA and not str(c.get("ProyectoID", "")).strip():
        st.info(":material/construction: Aceptada. En la próxima versión, desde aquí se "
                "creará el proyecto con este presupuesto y margen.")'''

NUEVO = '''    # ── Fase 3: de cotización ganada a obra ──────────────────────
    if est == Q.ACEPTADA and not str(c.get("ProyectoID", "")).strip():
        _crear_proyecto(grupo, c, t)
    elif str(c.get("ProyectoID", "")).strip():
        _comparacion(cid, c)


def _crear_proyecto(grupo, c, t):
    """Aceptada y sin obra todavía: darla de alta con lo ya pactado."""
    st.markdown("---")
    st.markdown("### :material/construction: Convertirla en proyecto")
    st.caption("Nace con el cliente, el presupuesto y el margen que acabas de cotizar. "
               "Desde ahí sigue el flujo de siempre: costos, horas y factura.")
    with st.form("cot_prj_" + str(c.get("ID"))):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre del proyecto",
                               value=str(c.get("ClienteNombre", "")) + " — Nº"
                                     + str(c.get("Numero", "")))
        tipo = c2.selectbox("Tipo", ["Instalación", "Delivery", "Ripout", "Otro"])
        c3, c4 = st.columns(2)
        ini = c3.date_input("Fecha de inicio", value=clock.today(grupo))
        ns = c4.number_input("Paradas (NS)", min_value=0, step=1, value=0,
                             help="Solo la instalación genera el cronograma estándar; "
                                  "con NS 0 el proyecto nace sin actividades.")
        ubic = st.text_input("Ubicación (opcional)")
        st.info(":material/savings: Presupuesto del proyecto: **"
                + T.dinero(t["costo"], 0) + "** — es tu **costo** cotizado, no el precio "
                "al cliente (" + T.dinero(t["subtotal"], 0) + "). Así la alerta de "
                "sobre-presupuesto salta cuando te comes el margen, no cuando ya "
                "estás perdiendo dinero.")
        if st.form_submit_button(":material/add_circle: Crear el proyecto",
                                 type="primary", use_container_width=True):
            ok, msg = Q.aceptar_y_crear_proyecto(
                c.get("ID"), nombre=nombre, tipo=tipo, fecha_inicio=ini,
                ns=ns, ubicacion=ubic, creado_por=_creado_por())
            if ok:
                st.success("Proyecto " + str(msg) + " creado desde esta cotización.")
                st.rerun()
            else:
                st.error(msg)


def _comparacion(cid, c):
    """Cotizado contra real: lo que hace que cotizar sirva para gestionar."""
    st.markdown("---")
    comp = Q.comparacion(cid)
    if not comp:
        st.caption("Enlazada al proyecto " + str(c.get("ProyectoID")) + ".")
        return
    st.markdown("### :material/compare_arrows: Cotizado vs. real — " + comp["proyecto"])

    def _tarj(etq, d, unidad=""):
        _col = T.VERDE if d["dif"] <= 0 else T.ROJO
        _sig = "+" if d["dif"] > 0 else ""
        _val = (("%g " % d["real"]) + unidad).strip() if unidad else T.dinero(d["real"], 0)
        _cot = (("%g " % d["cotizado"]) + unidad).strip() if unidad else T.dinero(d["cotizado"], 0)
        _pct = (" (" + _sig + ("%.0f" % d["pct"]) + "%)") if d["pct"] is not None else ""
        return (etq, _val, "cotizaste " + _cot + _pct, _col)

    # ⚠️ En la GANANCIA el sentido se invierte: subir es BUENO (el mismo cuidado que en
    # v341 con los costos, pero al revés). Se arma aparte para no pintarla en rojo.
    g = comp["ganancia"]
    _cg = T.VERDE if g["dif"] >= 0 else T.ROJO
    T.kpi_row([
        _tarj("Horas", comp["horas"], "h"),
        _tarj("Costo", comp["costo"]),
        ("Ingreso", T.dinero(comp["ingreso"], 0), "lo que aceptó el cliente"),
        ("Ganancia real", T.dinero(g["real"], 0),
         "cotizaste " + T.dinero(g["cotizado"], 0), _cg),
    ])
    _av = comp["avance"]
    if comp["costo"]["dif"] > 0 and _av < 100:
        st.warning(":material/warning: Llevas **" + T.dinero(comp["costo"]["dif"], 0)
                   + " por encima** de lo cotizado con el proyecto al **"
                   + ("%.0f" % _av) + "%**. A este ritmo la ganancia final será menor "
                   "que la cotizada.")
    elif comp["costo"]["dif"] <= 0 and _av > 0:
        st.success(":material/check_circle: Vas **"
                   + T.dinero(abs(comp["costo"]["dif"]), 0) + " por debajo** de lo "
                   "cotizado con el proyecto al " + ("%.0f" % _av) + "%.")
    if st.button(":material/folder: Abrir " + comp["proyecto"], key="cot_prj_open_" + str(cid)):
        from core import home_ui
        st.session_state["_prjsel_pending"] = comp["proyecto_id"]
        st.session_state["_admin_open_proj"] = comp["proyecto_id"]
        home_ui.navegar("proyectos", "📊 Proyectos")'''

assert VIEJO in s, "ancla no encontrada"
s = s.replace(VIEJO, NUEVO)
if "from core import clock" not in s:
    s = s.replace("from core import catalogo as CAT",
                  "from core import catalogo as CAT\nfrom core import clock")
p.write_text(s, encoding="utf-8")
print("fase 3 insertada en quotes_ui.py")
