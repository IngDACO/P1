# -*- coding: utf-8 -*-
"""v541: el recorrido en el navegador, comprobado (07/10/2026). Un solo uso."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VIEJA = ("el recorrido en el navegador (cerrar la jornada dentro de Rieles y volver a fichar en la "
         "misma obra) queda PENDIENTE: el panel del navegador quedó oculto. Lo cubren verif_v541 "
         "(la pasada cortada por st.rerun, como los botones del fichaje) y la batería")
NUEVA = ("con la cuenta de campo, en Rieles y fichando desde el menú lateral: PRUEBA MOVIL con "
         "LFKK 1234 y 3 rieles → «Close workday and project» → siguen (con v540 pasaban a 0) → "
         "fichar otra vez en PRUEBA MOVIL → siguen → cerrar y fichar en ZZ PRUEBA → a 0. Tres "
         "jornadas de prueba de ~1 min, cerradas (0 fichajes abiertos)")
for p in ("C:/Users/diego/P1/CLAUDE.md", "C:/Users/diego/P1/HISTORIAL.md"):
    s = io.open(p, encoding="utf-8").read()
    n = s.count(VIEJA)
    if n < 1:
        raise SystemExit("ancla no encontrada en %s" % p)
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(VIEJA, NUEVA))
    print(p, "reemplazos:", n)
