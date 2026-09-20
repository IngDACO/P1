# -*- coding: utf-8 -*-
"""¿El guardian de v486 CAZA sus fallos, o solo aprueba lo que ya funciona?

Se comprueba el VERDE DE BASE antes de la tanda: sin ese paso, un guardian rojo o que
revienta hace que las 9 roturas salgan «cazadas» sin probar nada (v459/v461/v463).
Incluye un CONTROL: un cambio inocuo que debe seguir pasando.

Copia a disco ANTES de tocar, VERIFICA el restore y ABORTA si no puede (v484).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARDIAN = os.path.join(AQUI, "verif_v486.py")
NL = chr(10)

ROTURAS = [
    # ── el fallo que yo mismo cometi: float() en vez de num() ──
    ("tabla.py", "celda vuelve a usar float() (el fallo de v323)",
     "    v = _num(valor, None)",
     "    try:" + NL + "        v = float(valor)" + NL +
     "    except (TypeError, ValueError):" + NL + "        return vacio"),
    ("tabla.py", "celda devuelve el NUMERO en vez de la cadena",
     '    return f"{simbolo}{v:,.{dec}f}"',
     "    return v"),
    ("tabla.py", "el CERO se trata como ausencia",
     "    if valor is None:",
     "    if not valor:" + NL + "        return vacio" + NL + "    if valor is None:"),
    ("tabla.py", "cambia el formato: se pierde el separador de miles",
     '    return f"{simbolo}{v:,.{dec}f}"',
     '    return f"{simbolo}{v:.{dec}f}"'),
    ("tabla.py", "derecha() pierde su respaldo",
     NL.join(['    try:',
              '        return st.column_config.Column(label, alignment="right")',
              '    except TypeError:                                     # Streamlit sin `alignment`',
              '        return st.column_config.Column(label)']),
     '    return st.column_config.Column(label, alignment="right")'),
    ("tabla.py", "tabla.py deja de ser modulo HOJA",
     "from core.num import num as _num",
     "from core.num import num as _num" + NL + "from core import projects"),
    # ── los sitios ──
    ("payroll_ui.py", "Rate/h vuelve a llevar NumberColumn",
     '"Rate/h": tabla.derecha(t("Rate/h"))}))',
     '"Rate/h": st.column_config.NumberColumn(t("Rate/h"), format="$%,.2f")}))'),
    ("catalogo_ui.py", "un sitio deja de usar tabla.celda",
     '"Horas": (tabla.celda(i.get("EstHours"), 2)',
     '"Horas": (round(_num(i.get("EstHours")), 2)'),
    ("inventory_ui.py", "el import de tabla baja DENTRO de una funcion",
     "from core import tabla",
     "# (movido)"),
    # ── CONTROL ──
    ("tabla.py", "CONTROL: solo un comentario nuevo",
     "def derecha(label):",
     "# comentario inocuo" + NL + "def derecha(label):"),
]


def _leer(r):
    with io.open(r, encoding="utf-8") as f:
        return f.read()


def _escribir(r, t):
    with io.open(r, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def _restaurar(r, orig, que):
    for i in range(5):
        try:
            _escribir(r, orig)
            if _leer(r) == orig:
                return True
        except OSError as e:
            print("       (reintento %d: %s)" % (i + 1, e))
        time.sleep(1.0)
    print("  *** NO SE PUDO RESTAURAR %s tras «%s» — SE ABORTA" % (r, que))
    return False


def corre():
    return subprocess.run([sys.executable, GUARDIAN], cwd=RAIZ, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode


_COPIA = {}
for _f in {f for f, *_ in ROTURAS}:
    _r = os.path.join(RAIZ, "core", _f)
    _c = os.path.join(AQUI, "_v486r_" + _f)
    _escribir(_c, _leer(_r))
    _COPIA[_r] = _c
print("copias: %s" % ", ".join(os.path.basename(v) for v in _COPIA.values()))

base = corre()
print("verde de BASE: %s" % ("OK" if base == 0
                             else "*** ROJO: la tanda no valdria nada ***"))
if base != 0:
    sys.exit(2)
print("")

mal = 0
for fich, que, viejo, nuevo in ROTURAS:
    ruta = os.path.join(RAIZ, "core", fich)
    orig = _leer(ruta)
    if orig.count(viejo) != 1:
        print("  ??   %-54s ANCLA aparece %d veces" % (que[:54], orig.count(viejo)))
        mal += 1
        continue
    cod = None
    try:
        _escribir(ruta, orig.replace(viejo, nuevo, 1))
        cod = corre()
    finally:
        if not _restaurar(ruta, orig, que):
            sys.exit(2)
    ctrl = que.startswith("CONTROL")
    bien = (cod == 0) if ctrl else (cod != 0)
    mal += 0 if bien else 1
    print("  %s %-54s (%s)" % ("ok  " if bien else "ESCAPA", que[:54],
                               "pasa" if cod == 0 else "rojo"))

print("")
print("%d mal" % mal)
sys.exit(0 if mal == 0 else 1)
