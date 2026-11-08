# -*- coding: utf-8 -*-
"""v653 · Barrido: un DATO de la hoja metido en HTML (o en el marcado de un PDF) sin escapar.

Módulo de apoyo de `verif_v653` (y de su batería): solo lee el fuente de la app.

## Qué mira
Toda función de `survey_app` que arme texto con marcado (una cadena con «<» o «style=»):
f-strings, concatenaciones con `+`, `%` y `.format()`. Un trozo interpolado es SOSPECHOSO si:
- es un acceso a un campo de la hoja: `x.get("Campo")`, `x["Campo"]` (nombre de columna:
  mayúscula y minúsculas, «Name», «ExpiryDate»; los parámetros técnicos van EN MAYÚSCULAS);
- o es una variable a la que, EN ESA MISMA FUNCIÓN, se le asignó algo que contiene uno
  (por cadenas: `a = r.get("Client")`, `b = str(a).strip()`, `c = f"{b} · …"` → las tres);
y NO pasa por un escapador (un nombre con «esc», «escape», «quote» o «literal»), por una
conversión que solo puede dar números o fechas, ni por un constructor que escapa por dentro.

## Lo que NO ve (trampa 30: su «0» es «0 de lo que esta red ve»)
- un dato que llega por PARÁMETRO (la función no sabe de dónde viene): por eso los
  constructores de HTML que reciben texto (`theme.kpi_row`, `maps_link_html`…) escapan DENTRO.
- un dato guardado en `session_state` o devuelto por otra función que lo lee de la hoja.
La red de fondo es escapar en el constructor; esto vigila los sitios que arman HTML con datos.
"""
import ast
import os

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "survey_app"))

# conversiones que no pueden dejar pasar marcado (números, fechas, importes, colores validados)
SEGURAS = {"int", "float", "round", "len", "abs", "bool", "_num", "num", "dinero", "dinero_html",
           "_money", "money", "_horas_txt", "_ddmm", "_dmy", "dmy", "_fmt_fecha", "_fecha", "_fdma",
           "_hhmm", "_hm", "strftime", "_n", "_n0", "_m1", "_pct", "pct", "fstr", "fv",
           "color_seguro", "_texto_sobre", "isoformat", "maps_url", "solo_digitos"}

# constructores que ESCAPAN lo que reciben por dentro (comprobado al escribir esto, v653):
# `_kpi_card` → `theme.kpi_row` (`theme._esc`); `kpi_row`, `chip`, `section` (`theme._esc`);
# `_MI` (solo icono y color del código); los SVG escapan sus textos (`schedule._esc`,
# `expenses._esc`, `texto_svg.escape` en las plomadas); `maps_link_html` (v603).
CONSTRUCTORES = {"_kpi_card", "kpi_row", "chip", "section", "_MI", "schedule_svg", "spend_svg",
                 "plumb_svg", "plumb_iso_svg", "plumb_detail_svg", "plumb_card_svg",
                 "maps_link_html", "belting_svg", "buffer_cut_svg", "rail_cut_svg",
                 "floor_plan_svg", "shaft_iso_svg"}      # los cinco últimos: `texto_svg.cabe` (v590)

# ⚠️ Los parámetros del Survey van EN MAYÚSCULAS, y estos cinco son TEXTO que teclea la oficina
# (`survey_ui`: proyecto, ingeniero, cliente, ubicación; el modelo, del plano o a mano).
CAMPOS_TEXTO_MAYUS = {"PROYECTO", "CLIENTE", "UBICACION", "INGENIERO", "MODELO"}


# Las funciones que arman el texto de un AVISO (correo y Telegram) lo mandan por
# `notify.notify_user`, que lo escapa TODO y devuelve solo las etiquetas de la app
# (`notify.html_seguro`, v603). No se escapan aquí a propósito: se escaparía dos veces.
# ⚠️ `por_aviso_comprobado()` exige que cada una SIGA llamando a `notify_user`.
POR_AVISO = {("core/notify.py", "notify_assignment"), ("core/credentials.py", "notify_expiring"),
             ("core/ausencias_ui.py", "_avisar_cancelacion"), ("core/ausencias_ui.py", "_avisar_exceso"),
             ("core/ausencias_ui.py", "_avisar_persona"), ("core/ausencias_ui.py", "_avisar_persona_cancelada")}


