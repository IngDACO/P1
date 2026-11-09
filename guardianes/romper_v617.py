# -*- coding: utf-8 -*-
"""Bateria de roturas de v617 (Enter no envía un formulario de varios campos; los céntimos del
recibo; los errores en español). ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite
(v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

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
G = "verif_v617"
PU = "core/projects_ui.py"
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
    # ── Enter ──
    ("⚠️ el recibo vuelve a guardarse a medias con Enter", PU,
     [('with st.form(f"{key_prefix}_add_{pid}{_sf}", clear_on_submit=False, enter_to_submit=False):',
       'with st.form(f"{key_prefix}_add_{pid}{_sf}", clear_on_submit=False):')]),
    ("⚠️ el alta de obra, con Enter (el barrido, no solo el recibo)", PU,
     [('with st.form(f"np_form_{key}", enter_to_submit=False):', 'with st.form(f"np_form_{key}"):')]),
    ("el cobro de una factura, con Enter", "core/invoices_ui.py",
     [('with st.form(f"cob_{fid}", enter_to_submit=False):', 'with st.form(f"cob_{fid}"):')]),
    # (v627: la ausencia ya no es un `st.form`: Enter no puede enviarla, va con su botón)
    ("el alta de un usuario de campo, con Enter", "core/auth_ui.py",
     [('with st.form(f"form_campo_{_g}", clear_on_submit=False, enter_to_submit=False):',
       'with st.form(f"form_campo_{_g}", clear_on_submit=False):')]),
    ("`enter_to_submit` a True a propósito tampoco vale", PU,
     [('with st.form(f"edit_{pid}", enter_to_submit=False):',
       'with st.form(f"edit_{pid}", enter_to_submit=True):')]),
    ("la caja de «To-do» pierde el Enter (es de UN campo: ahí es lo natural)", "core/tareas_ui.py",
     [('with st.form(f"{kp}_td_form_{pid}", border=False):',
       'with st.form(f"{kp}_td_form_{pid}", border=False, enter_to_submit=False):')]),
    # ── los céntimos ──
    ("⚠️ el importe vuelve a perder los céntimos", PU,
     [('f"{theme.dinero(_amt, 2 if abs(_amt - round(_amt)) > 1e-9 else 0)}")', 'f"{theme.dinero(_amt, 0)}")')]),
    # v670 · re-anclada: el aviso de borrar un recibo usa la misma expresión (H9 del ciclo 2)
    ("uno redondo sale con «.00»", PU,
     [('f"{theme.dinero(_amt, 2 if abs(_amt - round(_amt)) > 1e-9 else 0)}")', 'f"{theme.dinero(_amt, 2)}")')]),
    ("el «$» del importe sin escapar", PU,
     [('f"{theme.dinero(_amt, 2 if abs(_amt - round(_amt)) > 1e-9 else 0)}")',
       'f"{theme.dinero_html(_amt, 2 if abs(_amt - round(_amt)) > 1e-9 else 0)}")')]),
    # ── los errores ──
    ("«Error leyendo» vuelve en los recibos", "core/expenses.py",
     # v670 · re-anclada: `adjuntar` lee la hoja igual (H8 del ciclo 2); esta es la de `delete`
     [('return False, t("Error reading: {e}", e=e)\n    for i, r in enumerate(recs):\n        if str(r.get("ID", "")) == str(gid):\n            did = ',
       'return False, f"Error leyendo: {e}"\n    for i, r in enumerate(recs):\n        if str(r.get("ID", "")) == str(gid):\n            did = ')]),
    ("«Error creando grupo» vuelve", "core/auth.py",
     [('return False, t("Error creating the group: {e}", e=e)', 'return False, f"Error creando grupo: {e}"')]),
    ("el mensaje interno vuelve al español", "core/correcciones.py",
     [('return False, f"internal: {len(fila)} values for {len(HEADERS)} columns"',
       'return False, f"internal: {len(fila)} valores para {len(HEADERS)} columnas"')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PU, [('# ⚠️ v617 · SIN Enter: visto en producción', '# ⚠️ v617 (control) · SIN Enter: visto en producción')])


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
