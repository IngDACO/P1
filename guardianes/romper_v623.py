# -*- coding: utf-8 -*-
"""Batería de roturas de v623. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455)."""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v623"
TOPE_S = 240
U = "core/prestart_ui.py"
M = "core/prestart.py"
PD = "core/prestart_pdf.py"
TU = "core/timeclock_ui.py"
HU = "core/home_ui.py"

ROTURAS = [
    ("⚠️ el formulario vuelve a ser el mismo para todas las obras", U,
     [('    kp = f"{pid}_{_gen}"\n', '    kp = f"x_{_gen}"\n')]),
    ("⚠️ el formulario no se vacía tras generar", U,
     [('            st.session_state[f"_ps_gen_{pid}"] = _gen + 1      # el formulario nace vacío\n', "")]),
    ("⚠️ la firma de una charla pasa a otra", U,
     [('res = st_canvas(key=f"ps_firma_{kp}_{_k}", **_LIENZO)', 'res = st_canvas(key=f"ps_firma_{_k}", **_LIENZO)')]),
    ("⚠️ la firma tardía pasa a otra obra", U,
     [('res = st_canvas(key=f"ps_firma_tarde_{_pid}", **_LIENZO)', 'res = st_canvas(key="ps_firma_tarde", **_LIENZO)')]),
    ("⚠️ near miss sin descripción, en la pantalla", U,
     [('    elif nm == "YES" and not str(nm_desc).strip():\n        _pend.append(t("section 2: describe the near miss / hazard"))\n', "")]),
    ("⚠️ near miss sin descripción, en el motor", M,
     [("""    if str(data.get("near_miss", "")).upper() == "YES" and not str(data.get("near_miss_desc", "")).strip():\n""",
       "    if False:\n")]),
    ("⚠️ la alarma que falla vuelve a ser silenciosa", U,
     [('    elif r.get("nm"):\n', '    elif False:\n')]),
    ("⚠️ el campo vuelve a elegir la fecha", U,
     [('                      disabled=True, help=t("The Pre-Start is always recorded for today."))\n        f_fecha = hoy\n',
       '                      help=t("The Pre-Start is always recorded for today."))\n        f_fecha = hoy\n')]),
    ("⚠️ el motor deja al campo registrar otro día", M,
     [('    if not data.get("gestor", True) and _dia != _hoy:\n', "    if False:\n")]),
    ("la pantalla no dice que es el campo", U,
     [('"forzar": bool(_forzar), "gestor": _gestor,', '"forzar": bool(_forzar),')]),
    ("la oficina puede poner un día futuro", U, [("value=hoy, max_value=hoy, key=", "value=hoy, key=")]),
    ("⚠️ el duplicado vuelve a mirar solo hoy", M,
     [('               and _parse_date(r.get("Date")) == _dia]\n', '               and _parse_date(r.get("Date")) == _hoy]\n')]),
    ("⚠️ el número vuelve a calcularse después del PDF", M,
     [('    data = {**data, "id": aid}\n', "")]),
    ("el PDF no lleva el número", PD, [('[_esc(data.get("id"))] if data.get("id") else [])', "[])")]),
    ("⚠️ la firma tardía sin login", M,
     [('        _nuevo["usuario"] = str(usuario).strip()\n', "        pass\n")]),
    ("⚠️ el documento muerto vuelve a quedarse en «Files»", M,
     [('            projects.delete_document_record(str(fila.get("ProjectID", "")), drive_id)\n', "")]),
    ("⚠️ dice archivado aunque no lo esté", M, [('    res["archivado"] = bool(nuevo_id)\n', '    res["archivado"] = True\n')]),
    ("⚠️ el historial vuelve a bajar los PDF al pintar", U,
     [("                       data=lambda: drive_store.download(_did),\n",
       "                       data=drive_store.download(_did),\n")]),
    ("el historial enseña todas de entrada", U,
     [("_vis = _lista if st.session_state.get(_tk) else _lista[:_MAX_HIST]", "_vis = _lista")]),
    ("⚠️ las cifras dejan de filtrar", U,
     [('                st.session_state[_fk] = _s\n', "                pass\n")]),
    ("⚠️ la fecha del historial vuelve a ISO", U,
     [("""_tit = (f"{_flag}  {_dmy(d['fecha'])} · """, """_tit = (f"{_flag}  {d['fecha']} · """)]),
    ("⚠️ el texto del near miss sin escapar", U,
     [('(literal_md(d["near_miss_desc"]) or t("(no description)"))', '(d["near_miss_desc"] or t("(no description)"))')]),
    ("⚠️ con la charla hecha sale el formulario entero", U,
     [("    if _ya_hoy and not _pf:\n        if not _r:\n", "    if False:\n        if not _r:\n")]),
    ("⚠️ el resultado se va al primer toque", U,
     [('            st.session_state[f"_ps_res_{pid}"] = {**res, "nm": nm == "YES", "dia": hoy.isoformat()}\n', "")]),
    ("⚠️ «Do it now» deja de decir qué obra", TU,
     [('        st.session_state["_ps_proy_pending"] = str(pid)\n', "        pass\n")]),
    ("un botón vuelve a no decir qué obra", HU,
     [("            from core.timeclock_ui import _ir_a_prestart\n            _ir_a_prestart(pid)\n\n\ndef _norm_busq",
       "            from core.timeclock_ui import _ir_a_prestart\n            _ir_a_prestart()\n\n\ndef _norm_busq")]),
    ("el banner sin escapar", HU, [('_nom = _html.escape(str(prj.get("proyecto", "") or t("this job")))',
                                     '_nom = str(prj.get("proyecto", "") or t("this job"))')]),
    ("un aviso vuelve a ir sin `t()`", U,
     [('''st.warning(t(":material/info: Today there are **{n} talks** recorded on this site. The "
                         "most recent one is offered; if you signed a different one, tell whoever "
                         "recorded it.", n=_otras + 1))''',
       '''st.warning(f":material/info: Today there are **{_otras + 1} talks** recorded on this site.")''')]),
    ("⚠️ el lienzo de firma vuelve a cortarse", U,
     [("        _k = _clave_firma(a)\n", "        _k = _clave_firma(a)\n        st.columns([2, 3])\n")]),
    ("la cabecera vuelve a apilarse en el móvil", U,
     [('    st.markdown(theme.por_fila("cpx_ps_cab", 2), unsafe_allow_html=True)\n', "")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", U,
           [("_MAX_HIST = 10             # las charlas", "_MAX_HIST = 10             # (control) las charlas")])


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
