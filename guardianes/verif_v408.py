"""v408: lo que se ve PRIMERO en la cartera, y el aviso que no señala al vacío.

Dos afirmaciones, escritas sobre el PRINCIPIO y no sobre la forma (regla v392), para que
no caduquen si mañana se añade una columna o se retoca una frase:

  (a) En `Proyectos · Lista`, las tres señales de atención (`Sin facturar`, `Situación`,
      `Alertas`) van ANTES que el contexto (`Cliente`, `Tipo`, `Inicio`, `Fin`, `Ppto`),
      y las dos de identidad (`ID`, `Proyecto`) van `pinned`.
      ⚠️ Se comprueba por AST sobre el código SIN comentarios: mis propios comentarios
      nombran esas columnas y un grep las contaría como uso (trampa nº2, que ya ha
      mordido cinco veces).

  (b) El aviso de duplicado del Pre-Start (v407) NO puede decir «fírmalo arriba» salvo
      cuando el bloque de firma se está pintando de verdad — es decir, la rama que lo
      dice tiene que colgar de `_pf`, no de `_ya_hoy`.
"""
import ast
import io
import sys
import tokenize


def _cc_dict(v):
    """El dict de `column_config`, venga literal o por `tabla.cfg(None, {...})`.

    ⚠️ v450 movió la configuración a `tabla.cfg`, que traduce la CABECERA sin tocar la
    clave. Sin resolverlo, un chequeo que solo entiende `ast.Dict` deja de mirar todas
    las tablas y devuelve 0 — que parece un aprobado y no lo es.
    """
    import ast as _a
    if isinstance(v, _a.Call) and getattr(v.func, "attr", "") == "cfg":
        v = v.args[1] if len(v.args) > 1 else None
    return v if isinstance(v, _a.Dict) else None
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def sin_comentarios(src: str) -> str:
    """Quita comentarios y docstrings: un comentario NO es un uso (trampa nº2)."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            out.append(tok)
        return tokenize.untokenize(out)
    except Exception:
        return src


def fn_de(arbol, nombre):
    for n in ast.walk(arbol):
        if isinstance(n, ast.FunctionDef) and n.name == nombre:
            return n
    return None


# ── (a) La cartera ────────────────────────────────────────────────────────────
print("== a) Proyectos · Lista: lo que necesita atención va primero ==")
src = (RAIZ / "core" / "projects_ui.py").read_text(encoding="utf-8")
arb = ast.parse(sin_comentarios(src))
f = fn_de(arb, "_cartera_lista")
chk("existe `_cartera_lista`", f is not None)

# El orden de columnas es el orden de claves del dict que se le pasa a `_rows.append`.
claves = []
for n in ast.walk(f):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
            and n.func.attr == "append" and n.args and isinstance(n.args[0], ast.Dict):
        claves = [k.value for k in n.args[0].keys if isinstance(k, ast.Constant)]
        break
chk("se localiza el dict de la fila", bool(claves))
print(f"         orden real: {claves}")

# ⚠️ CADUCADO por v440/v444 (i18n): las columnas pasaron al inglés a propósito. La
# regla —toda señal de atención antes que todo contexto— no depende del idioma, así
# que se resuelve el nombre REAL de cada una en vez de fijar el literal; si mañana
# se traduce el resto, este chequeo sigue midiendo lo que dice medir.
def _col(*nombres):
    for x in nombres:
        if x in claves:
            return x
    return nombres[0]


ATENCION = [_col("Not invoiced", "Sin facturar"),
            _col("Status", "Situación"),
            _col("Alerts", "Alertas")]
CONTEXTO = ["Client", "Type", "Inicio", "Fin", "Ppto"]
chk("las 3 de atención están todas", all(c in claves for c in ATENCION))
chk("las 5 de contexto están todas", all(c in claves for c in CONTEXTO))
if claves and all(c in claves for c in ATENCION + CONTEXTO):
    peor_atencion = max(claves.index(c) for c in ATENCION)
    mejor_contexto = min(claves.index(c) for c in CONTEXTO)
    chk("toda señal de atención va ANTES que todo contexto",
        peor_atencion < mejor_contexto)
    print(f"         última de atención en {peor_atencion}, "
          f"primera de contexto en {mejor_contexto}")

# `pinned` en las dos de identidad: si se pierden al desplazarse, mirar qué obra
# tiene problemas deja de decirte CUÁL es (y el ID es la identidad, v306).
cfg = {}
for n in ast.walk(f):
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
            and n.func.attr == "dataframe":
        for kw in n.keywords:
            if kw.arg == "column_config" and _cc_dict(kw.value) is not None:
                _cc = _cc_dict(kw.value)
                for k, v in zip(_cc.keys, _cc.values):
                    if isinstance(k, ast.Constant) and isinstance(v, ast.Call):
                        cfg[k.value] = {x.arg: x.value for x in v.keywords}
chk("se localiza el `column_config`", bool(cfg))
for col in ("ID", "Project"):
    p = cfg.get(col, {}).get("pinned")
    chk(f"`{col}` va pinned",
        isinstance(p, ast.Constant) and p.value is True)

# ⚠️ Los anchos se fijaron MIDIENDO el texto real contra el ancho de columna. No se
# comprueba el número (eso caducaría al retocar), sino que las que se apretaron a mano
# sigan teniendo un ancho declarado: sin él vuelven a auto-dimensionarse y el orden
# deja de garantizar nada.
for col in ATENCION + ["Status", _col("Users", "Usuarios"), "Progress"]:
    chk(f"`{col}` tiene ancho declarado", "width" in cfg.get(col, {}))


# ── (b) El aviso del Pre-Start ────────────────────────────────────────────────
print("\n== b) el aviso de duplicado no señala a un bloque que no está ==")
src2 = (RAIZ / "core" / "prestart_ui.py").read_text(encoding="utf-8")
arb2 = ast.parse(sin_comentarios(src2))
f2 = fn_de(arb2, "render_prestart_tab")
chk("existe `render_prestart_tab`", f2 is not None)

# Todo literal que diga «arriba» tiene que estar dentro de un `if` que dependa de `_pf`.
def _prueba_usa_pf(nodo):
    return any(isinstance(x, ast.Name) and x.id == "_pf" for x in ast.walk(nodo.test))


# ⚠️ Hay que mirar el `if` MÁS INTERNO que envuelve el texto, no cualquiera que lo
# contenga: la primera versión de este guardián contaba también el `if _ya_hoy:`
# exterior —que es el PADRE del `if _pf:`— y daba FALLO con el código correcto. Es la
# misma familia que los falsos positivos de v322/v385: el chequeo acusando a código sano.
padre = {}
for n in ast.walk(f2):
    for h in ast.iter_child_nodes(n):
        padre[h] = n

con_arriba, con_arriba_bajo_pf = 0, 0
for n in ast.walk(f2):
    if not (isinstance(n, ast.Constant) and isinstance(n.value, str)
            and ("fírmalo arriba" in n.value
                 # ⚠️ CADUCADO por v439 (i18n F2): el aviso pasó al inglés.
                 or "sign it above" in n.value)):
        continue
    con_arriba += 1
    p = padre.get(n)
    while p is not None and not isinstance(p, ast.If):
        p = padre.get(p)
    if p is not None and _prueba_usa_pf(p):
        con_arriba_bajo_pf += 1

chk("el texto «fírmalo arriba» existe (si no, el chequeo pasa en vacío)", con_arriba > 0)
chk("...y toda aparición cuelga de una condición sobre `_pf`",
    con_arriba_bajo_pf == con_arriba)

# Y el bloque de firma se pinta bajo esa misma señal: si dejara de hacerlo, el texto
# volvería a señalar al vacío por el otro lado.
pinta_bajo_pf = False
for n in ast.walk(f2):
    if isinstance(n, ast.If) and _prueba_usa_pf(n):
        for hijo in ast.walk(n):
            if isinstance(hijo, ast.Call) and isinstance(hijo.func, ast.Name) \
                    and hijo.func.id == "_bloque_firmar":
                pinta_bajo_pf = True
chk("`_bloque_firmar` se pinta bajo la misma señal `_pf`", pinta_bajo_pf)

# La bandera que separa «no le falta firmar» de «no se pudo consultar».
chk("existe `_pf_ok` (no afirmar «ya constas» tras un fallo de lectura)",
    any(isinstance(n, ast.Name) and n.id == "_pf_ok" for n in ast.walk(f2)))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
