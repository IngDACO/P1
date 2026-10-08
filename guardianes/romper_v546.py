# -*- coding: utf-8 -*-
"""Bateria de roturas de v546. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la
suite (v455). Con TOPE de tiempo (v522). Cada rotura es una LISTA de cambios (v526).

⚠️ La primera devuelve lo visto en producción: una jornada abierta «a las 18:00» que
pisaba otra ya cerrada, y esos minutos contaban dos veces como tiempo pagado.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v546"
TC = "core/timeclock.py"
TU = "core/timeclock_ui.py"
PU = "core/projects_ui.py"
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
    ("⚠️ el solape no se detecta nunca (las horas cuentan dos veces)",
     TC, [("        if ini < r1 and r0 < _fin:\n", "        if False:\n")]),

    ("abrir a una hora pasada no comprueba el solape",
     TC, [("        if _r:\n            return False, _msg_choque(_r, tipo)\n", "")]),

    ("corregir una hora no comprueba el solape",
     TC, [("    if _r:\n        return False, _msg_choque(_r, _tipo_of(actual))\n", "")]),

    ("el solape no distingue tipo (una obra dentro de la jornada chocaría)",
     TC, [(" or _tipo_of(r) != tipo:\n", ":\n")]),

    ("la fila corregida choca consigo misma",
     TC, [("        if i == excluir or not _matches(", "        if not _matches(")]),

    ("⚠️ «Did you forget…» sin clave (se cierra solo)",
     TU, [('icon=":material/schedule_send:", key="tc_corregir")', 'icon=":material/schedule_send:")')]),

    ("la lectura de la IA sin clave",
     PU, [(", key=\"cpx_lectura_ia\")", ")")]),

    ("⚠️ el selector de la pantalla ficha sin avisar del Pre-Start",
     TU, [("                    _fichar(nombre, _nom_de.get(_pid, \"\"), grupo, usuario, _pid)\n",
           "                    timeclock.fichar_proyecto(nombre, _nom_de.get(_pid, \"\"), grupo, usuario, _pid)\n"
           "                    st.rerun()\n")]),

    ("«Switch» no avisa del Pre-Start de la obra nueva",
     TU, [("                            _armar_aviso_prestart(_nuevo, _nom, grupo)   # otra obra: su charla\n", "")]),

    ("volver a fichar no re-arma un aviso descartado",
     TU, [("            st.session_state.pop(f\"_ps_visto_{pid}\", None)\n    except Exception:\n"
           "        pass                          # sin pre-starts configurados: no se estorba\n",
           "            pass\n    except Exception:\n"
           "        pass                          # sin pre-starts configurados: no se estorba\n")]),

    ("vuelve «— cambiar a… —»",
     TU, [("vacio=t(\"— switch to… —\"))", "vacio=\"— cambiar a… —\")")]),

    ("el historial vuelve a mes/día",
     TU, [("f\"{f['entrada'][8:10]}/{f['entrada'][5:7]} {f['entrada'][11:16]}\"",
           "f[\"entrada\"][5:16].replace(\"-\", \"/\")")]),
]

CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           TC, [("def _msg_choque(r, tipo) -> str:\n",
                 "# comentario inocuo del control\ndef _msg_choque(r, tipo) -> str:\n")])


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
