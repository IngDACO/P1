# -*- coding: utf-8 -*-
"""Bateria de roturas de v577 (Finance → Hours, probada acción por acción). ⚠️ Verde de BASE
primero (v459) y NO en paralelo con la suite (v455). Anclas en LÍNEA y literales (v570).
`--anclas` solo comprueba que cada ancla casa UNA vez.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v577"
PU = "core/projects_ui.py"
TC = "core/timeclock.py"
HU = "core/home_ui.py"
TH = "core/theme.py"
AU = "core/auth_ui.py"
TOPE_S = 300

ROTURAS = [
    ("⚠️ los periodos vuelven a contar un día de más", PU,
     [('        days = {"Week": 6, "Mes": 29, "Todo": None}[per]\n',
       '        days = {"Week": 7, "Mes": 30, "Todo": None}[per]\n')]),
    ("«Today» vuelve a pedir 0 (= todo el histórico)", PU,
     [("                   / 86400.0, 1e-6)\n", "                   / 86400.0 * 0, 0)\n")]),
    ("el periodo deja de recordarse", PU,
     [('horizontal=True, key="cpxseg_gh_per", label_visibility="collapsed",\n'
       '                   persist_state="session")\n',
       'horizontal=True, key="cpxseg_gh_per", label_visibility="collapsed")\n')]),
    ("⚠️ un periodo vacío vuelve a dejar la pantalla en blanco", PU,
     [("    # ── Totales del grupo ──\n", "    if not data:\n        return\n    # ── Totales del grupo ──\n")]),
    ("el vacío ya no ofrece el periodo más amplio", PU,
     [('        _ofrece = [o for o in ("Week", "Todo") if list(_PERH).index(o) > list(_PERH).index(per)]\n',
       "        _ofrece = []\n")]),
    ("…o lo ofrece y no cambia nada", PU,
     [('                st.session_state["_gh_per_pending"] = _o\n', "                pass\n")]),
    ("el aviso del vacío vuelve sin `t()`", PU,
     [('        st.info(t(":material/event_busy: No time entries in this period."))\n',
       '        st.info(":material/event_busy: No time entries in this period.")\n')]),
    ("las cifras vuelven a no hacer nada", PU,
     [('                st.session_state["_gh_orden"] = _ir\n', "                pass\n")]),
    ("la cifra «On overhead» sale sin estructura", PU,
     [("    if tot_intn > 0:\n        _K.append(", "    if True:\n        _K.append(")]),
    ("⚠️ el pie del coste vuelve a «+ $X interna»", PU,
     [('            t("+ {x} on overhead", x=theme.dinero(tot_cint, 0)) if tot_cint > 0\n',
       '            f"+ {theme.dinero(tot_cint, 0)} interna" if tot_cint > 0\n')]),
    ("la cifra sin asignar ya no se pone roja", PU,
     [("    if _dudoso or pct_sina > 25:\n", "    if False:\n")]),
    ("las cifras vuelven a apilarse en estrecho", PU,
     [('    st.markdown(theme.por_fila("cpx_gh_kpis", 3), unsafe_allow_html=True)\n', "")]),
    ("⚠️ las cifras vuelven a partirse fila a fila (2 / 1 / 2)", PU,
     [('    st.markdown(theme.por_fila("cpx_gh_kpis", 3), unsafe_allow_html=True)\n',
       '    st.markdown(theme.dos_por_fila("cpx_gh_kpis"), unsafe_allow_html=True)\n')]),
    ("…o la regla de 700 px pierde (va delante)", TH,
     [("    return (f\"<style>{_c} [data-testid='stHorizontalBlock']{{flex-wrap:wrap!important}}\"\n",
       "    return dos_por_fila(clave) + (f\"<style>{_c} [data-testid='stHorizontalBlock']{{flex-wrap:wrap!important}}\"\n"),
      ("            + dos_por_fila(clave))\n", "            )\n")]),
    ("⚠️ la persona vuelve sin ancho (~57 px, nombres cortados)", PU,
     [('            "User": st.column_config.TextColumn(t("Person"), pinned=True, width=_w_pers),\n',
       '            "User": st.column_config.TextColumn(t("Person"), pinned=True),\n')]),
    ("…o el ancho no crece con el nombre", PU,
     [("    _w_pers = int(min(220, max(90, 24 + 8 * max((len(_etiqueta(d)) for d in data), default=0))))\n",
       "    _w_pers = 90\n")]),
    ("⚠️ la matriz vuelve a números sueltos (cada columna alineada a su aire)", PU,
     [('                _fila[_rot(k)] = tabla.celda(_pp.get(k), 2) if _pp.get(k) else ""\n',
       '                _fila[_rot(k)] = round(_pp.get(k, 0.0), 2) if _pp.get(k) else ""\n')]),
    ("…o pierde la alineación a la derecha", PU,
     [("                                    **{_rot(k): tabla.derecha(_rot(k)) for k in _cols}}))\n",
       "                                    }))\n")]),
    ("⚠️ un administrador sin tarifa vuelve a mandarse a Planning → Users", PU,
     [('                if _rol_de.get(d["usuario"]) not in ("administrator", "owner")]\n',
       "                if True]\n")]),
    ("⚠️ Users vuelve a perder en silencio a quien no es de campo", AU,
     [('        if not any(u["User"] == _du for u in gente):\n            _nom =',
       '        if False:\n            _nom =')]),
    ("…o a alguien sin cuenta lo da por administrador", AU,
     [("            if _otro is not None:\n                st.info(t(\":material/info: **{n}** is not a field user",
       "            if True:\n                st.info(t(\":material/info: **{n}** is not a field user")]),
    ("⚠️ la tarifa vuelve a «40.0»", PU,
     [('                "Rate/h": tabla.celda(d["tarifa"], 2, "$") if d["tarifa"] else "—",\n',
       '                "Rate/h": d["tarifa"],\n')]),
    ("el coste vuelve sin $", PU,
     [('            "Labour cost": st.column_config.NumberColumn(t("Labour cost"), format="$%,.2f"),\n',
       '            "Labour cost": st.column_config.NumberColumn(t("Labour cost"), format="%.2f"),\n')]),
    ("la persona deja de ir fijada", PU,
     [('            "User": st.column_config.TextColumn(t("Person"), pinned=True, width=_w_pers),\n',
       '            "User": st.column_config.TextColumn(t("Person"), width=_w_pers),\n')]),
    ("⚠️ un toque en la persona ya no abre su ficha", PU,
     [("    if _hr and 0 <= _hr[0] < len(datos):\n", "    if False:\n")]),
    ("…o la tabla no cambia de clave (reabriría la misma)", PU,
     [('        st.session_state["_gh_tbl_gen"] = _gen + 1\n', "")]),
    ("⚠️ el motor vuelve a juntar las obras por NOMBRE", TC,
     [('            _k = _pid or ("~" + pn)\n', '            _k = "~" + pn\n')]),
    ("…o la pantalla lee el reparto por nombre", PU,
     [('        for _k, _h in (d.get("por_proyecto_id") or {}).items():\n',
       '        for _k, _h in (d.get("por_proyecto") or {}).items():\n')]),
    ("una obra con nombre repetido pierde su ID", PU,
     [('        return f"{_nom_id[k]} ({k})" if _rep[_nom_id[k]] > 1 and not k.startswith("~") else _nom_id[k]\n',
       "        return _nom_id[k]\n")]),
    ("⚠️ tocar una obra no abre nada", PU,
     [("            if not _k.startswith(\"~\"):\n                _gh_abrir_obra(_k, _internos)\n",
       "            pass\n")]),
    ("tocar una localización la abre en la cartera", PU,
     [("    if pid in internos:\n", "    if False:\n")]),
    ("⚠️ la matriz vuelve a no abrir nada", PU,
     [("            if _mc and 0 <= _mc[0][0] < len(_filas_m):\n", "            if False:\n")]),
    ("en la matriz, el nombre ya no abre la ficha", PU,
     [('                if _col == "Persona":\n', "                if False:\n")]),
    ("la matriz cuenta las filas de quien no sale en ella", PU,
     [("                _fila_d, _col = _filas_m[_mc[0][0]], _mc[0][1]\n",
       "                _fila_d, _col = datos[_mc[0][0]], _mc[0][1]\n")]),
    ("⚠️ Horas vuelve a ser el «si no» de Finanzas", HU,
     [('    elif sub == "⏱ Horas":\n        PU.render_group_hours(grupo)\n    else:\n',
       '    else:\n        PU.render_group_hours(grupo)\n    if False:\n')]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", PU,
           [("def render_group_hours(grupo: str):\n", "def render_group_hours(grupo: str):   # (control)\n")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep)))
    bak = io.open(p, encoding="utf-8").read()
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
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
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
        print("  %s %s" % ("CAZADA  " if verde is False else "ESCAPADA", desc))
    _ok, bak, p, det = aplica(*CONTROL[1:])
    try:
        control_ok = corre() is True
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if control_ok else "MAL    ", CONTROL[0]))
    print("\n=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(0 if cazadas == total == len(ROTURAS) and control_ok else 1)
