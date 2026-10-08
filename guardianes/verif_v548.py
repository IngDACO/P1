# -*- coding: utf-8 -*-
"""v548 · SEGUNDA TANDA DEL BARRIDO: CONTROLES DENTRO DE FUNCIONES AUXILIARES.

Recorriendo la app en producción tras v547, «Create field user» (Planning · Users) seguía sin
clave: sus controles están en `_crear_usuario_form`, y el barrido —y su guardián— solo miraban
las llamadas DIRECTAS del cuerpo del desplegable. Siguiendo las funciones salieron 11: los dos
«Create field user», el «Upload drawing» de las 4 herramientas, dos de Contabilidad, la
ubicación y la ganancia de la obra (que se abren solos según los datos) y el plan semanal
del campo. Y, de paso, las claves de «Progress claims» y de la entrega se hacen distintas
entre sí (compartían el esquema `{key_prefix}_exp_{pid}`; hoy no chocaban, por prefijo).
"""
import ast
import io
import os
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
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


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


def claves(f, trozo):
    """Las `key=` de los desplegables de `f` cuya etiqueta contiene `trozo`."""
    out = []
    for n in ast.walk(ast.parse(_fuente(f))):
        if (isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "expander" and n.args
                and trozo in ast.unparse(n.args[0])):
            k = next((kw.value for kw in n.keywords if kw.arg == "key"), None)
            out.append(ast.unparse(k) if k is not None else None)
    return out


print("1. Los 11 con los controles en una función auxiliar llevan clave")
for f, trozo, n in (("core/auth_ui.py", "Create field user", 2),
                    ("core/belting_ui.py", "Upload it here", 1),
                    ("core/buffer_cut_ui.py", "Upload it here", 1),
                    ("core/plumb_ui.py", "Upload it here", 1),
                    ("core/rail_cut_ui.py", "Upload it here", 1),
                    ("core/contable_ui.py", "Payroll names", 1),
                    ("core/contable_ui.py", "Chart of accounts", 1),
                    ("core/projects_ui.py", "Location on the map", 1),
                    ("core/projects_ui.py", "How much you make", 1),
                    ("core/projects_ui.py", "the whole crew", 1)):
    _k = claves(f, trozo)
    chk("%s «%s»: %d con clave" % (os.path.basename(f), trozo, n),
        len(_k) == n and all(_k), _k)
_cf = claves("core/auth_ui.py", "Create field user")
chk("los dos «Create field user» (ramas excluyentes) con claves DISTINTAS",
    len(set(_cf)) == 2, _cf)

print("\n2. Los que se abren solos según los datos llevan la condición en la clave")
chk("la ubicación: «se abre si la obra no tiene coordenadas»",
    "not location_ui.to_float(prj.get('Lat'))" in (claves("core/projects_ui.py",
                                                          "Location on the map")[0] or ""))
chk("la ganancia: «se abre si no hay ganancia o va a costo»",
    "bool(rev.get('sin_ganancia')) or _a_costo" in (claves("core/projects_ui.py",
                                                           "How much you make")[0] or ""))

print("\n3. «Progress claims» y la entrega no pueden chocar aunque compartan prefijo")
_cl = claves("core/claims_ui.py", "request_quote")
_ho = claves("core/handover_ui.py", "inventory")
_ev = lambda tpl: eval(tpl, {}, {"key_prefix": "x", "pid": "PRJ-1"})   # noqa: E731
chk("con el MISMO key_prefix y la misma obra dan claves distintas",
    _cl and _ho and _ev(_cl[0]) != _ev(_ho[0]), (_cl, _ho))

print("\n4. El guardián del barrido (v547, ampliado) en verde sobre el código real")
r = subprocess.run([sys.executable, os.path.join(AQUI, "verif_v547.py")], cwd=RAIZ,
                   capture_output=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                   timeout=300)
chk("verif_v547 (sigue las funciones auxiliares) pasa", r.returncode == 0,
    r.stdout.decode("utf-8", "replace")[-400:])

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
