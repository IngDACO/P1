# -*- coding: utf-8 -*-
"""La fila y la sección de v542 decían «el aviso sale una pasada tarde: pendiente»: se
arregló en v543. Un solo uso."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VIEJA = ("El aviso «empezó de cero» sale una pasada tarde (los avisos de flash se pintan antes "
         "de que el Survey lo encole): pendiente")
NUEVA = ("El aviso «empezó de cero» salía una pasada tarde (los avisos de flash se pintan antes "
         "de que el Survey lo encole): arreglado en v543")
for p in ("C:/Users/diego/P1/CLAUDE.md", "C:/Users/diego/P1/HISTORIAL.md"):
    s = io.open(p, encoding="utf-8").read()
    n = s.count(VIEJA)
    if n < 1:
        raise SystemExit("ancla no encontrada en %s" % p)
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(VIEJA, NUEVA))
    print(p, "reemplazos:", n)
