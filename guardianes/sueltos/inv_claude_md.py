"""Inventario de CLAUDE.md para decidir QUE se comprime, con numeros.

Clasifica cada seccion de nivel 2 por la version MAS ALTA que menciona su titulo.
- sin version en el titulo -> REFERENCIA (modulos, formulas, geometria): NO se toca.
- version <= 130            -> narrativa antigua: candidata a comprimir.
"""
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"
L = io.open(P, encoding="utf-8").read().splitlines()

secs = []
for i, l in enumerate(L):
    if l.startswith("## "):
        secs.append([l[3:].strip(), i, None])
for k, s in enumerate(secs):
    s[2] = secs[k + 1][1] if k + 1 < len(secs) else len(L)


def vers(t):
    return [int(x) for x in re.findall(r"\bv(\d{1,3})\b", t)]


ref, viejas, nuevas = [], [], []
for n, a, b in secs:
    vs = vers(n)
    if not vs:
        ref.append((n, a, b))
    elif max(vs) <= 130:
        viejas.append((n, a, b))
    else:
        nuevas.append((n, a, b))


def resumen(nom, xs):
    print(f"{nom:<28} {len(xs):>3} secciones · {sum(b - a for _n, a, b in xs):>5} lineas")


resumen("REFERENCIA (no se toca)", ref)
resumen("narrativa <= v130", viejas)
resumen("narrativa > v130", nuevas)

print("\n== candidatas (narrativa <= v130), por tamano ==")
for n, a, b in sorted(viejas, key=lambda s: s[1] - s[2]):
    txt = "\n".join(L[a:b])
    print(f"  {b - a:>4} ln · {len(re.findall('⚠️', txt)):>2}⚠️ · L{a + 1:<5} {n[:76]}")

print("\n== REFERENCIA, para confirmar que no me llevo nada por delante ==")
for n, a, b in sorted(ref, key=lambda s: s[1] - s[2])[:16]:
    print(f"  {b - a:>4} ln · {n[:76]}")
