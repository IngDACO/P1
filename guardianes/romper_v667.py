# -*- coding: utf-8 -*-
"""Batería de roturas de v667. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v667"
TOPE_S = 400
P = "core/projects.py"
PU = "core/projects_ui.py"
H = "core/home_ui.py"
TU = "core/timeclock_ui.py"
IUI = "core/inventory_ui.py"
INV = "core/inventory.py"
LU = "core/location_ui.py"
QU = "core/quotes_ui.py"
UC = "core/ui_common.py"
AUI = "core/auth_ui.py"

ROTURAS = [
    # ── H28 ──
    ("⚠️ una obra en pausa vuelve a contar como activa", P,
     [('ESTADOS_ACTIVOS = ("Planned", "In progress")', 'ESTADOS_ACTIVOS = ("Planned", "In progress", "On hold")')]),
    ("la tarjeta «Active» vuelve a su propia cuenta", PU,
     [("activos = [p for p in proys if P.es_activa(p)]", 'activos = [p for p in proys if str(p.get("Status", "")) not in ("Completed", "Cancelled")]')]),
    ("la lista de Home vuelve a su propia cuenta", H,
     [("proys = [p for p in P.list_projects(grupo) if P.es_activa(p)]     # v667", "proys = [p for p in P.list_projects(grupo)]     # v667")]),
    # ── H1 · H22 · H11 ──
    ("la ficha de una persona vuelve sin su usuario", AUI,
     [('st.markdown(f"**{_nom_f}**{_login}  ·  _', 'st.markdown(f"**{_nom_f}**  ·  _')]),
    ("la línea base vuelve a la fecha ISO", PU,
     [('c=_fmt_fecha(str(_o.get("fijada", ""))[:10]),', 'c=str(_o.get("fijada", ""))[:10],')]),
    ("la línea base vuelve al login", PU,
     [('q=_nombres_de([_o.get("por", "?")], grupo)[0]))', 'q=_o.get("por", "?")))')]),
    ("⚠️ «Save changes» vuelve al toast que se pierde", PU,
     [('                    flash.exito(t("Changes saved.") + (" " + t(":material/send: {n} field user(s) notified: {l}.",',
       '                    st.toast(t("Changes saved.") + (" " + t(":material/send: {n} field user(s) notified: {l}.",')]),
    ("los avisos del tablero se vuelven a perder al guardar", PU,
     [("_autoagenda(grupo, pid, nuevos, _quitados, f_ini, f_fin, al_flash=True)", "_autoagenda(grupo, pid, nuevos, _quitados, f_ini, f_fin)")]),
    # ── H41 ──
    ("el buscador enseña activos y facturas también al campo", H,
     [('    if _rol() == "administrator":\n        try:\n            from core import inventory as INV',
       '    if True:\n        try:\n            from core import inventory as INV')]),
    ("⚠️ un activo no se encuentra por su ID", H,
     [('r = _rank(aid, a.get("Name"), a.get("Serial"), a.get("Brand"), a.get("Model"))', 'r = _rank(a.get("Name"))')]),
    ("el activo encontrado no abre su ficha", H,
     [('        st.session_state.pop("_inv_nuevo", None)\n        st.session_state["_inv_open"] = res["id"]\n        navegar("inventario", None)\n    elif res["tipo"] == "factura":',
       '        st.session_state.pop("_inv_nuevo", None)\n        navegar("inventario", None)\n    elif res["tipo"] == "factura":')]),
    ("la factura encontrada no se abre", H,
     [('        st.session_state["_fac_open"] = res["id"]\n', "")]),
    ("la cotización encontrada no se abre", H,
     [('        st.session_state["_cot_open"] = res["id"]\n', "")]),
    # ── H13/H18 ──
    ("⚠️ al fichar vuelven las obras cerradas", TU,
     [('        return [p for p in lst if str(p.get("Status", "")) not in projects_data.CERRADAS]', "        return list(lst)")]),
    ("una localización cerrada deja de contar como cerrada", P,
     [('CERRADAS = ("Completed", "Cancelled", "Archived", INTERNO_CERRADA)', 'CERRADAS = ("Completed", "Cancelled", "Archived")')]),
    ("la etiqueta no marca las localizaciones", P,
     [("out[_pid] = f\"{_nom} ({_pid} · {t('location')})\" if es_interno(p) else f\"{_nom} ({_pid})\"",
       'out[_pid] = f"{_nom} ({_pid})"')]),
    ("la barra lateral vuelve a la etiqueta sin ID", TU,
     [("    # ⚠️ v667 · con el ID y «location» a la vista: aquí se elige DÓNDE se trabaja (`etiqueta_con_id`)\n"
       "    idmap = {_lbl: _pid for _pid, _lbl in _P.etiqueta_con_id(proys).items()}",
       "    # ⚠️ v667 · con el ID y «location» a la vista: aquí se elige DÓNDE se trabaja (`etiqueta_con_id`)\n"
       "    idmap = {_lbl: _pid for _pid, _lbl in _P.etiqueta_proyectos(proys).items()}")]),
    ("el destino de un activo vuelve a la etiqueta sin ID", IUI,
     [("        _lbl = P.etiqueta_con_id(_ps)          # v667", "        _lbl = P.etiqueta_proyectos(_ps)          # v667")]),
    # ── H10 · H44 ──
    ("⚠️ se vuelve a guardar la dirección de Google", LU,
     [('st.session_state[f"{key}_addr"] = _sel if (_usar_g or not _escrito) else _escrito', 'st.session_state[f"{key}_addr"] = _sel')]),
    ("no se apunta lo que se escribió", LU,
     [('        st.session_state[f"{key}_qbusq"] = str(q or "").strip()      # v667', "        pass      # v667")]),
    ("⚠️ la obra desde una cotización vuelve a nacer sin punto", QU,
     [("                _ubicar_obra(str(msg), ubic)          # v667", "                pass          # v667")]),
    ("el punto no se guarda", QU,
     [('            _P.update_project(pid, {"Lat": _ll[0], "Lng": _ll[1]})', "            pass")]),
    # ── H17/H42 ──
    ("⚠️ los códigos del inventario vuelven en minúscula", IUI,
     [("    return s[:1].upper() + s[1:] if s and (str(v) in _CODIGOS or s in _CODIGOS) else s", "    return s")]),
    ("se pone mayúscula a lo que escribió una persona", IUI,
     [("if s and (str(v) in _CODIGOS or s in _CODIGOS) else s", "if s else s")]),
    ("la vida útil vuelve a «5.00»", IUI,
     [('vida = c4.number_input(t("Useful life (years)"), min_value=0.0, step=1.0, format="%g",',
       'vida = c4.number_input(t("Useful life (years)"), min_value=0.0, step=1.0,')]),
    ("⚠️ la devolución vuelve a nacer con «Store»", IUI,
     [('value=INV.ultima_bodega(grupo, aid) or t("Store"),', 'value=t("Store"),')]),
    ("ultima_bodega toma la salida MÁS VIEJA", INV,
     [('key=lambda m: (str(m.get("Date", "")), str(m.get("ID", ""))), reverse=True):',
       'key=lambda m: (str(m.get("Date", "")), str(m.get("ID", "")))):')]),
    ("la factura del buscador vuelve a la fecha ISO", H,
     [('                                                          _dmy(f.get("Date", ""))] if x), "id": fid})',
       '                                                          str(f.get("Date", ""))[:10]] if x), "id": fid})')]),
    # ── H3 ──
    ("⚠️ el icono vuelve a la etiqueta de una fecha", UC,
     [('    label = _re.sub(r":material/[a-z0-9_]+:\\s*", "", str(label or "")).strip()', '    label = str(label or "")')]),
    # ── H19 ──
    ("⚠️ vuelve el formulario mientras se lee la cookie", AUI,
     [('        if not _contesto and not st.session_state.get("_ver_login"):', "        if False:")]),
    ("sin respuesta del componente, se queda en «Restoring» para siempre", AUI,
     [('or st.session_state["_ck_pasadas"] >= 3', 'or st.session_state["_ck_pasadas"] >= 300')]),
    # ── H36 ──
    ("⚠️ el menú no se pliega al cambiar de sección", H,
     [("        if ant[0] != v[0]:\n            _plegar_menu_movil()", "        if False:\n            _plegar_menu_movil()")]),
    ("se pliega también en el escritorio", H,
     [('"function ir(){if(W.innerWidth>=768)return;"', '"function ir(){"')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", P,
           [("# ⚠️ v667 · Lo que ya no admite trabajo", "# ⚠️ v667 (control) · Lo que ya no admite trabajo")])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
