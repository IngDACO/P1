"""¿Que hay DENTRO de CLAUDE.md? Reparto por bloques, para decidir con numeros."""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
lineas = io.open(P, encoding="utf-8").read().splitlines()
print(f"{len(lineas):,} lineas · {sum(len(x) + 1 for x in lineas) / 1024:,.0f} KB\n")

# secciones de nivel 2
secs, act = [], None
for i, l in enumerate(lineas):
    if l.startswith("## "):
        if act:
            act[2] = i
        act = [l[3:].strip(), i, len(lineas)]
        secs.append(act)
if act:
    act[2] = len(lineas)

tabla = [s for s in secs if s[0].startswith("Versiones desplegadas")]
n_tabla = sum(s[2] - s[1] for s in tabla)
filas = [l for l in lineas if re.match(r"^\|\s*v\d+\s*\|", l)]

print(f"tabla de versiones : {n_tabla:>5} lineas  ({len(filas)} filas)")
print(f"resto (secciones)  : {len(lineas) - n_tabla:>5} lineas  ({len(secs) - len(tabla)} secciones)\n")

# secciones que describen codigo que YA NO EXISTE
muertas = [s for s in secs
           if re.search(r"REVERTID|REEMPLAZAD|se elimina|se ELIMIN|ya no existe|YA NO EXISTE",
                        "\n".join(lineas[s[1]:s[2]]), re.I)]
print(f"secciones que hablan de codigo revertido/eliminado: {len(muertas)}")
for n, a, b in sorted(muertas, key=lambda s: s[1] - s[2])[:8]:
    print(f"   {b - a:>4} lineas · {n[:78]}")
print(f"   -> suman {sum(b - a for _n, a, b in muertas):,} lineas\n")

print("las 10 secciones mas largas:")
for n, a, b in sorted(secs, key=lambda s: s[1] - s[2])[:10]:
    print(f"   {b - a:>4} lineas · {n[:78]}")
