# -*- coding: utf-8 -*-
"""Chequeo permanente: ningun ROL literal fuera de `auth.ROLES` llega a `add_user`.

⚠️ Va en `verif_v469` porque el hueco era SUYO: su barrido mira `ast.Compare` —las
ramas muertas— y estos dos literales entraban como ARGUMENTO, asi que pasaron por
delante. Resultado: el admin no podia crear un usuario de campo («Invalid role.») y el
bootstrap no podia crear el primer propietario. La regla se DERIVA de `auth.ROLES`, no
de una lista a mano, que es lo que se queda viejo (v433/v434).
"""
import ast
import io

P = "verif_v469.py"
s = io.open(P, encoding="utf-8").read()

BLOQUE = '''

print("\\n9. Ningun ROL literal fuera de `auth.ROLES` llega a las funciones que validan")
# ⚠️ El hueco que dejo pasar «Invalid role» en v475: el barrido de arriba mira
# COMPARACIONES y estos entraban como ARGUMENTO. Los nombres de funcion se declaran
# (son las que validan contra ROLES); los roles validos se DERIVAN de la constante.
_FN_ROL = {"add_user", "set_role"}


def roles_literales(src):
    """[(funcion, valor, linea)] de cada rol literal pasado a una de esas funciones."""
    try:
        arbol = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "attr", None) or getattr(n.func, "id", None) or ""
        if fn not in _FN_ROL:
            continue
        for a in list(n.args) + [k.value for k in n.keywords]:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append((fn, a.value, n.lineno))
    return out


# la sonda, validada contra un caso construido antes de creerse su cero (trampa nº12)
_MALO = 'auth.add_user(u, pw, "campo", nm, grupo)'
_BUENO = 'auth.add_user(u, pw, "field", nm, grupo)'
_ve_malo = [v for _f, v, _l in roles_literales(_MALO) if v not in auth.ROLES]
_ve_bueno = [v for _f, v, _l in roles_literales(_BUENO) if v not in auth.ROLES]
(ok if (_ve_malo and not _ve_bueno) else fallo)(
    "la sonda ve el rol viejo y no marca el canonico")

_malos = []
for _f in sorted(os.listdir("core")) + ["app.py"]:
    _ruta = os.path.join("core", _f) if _f != "app.py" else "app.py"
    if not _ruta.endswith(".py"):
        continue
    for _fn, _v, _ln in roles_literales(io.open(_ruta, encoding="utf-8").read()):
        if _v not in auth.ROLES:
            _malos.append("%s:%d %s(… %r …) — no esta en ROLES=%s"
                          % (os.path.basename(_ruta), _ln, _fn, _v, auth.ROLES))
(ok if not _malos else fallo)(
    "todas las llamadas pasan un rol de `auth.ROLES`", _malos)
'''

# se engancha justo antes del veredicto final
import re
m = list(re.finditer(r'\nprint\(""\)\nif _f:', s))
if len(m) != 1:
    # el fichero puede cerrar de otra forma: se busca el sys.exit final
    m = list(re.finditer(r'\nsys\.exit\(', s))
    if not m:
        raise SystemExit("no encuentro el cierre del guardian")
    pos = m[-1].start()
else:
    pos = m[0].start()

s = s[:pos] + BLOQUE + s[pos:]
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v469.py: bloque 9 (roles literales en argumentos)")
