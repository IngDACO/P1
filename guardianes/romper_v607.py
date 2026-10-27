# -*- coding: utf-8 -*-
"""Bateria de roturas de v607 (el agente del parte diario). ⚠️ Verde de BASE primero (v459) y NO
en paralelo con la suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios
(v526).

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
G = "verif_v607"
PA = "core/parte_agente.py"
DLU = "core/daily_log_ui.py"
DLG = "core/daily_log.py"
PPR = "core/parte_propuestas.py"
REQ = "requirements.txt"
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
    # ── el modelo y la llamada ──
    ("otro modelo (Haiku) sin que el usuario lo pida", PA,
     [('MODELO = "claude-sonnet-5-5"\n', 'MODELO = "claude-haiku-5-5"\n')]),
    ("esfuerzo alto (más lento y caro en el móvil)", PA,
     [('ESFUERZO = "low"\n', 'ESFUERZO = "high"\n')]),
    ("⚠️ sin la guarda de AppTest (la suite llamaría a la API de pago)", PA,
     [('    if "streamlit.testing.v1.local_script_runner" in sys.modules:\n        return ""\n', '')]),
    ("las instrucciones sin su marca de caché", PA,
     [('    return [{"type": "text", "text": _txt, "cache_control": {"type": "ephemeral"}}]\n',
       '    return [{"type": "text", "text": _txt}]\n')]),
    ("sin el respaldo del servidor ante un rechazo", PA,
     [('            fallbacks="default",\n', '')]),
    ("vuelve `temperature` (400 desde el 21/10/2026)", PA,
     [('            max_tokens=MAX_TOKENS,\n', '            max_tokens=MAX_TOKENS,\n            temperature=0,\n')]),
    ("un rechazo del modelo se lee como respuesta", PA,
     [('    if r.stop_reason == "refusal":\n        raise _Fallo("refusal")\n', '')]),
    ("⚠️ sin tope de rondas (gasto sin fin en un parte)", PA,
     [('    if previa and _ronda > MAX_RONDAS:\n        return None, "max_rondas"\n', '')]),
    ("la clave de la lectura no mira el plan (una lectura de otro plan valdría)", PA,
     [('"\\x1f".join([MODELO, str(PROMPT_V), _txt, str(texto or "")])',
       '"\\x1f".join([MODELO, str(PROMPT_V), str(texto or "")])')]),
    ("⚠️ las atribuciones con el nombre de una persona van al modelo", PA,
     [('        return _ATRIBUCION.sub("", _DOC.read_text(encoding="utf-8"))\n',
       '        return _DOC.read_text(encoding="utf-8")\n')]),
    ("la lectura no dice cuánto documento llegó (no se ve en producción)", PA,
     [('"seg": info["seg"], "ref": len(_referencia()),', '"seg": info["seg"],')]),
    ("el parte sin su marca de cierre (el modelo pegaba texto a la última línea)", PA,
     [('    {"type": "text", "text": "DAILY LOG%s (numbered lines):\\n%s\\n<end of log>" % (',
       '    {"type": "text", "text": "DAILY LOG%s (numbered lines):\\n%s" % (')]),
    # ── validar ──
    ("⚠️ un código fuera del plan se acepta tal cual", PA,
     [('            else:\n                inval += 1\n', '            else:\n                acts.append(c)\n')]),
    ("«hecho» sin código válido se queda como hecho", PA,
     [('        if cl in ("done", "question") and not acts:\n            cl = "unclear"\n',
       '        if False:\n            cl = "unclear"\n')]),
    ("«no entendido» con candidatas se queda en una caja en blanco", PA,
     [('        elif cl == "unclear" and acts:\n            cl = "question"\n', '')]),
    ("⚠️ la línea que el modelo se salta se ignora", PA,
     [('        if l.strip() and i not in _cubiertas:\n', '        if False:\n')]),
    ("⚠️ lo hecho bajo «Issues/Pendings» sale sin aviso", PA,
     [('        if f["clase"] == "done" and f["linea"] in _bloque:\n',
       '        if False:\n')]),
    # ── de la lectura a la tarjeta ──
    ("⚠️ lo EMPEZADO se propone como hecho", PA,
     [('        if cl == "done":\n', '        if cl in ("done", "started"):\n')]),
    ("repartida la nota, cada destino ve la nota entera", PA,
     [('    if lineas_dest is None:\n        return True\n', '    return True\n')]),
    ("el aviso de «Issues/Pending» no llega a la fila", PA,
     [('                            aviso="bajo_pendiente" if f.get("bajo_pendiente") else "",\n',
       '                            aviso="",\n')]),
    # ── la pantalla ──
    ("⚠️ se leen también los partes YA revisados", DLU,
     [('             if str(r.get("Author", "")) == str(usuario) and not DL.revisado(r)\n',
       '             if str(r.get("Author", "")) == str(usuario)\n')]),
    ("⚠️ se leen los partes de OTROS", DLU,
     [('             if str(r.get("Author", "")) == str(usuario) and not DL.revisado(r)\n',
       '             if not DL.revisado(r)\n')]),
    ("⚠️ sin la lectura de la sesión (cada recarga vuelve a llamar)", DLU,
     [('        st.session_state.setdefault(_LECT, {}).update(lecturas)\n', '')]),
    ("⚠️ un fallo se reintenta en cada recarga", DLU,
     [('             and not _fallo(r.get("ID"))]\n', '             ]\n')]),
    ("todo en paralelo desde el primero (nadie aprovecha la caché)", DLU,
     [('        res = [_uno(falta[0])]\n        if len(falta) > 1:\n'
       '            with ThreadPoolExecutor(max_workers=4) as ex:\n'
       '                res += list(ex.map(_uno, falta[1:]))\n',
       '        with ThreadPoolExecutor(max_workers=4) as ex:\n'
       '            res = list(ex.map(_uno, falta))\n')]),
    ("la lectura no se guarda en la hoja (se paga en cada sesión)", DLU,
     [('        ok, _n = DL.guardar_lecturas({k: AG.a_json(v) for k, v in lecturas.items()})\n',
       '        ok, _n = True, 0\n')]),
    ("lo no entendido sin su caja para contestar", DLU,
     [('    _dudas = AG.sin_entender(reg)\n    if _dudas:\n', '    _dudas = []\n    if _dudas:\n')]),
    # v610 · re-anclada: la llamada lleva ahora también la memoria (la rotura es la MISMA).
    ("«Read it again» manda solo la última respuesta", DLU,
     [('                           list(previa.get("respuestas") or []) + pet["respuestas"], idioma(),\n',
       '                           pet["respuestas"], idioma(),\n')]),
    ("«Read it again» sin respuestas llama igual", DLU,
     [('    if not pet.get("respuestas"):\n', '    if False:\n')]),
    ("⚠️ el fallo del agente no se dice (la lista de palabras pasa por el agente)", DLU,
     [('    if _m and AG.disponible():\n', '    if False:\n')]),
    ("⚠️ un parte que el agente no entendió entero se queda sin tarjeta", DLU,
     [('    if not _prev["hay_algo"] and not (reg and AG.sin_entender(reg)):\n',
       '    if not _prev["hay_algo"]:\n')]),
    ("lo empezado no se enseña", DLU,
     [('    _emp = p.get("empezadas") or []\n', '    _emp = []\n')]),
    ("el aviso de «Issues/Pending» sin texto en la pantalla", DLU,
     [('    "bajo_pendiente": ":material/pending: Your log lists this under «Issues/Pending». Tick it "\n'
       '                      "only if it was finished.",\n', '')]),
    ("el registro no dice quién leyó el parte", PPR,
     [('    if lector:\n        out["lector"] = str(lector)\n', '')]),
    # ── la hoja y el SDK ──
    ("`Reading` en medio de la cabecera (todo se desplaza, v363)", DLG,
     [('           "Reviewed", "ReviewedBy", "Proposals", "Reading"]\n',
       '           "Reviewed", "ReviewedBy", "Reading", "Proposals"]\n')]),
    ("la fila nueva sin la celda de `Reading`", DLG,
     [('                      _hoy.strftime("%Y-%m-%d %H:%M:%S"), "", "", "", ""],\n',
       '                      _hoy.strftime("%Y-%m-%d %H:%M:%S"), "", "", ""],\n')]),
    ("el SDK vuelve a un rango (el Cloud instalaría otra cosa que la suite)", REQ,
     [('anthropic==1.17.0\n', 'anthropic>=0.25.0,<2\n')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PA, [('PROMPT_V = 2\n', 'PROMPT_V = 2   # (control)\n')])


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
