# -*- coding: utf-8 -*-
"""Bateria de roturas de v599 (Inventory, probada en producción). ⚠️ Verde de BASE primero (v459)
y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570). `--anclas` solo comprueba
que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v599"
IN = "core/inventory.py"
IU = "core/inventory_ui.py"
HU = "core/home_ui.py"
TOPE_S = 900

ROTURAS = [
    # ── el motor ──
    # (v600 · re-ancladas tres: la baja y la reactivación escriben la CONSTANTE `BAJA` —el dato
    # en inglés; escribían «baja»— y las cifras filtran por `_filtrar`, que es quien baja a la tabla)
    ("⚠️ la baja vuelve a PISAR la nota con el motivo", IN,
     [('    ok, msg = update_activo(aid, {"Active": "NO", "Status": BAJA})\n',
       '    ok, msg = update_activo(aid, {"Active": "NO", "Status": BAJA,\n'
       '                                  "Note": (motivo or "Decommissioned")})\n')]),
    ("⚠️ la edición vuelve a guardar SIN nombre", IN,
     [('    if "Name" in fields and not str(fields.get("Name") or "").strip():\n',
       '    if False:\n')]),
    ("⚠️ llevarlo a reparar vuelve a dejarlo «available»", IN,
     [("    if hacia_tipo == REPARACION:\n", "    if False:\n")]),
    ("…o de vuelta del taller se queda en mantenimiento", IN,
     [('    elif str(a.get("LocationType", "")) == REPARACION and str(a.get("Status", "")) == MANTENIMIENTO:\n',
       "    elif False:\n")]),
    ("⚠️ la salida vuelve a aceptar una devolución PASADA", IN,
     [('    if str(fecha_devolucion or "").strip() and _fd and _fd < clock.today():\n', "    if False:\n")]),
    ("«tool» vuelve a entrar junto a «Tool»", IN,
     [("    if nombre.casefold() in {c.casefold() for c in categorias(grupo)}:\n",
       "    if nombre in categorias(grupo):\n")]),
    ("«Remove» vuelve a ofrecer las de fábrica", IN,
     [("    return [c for c in categorias(grupo) if c.casefold() not in _fab]\n",
       "    return categorias(grupo)\n")]),
    ("⚠️ la SERIE repetida deja de avisar", IN,
     [('(_s and " ".join(str(a.get("Serial", "")).casefold().split()) == _s)', "(False)")]),
    ("⚠️ la edición vuelve a ofrecer «written off» e «in use»", IN,
     [("ESTADOS_EDITABLES = [DISPONIBLE, MANTENIMIENTO, DANADO]\n", "ESTADOS_EDITABLES = ESTADOS\n")]),
    ("el alta vuelve a ofrecer obra/persona en texto libre", IN,
     [('UBIC_TIPOS_ALTA = ["warehouse", REPARACION]\n', "UBIC_TIPOS_ALTA = UBIC_TIPOS\n")]),
    ("reactivar vuelve a no dejar movimiento", IN,
     [('        _log_mov(grupo or str(a.get("Group", "")), aid, "reactivated", BAJA, ubic_str(a),\n'
       '                 "", "", "", creado_por=creado_por)\n', "        pass\n")]),
    ("…o a decir «Asset updated.»", IN,
     [('        return True, t("Asset reactivated.")\n', '        return True, t("Asset updated.")\n')]),
    # ── la lista ──
    ("«Service overdue» deja de filtrar", IU,
     [('"uso": INV.EN_USO, "mant": _FILTRO_MANT}[_s]', '"uso": INV.EN_USO, "mant": "Todos"}[_s]')]),
    ("las cifras dejan de bajar a la tabla", IU,
     [('    st.session_state["_bajar_cpx_inv_tabla"] = True\n', "    pass\n")]),
    ("⚠️ la tabla vuelve SIN el ID", IU, [('            "ID":          a.get("ID", ""),\n', "")]),
    ("…o el responsable por su usuario", IU,
     [('            "Assigned to":  _nom.get(str(a.get("AssignedTo", "")), a.get("AssignedTo", "")) or "—",\n',
       '            "Assigned to":  a.get("AssignedTo", "") or "—",\n')]),
    ("los informes vuelven a dos columnas (cifras cortadas)", IU,
     [('            st.markdown(t("**By category**"))\n',
       '            ca, cb = st.columns(2)\n            st.markdown(t("**By category**"))\n')]),
    # ── la ficha ──
    ("⚠️ la fecha vencida vuelve en ISO", IU,
     [("{t('Maintenance OVERDUE')}: {_dmy(_pm)}]", "{t('Maintenance OVERDUE')}: {_pm}]")]),
    ("vuelve «Leave the asset IN service»", IU,
     [('t("Mark it as under maintenance (out of use)")', 't("Leave the asset IN service")')]),
    ("vuelve «Etiqueta_….pdf»", IU, [('file_name=f"Asset_label_{aid}.pdf"', 'file_name=f"Etiqueta_{aid}.pdf"')]),
    ("⚠️ la salida vuelve a ofrecer obras CERRADAS", IU,
     [('               if str(p.get("ID", "")).strip() and str(p.get("Status", "")) not in _CERRADAS]\n',
       '               if str(p.get("ID", "")).strip()]\n')]),
    ("…o deja elegir una devolución pasada", IU,
     [('    _kw = {"min_value": clock.today()} if desde_hoy else {}\n', "    _kw = {}\n")]),
    ("…o el responsable por su usuario", IU,
     [('format_func=lambda u: u if u == "—" else _nom.get(u, u))', "format_func=str)")]),
    ("⚠️ el traslado a una obra vuelve a texto libre", IU,
     [('            if _tt == "project":\n', "            if False:\n")]),
    ("⚠️ las fechas de la edición vuelven a clave FIJA (deshace el mantenimiento)", IU,
     [("""                                f"inv_pm_{aid}_{a.get('NextService', '')}")""",
       """                                f"inv_pm_{aid}")""")]),
    ("la edición vuelve a enviarse con Enter", IU,
     [('    with st.form(f"inv_edit_{aid}", enter_to_submit=False):\n', '    with st.form(f"inv_edit_{aid}"):\n')]),
    ("…o el alta", IU,
     [('    with st.form(f"inv_reg_{_g}", enter_to_submit=False):\n', '    with st.form(f"inv_reg_{_g}"):\n')]),
    ("⚠️ la baja vuelve SIN confirmación", IU,
     [('key=f"inv_baja_{aid}", disabled=not _conf):', 'key=f"inv_baja_{aid}", disabled=False):')]),
    ("…o sin aviso", IU,
     [("                    flash.exito(msg)\n                    st.session_state.pop(\"_inv_open\", None)\n",
       "                    st.session_state.pop(\"_inv_open\", None)\n")]),
    ("…o la ficha de baja sin su motivo", IU,
     [('                   + (" " + t("Reason: {x}", x=_mot) if _mot else ""))\n', "                   )\n")]),
    ("⚠️ el alta deja de avisar de los repetidos", IU,
     [("        if _dups and not st.session_state.get(_k_dup(nombre, serie)):\n", "        if False:\n")]),
    ("…o deja de decir que registró", IU,
     [('            flash.exito(t("Asset {id} «{n}» registered.", id=res, n=str(nombre).strip()))\n', "")]),
    ("el campo de categoría deja de vaciarse", IU,
     [('            st.session_state["inv_cat_new"] = ""\n', "            pass\n")]),
    ("la condición vuelve sin su etiqueta", IU,
     [('        condicion = e1.selectbox(t("Condition"), _conds, index=_cdi, format_func=_etq)\n',
       '        condicion = e1.selectbox(t("Condition"), _conds, index=_cdi)\n')]),
    # ── la campana ──
    ("⚠️ la alerta vuelve a llevar a la LISTA", HU,
     [('"destino": ("activo", e.get("id", ""))', '"destino": ("ir", "inventario", None)')]),
    ("…o `_ir_alerta` deja de abrir la ficha", HU,
     [('        st.session_state["_inv_open"] = str(destino[1])\n', "        pass\n")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", IU,
           [("def _norm(s) -> str:\n", "def _norm(s) -> str:   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8", newline="").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s" % (txt.count(viejo), desc))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)
    if not corre():
        print("⚠️ %s YA esta rojo: la tanda no probaria nada" % G)
        sys.exit(1)
    print("0. %s verde de base" % G)
    cazadas = total = 0
    for desc, rel, cambios in ROTURAS:
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s -> %s" % (det, desc))
            continue
        total += 1
        try:
            verde = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        cazadas += (verde is False)
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc), flush=True)
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
