# -*- coding: utf-8 -*-
"""Bateria de roturas de v564. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto en el recorrido de Locations en producción.
Una rotura puede nombrar OTRO guardián (4º elemento): la clave de un desplegable con
condición la vigila verif_v547, no AppTest (que respeta `expanded` en la 1ª pasada).
`--anclas` solo comprueba que cada ancla casa UNA vez; un argumento suelto filtra roturas.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v564"
PU = "core/projects_ui.py"
HU = "core/home_ui.py"
PS = "core/prestart_ui.py"
RU = "core/roster_ui.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── 1. Expenses de una localización ──
    ("⚠️ vuelve «cuánto ganas con cada persona» a una localización", PU,
     [("    if can_delete and not _loc:\n        _ganancia_section(pid, grupo)\n",
       "    if can_delete:\n        _ganancia_section(pid, grupo)\n")]),
    ("⚠️ vuelve el atajo «Invoice» a una localización", PU,
     [("    if can_delete and not _loc:         # solo gestión: el campo no factura\n",
       "    if can_delete:         # solo gestión: el campo no factura\n")]),
    ("⚠️ vuelven las reclamaciones de obra a una localización", PU,
     [("    if not _loc:\n        try:\n            from core import claims_ui as _CLU\n",
       "    if True:\n        try:\n            from core import claims_ui as _CLU\n")]),
    # ── 2. Archivada ──
    ("⚠️ la archivada vuelve a la lista", PU,
     [("    _vis = [p for p in locs if not _loc_archivada(p)]\n", "    _vis = list(locs)\n")]),
    ("⚠️ la archivada vuelve a rotularse «closed»", PU,
     [('    if _loc_archivada(p):\n        return t(":material/inventory_2: archived")\n', "")]),
    ("desaparece «Show archived» (no habría forma de recuperarla)", PU,
     [('        _ver_arch = st.toggle(t("Show archived ({n})").replace("{n}", str(len(_arch))),\n'
       '                              key="loc_ver_arch")\n', "        _ver_arch = False\n")]),
    ("la ayuda del estado vuelve a prometer lo que no pasa", PU,
     [("help=t(\"Closed = no longer used, but it stays in the list with its history. Archived = it "
       "leaves the list; «Show archived» brings it back.\"))",
       "help=t(\"Closed = no longer used, but its history is kept. Archived = it also disappears "
       "from the list.\"))")]),
    # ── 3/4. Personas: nombre y «Select all» ──
    ("⚠️ el alta vuelve a enseñar LOGINS en «Who normally works here»", PU,
     [("                             format_func=lambda u: _etq_us(campos).get(u, u),\n"
       "                             help=t(\"Being assigned",
       "                             help=t(\"Being assigned")]),
    ("⚠️ el alta vuelve a ofrecer «Select all»", PU,
     [('key=f"nloc_asg{_sf}", select_all=False,', 'key=f"nloc_asg{_sf}",')]),
    ("⚠️ Data vuelve a ofrecer «Select all» (asignaría a todo el campo)", PU,
     [("format_func=lambda u: _nm_opc.get(u, u), select_all=False)",
       "format_func=lambda u: _nm_opc.get(u, u))")]),
    ("el roster vuelve a ofrecer «Select all» entre los libres", RU,
     [('list(_opts), key="ai_pick", select_all=False)', 'list(_opts), key="ai_pick")')]),
    ("«Permanently assigned» vuelve a los logins", PU,
     [('                    st.markdown(f"· {_nm.get(u, u)}")\n',
       '                    st.markdown(f"· {u}")\n')]),
    # ── 5. Data: dirección y pin ──
    ("⚠️ Data deja de ofrecer la dirección y el pin", PU,
     [('        _plat, _plng = location_ui.location_picker(\n'
       '            f"elocloc_{pid}", lat=location_ui.to_float(prj.get("Lat")),\n'
       '            lng=location_ui.to_float(prj.get("Lng")), direccion=str(prj.get("Location", "")))\n',
       '        _plat, _plng = location_ui.to_float(prj.get("Lat")), location_ui.to_float(prj.get("Lng"))\n')]),
    ("⚠️ guardar Data ignora la dirección confirmada", PU,
     [('            "Location": _ubic,\n', '            "Location": prj.get("Location", ""),\n')]),
    ("guardar Data no escribe el pin", PU,
     [('            "Lat": "" if _plat is None else _plat,\n'
       '            "Lng": "" if _plng is None else _plng,\n        })\n', "        })\n")]),
    ("el desplegable de la dirección pierde la condición en su clave", PU,
     [('expanded=_sin_pin, key=f"exp_eloc_ubic_{pid}_{_sin_pin}"):',
       'expanded=_sin_pin, key=f"exp_eloc_ubic_{pid}"):')], "verif_v547"),
    # ── 6. Team ──
    ("⚠️ la cabecera «Hours» vuelve a la clave en español", PU,
     [('                     "Horas": st.column_config.NumberColumn(t("Hours"), format="%.2f"),\n',
       '                     "Horas": st.column_config.NumberColumn(format="%.2f"),\n')]),
    ("el aviso «sin tarifa» vuelve a los logins", PU,
     [('", ".join(_et.get(str(u), str(u)) for u in filas["sin_tarifa"])',
       '", ".join(str(u) for u in filas["sin_tarifa"])')]),
    # ── 7. Pre-Start ──
    ("la fecha del pre-start vuelve al ISO", PU,
     [("**{_fmt_fecha(d.get('fecha', ''))}** \"", "**{d.get('fecha', '')}** \"")]),
    ("«attendee(s)» vuelve al español", PU,
     [('t("{n} attendee(s)").replace("{n}", str(len(d.get("asistentes", []))))',
       '"{n} asistente(s)".replace("{n}", str(len(d.get("asistentes", []))))')]),
    ("⚠️ «Do today's Pre-Start here» lleva sin la localización", PU,
     [('        st.session_state["_ps_proy_pending"] = str(pid)\n', "")]),
    ("⚠️ el Pre-Start ignora la localización pedida", PS,
     [('    _ps_pend = st.session_state.pop("_ps_proy_pending", None)\n', "    _ps_pend = None\n")]),
    ("el Pre-Start la encuentra pero no la ELIGE", PS,
     [('            st.session_state["ps_proy"] = _k_pend\n', "            pass\n")]),
    # ── 8/9/10. Lista ──
    ("⚠️ sin ninguna, vuelven las tarjetas a 0 y el alta plegada", PU,
     [("    if not _vis and not _ver_arch:\n", "    if False:\n")]),
    ("el alta abierta pierde la condición en su clave", PU,
     [('key=f"exp_loc_new_{abierto}"):', 'key="exp_loc_new"):')], "verif_v547"),
    ("⚠️ las tarjetas KPI vuelven a ser PASIVAS", PU,
     [('            st.session_state["_loc_kpi"] = None if _sel == slug else slug\n',
       "            pass\n")]),
    ("las horas vuelven a redondearse a entero («0 h»)", PU,
     [('    return f"{h:.1f} h" if h < 10 else f"{h:,.0f} h"\n', '    return f"{h:,.0f} h"\n')]),
    ("desaparece el recuento de la cabecera", PU,
     [("    st.markdown(_cab)\n", "")]),
    ("una sola tarjeta vuelve a ocupar media fila", PU,
     [("    _por_fila = 1 if len(_ord) == 1 else 2\n", "    _por_fila = 2\n")]),
    # ── 11. Cabecera ──
    ("vuelve «resp.»", PU,
     [('_c.append(t("Person in charge: {x}").replace("{x}", P.head_installers_label(prj, grupo)))',
       '_c.append("resp. " + P.head_installers_label(prj, grupo))')]),
    # ── 12. URL, menú y sección ──
    ("⚠️ la URL pierde `&l=`", HU,
     [('            quiero["l"] = str(loc)\n', "            pass\n")]),
    ("un enlace con `&l=` deja de abrirla", HU,
     [('            st.session_state["_loc_open"] = str(qp.get("l"))\n', "            pass\n")]),
    ("⚠️ el menú deja de volver a la lista de Locations", HU,
     [('                   ("proyectos", "🗂 Agrupaciones"): "_admin_open_agr",\n'
       '                   ("proyectos", "🏢 Localizaciones"): "_loc_open"}      # v564\n',
       '                   ("proyectos", "🗂 Agrupaciones"): "_admin_open_agr"}\n')]),
    ("⚠️ la sección vuelve a empezar siempre en Team", PU,
     [('default="👥 Equipo", key="cpxseg_loc_sec", label_visibility="collapsed",\n'
       '        persist_state="session")',
       'default="👥 Equipo", key="cpxseg_loc_sec", label_visibility="collapsed")')]),
    # ── 13. El alta se vacía ──
    ("⚠️ el alta vuelve a quedarse con lo escrito", PU,
     [('            st.session_state["_loc_new_gen"] = _ng + 1\n', "")]),
    ("la dirección del alta no cambia de generación", PU,
     [('        _kl = f"nlocloc{_sf}"\n', '        _kl = "nlocloc"\n')]),
    # ── 14. Textos ──
    ("un aviso de Locations vuelve a una f-string sin `t()`", PU,
     [('st.caption(t("The hours could not be read: {e}").replace("{e}", str(e)))',
       'st.caption(f"The hours could not be read: {e}")')]),
    ("un titular de Expenses vuelve a ir SIN `t()` por una variable (trampa 30)", PU,
     [('        _t = t("This project **has no budget set**, so there is nothing to compare',
       '        _t = ("This project **has no budget set**, so there is nothing to compare')]),
    ("vuelve «Interno»", PU,
     [('                _tipo = str(p.get("Type", "")) or t("Internal")\n',
       '                _tipo = str(p.get("Type", "")) or "Interno"\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [("    aunque la ayuda del estado prometía que desaparecía (visto en el recorrido).",
                 "    aunque la ayuda del estado prometía que desaparecía (visto en el recorrido). (control)")])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    txt = bak
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
    print("0. Verde de base")
    for _g in sorted({r[3] if len(r) > 3 else G for r in _rot} | {G}):
        _base = corre(_g)
        if not _base:
            print("   ⚠️ %s YA esta %s: la tanda saldria «cazada» sin probar nada"
                  % (_g, "COLGADO" if _base is None else "rojo"))
            sys.exit(1)
        print("   %s verde" % _g)

    print("")
    print("1. Roturas (cada una debe ponerse ROJA)")
    cazadas = total = 0
    saltadas, colgadas = [], []
    for r in _rot:
        desc, rel, cambios = r[:3]
        _g = r[3] if len(r) > 3 else G
        _ok, bak, p, det = aplica(rel, cambios)
        if _ok is None:
            print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
            saltadas.append(desc)
            continue
        total += 1
        try:
            verde = corre(_g)
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
        if verde is None:
            colgadas.append(desc)
            print("  COLGADA  %s" % desc)
            continue
        cazadas += (not verde)
        print("  %s %s%s" % ("CAZADA  " if not verde else "ESCAPADA", desc,
                             "" if _g == G else "  [%s]" % _g))

    print("")
    print("2. Control (debe seguir VERDE)")
    _d, _r, _c = CONTROL
    _ok, bak, p, det = aplica(_r, _c)
    control_ok = False
    if _ok is None:
        print("  ??      ancla del control %s" % det)
    else:
        try:
            control_ok = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        print("  %s %s" % ("ok     " if control_ok else "MAL    ", _d))

    print("")
    print("=== %d de %d roturas cazadas ===" % (cazadas, total))
    if saltadas:
        print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
              % len(saltadas))
    if colgadas:
        print("⚠️ %d rotura(s) COLGARON el guardian (tope %d s): no son detecciones"
              % (len(colgadas), TOPE_S))
    sys.exit(0 if cazadas == total and not saltadas and not colgadas and control_ok else 1)
