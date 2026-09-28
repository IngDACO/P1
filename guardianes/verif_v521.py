# -*- coding: utf-8 -*-
"""v521 · LA TARJETA «MODELS» CUENTA MODELOS, NO FILAS DEL CATÁLOGO.

Tras cargar la biblioteca (v520) el catálogo tenía dos filas —«Schindler» y «Sematic»,
las dos SIN modelo— y la tarjeta decía «Models 2» con cero modelos, mientras el
desplegable de modelos no ofrecía ninguno. Una marca sin modelo es un estado LEGÍTIMO
(`SIN_MODELO`), así que el fallo no estaba en el dato sino en contar filas.

Lo que protege:
  (a) que una fila con marca y sin modelo NO cuente como modelo — con el catálogo que
      hay HOY en producción el número es 0;
  (b) que sí cuenten los modelos de verdad, sin duplicados y sin los desactivados;
  (c) ⚠️ que la tarjeta y el desplegable digan LO MISMO: cuentan con el mismo criterio,
      así que no pueden volver a contradecirse;
  (d) que la tarjeta de la pantalla lea ese número (si leyera otro, el arreglo no
      llegaría a verse).
Todo EJECUTANDO `resumen()` con el catálogo sustituido: importar no ejecuta (v378).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "owner", "grupo": ""}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s %s" % (q, ("-> %s" % (det,)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("")
    print(x)


from core import library as LIB                                   # noqa: E402

_cat = []
LIB._modelos_records = lambda: list(_cat)
LIB._records = lambda: []


def fila(b, m, a="SI"):
    return {"Brand": b, "Model": m, "Active": a}


def ofrecidos():
    """Lo que ofrece el desplegable: los modelos de cada marca, como en `_barra`."""
    return sum(len(LIB.modelos_de(b)) for b in LIB.marcas())


# ═════════════════════════════════════════════════════════════════
sec("1. Una marca sin modelo NO es un modelo (el catálogo de HOY en producción)")
_cat[:] = [fila("Schindler", ""), fila("Sematic", "")]
r = LIB.resumen()
chk("dos marcas", r["marcas"] == 2, r["marcas"])
chk("…y CERO modelos (antes salía 2)", r["modelos"] == 0, r["modelos"])

# ═════════════════════════════════════════════════════════════════
sec("2. Los modelos de verdad sí cuentan: sin duplicados y sin desactivados")
_cat[:] = [fila("Schindler", ""), fila("Sematic", ""),
           fila("Schindler", "ES1"), fila("Schindler", "ES5.0"),
           fila("Schindler", "ES1"),                      # repetido
           fila("KONE", "MonoSpace", "NO")]               # desactivado
r = LIB.resumen()
chk("dos modelos (ES1 y ES5.0): ni el repetido ni el desactivado", r["modelos"] == 2,
    r["modelos"])
chk("las marcas siguen sin contar la desactivada", r["marcas"] == 2, r["marcas"])
_cat[:] = [fila("Schindler", "ES1"), fila("KONE", "MonoSpace")]
chk("un modelo por marca, dos marcas → 2", LIB.resumen()["modelos"] == 2,
    LIB.resumen()["modelos"])
_cat[:] = []
chk("catálogo vacío → 0 (sin reventar)", LIB.resumen()["modelos"] == 0)

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ La tarjeta y el desplegable dicen lo mismo")
for _caso in ([fila("Schindler", ""), fila("Sematic", "")],
              [fila("Schindler", "ES1"), fila("Schindler", ""), fila("Sematic", "S2")],
              [fila("A", "x"), fila("A", "y"), fila("B", "x", "NO"), fila("C", "")]):
    _cat[:] = _caso
    chk("tarjeta %d = desplegable %d" % (LIB.resumen()["modelos"], ofrecidos()),
        LIB.resumen()["modelos"] == ofrecidos())

# ═════════════════════════════════════════════════════════════════
sec("4. La tarjeta de la pantalla lee ese número")
_a = ast.parse(io.open("core/library_ui.py", encoding="utf-8").read())
_lee = []
for n in ast.walk(_a):
    if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "kpi_row":
        for x in ast.walk(n):
            if isinstance(x, ast.Subscript) and isinstance(x.slice, ast.Constant):
                _lee.append(x.slice.value)
chk("se encontró la fila de tarjetas (si no, esto pasaría en vacío)", bool(_lee), _lee)
chk("la tarjeta «Models» lee resumen()['modelos']", "modelos" in _lee, _lee)

print("")
print("=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "HAY FALLOS" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
