# -*- coding: utf-8 -*-
"""Reancla el chequeo del selector de estado manual de verif_v442 (caducado por v487)."""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v442.py")
lineas = io.open(P, encoding="utf-8").read().split("\n")
idx = [i for i, l in enumerate(lineas) if "estado manual usa format_func" in l and l.startswith("chk(")]
if len(idx) != 1:
    raise SystemExit("linea del chequeo aparece %d veces" % len(idx))
i = idx[0]
if "P.ESTADOS_MANUAL," not in lineas[i + 1]:
    raise SystemExit("la segunda linea no es la esperada: %r" % lineas[i + 1])

NUEVO = [
    "# ⚠️ REANCLADO en v487: comparaba el TEXTO literal «P.ESTADOS_MANUAL, format_func=_etq,»",
    "# y v487 pasa las opciones por `ui.opciones_con_actual` (para no des-archivar una obra",
    "# en silencio), asi que llegan en `_ems`. Lo que esta regla protege no es la forma: es",
    "# que el desplegable que GUARDA el estado muestre la etiqueta con `format_func` y NO",
    "# traduzca las OPCIONES (guardaria el texto traducido y dejaria la rama muerta, v442).",
    "import ast as _ast442",
    "_sel442 = [n for n in _ast442.walk(_ast442.parse(_pu)) if isinstance(n, _ast442.Call)",
    "           and getattr(n.func, 'attr', '') == 'selectbox' and n.args",
    "           and 'Manual status (override)' in _ast442.unparse(n.args[0])]",
    "_trad442 = ('t', 'd', 'etiqueta', '_etq')",
    "_ok442 = bool(_sel442) and all(",
    "    any(k.arg == 'format_func' for k in n.keywords) and len(n.args) > 1",
    "    and not any(isinstance(c, _ast442.Call)",
    "                and (getattr(c.func, 'id', None) or getattr(c.func, 'attr', '')) in _trad442",
    "                for c in _ast442.walk(n.args[1]))",
    "    for n in _sel442)",
    lineas[i] + " _ok442,",
    '    "selectbox encontrados: %d" % len(_sel442))',
]
lineas[i:i + 2] = NUEVO
s = "\n".join(lineas)
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v442 reanclado (lineas %d-%d)" % (i + 1, i + 2))
