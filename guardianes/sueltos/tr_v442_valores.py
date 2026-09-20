"""v442 · los VALORES de dato se MUESTRAN en inglés (sin tocar la hoja).

⚠️ El hallazgo: `core/i18n.etiqueta()` existe desde v436 con el mapa completo
(`i18n.VALORES`: estados, tipos, roles, categorías, estados de factura/nómina/cotización,
tipos de ausencia…) y **solo la usaban los 3 PDF**. La interfaz pintaba el valor CRUDO,
así que en pantalla seguían saliendo «En progreso», «vencida», «campo», «Materiales»…
Es el patrón «se escribe y nadie lo lee» de v131/v148, esta vez con el i18n.

⚠️ LO QUE NO SE TOCA, y es la línea que separa esto de romper la app:
  · las COMPARACIONES (`if est == "En pausa"`) — traducirlas rompe el matching en
    silencio, que es la regla de oro de toda la migración;
  · los dicts que se ESCRIBEN en la hoja (`"Estado": P.derive_estado(...)` dentro de
    `update_project` / `create_project`) — ahí el valor español ES el dato;
  · las OPCIONES de un selectbox cuyo valor se guarda: se muestran con `format_func`,
    que cambia lo que se lee sin tocar lo que se devuelve.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
 "core/projects_ui.py": [
   # chip de estado en la cartera y en la cabecera del detalle
   ("""f'color:{fg};white-space:nowrap;flex:none;">{est}</span>'""",
    """f'color:{fg};white-space:nowrap;flex:none;">{_etq(est)}</span>'"""),
   ("""f'color:{_fg};white-space:nowrap;">{est}</span></div>'""",
    """f'color:{_fg};white-space:nowrap;">{_etq(est)}</span></div>'"""),
   # vista Lista de la cartera
   ('''            "Estado": str(p.get("Estado", "") or "—"),''',
    '''            "Estado": _etq(str(p.get("Estado", ""))) or "—",'''),
   # tabla de elevadores de una agrupación
   ('''            "Elevador": p.get("Nombre"), "Estado": p.get("Estado"),''',
    '''            "Elevador": p.get("Nombre"), "Estado": _etq(str(p.get("Estado", ""))),'''),
   # tabla del propietario
   ('''            "Estado":    est,''', '''            "Estado":    _etq(est),'''),
   # tarjetas KPI de una localización interna
   ('''        tarj = [_kpi_card(t("Status"), est),
                _kpi_card(t("Type"), str(prj.get("Tipo", "")) or "Interno"),''',
    '''        tarj = [_kpi_card(t("Status"), _etq(est)),
                _kpi_card(t("Type"), _etq(str(prj.get("Tipo", ""))) or t("Internal")),'''),
   # estado de una orden de compra
   ('''st.caption(f"{_oid} · {_est} · ordered {o.get('Fecha','')}")''',
    '''st.caption(f"{_oid} · {_etq(_est)} · ordered {o.get('Fecha','')}")'''),
   # ⚠️ El selectbox GUARDA su valor: se cambia lo que se LEE, no lo que devuelve.
   ('''            est_man = st.selectbox(t("Manual status (override)"), P.ESTADOS_MANUAL,''',
    '''            est_man = st.selectbox(t("Manual status (override)"), P.ESTADOS_MANUAL,
                                   format_func=_etq,'''),
 ],
 "core/home_ui.py": [
   ('''    bits = [f":material/bar_chart: **{av}%**", f"{_sem} {_e(prj.get('Estado'))}"]''',
    '''    bits = [f":material/bar_chart: **{av}%**", f"{_sem} {_e(_etq(str(prj.get('Estado', ''))))}"]'''),
 ],
 "core/auth_ui.py": [
   ('''        st.markdown(f"{_ic} **{u.get('Nombre') or u.get('Usuario')}** · {u.get('Rol','')}''',
    '''        st.markdown(f"{_ic} **{u.get('Nombre') or u.get('Usuario')}** · {_etq(str(u.get('Rol','')))}'''),
 ],
}

fallos, hechos = [], 0
for rel, pares in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for viejo, nuevo in pares:
        c = s.count(viejo)
        if c != 1:
            fallos.append(f"{rel}: ({c}x) {viejo[:72]}")
            continue
        s = s.replace(viejo, nuevo, 1)
        n += 1
    # ⚠️ El import va a nivel de MÓDULO: uno dentro de otra función engaña al chequeo
    # de ámbito (v342) y deja un NameError que solo asoma al abrir la pantalla.
    if n and "etiqueta as _etq" not in s:
        s = s.replace("from core.i18n import t", "from core.i18n import t, etiqueta as _etq", 1)
    try:
        ast.parse(s)
    except SyntaxError as e:
        fallos.append(f"{rel}: NO COMPILA {e}")
        continue
    p.write_text(s, encoding="utf-8")
    hechos += n
    print(f"  {rel:26} {n} puntos de pantalla")

print(f"\n{hechos} hechas")
if fallos:
    print("⚠️ ANCLAS QUE NO CASAN (no prueban nada, hay que mirarlas):")
    for f in fallos:
        print("   ", f)
    sys.exit(1)