def por_aviso_comprobado(fuentes=None) -> dict:
    """{(fichero, función): ¿llama a notify_user?} — para que la lista de arriba no se pudra."""
    out = {}
    for rel, fn in POR_AVISO:
        src = (fuentes or {}).get(rel) or open(os.path.join(RAIZ, rel), encoding="utf-8").read()
        f = next((n for n in ast.walk(ast.parse(src))
                  if isinstance(n, ast.FunctionDef) and n.name == fn), None)
        out[(rel, fn)] = bool(f) and any(isinstance(c, ast.Call) and _nombre(c) == "notify_user"
                                         for c in ast.walk(f))
    return out


def _nombre(call):
    f = call.func
    return f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")


def es_escapador(n: str) -> bool:
    n = n.lower()
    return any(k in n for k in ("esc", "escape", "quote", "literal"))


def _es_campo(k) -> bool:
    """Un nombre de columna de la hoja: «Name», «Client», «ExpiryDate» (mayúscula + minúsculas).
    Los parámetros técnicos van EN MAYÚSCULAS («BS», «WALL_STOP», «V1») y no son texto de nadie."""
    return isinstance(k, str) and ((k[:1].isupper() and any(c.islower() for c in k))
                                   or k in CAMPOS_TEXTO_MAYUS)


def _base_constante(e) -> bool:
    """`styles["UBody"]` (hojas de estilo del PDF) y `_COL["Note"]` / `ESTADOS[x]` (mapas fijos
    del código, en mayúsculas) no son registros de la hoja."""
    if isinstance(e, ast.Name):
        return e.id == "styles" or e.id.strip("_").isupper()
    return False


def es_registro(e) -> bool:
    """`x.get("Campo"…)` o `x["Campo"]` (un campo de la hoja por su nombre)."""
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr == "get" \
            and e.args and isinstance(e.args[0], ast.Constant) and _es_campo(e.args[0].value) \
            and not _base_constante(e.func.value):
        return True
    if isinstance(e, ast.Subscript) and isinstance(e.slice, ast.Constant) \
            and _es_campo(e.slice.value) and not _base_constante(e.value):
        return True
    return False


def limpio(e, sucios) -> bool:
    """¿El valor de esta expresión ya no puede llevar marcado de un dato?"""
    if isinstance(e, ast.Constant):
        return True
    if isinstance(e, ast.Call):
        n = _nombre(e)
        if es_escapador(n) or n in SEGURAS or n in CONSTRUCTORES:
            return True
    if isinstance(e, ast.Name):
        return e.id not in sucios
    if es_registro(e):
        return False
    if isinstance(e, ast.JoinedStr):
        return all(limpio(v.value, sucios) for v in e.values if isinstance(v, ast.FormattedValue))
    if isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add):
        return limpio(e.left, sucios) and limpio(e.right, sucios)
    if isinstance(e, ast.BinOp):
        return True                        # aritmética: un número
    if isinstance(e, ast.IfExp):
        return limpio(e.body, sucios) and limpio(e.orelse, sucios)
    if isinstance(e, ast.BoolOp):
        return all(limpio(v, sucios) for v in e.values)
    if isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr == "get":
        # `mapa.get(clave)`: sale el VALOR del mapa, no la clave (una clave sucia no ensucia
        # lo que devuelve); un campo de la hoja ya se vio arriba
        return limpio(e.func.value, sucios) and all(limpio(a, sucios) for a in e.args[1:])
    if isinstance(e, ast.Call):
        # str(x), x.strip(), " ".join(...), x or "—"… heredan lo de dentro
        hijos = list(e.args) + [k.value for k in e.keywords]
        if isinstance(e.func, ast.Attribute):
            hijos.append(e.func.value)
        return all(limpio(h, sucios) for h in hijos)
    if isinstance(e, ast.Subscript) and not isinstance(e.slice, ast.Constant):
        return limpio(e.value, sucios)     # `mapa[clave]`: como `.get(clave)`
    if isinstance(e, (ast.Attribute, ast.Subscript)):
        return limpio(e.value, sucios)     # `d["clave"]` en minúsculas: dato interno
    if isinstance(e, (ast.List, ast.Tuple)):
        return all(limpio(x, sucios) for x in e.elts)
    if isinstance(e, ast.Dict):
        return all(limpio(v, sucios) for v in e.values if v is not None)
    if isinstance(e, (ast.GeneratorExp, ast.ListComp)):
        return limpio(e.elt, sucios)
    return True


