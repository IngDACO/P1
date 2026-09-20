"""Lo que NO puede perderse al comprimir el bloque v102-v130.

Antes de reescribir nada: sacar TODA linea con ⚠️ o con la palabra REGLA/regla,
mas los titulos. Si un concepto no aparece en el texto nuevo ni en otra parte del
documento, es que lo he perdido — y eso se comprueba despues, no se supone.
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
L = io.open(P, encoding="utf-8").read().splitlines()

# limites del bloque: de la seccion v130 hasta la ultima <= v130 seguida
ini = next(i for i, l in enumerate(L) if l.startswith("## Herramientas de calculo, parte 2"))
fin = next(i for i, l in enumerate(L) if l.startswith("## HOME del admin"))
print(f"bloque: L{ini + 1} .. L{fin}  ({fin - ini} lineas)\n")

secciones = [(i, l) for i, l in enumerate(L[ini:fin], start=ini) if l.startswith("## ")]
print(f"{len(secciones)} secciones:")
for i, l in secciones:
    print(f"   L{i + 1:<5} {l[3:][:88]}")

bloque = L[ini:fin]
avisos = [l.strip() for l in bloque if "⚠️" in l]
reglas = [l.strip() for l in bloque
          if re.search(r"\bREGLA\b|\bRegla\b|\bregla\b", l) and "⚠️" not in l]

print(f"\n== {len(avisos)} lineas con ⚠️ ==")
for a in avisos:
    print(f"   {a[:150]}")

print(f"\n== {len(reglas)} lineas con REGLA (sin ⚠️) ==")
for r in reglas:
    print(f"   {r[:150]}")
