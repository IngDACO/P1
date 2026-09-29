# -*- coding: utf-8 -*-
"""Bateria de roturas de v525. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522).

⚠️ Las dos preguntas: ¿puede una etapa quedar fechada el dia en que se CONFIRMO en vez del
dia en que se TRABAJO? ¿Puede una linea sin ascensor acabar en una obra que nadie eligio?
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v525"
UI = "core/daily_log_ui.py"
SPR = "core/stage_progress.py"
PRJ = "core/projects.py"
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
    # ── (1A) la fecha del trabajo ────────────────────────────────────────────
    # ⚠️ v528 · Cuatro espacios más: la llamada vive ahora dentro del `with st.spinner`.
    ("la pantalla deja de pasar la fecha del parte (todo se fecha al confirmar)",
     UI, 'origen=SP.PARTE,\n                                           fecha=str(r.get("Date", "") or ""))',
     "origen=SP.PARTE)"),

    ("los creditos NUEVOS no guardan su dia de trabajo",
     SPR, 'str(origen), str(quien), _ahora, _dia])', "str(origen), str(quien), _ahora])"),

    # ⚠️ v528 · Sin la coma final: la lista va ahora dentro de un `_lote_sp += [...]`.
    ("al re-acreditar una fila, su dia de trabajo se queda el viejo",
     SPR, '("Updated", _ahora), ("WorkDate", _dia))]', '("Updated", _ahora))]'),

    ("el credito de AHORA no cuenta para las fechas de la etapa",
     SPR, "        _fechas[(_et, _ac)] = _dia\n", ""),

    ("el inicio de la etapa sale del ULTIMO dia en vez del primero",
     SPR, '"inicio": _ds[0] if _ds else "",', '"inicio": _ds[-1] if _ds else "",'),

    ("el fin de la etapa sale del PRIMER dia en vez del ultimo",
     SPR, '"fin": _ds[-1] if (_ds and _det[o]["pct"] >= 100) else ""',
     '"fin": _ds[0] if (_ds and _det[o]["pct"] >= 100) else ""'),

    ("una fecha del FUTURO llega a la hoja (avance dibujado antes de pasar)",
     SPR, "return min(_dt.date.fromisoformat(s), hoy).isoformat()",
     "return _dt.date.fromisoformat(s).isoformat()"),

    ("los creditos de antes de v525 (sin `WorkDate`) dejan de contar para las fechas",
     SPR, 'for k in ("WorkDate", "Updated"):', 'for k in ("WorkDate",):'),

    ("`WorkDate` se mete en MEDIO de la cabecera (todo se desplaza, v363)",
     SPR, '"UpdatedBy", "Updated", "WorkDate"]', '"WorkDate", "UpdatedBy", "Updated"]'),

    ("`save_field_progress` ignora el inicio que le llega (fecha HOY)",
     PRJ, '"values": [[fi_n or hoy]]})', '"values": [[hoy]]})'),

    ("`save_field_progress` ya no ADELANTA un inicio posterior",
     PRJ, "elif av > 0 and fi_n and _dia_iso(fi) and fi_n < fi:", "elif False:"),

    ("`save_field_progress` ATRASA un inicio anterior (lo mueve al del parte)",
     PRJ, "and fi_n < fi:", "and fi_n > fi:"),

    ("`save_field_progress` ignora el fin que le llega (fecha HOY)",
     PRJ, '"values": [[ff_n or hoy]]})', '"values": [[hoy]]})'),

    # ── (2B) las lineas sin ascensor ─────────────────────────────────────────
    ("sin selector: las lineas sin ascensor vuelven a caer en la obra del parte",
     UI, '_sin_rel = _p_sin["hay_algo"]', "_sin_rel = False"),

    ("el selector de las lineas sin ascensor nace con una obra elegida",
     UI, "t(\"Lines that don't name a lift\"), _opts, index=None,",
     "t(\"Lines that don't name a lift\"), _opts, index=0,"),

    ("un trozo sin nada que ensenar deja un «→ obra» vacio",
     UI, '"retiradas", "fuera")):\n                continue\n',
     '"retiradas", "fuera")) and False:\n                continue\n'),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           SPR, 'SHEET = "StageProgress"', '# comentario inocuo del control\nSHEET = "StageProgress"')


def aplica(rel, viejo, nuevo):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    if bak.count(viejo) != 1:
        return None, bak, p, bak.count(viejo)
    io.open(p, "w", encoding="utf-8", newline="").write(bak.replace(viejo, nuevo, 1))
    return True, bak, p, 1


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
for desc, rel, viejo, nuevo in ROTURAS:
    _ok, bak, p, n = aplica(rel, viejo, nuevo)
    if _ok is None:
        print("  ??      ancla %s en %s -> %s" % ("ausente" if n == 0 else "x%d" % n, rel, desc))
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
_d, _r, _v, _n = CONTROL
_ok, bak, p, n = aplica(_r, _v, _n)
control_ok = False
if _ok is None:
    print("  ??      ancla del control %s" % ("ausente" if n == 0 else "x%d" % n))
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
