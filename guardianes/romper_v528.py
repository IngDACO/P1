# -*- coding: utf-8 -*-
"""Bateria de roturas de v528. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

Lo que rompe: el lote de lectura y de escritura, decidir con la caché, escribir cuando no
se debe, el rastro de cambios, el heartbeat en segundo plano y los «Saving…».
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v528"
HJ = "core/hojas.py"
SPR = "core/stage_progress.py"
AU = "core/auth.py"
APPF = "app.py"
SPU = "core/stage_progress_ui.py"
DUI = "core/daily_log_ui.py"
TOPE_S = 420


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    # ── el lote ──────────────────────────────────────────────────────────────
    ("⚠️ el guardado vuelve a LEER hoja por hoja",
     HJ, [("    ss = _mismo_libro(ws)\n", "    ss = None\n")]),

    ("⚠️ el guardado vuelve a ESCRIBIR hoja por hoja",
     HJ, [('    if ss is None or not hasattr(ss, "values_batch_update"):', "    if True:")]),

    ("⚠️ la fila vacia de en medio se salta: se escribe en la fila de OTRO",
     HJ, [("           for f in datos[1:]]", "           for f in datos[1:] if f]")]),

    ("se escribe USER_ENTERED: «007» pasa a ser 7 (v42)",
     HJ, [('"valueInputOption": "RAW",', '"valueInputOption": "USER_ENTERED",')]),

    ("los rangos van sin su hoja delante (todo cae en la primera pestaña)",
     HJ, [('absolute_range_name(w.title, x["range"])', 'x["range"]')]),

    # ── que decide y que escribe ─────────────────────────────────────────────
    ("⚠️ se decide con la CACHE (lo que acredito otro se pierde y la etapa baja)",
     SPR, [("_indice(_leido.get(SHEET), pid)", "_indice(creditos(pid), pid)")]),

    ("⚠️ el avance de la obra se calcula con las actividades de ANTES de escribir",
     SPR, [("pid, _acts)", "pid, [r for r in _leido.get(P.ACTIVITIES_SHEET) "
                           "if str(r.get('ProjectID')) == str(pid)])")]),

    ("⚠️ sin la guarda de la obra: se escribe aunque no este en Projects",
     SPR, [("        if _lote_prj is None:", "        if False:")]),

    ("un fallo SIN filas nuevas se cuenta como «guardado a medias»",
     SPR, [("        if _nuevas and _cambios:", "        if _nuevas or _cambios:")]),

    # ── el rastro de cambios ─────────────────────────────────────────────────
    ("el rastro de cambios desaparece",
     SPR, [('            auditoria.registrar("proyecto", pid, auditoria.diff(_antes, _escritos),',
            '            (lambda *a, **k: None)("proyecto", pid, auditoria.diff(_antes, _escritos),')]),

    ("⚠️ el «antes» del rastro sale de la CACHE",
     SPR, [("auditoria.diff(_antes, _escritos)", "auditoria.diff(P.get_project(pid), _escritos)")]),

    # ── el heartbeat ─────────────────────────────────────────────────────────
    ("⚠️ el heartbeat vuelve a BLOQUEAR la pagina (el hilo corre en primer plano)",
     AU, [("    h.start()", "    h.run()")]),

    ("⚠️ algo inesperado en el hilo EXPULSA a quien este dentro",
     AU, [("        ok = True\n    with _HB_LOCK:", "        ok = False\n    with _HB_LOCK:")]),

    ("sin guarda de hilo repetido: un heartbeat por pasada",
     AU, [('        if (_HB.get(clave) or {}).get("hilo") is not None:', "        if False:")]),

    ("⚠️ app.py deja de mirar el veredicto (el desplazado ya no sale nunca)",
     APPF, [('if heartbeat_resultado(_a.get("usuario", ""), _a.get("token", "")) is False:',
             "if False:")]),

    ("⚠️ app.py expulsa con «aun no se sabe» (None): fuera todos al entrar",
     APPF, [('if heartbeat_resultado(_a.get("usuario", ""), _a.get("token", "")) is False:',
             'if not heartbeat_resultado(_a.get("usuario", ""), _a.get("token", "")):')]),

    ("app.py vuelve al heartbeat SINCRONO",
     APPF, [('    heartbeat_en_fondo(_a.get("usuario", ""), _a.get("token", ""))',
             '    heartbeat(_a.get("usuario", ""), _a.get("token", ""))')]),

    # ── «Saving…» ────────────────────────────────────────────────────────────
    ("guardar una etapa sin «Saving…»",
     SPU, [('                    with st.spinner(t("Saving stage {n}…", n=e["orden"])):',
            "                    if True:")]),

    ("confirmar un parte sin «Saving…»",
     DUI, [('            with st.spinner(t("Saving…")):\n                for d, res in',
            "            if True:\n                for d, res in")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           HJ, [("# ── Leer y escribir VARIAS hojas en una llamada, para GUARDAR (v528) ",
                 "# comentario inocuo del control\n"
                 "# ── Leer y escribir VARIAS hojas en una llamada, para GUARDAR (v528) ")])


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


print("0. Verde de base")
_base = corre()
if not _base:
    print("   ⚠️ el guardian YA esta %s: la tanda saldria «cazada» sin probar nada"
          % ("COLGADO" if _base is None else "rojo"))
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
saltadas, colgadas = [], []
for desc, rel, cambios in ROTURAS:
    _ok, bak, p, det = aplica(rel, cambios)
    if _ok is None:
        print("  ??      ancla %s en %s -> %s" % (det, rel, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE
    if verde is None:
        colgadas.append(desc)
        print("  COLGADA  %s" % desc)
        continue
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

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
