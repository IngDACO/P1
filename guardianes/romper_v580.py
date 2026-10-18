# -*- coding: utf-8 -*-
"""Bateria de roturas de v580 (Finance → Quotes, probada acción por acción). ⚠️ Verde de BASE
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
G = "verif_v580"
QS = "core/quotes.py"
QU = "core/quotes_ui.py"
HU = "core/home_ui.py"
PU = "core/projects_ui.py"
TOPE_S = 400

ROTURAS = [
    ("⚠️ el motor deja de canonizar el tipo (una instalación sin cronograma)", QS,
     [("    tipo = valores.canon(tipo)\n", "")]),
    ("⚠️ el formulario vuelve a los tipos viejos («Instalación», «Otro»)", QU,
     [('        tipo = c2.selectbox(t("Type"), list(P.TIPOS), format_func=_etq)\n',
       '        tipo = c2.selectbox(t("Type"), ["Instalación", "Delivery", "Ripout", "Otro"], format_func=_etq)\n')]),
    ("el nombre por defecto del motor vuelve a «Nº»", QS,
     [("""f"{c.get('ClientName','')} — No. {c.get('Number','')}",""",
       """f"{c.get('ClientName','')} — Nº{c.get('Number','')}",""")]),
    ("…o el del formulario", QU,
     [('                               value=str(c.get("ClientName", "")) + " — No. "\n',
       '                               value=str(c.get("ClientName", "")) + " — Nº"\n')]),
    ("⚠️ la versión nueva vuelve a sacar otro número («0005 v2»)", QS,
     [('origen=str(c.get("ID", "")), numero=str(c.get("Number", "")) or None,',
       'origen=str(c.get("ID", "")), numero=None,')]),
    ("…o no sube de la más alta", QS,
     [('            mx = max(mx, int(_num(r.get("Version"), 1)))\n', "            pass\n")]),
    ("`crear` ignora el número pedido", QS,
     [('    num = str(numero) if numero else f"{mx_num + 1:04d}"\n', '    num = f"{mx_num + 1:04d}"\n')]),
    ("la nota no se guarda", QS,
     [('        _campos["Note"] = str(nota)\n', "        pass\n")]),
    ("la lista vuelve a ordenarse solo por fecha (la nueva, la última)", QS,
     [('    return sorted(out, key=lambda c: (str(c.get("Date", "")), _num(c.get("Number")),\n'
       '                                      _num(c.get("Version"), 1)), reverse=True)\n',
       '    return sorted(out, key=lambda c: str(c.get("Date", "")), reverse=True)\n')]),
    ("⚠️ una obra borrada no se detecta", QS,
     [("    return not P.get_project(pid)\n", "    return False\n")]),
    ("…o se suelta una que EXISTE", QS,
     [('    if not proyecto_perdido(c):\n        return False, t("That project still exists: it cannot be unlinked.")\n',
       "")]),
    ("⚠️ en un borrador, «Add to the quote» vuelve a no añadir", QU,
     [('        _trab = st.session_state.get(f"{_k}_lineas")\n', "        _trab = None\n")]),
    ("el selector del catálogo no se vacía al añadir", QU,
     [('        st.session_state[f"{key}_selgen"] = _sg + 1\n', "")]),
    ("⚠️ sin «Undo» (aceptar o rechazar, sin vuelta atrás)", QU,
     [('    elif est in (Q.ACEPTADA, Q.RECHAZADA) and not str(c.get("ProjectID", "")).strip():\n',
       "    elif False:\n")]),
    ("…o «Undo» con la obra ya creada", QU,
     [('    elif est in (Q.ACEPTADA, Q.RECHAZADA) and not str(c.get("ProjectID", "")).strip():\n',
       "    elif est in (Q.ACEPTADA, Q.RECHAZADA):\n")]),
    ("⚠️ vuelve «cotizaste»", QU,
     [('        return (etq, _val, t("you quoted {x}", x=_cot) + _pct, _col)\n',
       '        return (etq, _val, "cotizaste " + _cot + _pct, _col)\n')]),
    ("vuelve el «-100%» sin nada gastado", QU,
     [('        if not _num(d["real"]):\n', "        if False:\n")]),
    ("⚠️ la vencida vuelve a «overdue» (el de las facturas)", QU,
     [("    return t(\"expired\") if str(est) == Q.VENCIDA else _etq(str(est))\n",
       "    return _etq(str(est))\n")]),
    ("⚠️ el pie de la calle vuelve a no contar las vencidas", QU,
     [('           (t("{n} sent · {v} expired", n=_env + _ven, v=_ven) if _ven\n',
       '           (t("{n} sent · {v} expired", n=_env, v=_ven) if _ven\n')]),
    ("las cifras vuelven a no filtrar", QU,
     [('                st.session_state["_cot_filt_pending"] = _fl\n', "                pass\n")]),
    ("las cifras se apilan (sin el reparto de v578)", QU,
     [('    st.markdown(T.por_fila("cpx_cot_kpis", 4), unsafe_allow_html=True)\n', "")]),
    ("⚠️ un toque en la tabla no abre", QU,
     [("    if _fs and 0 <= _fs[0] < len(_lista):\n", "    if False:\n")]),
    ("…o la tabla vuelve a `single-row` (solo enmarca)", QU,
     [('            selection_mode="single-cell", key=f"cot_tbl_{_gen}",\n',
       '            selection_mode="single-row", key=f"cot_tbl_{_gen}",\n')]),
    ("las fechas vuelven en ISO", QU,
     [('            "Fecha":   _dmy(c.get("Date")),\n', '            "Fecha":   c.get("Date", ""),\n')]),
    ("«Markup %» vuelve a «Margin»", QU,
     [('                "Markup":  st.column_config.NumberColumn(t("Markup %"), format="%.1f%%",\n',
       '                "Markup":  st.column_config.NumberColumn(t("Margin"), format="%.1f%%",\n')]),
    ("las vencidas vuelven a ser texto", QU,
     [("""            if st.button(f":material/open_in_new: {t('No.')} {_num_txt(c)} · "\n""",
       """            if False and st.button(f":material/open_in_new: {t('No.')} {_num_txt(c)} · "\n""")]),
    ("⚠️ crear vuelve a no avisar", QU,
     [('                flash.exito(t("Quote No. {n} created.",\n',
       '                (lambda *a, **k: None)(t("Quote No. {n} created.",\n')]),
    ("…ni la versión nueva", QU,
     [('                flash.exito(t("Version {v} of No. {n} created.",\n',
       '                (lambda *a, **k: None)(t("Version {v} of No. {n} created.",\n')]),
    ("la nota de una enviada no se ve", QU,
     [('            st.caption(t(":material/sticky_note_2: Note for the client: {n}", n=str(c.get("Note"))))\n',
       "            pass\n")]),
    ("⚠️ guardar el borrador pierde la nota", QU,
     [("                ok, msg = Q.guardar_lineas(cid, nuevas, impuesto_pct=imp, nota=nota)\n",
       "                ok, msg = Q.guardar_lineas(cid, nuevas, impuesto_pct=imp)\n")]),
    ("«Discard» no repone la nota", QU,
     [('            st.session_state[f"cot_nota_{cid}"] = _nota0\n', "")]),
    ("⚠️ la obra borrada no se dice (cotización atada a nada)", QU,
     [("    _perdida = Q.proyecto_perdido(c)\n", "    _perdida = False\n")]),
    ("el PDF vuelve a «Cotizacion_»", QU,
     [("""file_name=f"Quote_{_num_txt(c).replace(' ', '_')}.pdf",""",
       """file_name=f"Cotizacion_{c.get('Number','')}.pdf",""")]),
    ("⚠️ «Quotes» en el menú ya no cierra la cotización abierta", HU,
     [('                   ("finanzas", "📄 Cotizaciones"): ("_cot_open", "_cot_nueva")}\n', "                   }\n")]),
    ("…o el menú no sabe cerrar una tupla", HU,
     [("                        for _ab in (_abierto if isinstance(_abierto, tuple) else (_abierto,)):\n",
       "                        for _ab in (_abierto,):\n")]),
    ("vuelve «0.0 h worked»", PU,
     [("""        f'<b style="color:#374151">{_horas_txt(_horas)}</b> {t("worked")}</span>'\n""",
       """        f'<b style="color:#374151">{_horas:.1f} h</b> {t("worked")}</span>'\n""")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", QU,
           [("def render_cotizaciones(grupo):\n", "def render_cotizaciones(grupo):   # (control)\n")])


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
