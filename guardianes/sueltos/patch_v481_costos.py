# -*- coding: utf-8 -*-
"""El campo deja de ver el dinero de la obra (decisión del usuario).

En 💰 Recibos, un usuario de campo veía el titular «a este ritmo costará X, Y por
encima», las tarjetas Costo total · Compras · Mano de obra · Presupuesto · Costo al
terminar · Comprometido, la barra «llevas gastado X de Y», las órdenes de compra, el
reparto del costo, **la mano de obra PERSONA POR PERSONA** y la curva de gasto.
Se queda con lo suyo: subir recibos y ver los recibos de la obra.

⚠️ Se hace EXTRAYENDO el bloque, no envolviéndolo en un `if`: el código ya está a
profundidad de cuerpo de función, así que extraerlo **no reindenta ni una línea** —y
reindentar 125 líneas es exactamente lo que rompió v120 y v148—.

⚠️ El parámetro nuevo es `ver_costos`, no reutilizar `can_delete`: ese dice «puede
borrar recibos» y ya estaba haciendo de «es gestión» por accidente. Quien mañana quiera
dejar al campo borrar SUS recibos le pondría `can_delete=True` y le abriría las
finanzas de la obra sin enterarse. Su valor por defecto es **False**: si un sitio de
llamada nuevo se olvida, no enseña dinero — falla cerrado.
"""
import ast
import builtins
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\projects_ui.py"
s = io.open(P, encoding="utf-8").read()

INI = ('    cp    = E.cost_projection(pid, grupo)      # incluye todo lo de project_cost\n'
       '    lb    = E.labor_breakdown(pid, grupo)\n'
       '    gastos = E.project_expenses(pid)\n')
FIN = '    # ── Cargar recibo ──\n'

if s.count(INI) != 1 or s.count(FIN) != 1:
    raise SystemExit("anclas: INI=%d FIN=%d" % (s.count(INI), s.count(FIN)))

i0 = s.index(INI)
i1 = s.index(FIN)
region = s[i0 + len(INI):i1]            # todo lo de dinero, SIN las 3 líneas de arriba

CABECERA = '''def _costos_section(pid, grupo, gastos, can_delete, key_prefix):
    """El dinero de la obra: proyección, presupuesto, compras, mano de obra y curva.

    ⚠️ v481 · Extraído de `render_expenses` porque **el campo ya no lo ve** (decisión
    del usuario). Antes vivía suelto en esa función, así que lo veía cualquiera que
    abriera 💰 Recibos — incluida la **mano de obra persona por persona**, de donde se
    deduce lo que cobra cada compañero. El campo conserva lo suyo: cargar recibos y
    verlos.

    ⚠️ Se extrajo TAL CUAL, sin reindentar ni una línea: el bloque ya estaba a
    profundidad de cuerpo de función. Envolverlo en un `if` habría movido 125 líneas,
    que es la clase de cambio que rompió v120 y v148.
    """
    from core import expenses as E
    cp    = E.cost_projection(pid, grupo)      # incluye todo lo de project_cost
    lb    = E.labor_breakdown(pid, grupo)
'''

NUEVO_CUERPO = ('    gastos = E.project_expenses(pid)\n'
                '    # ⚠️ v481 · El bloque de dinero, solo para gestión. `ver_costos` por defecto\n'
                '    # es False: un sitio de llamada que se olvide NO enseña finanzas.\n'
                '    if ver_costos:\n'
                '        _costos_section(pid, grupo, gastos, can_delete, key_prefix)\n\n')

nuevo = s[:i0] + NUEVO_CUERPO + s[i1:]

ANCLA_DEF = 'def render_expenses(pid, grupo, can_delete=False, key_prefix="ex"):'
if nuevo.count(ANCLA_DEF) != 1:
    raise SystemExit("firma no unica")
nuevo = nuevo.replace(ANCLA_DEF, CABECERA + region + "\n\n" + ANCLA_DEF)
nuevo = nuevo.replace(ANCLA_DEF,
                      'def render_expenses(pid, grupo, can_delete=False, key_prefix="ex",\n'
                      '                    ver_costos=False):')

for viejo, nuev in (
        ('render_expenses(pid, grupo, can_delete=True, key_prefix="adm")',
         'render_expenses(pid, grupo, can_delete=True, key_prefix="adm", ver_costos=True)'),
        ('render_expenses(pid, grupo, can_delete=True, key_prefix="loc")',
         'render_expenses(pid, grupo, can_delete=True, key_prefix="loc", ver_costos=True)')):
    if nuevo.count(viejo) != 1:
        raise SystemExit("sitio de llamada no unico: %r" % viejo[:50])
    nuevo = nuevo.replace(viejo, nuev)

arbol = ast.parse(nuevo)


def locales_de(fn):
    """Todo lo que esa función define por dentro: parámetros, asignaciones, imports,
    excepciones, funciones ANIDADAS y sus parámetros, y lambdas.

    ⚠️ Sin las anidadas, el verificador acusaba a `_blq_reparto` y `_blq_categorias`,
    que se definen dentro de la propia región extraída.
    """
    out = {a.arg for a in fn.args.args}
    for x in ast.walk(fn):
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
            out.add(x.id)
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            for a in x.names:
                out.add(a.asname or a.name.split(".")[0])
        if isinstance(x, ast.ExceptHandler) and x.name:
            out.add(x.name)
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and x is not fn:
            out.add(x.name)
            out |= {a.arg for a in getattr(getattr(x, "args", None), "args", [])}
        if isinstance(x, ast.Lambda):
            out |= {a.arg for a in x.args.args}
    return out


def huerfanos_de(fn, globales):
    return sorted({x.id for x in ast.walk(fn)
                   if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)}
                  - locales_de(fn) - globales
                  - {n for n in dir(builtins)})


# ⚠️ CONTROL antes de creerse ningún cero (trampa nº12): el verificador tiene que VER
# un huérfano construido, incluso con una función anidada de por medio.
_ctrl_src = "\n".join(["def f(a):", "    def g():", "        return a",
                       "    return g() + noexiste_xyz"])
_ctrl = ast.parse(_ctrl_src).body[0]
if "noexiste_xyz" not in huerfanos_de(_ctrl, set()):
    raise SystemExit("el verificador NO ve un huerfano construido: su cero no vale")
if huerfanos_de(_ctrl, set()) != ["noexiste_xyz"]:
    raise SystemExit("el verificador acusa de mas: %s" % huerfanos_de(_ctrl, set()))
print("   control: ve el huerfano construido, y solo ese")

glob = {n.name for n in arbol.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
for n in arbol.body:
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        for a in n.names:
            glob.add(a.asname or a.name.split(".")[0])
    if isinstance(n, ast.Assign):
        glob |= {t.id for t in n.targets if isinstance(t, ast.Name)}

fn = next(x for x in arbol.body if isinstance(x, ast.FunctionDef) and x.name == "_costos_section")
h = huerfanos_de(fn, glob)
if h:
    raise SystemExit("NOMBRES HUERFANOS en _costos_section: %s" % h)

io.open(P, "w", encoding="utf-8", newline="").write(nuevo)
print("core/projects_ui.py: el dinero de la obra sale de la pantalla del campo")
print("   region extraida: %d lineas - 0 nombres huerfanos" % region.count("\n"))
