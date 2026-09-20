# -*- coding: utf-8 -*-
"""La exencion de los lectores GLOBALES se DERIVA, no se escribe a mano.

⚠️ `GLOBALES_OK` era un conjunto de (fichero, funcion) mantenido a mano en paralelo a
`timeclock.SHEETS_GLOBALES`, que es donde vive la verdad. Al añadir un modulo global
(la biblioteca de v472) el guardian lo denuncio como fuga de inquilino **sin serlo**:
la lista se quedo vieja, que es exactamente el patron que v433 (`auth._COL`) y v434
(la proyeccion de `list_users`) identificaron como recurrente — dos sitios que
describen lo mismo y se desincronizan.

Derivarlo ademas AFINA el guardian en la otra direccion, que es lo que importa: si
mañana una hoja deja de ser global, su lector queda denunciado **solo**, sin que nadie
tenga que acordarse de borrar una linea de una lista.

Se resuelve por AST, sin importar `timeclock` (el guardian es puro AST a proposito:
importarlo arrastraria streamlit y los secrets, y con ello la trampa nº19).
"""
import ast
import io

P = "verif_v378.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = ('GLOBALES_OK = {("auth.py", "_login_records_cached"), ("auth.py", "_group_records"),\n'
         '               ("rails.py", "_records_cached"), ("rails.py", "_records"),\n'
         '               ("manuals.py", "_drive_records")}\n')

NUEVO = '''# ⚠️ Estas cinco NO se pueden derivar: leen con `get_all_records` sobre un worksheet
# ya resuelto, asi que en el AST no aparece el titulo de la hoja. Se quedan a mano y
# con su razon; las demas se DERIVAN (ver `_lee_solo_globales`).
GLOBALES_OK = {("auth.py", "_login_records_cached"), ("auth.py", "_group_records"),
               ("rails.py", "_records_cached"), ("rails.py", "_records"),
               ("manuals.py", "_drive_records")}


def _sheets_globales():
    """Los titulos de hoja GLOBAL, leidos de `timeclock.SHEETS_GLOBALES`.

    ⚠️ Se leen de ahi y no de una copia: una lista a mano en paralelo a la verdad es
    justo lo que dejo este guardian denunciando un modulo global como si fuera una
    fuga (v433/v434). Ojo: la constante esta en MINUSCULAS porque la comprobacion
    real es `.lower()`.
    """
    arbol = ast.parse((BASE / "timeclock.py").read_text(encoding="utf-8"))
    for n in ast.walk(arbol):
        if (isinstance(n, ast.Assign)
                and any(getattr(t_, "id", "") == "SHEETS_GLOBALES" for t_ in n.targets)):
            try:
                return {str(x).lower() for x in ast.literal_eval(n.value)}
            except Exception:
                return set()
    return set()


GLOBALES = _sheets_globales()


def _lee_solo_globales(fn, mod_consts):
    """La funcion lee UNICAMENTE hojas globales -> no puede haber fuga entre libros.

    Devuelve False si no se puede resolver ni una hoja: **no afirmar nada es mas
    seguro que eximir por no haber sabido mirar** (un falso negativo aqui es una fuga
    de datos entre empresas, que es lo que v378 vino a cerrar).
    """
    titulos = []
    for n in ast.walk(fn):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "registros" and n.args):
            continue
        a = n.args[0]
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            titulos.append(a.value)
        elif isinstance(a, ast.Name) and a.id in mod_consts:
            titulos.append(mod_consts[a.id])
        else:
            return False              # una hoja que no se pudo resolver
    return bool(titulos) and all(t_.lower() in GLOBALES for t_ in titulos)
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla GLOBALES_OK no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

# ── engancharlo en el bucle ──────────────────────────────────────────────────
VIEJO2 = ('for f in sorted(BASE.glob("*.py")):\n'
          '    arbol = ast.parse(f.read_text(encoding="utf-8"))\n'
          '    for n in ast.walk(arbol):\n')
NUEVO2 = ('for f in sorted(BASE.glob("*.py")):\n'
          '    arbol = ast.parse(f.read_text(encoding="utf-8"))\n'
          '    # constantes de MODULO que son cadenas: para resolver `registros(SHEET, ...)`\n'
          '    _consts = {}\n'
          '    for _n in arbol.body:\n'
          '        if (isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Constant)\n'
          '                and isinstance(_n.value.value, str)):\n'
          '            for _t in _n.targets:\n'
          '                if isinstance(_t, ast.Name):\n'
          '                    _consts[_t.id] = _n.value.value\n'
          '    for n in ast.walk(arbol):\n')

VIEJO3 = ('        if (f.name, n.name) in GLOBALES_OK:\n'
          '            continue\n')
NUEVO3 = ('        if (f.name, n.name) in GLOBALES_OK:\n'
          '            continue\n'
          '        if _lee_solo_globales(n, _consts):\n'
          '            continue      # hoja GLOBAL: todas las sesiones leen el MISMO libro\n')

for viejo, nuevo, etq in ((VIEJO2, NUEVO2, "consts"), (VIEJO3, NUEVO3, "exencion")):
    if s.count(viejo) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(viejo)))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v378.py: la exencion de globales se deriva de SHEETS_GLOBALES")
