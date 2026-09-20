# -*- coding: utf-8 -*-
"""v486 corrige la red de `verif_v467`: NaN NO vacia la celda, la pinta «None» igual.

La red estaba bien construida (v485 la rehizo con sus tres cegueras) pero su AFIRMACION
era falsa: acertaba en la FORMA (`None` en una celda) y se equivocaba en la CURA (`NaN`).
Medido en 1.57 con una tabla por caso: `nan`, `None` y `pd.NA` pintan «None» los tres,
con o sin `NumberColumn`, y hasta con `Styler(na_rep="")`. Lo unico que sale vacio es
una CADENA en una columna sin tipar.
"""
import io
import os

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v467.py")
NL = chr(10)

s = io.open(RUTA, encoding="utf-8").read()

# ── 1) el comentario de cabecera: decia lo contrario de lo medido ──────────────
VIEJO_CAB = NL.join([
    'print("3. Ninguna celda de tabla puede pintar el literal «None»")',
    '# ⚠️ Con TODA la columna a None, pandas la deja en `object` y Streamlit imprime el',
    '# texto; con NaN es float y la celda sale vacia. Medido, no supuesto.',
])
NUEVO_CAB = NL.join([
    'print("3. Ninguna celda de tabla puede pintar el literal «None»")',
    '# ⚠️ CORREGIDO EN v486: esta nota decia «con NaN es float y la celda sale vacia,',
    '# medido» y era FALSO. Medido en 1.57 con una tabla por caso e interceptando',
    '# `fillText`: `nan`, `None` y `pd.NA` pintan «None» LOS TRES —con o sin',
    '# `NumberColumn`, con formato o sin el, y hasta con `Styler(na_rep="")`—, porque',
    '# es el placeholder de valor ausente de Streamlit y una columna TIPADA convierte',
    '# incluso `""` en nulo. Lo UNICO que vacia la celda es una CADENA en una columna',
    '# sin tipar, y de ahi `tabla.celda()`. Por eso esta red caza tambien el NaN: con',
    '# la afirmacion vieja, «arreglar» un None poniendo NaN pasaba el chequeo y seguia',
    '# pintando «None» en pantalla (lo que hizo v485).',
])

# ── 2) la red: anadir NaN / np.nan / pd.NA ────────────────────────────────────
VIEJO_RED = NL.join([
    '            elif (isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "get"',
    '                    and len(v.args) == 1 and not v.keywords',
    '                    and not isinstance(v.args[0], ast.Constant)):',
    '                malas.append("%s:%s %s (.get de clave variable, sin defecto)"',
    '                             % (p.name, v.lineno, col))',
])
NUEVO_RED = NL.join([
    '            elif (isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "get"',
    '                    and len(v.args) == 1 and not v.keywords',
    '                    and not isinstance(v.args[0], ast.Constant)):',
    '                malas.append("%s:%s %s (.get de clave variable, sin defecto)"',
    '                             % (p.name, v.lineno, col))',
    '            # ⚠️ v486: el NaN cuenta IGUAL que el None. Cubre las tres formas de',
    '            # escribirlo —`float("nan")`, `np.nan`/`numpy.nan` y `pd.NA`— tanto como',
    '            # valor directo como en la rama `else` de un ternario, que es como se',
    '            # colo en las cuatro tablas de v467/v485.',
    '            else:',
    '                _nulo = _nulo_num(v) or (isinstance(v, ast.IfExp)',
    '                                         and _nulo_num(v.orelse))',
    '                if _nulo:',
    '                    malas.append("%s:%s %s (%s: se pinta «None» igual que None)"',
    '                                 % (p.name, v.lineno, col, _nulo))',
])

# ── 3) el helper `_nulo_num`, antes del bucle que usa la red ──────────────────
ANCLA_HELPER = 'for p in sorted(Path("core").glob("*_ui.py")):'
HELPER = NL.join([
    'def _nulo_num(n):',
    '    """¿Este nodo es un nulo numerico? Devuelve como se escribio, o "".',
    '',
    '    ⚠️ v486: `float("nan")`, `np.nan` y `pd.NA` se pintan «None» igual que None',
    '    (medido), asi que para esta red son el mismo fallo.',
    '    """',
    '    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "float":',
    '        a = n.args[0] if n.args else None',
    '        if isinstance(a, ast.Constant) and str(a.value).strip().lower() == "nan":',
    '            return \'float("nan")\'',
    '    if isinstance(n, ast.Attribute) and n.attr in ("nan", "NA", "NaN"):',
    '        mod = getattr(n.value, "id", "")',
    '        if mod in ("np", "numpy", "pd", "pandas", "math"):',
    '            return "%s.%s" % (mod, n.attr)',
    '    return ""',
    '',
    '',
])

for etq, a in (("cabecera", VIEJO_CAB), ("red", VIEJO_RED), ("helper", ANCLA_HELPER)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s aparece %d veces" % (etq, s.count(a)))

s = s.replace(VIEJO_CAB, NUEVO_CAB, 1)
s = s.replace(VIEJO_RED, NUEVO_RED, 1)
s = s.replace(ANCLA_HELPER, HELPER + ANCLA_HELPER, 1)

# ── 4) el veredicto, que afirmaba la cura equivocada ──────────────────────────
VIEJO_OK = 'ok("0 celdas con None (se usa NaN)")'
NUEVO_OK = 'ok("0 celdas con un nulo (None ni NaN): se usa `tabla.celda` -> cadena")'
if s.count(VIEJO_OK) != 1:
    raise SystemExit("ancla veredicto no unica")
s = s.replace(VIEJO_OK, NUEVO_OK, 1)

compile(s, RUTA, "exec")
io.open(RUTA, "w", encoding="utf-8", newline="").write(s)
print("verif_v467: red ensanchada al NaN + afirmacion corregida")
