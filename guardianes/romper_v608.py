# -*- coding: utf-8 -*-
"""Bateria de roturas de v608 (la cita una vez + «Tell the office»). ⚠️ Verde de BASE primero (v459)
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
G = "verif_v608"
DLU = "core/daily_log_ui.py"
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
    ("vuelve la cita repetida bajo cada casilla del mismo trozo", DLU,
     [('            if not (_sig and (_sig.get("pruebas") or []) == (f.get("pruebas") or [])\n',
       '            if True or not (_sig and (_sig.get("pruebas") or []) == (f.get("pruebas") or [])\n')]),
    ("los problemas de un parte SIN tarjeta no se enseñan", DLU,
     [('        _nada_que_confirmar(_prev)      # v586 · antes, nada debajo\n        if reg:\n'
       '            _problemas(reg, r, kp)\n',
       '        _nada_que_confirmar(_prev)      # v586 · antes, nada debajo\n        if reg:\n')]),
    ("los problemas de la tarjeta no se enseñan", DLU,
     [('        n = sum(len(v["marcadas"]) for v in por_destino.values())\n        if reg:\n'
       '            _problemas(reg, r, kp)\n',
       '        n = sum(len(v["marcadas"]) for v in por_destino.values())\n        if reg:\n')]),
    ("⚠️ lo ya enviado vuelve a ofrecer el botón", DLU,
     [('        if tx in _ya:\n', '        if False:\n')]),
    ("⚠️ lo enviado no se apunta en la lectura (se avisaría dos veces)", DLU,
     [('                                   + [{"texto": pet["texto"], "alerta": str(res)}])}, {})\n',
       '                                   )}, {})\n')]),
    ("⚠️ «Read it again» olvida lo enviado", DLU,
     [('        reg["avisos"] = list(previa.get("avisos") or [])\n', '')]),
    ("⚠️ un doble toque manda dos alarmas", DLU,
     [('    if not reg or pet["texto"] in {a.get("texto") for a in reg.get("avisos") or []}:\n',
       '    if not reg:\n')]),
    ("una caja vacía manda una alarma vacía", DLU,
     [('    if not pet.get("mensaje"):\n', '    if False:\n')]),
    ("⚠️ se manda el trozo original, no lo que el autor dejó en la caja", DLU,
     [('"mensaje": str(st.session_state.get(kt, "") or "").strip()}', '"mensaje": str(texto)}')]),
    ("un fallo de la alarma se da por enviado", DLU,
     [('    if ok:\n        _apuntar({pet["lid"]: dict(reg, avisos=list(reg.get("avisos") or [])\n',
       '    if True:\n        _apuntar({pet["lid"]: dict(reg, avisos=list(reg.get("avisos") or [])\n')]),
    ("el texto propuesto no dice de qué parte sale", DLU,
     [('    return "%s\\n\\n%s" % (tx, t("(From the daily log of {d}, {i}.)", d=_dmy(r.get("Date")),\n',
       '    return tx or "%s\\n\\n%s" % (tx, t("(From the daily log of {d}, {i}.)", d=_dmy(r.get("Date")),\n')]),
    ("«Cancel» no cierra", DLU,
     [('    st.session_state.pop(ko, None)\n\n\ndef _pedir_aviso', '    pass\n\n\ndef _pedir_aviso')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           DLU, [('_AVISAR = "_ag_avisar"          # la petición que dejó «Send to the office»\n',
                  '_AVISAR = "_ag_avisar"          # la petición que dejó «Send to the office» (control)\n')])


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
