# -*- coding: utf-8 -*-
"""v471 · las tablas editables, en las formas que `verif_v444` NO mira.

v444 vigila el `column_config` huérfano. Pero una tabla editable tiene DOS cosas más
que se desincronizan igual de callado cuando alguien renombra una clave — y v468 lo
hizo en las tres:

  1. la LECTURA del resultado  →  `_ed.iloc[i]["Hours"]` con la fila en "Horas" lanza
     **KeyError** y la pantalla revienta. Llevaba dos versiones así, invisible solo
     porque la demo está vacía.
  2. el `disabled`             →  la columna que debía estar bloqueada queda EDITABLE.
     Pasaba con las HORAS (vienen del fichaje) y con el COSTO de una cotización, que
     está congelado a propósito desde v355/v356.
  3. la CABECERA               →  una clave sin etiqueta se pinta cruda, en español,
     dentro de una tabla por lo demás inglesa (la sexta red de v450).

⚠️ Las tres sondas resuelven VARIABLES: casi ninguna de estas tablas construye su
DataFrame inline, y mirando solo dentro de la llamada 4 de 5 salían como huérfanas sin
serlo. Es el agujero del medidor de v450, y el mismo por el que v444 estaba verde.
⚠️ Y cada una se valida contra un caso conocido-bueno antes de creerse su cero.
"""
import ast
import io
import os
import re
import sys

sys.path.insert(0, os.path.abspath("."))

fallos, n_ok = [], 0


def ok(m, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % m)


def fallo(m, det=""):
    fallos.append(m)
    print("   FALLO %s%s" % (m, ("  -> " + str(det)) if det else ""))


def sec(t):
    print("\n%s" % t)


from core import tabla  # noqa: E402

GLOBAL = set(tabla.CABECERAS)
ESP = re.compile(r"[áéíóúñÁÉÍÓÚÑ]|^(Fecha|Estado|Tipo|Cliente|Horas|Costo|Nombre|Grupo|"
                 r"Unidad|Clase|Vence|Fragmentos|Contacto|Avance|Persona|Concepto|"
                 r"Precio|Ganancia|Ganas|Cant|Peso|Actividad|Orden|Nota|Riel|Elevador|"
                 r"Margen|D.as|Inicio|Fin)")


def _claves(nodo):
    out = set()
    for d in ast.walk(nodo):
        if isinstance(d, ast.Dict):
            for k in d.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    out.add(k.value)
    return out


def _tablas():
    """(fichero, linea, res, filas, disabled, etiquetas_locales) de cada tabla."""
    out = []
    for f in sorted(os.listdir("core")):
        if not f.endswith("_ui.py"):
            continue
        src = io.open("core/" + f, encoding="utf-8").read()
        a = ast.parse(src)
        for fn in [x for x in ast.walk(a) if isinstance(x, ast.FunctionDef)]:
            var = {}
            for nd in ast.walk(fn):
                if isinstance(nd, ast.Assign) and len(nd.targets) == 1 \
                   and isinstance(nd.targets[0], ast.Name):
                    k = _claves(nd.value)
                    if k:
                        var.setdefault(nd.targets[0].id, set()).update(k)
            for nd in ast.walk(fn):
                call, res = None, None
                if isinstance(nd, ast.Assign) and len(nd.targets) == 1 \
                   and isinstance(nd.targets[0], ast.Name) \
                   and isinstance(nd.value, ast.Call):
                    call, res = nd.value, nd.targets[0].id
                elif isinstance(nd, ast.Call):
                    call = nd
                if call is None or getattr(call.func, "attr", "") not in \
                        ("data_editor", "dataframe") or not call.args:
                    continue
                filas = _claves(call.args[0])
                for x in ast.walk(call.args[0]):
                    if isinstance(x, ast.Name) and x.id in var:
                        filas |= var[x.id]
                if not filas:
                    continue
                dis, loc = set(), set()
                for kw in call.keywords:
                    if kw.arg == "disabled" and isinstance(kw.value, ast.List):
                        dis = {x.value for x in kw.value.elts
                               if isinstance(x, ast.Constant)}
                    if kw.arg == "column_config":
                        for d in ast.walk(kw.value):
                            if isinstance(d, ast.Dict):
                                for k, v in zip(d.keys, d.values):
                                    if isinstance(k, ast.Constant) \
                                       and isinstance(v, ast.Call) and v.args:
                                        loc.add(k.value)
                        for x in ast.walk(kw.value):
                            if isinstance(x, ast.Name) and x.id in var:
                                loc |= var[x.id]
                out.append((f, call.lineno, res, filas, dis, loc, fn))
    return out


# ── 1 ─────────────────────────────────────────────────────────────────────────
sec("1. Ninguna LECTURA del resultado usa una clave que la fila no tiene")


