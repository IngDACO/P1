# -*- coding: utf-8 -*-
"""Bateria de roturas de v615 (la lista de pendientes de la obra). ⚠️ Verde de BASE primero (v459)
y NO en paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de
cambios (v526).

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
G = "verif_v615"
TA = "core/tareas.py"
TU = "core/tareas_ui.py"
PU = "core/projects_ui.py"
PJ = "core/projects.py"
HJ = "core/hojas.py"
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
    # ── apuntar ──
    ("⚠️ una pendiente igual se repite (doble toque, dos personas)", TA,
     [('            return False, t("That task is already on the list.")\n', '            pass\n')]),
    ("la de antes HECHA tampoco deja apuntarla otra vez", TA,
     [('        if any(str(r.get("ProjectID", "")) == str(pid) and _activa(r) and not hecha(r)\n',
       '        if any(str(r.get("ProjectID", "")) == str(pid) and _activa(r)\n')]),
    ("la de OTRA obra cuenta como repetida", TA,
     [('        if any(str(r.get("ProjectID", "")) == str(pid) and _activa(r) and not hecha(r)\n',
       '        if any(_activa(r) and not hecha(r)\n')]),
    ("el texto, sin limpiar", TA,
     [('    _txt = re.sub(r"\\s+", " ", str(texto or "")).strip()\n', '    _txt = str(texto or "")\n')]),
    ("las pendientes, la más vieja primero (la recién apuntada, al fondo)", TA,
     [('                  key=lambda r: (str(r.get("Created", "")), str(r.get("ID", ""))), reverse=True)\n',
       '                  key=lambda r: (str(r.get("Created", "")), str(r.get("ID", ""))))\n')]),
    # ── marcar ──
    ("⚠️ un doble toque escribe otra vez", TA,
     [('    if hecha(r) == bool(hecho):\n        return True, ""\n', '')]),
    ("marcar sin decir QUIÉN", TA,
     [('"values": [[str(quien) if hecho else ""]]},', '"values": [[""]]},')]),
    ("⚠️ una tarea de OTRA obra se marca (el ID sin su obra)", TA,
     [('        if str(r.get("ID", "")) == str(tid) and str(r.get("ProjectID", "")) == str(pid):\n',
       '        if str(r.get("ID", "")) == str(tid):\n')]),
    # ── borrar ──
    ("⚠️ el módulo deja borrar la de otro (solo la pantalla lo impedía)", TA,
     [('    if not puede_borrar(r, quien, gestor):\n', '    if False:\n')]),
    ("⚠️ el campo puede borrar cualquiera", TA,
     [('    return bool(gestor) or str((r or {}).get("CreatedBy", "")) == str(quien)\n', '    return True\n')]),
    ("borrar no oculta", TA,
     [('{"range": "%s%d" % (col_letter(_COL["Active"]), fila), "values": [["NO"]]},',
       '{"range": "%s%d" % (col_letter(_COL["Active"]), fila), "values": [[""]]},')]),
    ("las borradas siguen en la lista", TA,
     [('            if str(r.get("ProjectID", "")) == str(pid) and _activa(r)\n',
       '            if str(r.get("ProjectID", "")) == str(pid)\n')]),
    ("⚠️ borrar la obra se lleva las tareas de TODAS", TA,
     [('    filas = [i + 2 for i, r in enumerate(recs) if str(r.get("ProjectID", "")) == str(pid)]\n',
       '    filas = [i + 2 for i, r in enumerate(recs)]\n')]),
    ("borrar la obra, de arriba abajo (los índices se desplazan)", TA,
     [('    for fila in sorted(filas, reverse=True):\n', '    for fila in sorted(filas):\n')]),
    ("⚠️ borrar la obra deja su lista huérfana", PJ,
     [('        _TA.borrar_de_obra(pid)\n', '        pass\n')]),
    ("⚠️ `Tasks` fuera del lote (se escribe y se lee VACÍA)", HJ,
     [('    "Tasks",\n)', ')')]),
    # ── la pantalla ──
    ("⚠️ el texto de la persona sin escapar (cursivas, fórmulas)", TU,
     [('st.checkbox(literal_md(r.get("Text", "")), value=False, key=_c,',
       'st.checkbox(str(r.get("Text", "")), value=False, key=_c,')]),
    ("la caja no se vacía tras apuntar", TU,
     [('                st.session_state[_k] = int(st.session_state.get(_k, 0)) + 1   # la caja nace vacía\n', '')]),
    ("⚠️ la caja se vacía aunque NO se guardara (se pierde lo escrito)", TU,
     [('                # vuelve a escribir.\n                flash.error(r)\n',
       '                # vuelve a escribir.\n                _k = _clave_gen(pet.get("kp"), pid)\n'
       '                st.session_state[_k] = int(st.session_state.get(_k, 0)) + 1\n'
       '                flash.error(r)\n')]),
    ("quién la apuntó, por su login", TU,
     [('q=_nombre(r.get("CreatedBy"))', 'q=r.get("CreatedBy")')]),
    ("la fecha, en ISO", TU,
     [('d=_dmy(r.get("Created"))', 'd=r.get("Created")')]),
    ("⚠️ una petición de OTRA obra se aplica a la que se ve", TU,
     [('    if not pet or str(pet.get("pid")) != str(pid):\n', '    if not pet:\n')]),
    ("«Delete» sin elegir, llama igual", TU,
     [('        elif not pet.get("tid"):\n', '        elif False:\n')]),
    ("el desplegable de las hechas, sin clave (trampa 35)", TU,
     [('                         key=f"{kp}_td_exp_hechas_{pid}"):', '                         ):')]),
    # ── dónde vive ──
    ("⚠️ el campo con permiso de oficina", PU,
     [('                    gestor=False, key_prefix="fld")\n', '                    gestor=True, key_prefix="fld")\n')]),
    ("el campo pierde «To-do»", PU,
     [('"📝 Parte", "✅ Tareas", "🚨 Avisos"', '"📝 Parte", "🚨 Avisos"')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           TA, [('MAX_TEXTO = 200        # una tarea es una línea', 'MAX_TEXTO = 200        # (control) una tarea es una línea')])


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
