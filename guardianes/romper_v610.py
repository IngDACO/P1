# -*- coding: utf-8 -*-
"""Bateria de roturas de v610 (la memoria del agente del parte). ⚠️ Verde de BASE primero (v459)
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
G = "verif_v610"
DLU = "core/daily_log_ui.py"
MEMF = "core/agente_memoria.py"
PA = "core/parte_agente.py"
TC = "core/timeclock.py"
AUD = "core/auditoria.py"
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
    # ── qué se aprende ──
    ("una propuesta suelta sin marcar no cuenta como rechazo", MEMF,
     [('            out[k] = (c + ok, r + (not ok))\n', '            out[k] = (c + ok, r)\n')]),
    ("⚠️ una pregunta sin ninguna marcada enseña rechazos (no dijo nada de ellas)", MEMF,
     [('            if not ok and tipo == "q" and str(term) not in _q_con:\n', '            if False:\n')]),
    ("se aprende también de las listas de etapa", MEMF,
     [('            if tipo not in ("a", "q") or not f:\n', '            if not f:\n')]),
    ("la frase sin recortar (texto largo de un cliente a todos)", MEMF,
     [('    return s[:MAX_FRASE].strip()\n', '    return s.strip()\n')]),
    # ── qué recibe el agente ──
    ("un empate cuenta como lección", MEMF,
     [('        elif c >= 1 and c > x:\n', '        elif c >= 1 and c >= x:\n')]),
    ("«no es» con un solo rechazo", MEMF,
     [('MIN_RECHAZOS = 2          # «no es eso»: dos rechazos y ninguna confirmación\n',
       'MIN_RECHAZOS = 1          # «no es eso»: dos rechazos y ninguna confirmación\n')]),
    ("las reglas de la oficina dejan de ir primero", MEMF,
     [('    _rango = {"rule": 0, "means": 1, "not": 2}\n', '    _rango = {"rule": 1, "means": 0, "not": 2}\n')]),
    ("⚠️ el orden depende de cómo llegan (la caché del prompt se rompe)", MEMF,
     [('    out.sort(key=lambda z: (_rango[z[0]], -z[3], z[1]))\n', '')]),
    ("sin tope de lecciones en el prompt", MEMF,
     [('    return [z[:4] for z in out[:MAX_LECCIONES]]\n', '    return [z[:4] for z in out]\n')]),
    ("⚠️ la memoria va DETRÁS del plan (no se comparte entre obras)", PA,
     [('    bloques = ([{"type": "text", "text": memoria, "cache_control": {"type": "ephemeral"}}]\n'
       '               if memoria else []) + [\n',
       '    bloques = [\n')]),
    ("la memoria no llega a la llamada", PA,
     [('        crudo, info = _llamar(_k, texto, fecha, plan, mapa, previa, respuestas, idioma,\n'
       '                              memoria=memoria)\n',
       '        crudo, info = _llamar(_k, texto, fecha, plan, mapa, previa, respuestas, idioma)\n')]),
    ("`PROMPT_V` sin subir (los partes sin revisar se leerían con otras instrucciones)", PA,
     [('PROMPT_V = 2\n', 'PROMPT_V = 1\n')]),
    # ── global y fuera de los guardianes ──
    ("⚠️ la memoria deja de ser global (cada cliente aprendería solo)", TC,
     [('                   "agentmemory"}\n', '                   }\n')]),
    # ⚠️ La que cazó romper_v430 en la 1ª tanda: fuera del lote, la memoria se lee VACÍA siempre.
    # v615 · re-anclada: detrás de «AgentMemory» va ahora «Tasks» (la rotura es la MISMA: quitarla).
    ("⚠️ `AgentMemory` fuera del lote (la memoria se escribe y no se vuelve a leer)", "core/hojas.py",
     [('    "AgentMemory",\n', '')]),
    ("⚠️ bajo AppTest se escribe en la hoja REAL", MEMF,
     [('        return None\n    if not timeclock._secrets_present():\n        return None\n',
       '    if not timeclock._secrets_present():\n        return None\n')]),
    ("⚠️ bajo AppTest se lee la hoja REAL", MEMF,
     [('    if "streamlit.testing.v1.local_script_runner" in sys.modules:\n        return []\n', '')]),
    # ── escribir ──
    ("una lección repetida se añade otra vez en vez de sumarse", MEMF,
     [('        hit = idx.get((f, a))\n', '        hit = None\n')]),
    ("⚠️ un admin olvida lo de otro grupo", MEMF,
     [('        if not es_propietario and str(r.get("Group", "")) != str(grupo):\n', '        if False:\n')]),
    ("lecciones() deja ver lo de otros grupos al admin", MEMF,
     [('        if grupo is not None and str(r.get("Group", "")) not in (str(grupo), ""):\n', '        if False:\n')]),
    # ── la pantalla ──
    ("⚠️ confirmar un parte del agente no enseña nada", DLU,
     [('                        _aprender(reg, por_destino, grupo, usuario, lid)\n', '                        pass\n')]),
    ("lo leído por el vocabulario también enseña", DLU,
     [('    if not reg:\n        return\n    try:\n        from core import agente_memoria as MEM\n'
       '        ok, _n = MEM.aprender(',
       '    try:\n        from core import agente_memoria as MEM\n        ok, _n = MEM.aprender(')]),
    ("la lectura no recibe la memoria", DLU,
     [('    mapa, idi, _mem = SP.acreditado(pid), idioma(), _memoria()\n', '    mapa, idi, _mem = SP.acreditado(pid), idioma(), ""\n')]),
    ("⚠️ el panel le deja al admin olvidar lo de otro grupo", DLU,
     [('                     if _dueno or str(r.get("Group", "")) == str(grupo)}\n', '                     }\n')]),
    ("una regla del admin sale global", DLU,
     [('                                      "" if _dueno else grupo, _u)\n', '                                      "", _u)\n')]),
    ("«Forget» sin elegir nada llama igual", DLU,
     [('            if not pet.get("ids"):\n', '            if False:\n')]),
    # ── la auditoría ──
    ("⚠️ vuelve el «0.0 → 0» en la auditoría", AUD,
     [('        b = str("" if nuevo is None else nuevo).strip()\n', '        b = str(nuevo or "").strip()\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           MEMF, [('MAX_LECCIONES = 150       # las que van al agente: ≈ 2.000 tokens, en la caché\n',
                   'MAX_LECCIONES = 150       # las que van al agente: ≈ 2.000 tokens, en la caché (control)\n')])


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