def lecturas_rotas():
    mal = []
    for f, ln, res, filas, _d, _l, fn in _tablas():
        if not res:
            continue
        # ⚠️ v499: el código real suele hacer `r = _edited.iloc[i]` y luego `r["Peso"]`.
        # La sonda solo miraba la forma directa `_edited.iloc[i]["Peso"]`, así que el
        # `KeyError` del guardado de actividades (leía «Weight» y «Order», que son las
        # ETIQUETAS) pasó por delante. Se sigue UN nivel de alias.
        alias = {res}
        for a in ast.walk(fn):
            if isinstance(a, ast.Assign) and len(a.targets) == 1 and isinstance(a.targets[0], ast.Name):
                txt = ast.unparse(a.value)
                if txt.startswith(f"{res}.iloc") or txt.startswith(f"{res}.loc")                         or txt == res:
                    alias.add(a.targets[0].id)
        for sub in ast.walk(fn):
            if not (isinstance(sub, ast.Subscript)
                    and isinstance(sub.slice, ast.Constant)
                    and isinstance(sub.slice.value, str)):
                continue
            b, nom = sub.value, ""
            if isinstance(b, ast.Name):
                nom = b.id
            elif isinstance(b, ast.Subscript) and isinstance(b.value, ast.Attribute) \
                    and isinstance(b.value.value, ast.Name):
                nom = b.value.value.id
            if nom in alias and sub.slice.value not in filas:
                mal.append("%s:%d lee %r y la fila tiene %s"
                           % (f, sub.lineno, sub.slice.value, sorted(filas)[:5]))
    return sorted(set(mal))


_r = lecturas_rotas()
(ok if not _r else fallo)("0 lecturas por una clave inexistente (seria KeyError)", _r)


# ── 2 ─────────────────────────────────────────────────────────────────────────
sec("2. Ningun `disabled` apunta a una columna que no existe")


def disabled_rotos():
    mal = []
    for f, ln, _r_, filas, dis, _l, _fn in _tablas():
        h = sorted(dis - filas)
        if h:
            mal.append("%s:%d disabled=%s no existe (quedaria EDITABLE)" % (f, ln, h))
    return sorted(set(mal))


_d = disabled_rotos()
(ok if not _d else fallo)("0 columnas que se creen bloqueadas y no lo esten", _d)


# ── 3 ─────────────────────────────────────────────────────────────────────────
sec("3. Ninguna cabecera se pinta con su clave CRUDA en español")


def cabeceras_crudas():
    mal = []
    for f, ln, _r_, filas, _d_, loc, _fn in _tablas():
        for k in sorted(filas):
            if k not in GLOBAL and k not in loc and ESP.search(k):
                mal.append("%s:%d  %r" % (f, ln, k))
    return sorted(set(mal))


_c = cabeceras_crudas()
(ok if not _c else fallo)("0 cabeceras crudas en español", _c)


# ── 4 ─────────────────────────────────────────────────────────────────────────
sec("4. Las tres sondas VEN un caso conocido-bueno (si no, su cero no vale)")
# ⚠️ Sin esto, un cero no significa nada: `verif_v444` daba 0 con dos huerfanas
# delante (trampa nº12). Se rompe a proposito y se restaura.
PRUEBAS = [
    ("lectura", "core/quotes_ui.py", 'ed.iloc[i]["Cant."]', 'ed.iloc[i]["Qty"]',
     lecturas_rotas),
    ("disabled", "core/quotes_ui.py", 'disabled=["Concepto", "Costo"',
     'disabled=["Concepto", "Cost"', disabled_rotos),
    ("cabecera", "core/tabla.py", '    "Riel": "Rail",\n', "", cabeceras_crudas),
]
for etq, fich, viejo, nuevo, sonda in PRUEBAS:
    orig = io.open(fich, encoding="utf-8").read()
    if orig.count(viejo) != 1:
        fallo("la sonda de %s no se pudo validar: ancla ausente" % etq)
        continue
    try:
        io.open(fich, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        # ⚠️ `tabla` se relee del disco para la sonda de cabecera
        if etq == "cabecera":
            import importlib
            importlib.reload(tabla)
            GLOBAL = set(tabla.CABECERAS)
        visto = sonda()
    finally:
        io.open(fich, "w", encoding="utf-8", newline="").write(orig)
        if etq == "cabecera":
            import importlib
            importlib.reload(tabla)
            GLOBAL = set(tabla.CABECERAS)
    (ok if visto else fallo)("la sonda de %s ve el caso conocido-bueno" % etq,
                             "no lo ve: su cero no significaria nada")

print("")
if fallos:
    print("HAY FALLOS: %d de %d" % (len(fallos), len(fallos) + n_ok))
    sys.exit(1)
print("TODO OK - %d comprobaciones" % n_ok)
