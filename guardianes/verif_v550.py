# -*- coding: utf-8 -*-
"""v550 · LA CIFRA DE UNA TARJETA KPI NO SE PARTE NUNCA.

Desde v549 los botones parten su texto (`wrap=True`) con `overflow-wrap: break-word`. Medido
en producción a 1024 px con el menú abierto: la tarjeta KPI se queda en 62 px (31 útiles) y
«0%» salía «0» / «%», «4 h» salía «4» / «h». La etiqueta y el pie ya se recortan con «…» a
propósito (v303); la CIFRA tiene que leerse entera. Probado antes con un estilo temporal en
producción: con `nowrap` las tres cifras vuelven a una línea y la tarjeta a 96 px.
"""
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


from core import theme                                            # noqa: E402

_css = theme._CSS


def regla(selector):
    i = _css.find(selector + " {")
    return _css[i:_css.find("}", i)] if i >= 0 else ""


print("1. La cifra, en una línea")
_num = regla('[class*="st-key-cpxkpi_"] button p:nth-child(2):not(:last-child)')
chk("se encontró la regla de la cifra (no es un paso en vacío)", "font-size:26px" in _num, _num)
chk("⚠️ la cifra no parte línea (`white-space: nowrap`)", "white-space: nowrap !important" in _num, _num)
chk("...ni parte palabras (`break-word` del modo wrap)",
    "word-break: keep-all !important" in _num and "overflow-wrap: normal !important" in _num, _num)

print("\n2. La etiqueta y el pie siguen recortándose con «…» (v303), sin partirse")
for _sel, _q in (('[class*="st-key-cpxkpi_"] button p:first-child:not(:last-child)', "etiqueta"),
                 ('[class*="st-key-cpxkpi_"] button p:last-child:not(:first-child)', "pie")):
    _r = regla(_sel)
    chk("%s: nowrap + elipsis" % _q, "white-space: nowrap" in _r and "text-overflow: ellipsis" in _r, _r)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