def _tiene_marcado(n) -> bool:
    for s in ast.walk(n):
        if isinstance(s, ast.Constant) and isinstance(s.value, str) and ("<" in s.value or "style=" in s.value):
            return True
    return False


def _hojas_suma(n):
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
        return _hojas_suma(n.left) + _hojas_suma(n.right)
    return [n]


def _sucios_de(fun) -> set:
    """Variables a las que se asigna algo con un campo de la hoja sin escapar (punto fijo)."""
    asign = []
    for n in ast.walk(fun):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            asign.append((n.targets[0].id, n.value))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            asign.append((n.target.id, n.value))
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            asign.append((n.target.id, n.value))
        elif isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Tuple) \
                and isinstance(n.value, ast.Tuple) and len(n.value.elts) == len(n.targets[0].elts):
            for tg, v in zip(n.targets[0].elts, n.value.elts):
                if isinstance(tg, ast.Name):
                    asign.append((tg.id, v))
    sucios = set()
    while True:
        antes = len(sucios)
        for nom, v in asign:
            if nom in sucios:
                continue
            hay = any(es_registro(s) for s in ast.walk(v)) or any(
                isinstance(s, ast.Name) and s.id in sucios for s in ast.walk(v))
            if hay and not limpio(v, sucios):
                sucios.add(nom)
        if len(sucios) == antes:
            return sucios


def barrer(fuentes=None):
    """{(fichero, línea, función, expresión)} de los trozos sospechosos.

    `fuentes`: {ruta relativa: texto} para barrer EN MEMORIA (las roturas de la batería);
    sin él, se leen los ficheros de la app."""
    if fuentes is None:
        fuentes = {}
        for dp, _dn, fn in os.walk(RAIZ):
            if "__pycache__" in dp:
                continue
            for f in fn:
                if f.endswith(".py"):
                    p = os.path.join(dp, f)
                    fuentes[os.path.relpath(p, RAIZ).replace("\\", "/")] = open(p, encoding="utf-8").read()
    out = set()
    for rel, src in fuentes.items():
        arbol = ast.parse(src)
        for fun in [n for n in ast.walk(arbol) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if (rel, fun.name) in POR_AVISO:
                continue
            sucios = _sucios_de(fun)
            for n in ast.walk(fun):
                cand = []
                if isinstance(n, ast.JoinedStr) and _tiene_marcado(n):
                    cand = [v.value for v in n.values if isinstance(v, ast.FormattedValue)]
                elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add) and _tiene_marcado(n):
                    cand = [h for h in _hojas_suma(n) if not isinstance(h, (ast.Constant, ast.JoinedStr))]
                elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and _tiene_marcado(n.left):
                    cand = list(n.right.elts) if isinstance(n.right, ast.Tuple) else [n.right]
                elif isinstance(n, ast.Call) and _nombre(n) == "format" and isinstance(n.func, ast.Attribute) \
                        and _tiene_marcado(n.func.value):
                    cand = list(n.args) + [k.value for k in n.keywords]
                elif isinstance(n, ast.Call) and _nombre(n) == "Paragraph" and n.args:
                    # el 1er argumento de un `Paragraph` de reportlab ES marcado, lleve «<» o no
                    cand = [n.args[0]]
                for e in cand:
                    if not limpio(e, sucios):
                        out.add((rel, getattr(e, "lineno", n.lineno), fun.name, ast.unparse(e)[:100]))
    return out


if __name__ == "__main__":
    r = sorted(barrer())
    print(len(r), "sospechosos")
    for x in r:
        print(f"  {x[0]}:{x[1]}  {x[2]}: {x[3]}")
