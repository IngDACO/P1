"""v360 (2/2) — la pantalla: cuánto quieres ganar con cada persona en esta obra.

Va en 💰 Costos, justo donde ya se ve «Mano de obra por persona»: ahí es donde miras
quién trabajó y cuánto te costó, así que es donde tiene sentido decir cuánto quieres
ganar con cada uno.

⚠️ Mientras la obra no tenga ganancias puestas sigue con el modelo viejo (% sobre la
MO) y **se dice cuál está usando**. Cambiar de modelo es una decisión, no un efecto
secundario de abrir una pantalla.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

p = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")
s = p.read_text(encoding="utf-8")

ANCLA = '''    # ── Facturar esta obra (atajo, v357) ─────────────────────────'''
NUEVO = '''    # ── Cuánto ganas con cada persona (v360) ─────────────────────
    if can_delete:
        _ganancia_section(pid, grupo)

    # ── Facturar esta obra (atajo, v357) ─────────────────────────'''
assert ANCLA in s, "ancla del atajo de facturar no encontrada"
s = s.replace(ANCLA, NUEVO, 1)

FUNC = '''def _ganancia_section(pid, grupo):
    """Ganancia por trabajador y hora en ESTA obra (v360).

    La ganancia dejó de ser un % del proyecto: es un importe por rubro, y el trabajador
    es un rubro. Aquí se pone cuánto quieres ganar por cada hora de cada persona; el
    precio/hora al cliente y el % salen solos.
    """
    from core import expenses as E
    from core import finance as F
    from core import theme as _T
    try:
        rev = F.project_revenue(pid, grupo)
        lb = E.labor_breakdown(pid, grupo)
    except Exception:
        return
    _gh = P.ganancia_hora(pid)
    _items = lb.get("items") or []
    if not _items and not _gh:
        return                              # nadie ha fichado aquí: nada que decidir

    with st.expander(":material/savings: Cuánto ganas con cada persona",
                     expanded=bool(rev.get("sin_ganancia"))):
        if rev.get("modelo") == "margen":
            st.info(":material/info: Esta obra todavía usa el **modelo viejo**: un "
                    + f"**{rev['margen_pct']:g}%** sobre la mano de obra. En cuanto "
                    "pongas aquí lo que quieres ganar por hora, pasa al modelo nuevo "
                    "(importe por rubro) y el % se calcula solo.")
        else:
            st.success(":material/check_circle: Esta obra ya usa el modelo por rubro. "
                       "El " + f"{rev['margen_pct']:g}%" + " de margen es consecuencia, "
                       "no un dato que hayas tecleado.")
        if rev.get("sin_ganancia"):
            st.warning(":material/person_alert: Sin ganancia puesta, así que su trabajo "
                       "se facturaría **a costo**: **" + ", ".join(rev["sin_ganancia"])
                       + "**.")

        _ed = st.data_editor(
            pd.DataFrame([{
                "Persona": x.get("usuario", ""),
                "Horas": round(P._num(x.get("horas")), 2),
                "Costo/h": round(P._num(x.get("tarifa")), 2),
                "Ganancia/h": round(P._num(_gh.get(str(x.get("usuario", "")), 0)), 2),
                "Precio/h": round(P._num(x.get("tarifa"))
                                  + P._num(_gh.get(str(x.get("usuario", "")), 0)), 2),
                "Ganas": round(P._num(x.get("horas"))
                               * P._num(_gh.get(str(x.get("usuario", "")), 0)), 2),
            } for x in _items]),
            hide_index=True, use_container_width=True, key=f"gh_ed_{pid}",
            # ⚠️ Solo se teclea la GANANCIA. Precio/h y «Ganas» son consecuencia y van
            # bloqueados, igual que en la cotización (v355).
            disabled=["Persona", "Horas", "Costo/h", "Precio/h", "Ganas"],
            column_config={
                "Costo/h": st.column_config.NumberColumn("Costo/h", format="$%.2f",
                                                         help="Su tarifa. Lo que te cuesta."),
                "Ganancia/h": st.column_config.NumberColumn(
                    "Ganancia/h", format="$%.2f", min_value=0.0,
                    help="Lo que quieres ganar por cada hora suya en esta obra."),
                "Precio/h": st.column_config.NumberColumn("Precio/h", format="$%.2f",
                                                          help="Costo + ganancia. Lo que se le cobra al cliente."),
                "Ganas": st.column_config.NumberColumn("Ganas", format="$%.2f",
                                                       help="Horas × ganancia/h.")})

        _nuevo = {str(_ed.iloc[i]["Persona"]): P._num(_ed.iloc[i]["Ganancia/h"])
                  for i in range(len(_ed)) if P._num(_ed.iloc[i]["Ganancia/h"]) > 0}
        _tot = sum(P._num(_ed.iloc[i]["Horas"]) * P._num(_ed.iloc[i]["Ganancia/h"])
                   for i in range(len(_ed)))
        st.caption("Con estos valores ganarías **" + _T.dinero(_tot)
                   + "** de mano de obra en lo fichado hasta ahora. Los materiales se "
                     "facturan a costo (decisión de v360).")
        _c1, _c2 = st.columns([2, 1])
        if _c1.button(":material/save: Guardar ganancias", key=f"gh_save_{pid}",
                      type="primary", use_container_width=True):
            ok, msg = P.set_ganancia_hora(pid, _nuevo)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()
        # ⚠️ La vuelta atrás: si migraste una obra por error, se puede deshacer (v346).
        if _gh and _c2.button(":material/undo: Volver al %", key=f"gh_undo_{pid}",
                              use_container_width=True,
                              help="Quita las ganancias por hora y vuelve al margen %."):
            ok, msg = P.set_ganancia_hora(pid, {})
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()


def _facturar_atajo(pid, grupo, prj_nombre=""):'''
s = s.replace('''def _facturar_atajo(pid, grupo, prj_nombre=""):''', FUNC, 1)
p.write_text(s, encoding="utf-8")
print("✓ projects_ui: editor de ganancia por persona en 💰 Costos")

# ── Rentabilidad: decir qué modelo usa cada obra ────────────────
f = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\finance.py")
s = f.read_text(encoding="utf-8")
if '"modelo": r.get("modelo"' not in s:
    s = s.replace('''            "margen": r["margen_pct"],''',
                  '''            "margen": r["margen_pct"],
            # v360: qué modelo aplica esta obra («rubro» = importe por trabajador;
            # «margen» = el % viejo). La pantalla lo dice para que un margen que ya
            # no se teclea no parezca editable.
            "modelo": r.get("modelo", "margen"),''')
    f.write_text(s, encoding="utf-8")
    print("✓ finance.group_profitability: expone el modelo de cada obra")
