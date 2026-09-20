"""Verifica las guardas de la ruta de sesion SIN tocar produccion.

Se parchean `_get_login_ws` y `_records` (asi no se abre la hoja real ni se
migran cabeceras). Se comprueban las 2 direcciones: que un error de API ya no
tumba nada, y que el comportamiento NORMAL (incluida la expulsion legitima)
sigue igual.
"""
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

from core import auth

FILAS = [{"User": "dacox", "Password": "x", "Role": "propietario", "Name": "Daco",
          "Active": "SI", "Group": "", "SessionToken": "TOK-BUENO", "SessionTime": "0"}]


class WSFalso:
    """Worksheet de mentira: registra las escrituras en vez de hacerlas."""
    def __init__(self):
        self.escrituras = []

    def update_cell(self, row, col, val):
        self.escrituras.append((row, col, val))


class ErrorAPI(Exception):
    """Simula gspread.exceptions.APIError (429 / 503)."""


def montar(*, revienta_lectura: bool):
    ws = WSFalso()
    auth._get_login_ws = lambda: (ws, "")
    if revienta_lectura:
        def _boom(_lws):
            raise ErrorAPI("429 RESOURCE_EXHAUSTED")
        auth._records = _boom
    else:
        auth._records = lambda _lws: list(FILAS)
    return ws


ok = True


def check(nombre, real, esperado):
    global ok
    bien = real == esperado
    ok = ok and bien
    print(f"  {'OK ' if bien else 'FALLO'}  {nombre}: {real!r}")
    if not bien:
        print(f"         esperado: {esperado!r}")


print("== A) La API REVIENTA en la lectura (el caso del traceback) ==")
montar(revienta_lectura=True)
check("heartbeat -> no expulsa", auth.heartbeat("dacox", "TOK-BUENO"), True)
check("validate_session -> {}", auth.validate_session("dacox", "TOK-BUENO"), {})
_r, _m = auth.start_session("dacox")
check("start_session -> bloquea", _r, False)
print(f"         mensaje: {_m}")

print("\n== B) Comportamiento NORMAL (no se ha roto nada) ==")
ws = montar(revienta_lectura=False)
check("heartbeat token correcto -> True", auth.heartbeat("dacox", "TOK-BUENO"), True)
check("   y marca vida (1 escritura)", len(ws.escrituras), 1)

ws = montar(revienta_lectura=False)
check("heartbeat token DESPLAZADO -> False (expulsa)",
      auth.heartbeat("dacox", "TOK-VIEJO"), False)
check("   y NO escribe", len(ws.escrituras), 0)

ws = montar(revienta_lectura=False)
check("heartbeat usuario inexistente -> False", auth.heartbeat("nadie", "TOK-BUENO"), False)

ws = montar(revienta_lectura=False)
check("validate_session token correcto -> restaura",
      auth.validate_session("dacox", "TOK-BUENO").get("usuario"), "dacox")
check("validate_session token malo -> {}", auth.validate_session("dacox", "NO"), {})

ws = montar(revienta_lectura=False)   # SessionTime=0 -> sesion NO activa
_r, _t = auth.start_session("dacox")
check("start_session cuenta libre -> abre", _r, True)
check("   y escribe token + time (2)", len(ws.escrituras), 2)

import time as _t2
FILAS[0]["SessionTime"] = str(int(_t2.time()))   # sesion VIVA ahora
ws = montar(revienta_lectura=False)
_r, _m = auth.start_session("dacox")
check("start_session con sesion viva -> bloquea", _r, False)
# ⚠️ CADUCADO por v445 (i18n F5a): el mensaje pasó al inglés. Y lo que se comprueba
# ya no es el texto sino la IDENTIDAD con el centinela, que es de lo que depende el
# botón «cerrar la otra sesión»: si `start_session` devolviera otra cosa, `auth_ui`
# no lo reconocería y ese botón desaparecería sin dar ningún error.
check("   motivo correcto (es el CENTINELA, no un texto suelto)",
      _m == auth.SESION_OCUPADA, True)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
