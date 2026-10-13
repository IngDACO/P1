# -*- coding: utf-8 -*-
"""Bateria de roturas de v570. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven lo visto verificando v569 en producción. Una rotura puede nombrar
OTRO guardián (4º elemento): el aviso tardío lo tienen que cazar TAMBIÉN verif_v568 y
verif_v569, ahora que sus guiones pintan los avisos en el orden de la shell — con el orden
de antes, esas dos roturas se les ESCAPABAN (es como pasó el fallo a producción).
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
G = "verif_v570"
PU = "core/projects_ui.py"
IU = "core/invoices_ui.py"
CU = "core/clientes_ui.py"
V569 = "../guardianes/verif_v569.py"
TOPE_S = 480

# ⚠️ Las anclas, en LÍNEA y literales: check_anclas_roturas no lee variables (v570).


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── el aviso un clic tarde ──
    ("⚠️ anular vuelve a NO relanzar (el aviso, un clic tarde)", IU,
     [("        # (visto en producción). Es lo que hacen Absences y Time fixes.\n"
       "        st.rerun()\n",
       "        # (visto en producción). Es lo que hacen Absences y Time fixes.\n")]),
    ("⚠️ …y lo caza también el AppTest de v569 (guion en el orden de la shell)", IU,
     [("        # (visto en producción). Es lo que hacen Absences y Time fixes.\n"
       "        st.rerun()\n",
       "        # (visto en producción). Es lo que hacen Absences y Time fixes.\n")], "verif_v569"),
    ("⚠️ asignar una compra sin obra vuelve a NO relanzar", PU,
     [("        # el aviso salía en el clic siguiente (en producción, en v568, «no se llegó a leer»).\n"
       "        st.rerun()\n",
       "        # el aviso salía en el clic siguiente (en producción, en v568, «no se llegó a leer»).\n")]),
    ("⚠️ …y lo caza también el AppTest de v568 (guion en el orden de la shell)", PU,
     [("        # el aviso salía en el clic siguiente (en producción, en v568, «no se llegó a leer»).\n"
       "        st.rerun()\n",
       "        # el aviso salía en el clic siguiente (en producción, en v568, «no se llegó a leer»).\n")],
     "verif_v568"),
    # v570 · lo que el barrido encontró de MÁS: el aviso de campos vacíos de «My projects»
    # se encolaba antes de guardar y, si el guardado fallaba, salía un clic tarde.
    ("el aviso de campos vacíos vuelve a encolarse aunque NO se relance", PU,
     [("            ok, msg = P.save_field_progress(pid, cambios)\n"
       "            if ok:\n"
       "                if _msg_vac:\n"
       "                    flash.aviso(_msg_vac)\n",
       "            if _msg_vac:\n"
       "                flash.aviso(_msg_vac)\n"
       "            ok, msg = P.save_field_progress(pid, cambios)\n"
       "            if ok:\n"
       "                if False:\n"
       "                    flash.aviso(_msg_vac)\n")]),
    ("un aviso de un BOTÓN sin relanzar (el barrido mira toda la app, no solo lo diferido)", IU,
     [("                    (flash.exito if ok else st.error)(msg)\n"
       "                    if ok:\n"
       "                        st.rerun()\n",
       "                    (flash.exito if ok else st.error)(msg)\n"
       "                    if ok:\n"
       "                        pass\n")]),
    ("⚠️ un guion de prueba vuelve a pintar los avisos DESPUÉS de la sección", V569,
     [('flash.mostrar()\nIU.render_facturas("G")\n',
       'IU.render_facturas("G")\nflash.mostrar()\n')]),
    # ── la anulada ──
    ("⚠️ la anulada vuelve a «deber» en la tabla", IU,
     [('    if I.estado_cobro(f) == "anulada":\n        return 0.0\n',
       '    if False:\n        return 0.0\n')]),
    # ── la ficha del cliente ──
    ("⚠️ las cifras del cliente vuelven a no tocarse (desaparecen los botones)", CU,
     [('        IU.cifras_cobro(_facs, "clf")\n', "")]),
    ("la tabla del cliente vuelve a llevar la columna del cliente", CU,
     [('IU.tabla_facturas(_fr, f"cli_facs_{cid}", con_cliente=False)',
       'IU.tabla_facturas(_fr, f"cli_facs_{cid}", con_cliente=True)')]),
    ("el filtro del cliente deja de ser POR cliente", CU,
     [('IU.filtrar(_facs, "clf", f"cpxseg_clf_filt_{cid}")', 'IU.filtrar(_facs, "clf", "cpxseg_clf_filt")')]),
    ("⚠️ abrir una factura del cliente vuelve a pedir la casilla", IU,
     [('on_select="rerun", selection_mode="single-cell", key=f"{clave}_{_gen}",',
       'on_select="rerun", selection_mode="single-row", key=f"{clave}_{_gen}",')]),
    ("al volver, la tabla reabriría la misma factura (sin generación)", IU,
     [("        st.session_state[_gk] = _gen + 1\n", "")]),
    ("⚠️ el dinero vuelve a TRUNCAR (`%,d`)", IU,
     [('"Total":     st.column_config.NumberColumn(t("Total"), format="$%,.2f"),',
       '"Total":     st.column_config.NumberColumn(t("Total"), format="$%,d"),')]),
    ("⚠️ la fecha vuelve al ISO", IU,
     [('"Fecha":     _dmy(f.get("Date")),', '"Fecha":     str(f.get("Date", "")),')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           IU, [('    """Lo que falta por cobrar. ⚠️ v570 · una ANULADA no debe nada: la tabla le ponía',
                 '    """Lo que falta por cobrar. ⚠️ v570 · una ANULADA no debe nada: la tabla le ponía (control)')])


def aplica(rel, cambios):
    """Aplica TODOS los cambios o ninguno. Devuelve (ok, bak, p, detalle)."""
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
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for r in ROTURAS + [CONTROL]:
            desc, rel, cambios = r[:3]
            txt = io.open(os.path.normpath(os.path.join(RAIZ, rel.replace("/", os.sep))), encoding="utf-8").read()
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
