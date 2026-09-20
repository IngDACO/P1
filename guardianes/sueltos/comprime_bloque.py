# =====================================================================
# HISTORICO - NO SE PUEDE EJECUTAR (marcado el 20/09/2026)
#
# Apunta al scratchpad temporal de la sesion 1734b676..., que ya no existe,
# y ademas opera sobre ficheros intermedios de aquella tanda que tampoco
# existen: era una transformacion de un solo uso, ya aplicada.
#
# Se conserva como RASTRO de como se hizo aquel cambio, no como herramienta.
# Arreglarle la ruta no lo haria funcionar: lo que leia ya no esta.
# =====================================================================
"""Sustituye el bloque v102-v130 de CLAUDE.md por su version comprimida.

⚠️ Por defecto va EN SECO: dice que se perderia y no escribe. Con --apply escribe
(dejando respaldo). El chequeo no es "parece bien": se extrae CADA span de codigo
`asi` del texto viejo y se comprueba que siga existiendo en el documento nuevo. Lo
que no sobreviva se lista para decidirlo A MANO, no para asumirlo.
"""
import io
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = r"C:\Users\diego\P1\CLAUDE.md"
NUEVO = (r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
         r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad\bloque_v102_v130.md")
APLICAR = "--apply" in sys.argv

L = io.open(DOC, encoding="utf-8").read().splitlines()
ini = next(i for i, l in enumerate(L) if l.startswith("## Herramientas de calculo, parte 2"))
fin = next(i for i, l in enumerate(L) if l.startswith("## HOME del admin"))
viejo = L[ini:fin]
nuevo = io.open(NUEVO, encoding="utf-8").read().splitlines()

print(f"bloque viejo: {len(viejo)} lineas  ->  nuevo: {len(nuevo)} lineas "
      f"({len(viejo) - len(nuevo)} menos, {(1 - len(nuevo) / len(viejo)) * 100:.0f}% del bloque)")
print(f"documento: {len(L)} -> {len(L) - len(viejo) + len(nuevo)} lineas\n")

doc_nuevo = L[:ini] + nuevo + L[fin:]
texto_nuevo = "\n".join(doc_nuevo)
texto_viejo_bloque = "\n".join(viejo)

# --- lo que NO puede desaparecer: cada span de codigo del bloque viejo --------
spans = set(re.findall(r"`([^`\n]{2,60})`", texto_viejo_bloque))


def nucleo(s):
    """El IDENTIFICADOR del span: `_do_calculo()` y `_do_calculo` son lo mismo.

    ⚠️ Comparar el span literal sobre-avisa (128 falsos «perdidos» en la 1a pasada)
    y empuja a inflar el texto nuevo sin motivo. Una sonda que grita de mas es tan
    inutil como una que calla de mas.
    """
    s = s.split("(")[0].split("[")[0].split(" ")[0].strip()
    return s.rstrip(".,:;`")


perdidos = []
for s in spans:
    n = nucleo(s)
    if len(n) < 3 or not re.match(r"^[\w./_]+$", n):
        continue                              # trozos de frase, no identificadores
    if n not in texto_nuevo:
        perdidos.append((n, s))
perdidos = sorted(set(perdidos))
print(f"== identificadores del bloque viejo · NO sobreviven {len(perdidos)} ==")
for n, s in perdidos:
    ln = next((i for i, l in enumerate(viejo) if f"`{s}`" in l), 0)
    print(f"   {n:<40} {viejo[ln].strip()[:80]}")

# --- y cada linea con ⚠️ o REGLA debe tener eco -------------------------------
print("\n== avisos ⚠️ / REGLA del bloque viejo ==")
crit = [l.strip() for l in viejo if "⚠️" in l or re.search(r"\bREGLA\b", l)]
print(f"   {len(crit)} en el viejo · {sum(1 for l in nuevo if '⚠️' in l or 'v1' in l)} lineas marcadas en el nuevo")

if APLICAR:
    shutil.copy2(DOC, DOC + ".bak")
    io.open(DOC, "w", encoding="utf-8", newline="\n").write(texto_nuevo + "\n")
    print(f"\nESCRITO. Respaldo en {DOC}.bak")
else:
    print("\n(en seco: no se ha escrito nada — repetir con --apply)")
