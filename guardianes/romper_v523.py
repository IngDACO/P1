# -*- coding: utf-8 -*-
"""Bateria de roturas de v523. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO en paralelo con la suite (v455).

⚠️ Cada rotura dice que fallo REAL imita. Casi todas son la misma pregunta vista desde un
sitio distinto: ¿puede la app acreditar algo que el usuario NO confirmo, o perder la marca
que dice de donde salio? Esa es la regla que el usuario puso («la app no asume nada»), y
es la que tiene que quedar vigilada.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v523"
UI = "core/daily_log_ui.py"
PPR = "core/parte_propuestas.py"
DLG = "core/daily_log.py"
SPR = "core/stage_progress.py"

# ⚠️ Con TOPE de tiempo (v522): un cuelgue no es una rotura cazada, se cuenta aparte.
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
    # ── (a) nada se acredita sin que el usuario lo marque ────────────────────
    ("las casillas nacen MARCADAS (confirmar de un toque acreditaria todo lo leido)",
     UI, 'elif st.checkbox(f["actividad"], key=',
     'elif st.checkbox(f["actividad"], value=True, key='),

    ("se acredita lo NO marcado de la lista de una etapa (la casilla al reves)",
     UI, '                elif st.checkbox(o["actividad"],\n',
     '                elif not st.checkbox(o["actividad"],\n'),

    ("«Confirmar» se puede pulsar sin nada marcado",
     UI, 'type="primary", disabled=(n == 0), width="stretch"):',
     'type="primary", disabled=False, width="stretch"):'),

    ("lo ya acreditado se vuelve a ofrecer como casilla (marcar lo marcado no informa)",
     UI, '            if f["hecha"]:\n', '            if False:\n'),

    ("hay tarjeta aunque todo lo leido este ya hecho",
     PPR, 'out["hay_algo"] = any(not f["hecha"] for f in acts)',
     'out["hay_algo"] = any(True for f in acts)'),

    ("la lista de una etapa repite lo que ya se propone suelto (dos casillas, una duda)",
     PPR, "for n in e.get(\"actividades\") or [] if n not in _ya and n in idx]",
     "for n in e.get(\"actividades\") or [] if n in idx]"),

    ("una informativa se propone como si CONTARA para el avance (v519)",
     PPR, 'out.setdefault(n, (i, e.get("nombre", ""), False))',
     'out.setdefault(n, (i, e.get("nombre", ""), True))'),

    # ── (b) la marca de origen, que es lo que permitira medir el acierto ────
    ("se acredita como si fuera MANUAL (se pierde de donde salio)",
     UI, "quien=usuario, origen=SP.PARTE)", "quien=usuario)"),

    ("la nota ya no lleva el ID del parte",
     PPR, '"pct": 100.0, "nota": str(log_id)})', '"pct": 100.0, "nota": ""})'),

    ("los dos modulos dejan de llamar igual al origen",
     SPR, 'PARTE = "log"', 'PARTE = "parte"'),

    ("`de_parte` cuenta tambien lo marcado A MANO con esa nota",
     SPR, 'if str(r.get("Source", "")) == PARTE and str(r.get("Note", "")) == str(log_id)',
     'if str(r.get("Note", "")) == str(log_id)'),

    ("el contador cuenta dos veces lo marcado en dos sitios («3 marcadas» para 2)",
     UI, "    return list(dict.fromkeys(tick))", "    return tick"),

    # ── (c) varios ascensores: solo lo que el usuario asigno ─────────────────
    # ⚠️ Esta ancla murio el mismo dia: `reparto` paso de mirar solo la linea que NOMBRA
    # «L2» a retener tambien lo que cuelga de el (`_ret`). La rotura es la misma.
    ("«L2» sin contestar se reparte como si fuera un piso (decidir por el)",
     PPR, "        _ret = bool(_sr) and (l in retener or any(x.group(0) in _sr\n"
          "                                                  for x in V._ASC_DUDOSO.finditer(l)))",
     "        _ret = False"),

    ("un ascensor sin obra elegida cae en la obra del parte",
     PPR, "            d = asignacion.get(k)\n",
     '            d = asignacion.get(k) or asignacion.get("")\n'),

    ("al separar, la cabecera «Pending» se pierde (lo pendiente pasa a propuesta)",
     PPR, '                out.setdefault(d, []).append("Pending:")\n',
     "                out.setdefault(d, [])\n"),

    ("«L2» de CABECERA sin contestar: lo de debajo cae en la obra del parte",
     PPR, "    retener = {l for x in _sr for l in lineas_de(texto, x, tambien)}",
     "    retener = set()"),

    ("se pregunta por un «L2» cuyas lineas no proponen nada (friccion que enseña a no leer)",
     UI, '    dudosos = [d for d in asc["dudosos"] if PP.propone_algo(PP.lineas_de(texto, d), plan0)]',
     '    dudosos = list(asc["dudosos"])'),

    ("se pide obra para un ascensor que no hizo nada («lift 2 was in use by the builders»)",
     UI, "            _rel = [a for a in asc2[\"ascensores\"]\n"
         "                    if PP.propone_algo(PP.lineas_de(texto, a, tambien), plan0)]",
     '            _rel = list(asc2["ascensores"])'),

    ("lo hecho en ESTA obra esconde el trabajo de otro ascensor (la tarjeta no sale)",
     UI, 'if not PP.propuestas(texto, plan0, {} if partir else SP.acreditado(pid))["hay_algo"]:',
     'if not PP.propuestas(texto, plan0, SP.acreditado(pid))["hay_algo"]:'),

    ("«L2» nace contestado como ascensor",
     UI, 'index=None, horizontal=True, key="%s_dud_%s" % (kp, d))',
     'index=0, horizontal=True, key="%s_dud_%s" % (kp, d))'),

    ("el selector de obra nace con la primera obra elegida",
     UI, '_lab, _opts, index=None, key="%s_dest_%s" % (kp, a),',
     '_lab, _opts, index=0, key="%s_dest_%s" % (kp, a),'),

    ("al confirmar ya no se mira que el destino sea una obra SUYA",
     UI, "                if d not in _mias:\n", "                if False:\n"),

    ("un unico destino que NO es esta obra sale sin su nombre (se leeria como de esta)",
     UI, "            _cab = len(destinos) > 1 or d != str(pid)",
     "            _cab = len(destinos) > 1"),

    # ── (d) la revision del parte ────────────────────────────────────────────
    ("si `acreditar` falla, el parte se marca revisado igual (la tarjeta desaparece)",
     UI, "            if errores:\n", "            if False:\n"),

    ("cualquiera puede revisar el parte de OTRO",
     DLG,
     '        if str(r.get("Author", "")) != str(quien):\n'
     '            return False, t("Only the person who wrote it can review its proposals.")',
     '        if False:\n'
     '            return False, t("Only the person who wrote it can review its proposals.")'),

    ("la fecha de revision se escribe en OTRA columna (pisa `Created`)",
     DLG, 'col_letter(_COL["Reviewed"]), i + 2)', 'col_letter(_COL["Created"]), i + 2)'),

    ("`revisado` dice siempre que no (la tarjeta vuelve cada vez que se abre)",
     DLG, 'return bool(str((r or {}).get("Reviewed", "") or "").strip())', "return False"),

    ("la fila nueva vuelve a salir mas CORTA que la cabecera (v363)",
     DLG, '_hoy.strftime("%Y-%m-%d %H:%M:%S"), "", ""]', '_hoy.strftime("%Y-%m-%d %H:%M:%S")]'),

    ("la tarjeta sale tambien en los partes AJENOS (confirmar por quien no estuvo)",
     UI, "if (_mio and not DL.revisado(r)) else", "if (not DL.revisado(r)) else"),

    ("el parte vuelve a pintarse en UN parrafo (no se encuentran las lineas citadas)",
     UI, '    st.markdown(str(r.get("Text", "")).replace("\\n", "  \\n"))',
     '    st.markdown(str(r.get("Text", "")))'),
]

# ⚠️ El CONTROL es un cambio REAL que no puede poner nada rojo (v514).
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PPR, 'ORIGEN = "log"', '# comentario inocuo del control\nORIGEN = "log"')


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
