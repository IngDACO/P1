# -*- coding: utf-8 -*-
"""Bateria de roturas de v562. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ Las marcadas devuelven el clic perdido (reproducido en una mini-app: 8 de 8) o lo
convierten en algo peor (un clic que dispara dos veces o en otra pantalla).
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
G = "verif_v562"
BO = "core/botones.py"
AP = "app.py"
AU = "core/auth_ui.py"
TOPE_S = 480


def corre(g=G):
    """True = verde, False = rojo, None = COLGADO (supero el tope)."""
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                           cwd=RAIZ, capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


ROTURAS = [
    ("⚠️ el clic ya no se anota (vuelve a perderse)", BO,
     [("        def _anota():\n            _pendientes()[k] = time.monotonic()\n",
       "        def _anota():\n            pass\n")]),
    ("⚠️ la nota se ignora (vuelve a perderse)", BO,
     [("        return bool(r) or nota is not None\n", "        return bool(r)\n")]),
    ("⚠️ la nota no se gasta (el clic dispara DOS veces)", BO,
     [("        nota = p.pop(k, None)\n        if kwargs.get(\"disabled\"):",
       "        nota = p.get(k)\n        if kwargs.get(\"disabled\"):")]),
    ("⚠️ el cierre de pasada no tira nada (un clic dispara en otra pantalla)", BO,
     [("        if isinstance(p, dict) and p:\n            p.clear()\n",
       "        if isinstance(p, dict) and p:\n            pass\n")]),
    ("⚠️ las notas no caducan", BO,
     [("if ahora - _hora(v) > VIGENCIA_S]", "if ahora - _hora(v) > 10 ** 9]")]),
    ("un botón deshabilitado se dispara por su nota", BO,
     [("        if kwargs.get(\"disabled\"):\n            return bool(r)"
       "                        # deshabilitado: la nota no lo dispara\n", "")]),
    ("⚠️ las entregas de formulario quedan fuera", BO,
     [('_PEGAJOSOS = ("button", "form_submit_button")', '_PEGAJOSOS = ("button",)')]),
    ("la entrega sin clave ya no se reconoce", BO,
     [('            return f"{nom}:{fid}:{etq}"\n', '            return None\n')]),
    ("⚠️ el chat queda fuera", BO,
     [("        if not getattr(_oc, _MARCA_CHAT, False):\n",
       "        if False:\n")]),
    ("el chat anota pero no devuelve la pregunta", BO,
     [("        return nota[1] if isinstance(nota, tuple) else r\n", "        return r\n")]),
    ("se pisa el `on_click` propio de un botón", BO,
     [('    if kwargs.get("on_click") is not None or len(args) > 1:\n        return None\n',
       '    if len(args) > 1:\n        return None\n')]),
    ("⚠️ app.py ya no cierra la pasada", AP,
     [("_botones.fin_de_pasada()\n", "")]),
    ("vuelve un botón sin clave («Sign in»)", AU,
     [('width="stretch", key="login_entrar"):', 'width="stretch"):')]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           BO, [("def _hora(v) -> float:\n", "# comentario inocuo del control\ndef _hora(v) -> float:\n")])


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


if __name__ == "__main__":
    _filtro = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--anclas" in sys.argv:
        _m = 0
        for desc, rel, cambios in ROTURAS + [CONTROL]:
            txt = io.open(os.path.join(RAIZ, rel.replace("/", os.sep)), encoding="utf-8").read()
            for viejo, _ in cambios:
                if txt.count(viejo) != 1:
                    _m += 1
                    print("  x%d  %s  <- %s" % (txt.count(viejo), desc, viejo[:60]))
        print("anclas: %d mal de %d roturas" % (_m, len(ROTURAS) + 1))
        sys.exit(1 if _m else 0)

    _rot = [r for r in ROTURAS if not _filtro or any(f in r[0] for f in _filtro)]
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
    for desc, rel, cambios in _rot:
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
