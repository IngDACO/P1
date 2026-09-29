# -*- coding: utf-8 -*-
"""Bateria de roturas de v524. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522).

⚠️ La pregunta de todas: ¿puede el registro dejar de decir la VERDAD sobre lo que se
enseñó y lo que se aceptó? Un registro que miente es peor que ninguno: con él se va a
decidir cuanta autonomia darle a la app.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v524"
UI = "core/daily_log_ui.py"
PPR = "core/parte_propuestas.py"
DLG = "core/daily_log.py"
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
    # ── (a) lo guardado = lo que se pinto ────────────────────────────────────
    ("no se anotan las opciones de la lista de una etapa (el registro dice menos)",
     UI, '                ofr.append(["e", o["orden"], o["actividad"], e["termino"]])\n', ""),

    ("no se anotan las opciones de las preguntas",
     UI, '            ofr.append(["q", o["orden"], o["actividad"], q["termino"]])\n', ""),

    ("lo ya acreditado se anota como OFRECIDO (un rechazo que no existio)",
     UI, '        hechas.append((o["orden"], o["actividad"]))\n',
     '        hechas.append((o["orden"], o["actividad"]))\n'
     '        ofr.append(["a", o["orden"], o["actividad"], ""])\n'),

    # ⚠️ Con la linea de antes: `"termino": c.get("termino", "")}` sale DOS veces (tambien en
    # `fuera`), y la bateria se nego a aplicarla — la primera version del ancla.
    ("las propuestas dejan de llevar el termino que las trajo",
     PPR, '"fuente": c.get("fuente", ""),\n                "termino": c.get("termino", "")}',
     '"fuente": c.get("fuente", ""),\n                "termino": ""}'),

    ("no se guarda con que version del codigo se propuso",
     UI, "app=_version_app(),", 'app="",'),

    ("no se guarda lo que contesto de «L2»", UI, "                respuestas[d] = _r\n", ""),

    ("no se guarda la obra elegida para cada ascensor",
     UI, "                    elegidas[a] = asignacion[a]\n", ""),

    # ── (b) lo aceptado = lo que se acredito ─────────────────────────────────
    ("«Nothing to credit» guarda como ACEPTADO lo que tuviera marcado",
     PPR, '"marcadas": [] if nada else [[int(o), str(a)] for o, a in x.get("marcadas") or []],',
     '"marcadas": [[int(o), str(a)] for o, a in x.get("marcadas") or []],'),

    ("«Confirm» se registra como «nada»", UI, "propuestas=_registro(False))",
     "propuestas=_registro(True))"),

    ("«Nothing to credit» se registra como confirmado", UI, "propuestas=_registro(True))",
     "propuestas=_registro(False))"),

    ("al confirmar no se pasa el registro (se revisa sin el)",
     UI, "DL.marcar_revisado(lid, usuario, propuestas=_registro(False))",
     "DL.marcar_revisado(lid, usuario)"),

    # ── (c) donde y como se escribe ──────────────────────────────────────────
    ("el registro no se escribe (se revisa sin guardarlo)",
     DLG, '                {"range": "%s%d" % (col_letter(_COL["Proposals"]), i + 2),\n'
          '                 "values": [[str(propuestas or "")]]},\n', ""),

    ("el registro se escribe ENCIMA del texto del parte",
     DLG, 'col_letter(_COL["Proposals"])', 'col_letter(_COL["Text"])'),

    ("`Proposals` se mete en MEDIO de la cabecera (todo se desplaza, v363)",
     DLG, '"Reviewed", "ReviewedBy", "Proposals"]', '"Proposals", "Reviewed", "ReviewedBy"]'),

    ("sin el primer recorte: un registro grande pierde los terminos de golpe",
     PPR, "    if len(s) > _TOPE_REGISTRO:\n        # Primero sin los t",
     "    if False:\n        # Primero sin los t"),

    ("sin el ultimo recorte: un registro colosal revienta la celda (el parte no se revisa)",
     PPR, "    if len(s) > _TOPE_REGISTRO:\n        out[\"destinos\"] = {d: {k: len(v)",
     "    if False:\n        out[\"destinos\"] = {d: {k: len(v)"),

    ("`leer_registro` revienta con una celda vacia o editada a mano",
     PPR, "d = json.loads(s) if isinstance(s, str) and s.strip() else {}", "d = json.loads(s)"),

    # ── (d) lo que se mide ───────────────────────────────────────────────────
    ("`acierto` mezcla los tipos (las listas hundirian el acierto de las sueltas)",
     PPR, 'out[of[0]]["ofrecidas"] += 1', 'out["a"]["ofrecidas"] += 1'),

    ("`acierto` cuenta como aceptado todo lo ofrecido",
     PPR, 'out[of[0]]["marcadas"] += (int(of[1]), str(of[2])) in marc',
     'out[of[0]]["marcadas"] += 1'),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           PPR, "REGISTRO_V = 1", "# comentario inocuo del control\nREGISTRO_V = 1")


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
