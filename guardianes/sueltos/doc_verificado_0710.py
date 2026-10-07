# -*- coding: utf-8 -*-
"""Pone al día lo que v535 y v539 dejaban «pendiente de producción» y ya se comprobó
(07/10/2026, cuentas de admin y de campo). Un solo uso."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CLAUDE = "C:/Users/diego/P1/CLAUDE.md"
HIST = "C:/Users/diego/P1/HISTORIAL.md"

V539_VIEJA = ("Reabrir con el selector del admin, pendiente de entrar como admin: lo cubren el "
              "ensayo con los datos reales (33/33) y el guardián")
V539_NUEVA = ("Después, con el admin (07/10/2026): CAL-0004 reabierto en Belting y elegida 88 "
              "walker en el selector, el HGPR 1785 se queda")
V535_VIEJA = ("Sin comprobar en producción (sin las cuentas): el cambio de cuenta y el selector de "
              "obra del admin — los cubren el guardián y la batería")
V535_NUEVA = ("Comprobado después (07/10/2026): el NS = 6 del plano de 88 walker manda en el "
              "Survey; el selector de obra del admin olvidaba en el servidor pero NO en el "
              "navegador (arreglado en v540); y el cambio de cuenta en la MISMA página, sin "
              "recargar (admin → campo): el asistente del campo sale vacío, sin la pregunta del "
              "admin")
NOTA = """
_Comprobado después en producción (07/10/2026): el cambio de cuenta en la MISMA página (misma
hora de carga, sin recargar): el admin deja una pregunta marcada en su asistente, sale, entra
la cuenta de campo → su asistente, abierto, con 0 mensajes. Y v539 con el admin: CAL-0004
reabierto en Belting y elegida 88 walker, el HGPR 1785 se queda._
"""
A_V540 = "__PROD__"   # no se usa: la nota va al final de la sección de v540


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


c = io.open(CLAUDE, encoding="utf-8").read()
h = io.open(HIST, encoding="utf-8").read()
for txt, nom in ((c, "CLAUDE.md"), (h, "HISTORIAL.md")):
    print(nom, "v539:", txt.count(V539_VIEJA), "· v535:", txt.count(V535_VIEJA))
if c.count(V539_VIEJA) != 1 or c.count(V535_VIEJA) != 1 or h.count(V539_VIEJA) < 1:
    raise SystemExit("anclas inesperadas")
c = c.replace(V539_VIEJA, V539_NUEVA).replace(V535_VIEJA, V535_NUEVA)
h = h.replace(V539_VIEJA, V539_NUEVA).replace(V535_VIEJA, V535_NUEVA)
# La nota, justo antes de la sección de v539 (= al final de la de v540).
ANCLA = "## LO REABIERTO ES DE LA OBRA DEL CÁLCULO (v539)"
if h.count(ANCLA) != 1:
    raise SystemExit("ancla de sección no única")
h = h.replace(ANCLA, NOTA.strip() + "\n\n" + ANCLA)
escribir(CLAUDE, c)
escribir(HIST, h)
print("hecho")
