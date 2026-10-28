# -*- coding: utf-8 -*-
"""Bateria de roturas de v616 (el recorrido de «My projects», la obra del campo). ⚠️ Verde de BASE
primero (v459) y NO en paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una
LISTA de cambios (v526).

⚠️ Anclas en LÍNEA y literales: check_anclas_roturas no lee variables (v570).
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
G = "verif_v616"
PU = "core/projects_ui.py"
AL = "core/alerts.py"
SPU = "core/stage_progress_ui.py"
TOPE_S = 600


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── cabecera ──
    ("⚠️ vuelve la 3ª tarjeta «Client» (sola en la 2ª fila del móvil)", PU,
     [('                _kpi_card(t("Project progress"), f"{avance:.0f}%")]\n',
       '                _kpi_card(t("Project progress"), f"{avance:.0f}%"),\n'
       '                _kpi_card(t("Client"), prj.get("Client") or "—")]\n')]),
    ("el cliente, sin escapar", PU,
     [('[":material/business: " + maps.literal_md(_cli)]', '[":material/business: " + _cli]')]),
    # ── Progress ──
    ("⚠️ lo marcado sin guardar se pierde al cambiar de pestaña", SPU,
     [('                    value=_pend.get(f"{e[\'orden\']}|{a[\'nombre\']}", _sv), key=_k,\n'
       '                    disabled=not editable, help=',
       '                    value=_sv, key=_k,\n'
       '                    disabled=not editable, help=')]),
    ("las casillas no apuntan lo cambiado", SPU,
     [('                    disabled=not editable, help=_ayuda(_cred, e["orden"], a["nombre"], a["pct"]),\n'
       '                    on_change=_apuntar, args=(key_prefix, pid, e["orden"], a["nombre"], _k, _sv))\n'
       '            # ⚠️ v519',
       '                    disabled=not editable, help=_ayuda(_cred, e["orden"], a["nombre"], a["pct"]))\n'
       '            # ⚠️ v519')]),
    ("la etapa no dice cuántos cambios sin guardar", SPU,
     [('            _tit += " · :orange[" + t("{n} unsaved", n=_n_pend) + "]"\n', '')]),
    ("el botón de la etapa no se resalta", SPU,
     [('type="primary" if _n_pend else "secondary"', 'type="secondary"')]),
    ("⚠️ guardar UNA etapa tira lo pendiente de TODAS", SPU,
     [('for _ck in [ck for ck in _pend if ck.split("|", 1)[0] == str(e["orden"])]:',
       'for _ck in list(_pend):')]),
    ("lo que ya es verdad en la hoja se sigue contando como pendiente", SPU,
     [('        if _ck not in _guardado or _pend[_ck] == _guardado[_ck]:\n            _pend.pop(_ck, None)\n',
       '        pass\n')]),
    ("el «?» sin decir de qué parte vino", SPU,
     [('    if str(r.get("Source", "")) == SP.PARTE and str(r.get("Note", "")).strip():\n', '    if False:\n')]),
    ("el «?» con el login", SPU,
     [('q=_nombre(r.get("UpdatedBy"))', 'q=r.get("UpdatedBy")')]),
    ("⚠️ en otra pestaña no se avisa de lo pendiente", PU,
     [('    if _npend and _sec != "🏗 Avance":\n', '    if False:\n')]),
    # ── alarmas ──
    ("la fecha de la alarma, en ISO", PU,
     [("_{_fecha_hora(al.get('Date'))}_", "_{al.get('Date')}_")]),
    ("quien la reportó, por su login", PU,
     [('            _quien = _nombres_de([al.get("CreatedBy")], grupo)[0]\n',
       '            _quien = str(al.get("CreatedBy"))\n')]),
    ("⚠️ el texto de la alarma sin escapar", PU,
     [("f\"{maps.literal_md(al.get('Message'))}\")", "f\"{al.get('Message')}\")")]),
    ("⚠️ el campo ve «resolver» en todas", PU,
     [('            if alerts.puede_resolver(al, usuario, gestor):\n', '            if True:\n')]),
    ("el campo pasa por oficina", PU,
     [('    return str((st.session_state.get("auth") or {}).get("rol", "")) in ("administrator", "owner")\n',
       '    return True\n')]),
    ("resolver no le dice al módulo quién es", PU,
     [('alerts.resolve_alert(_pet.get("id"), usuario, gestor=gestor)',
       'alerts.resolve_alert(_pet.get("id"), usuario)')]),
    ("una petición de OTRA obra se aplica", PU,
     [('    if _pet and _pet.get("pid") == str(pid):\n', '    if _pet:\n')]),
    ("⚠️ la caja de la alarma no se vacía (un 2º toque manda otra)", PU,
     [('                        st.session_state[f"_rep_gen_{pid}"] = _rg + 1\n', '')]),
    ("«Alert sent…» sin traducir", PU,
     [('t("Alert sent to the administrator.") if ok else res', '"Alert sent to the administrator." if ok else res')]),
    ("⚠️ la regla deja al campo resolver cualquiera", AL,
     [('    return tipo == "cambio" or (tipo == "problema"\n', '    return True or (tipo == "problema"\n')]),
    ("⚠️ el módulo no mira el permiso", AL,
     [('            if not puede_resolver(r, resuelto_por, gestor):\n', '            if False:\n')]),
    # ── recibos ──
    ("⚠️ el campo vuelve a ver TODOS los recibos de la obra", PU,
     [('        items = [r for r in items if str(r.get("CreatedBy", "")) == str(solo_de)]\n', '        pass\n')]),
    ("la obra del campo no pide solo los suyos", PU,
     [('                        solo_de=(st.session_state.get("auth") or {}).get("usuario", ""))\n',
       '                        solo_de=None)\n')]),
    ("la fecha del recibo, en ISO", PU,
     [("{_fmt_fecha(r.get('Date'))} · \"", "{r.get('Date')} · \"")]),
    ("el proveedor sin escapar", PU,
     [('_ex = " · ".join(maps.literal_md(x) for x in', '_ex = " · ".join(x for x in')]),
    ("el «$» del importe sin escapar", PU,
     [("f\"\\\\${E._num(r.get('Amount')):,.0f}\")", "f\"${E._num(r.get('Amount')):,.0f}\")")]),
    # ── archivos ──
    ("⚠️ el campo sube cualquier archivo", PU,
     [('type=_FOTO_EXT if es_campo else None)', 'type=None)')]),
    ("vuelve el selector «foto» al campo", PU,
     [('        if es_campo:\n            tipo = "foto"\n', '        if False:\n            tipo = "foto"\n')]),
    ("la oficina ve los tipos internos", PU,
     [('format_func=lambda x: _TIPO_LABEL.get(x, x))', 'format_func=str)')]),
    ("el error de subida sin traducir", PU,
     [('st.error(t("It could not be uploaded: {e}", e=ex))', 'st.error(f"It could not be uploaded: {ex}")')]),
    ("«My route» sin clave", PU,
     [(', key="exp_mi_ruta"):', '):')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [('_ALR_PET = "_alr_pet"      # v616', '_ALR_PET = "_alr_pet"      # (control) v616')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
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
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))),
                          encoding="utf-8", newline="").read()
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
                             "" if _g == G else "  [%s]" % _g), flush=True)

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
