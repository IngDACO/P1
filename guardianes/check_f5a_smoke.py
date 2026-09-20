# -*- coding: utf-8 -*-
"""Smoke de F5a: EJECUTAR los mensajes de `auth` y `timeclock`.

⚠️ Estos dos módulos corren en CADA login y en CADA fichaje, así que un
`UnboundLocalError` o un `NameError` aquí tumba la entrada a la app para todo el
mundo. `compileall` y el import no los ven (v378): hay que LLAMAR a las funciones.

⚠️ Todo contra la hoja REAL en modo lectura o con rutas que fallan a propósito —
no se escribe nada en producción.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "dmoreno"}

ok = True


def chk(t_, cond, det=""):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det else ""))


from core import auth, timeclock                                   # noqa: E402

# ── auth: las rutas de error, que son las que se ven ──
# ⚠️ `verify_login` devuelve un DICT `{"ok":…, "error":…}`, NO una tupla. Mi primera
# versión lo desempaquetaba como tupla y obtenía las CLAVES ('ok', 'error'), así que
# daba tres FALLOS con el código perfecto. Regla v135: mirar la firma, no suponerla.
_r = auth.verify_login("no-existe-zzz", "x")
chk("auth.verify_login (usuario inexistente) se EJECUTA",
    isinstance(_r, dict) and _r.get("ok") is False)
chk("...y el mensaje va en inglés", "User not found" in str(_r.get("error")),
    str(_r.get("error")))

# ⚠️ Con usuario vacío responde «User not found.», no «required»: la validación de
# campos obligatorios vive en `auth_ui`, no aquí. Otra expectativa mía equivocada —
# el código estaba bien las tres veces.
_r = auth.verify_login("", "")
chk("auth.verify_login (vacío) → mensaje inglés",
    "User not found" in str(_r.get("error")), str(_r.get("error")))

# ⚠️ `_session_active` es donde estaba la variable `t` que se renombró: si el
# renombrado hubiera roto algo, revienta aquí y no al compilar.
chk("auth._session_active se EJECUTA tras renombrar su local `t`",
    auth._session_active({"SessionToken": "x", "SessionTime": "0"}) is False)
chk("...y con un heartbeat reciente devuelve True",
    auth._session_active({"SessionToken": "x",
                          "SessionTime": str(int(__import__("time").time()))}) is True)

# rol inválido / grupo obligatorio: rutas de validación, sin escribir
_o, _m = auth.add_user("zzz", "x", "rol-que-no-existe", "n", "cliente1")
chk("auth.add_user con rol inválido → inglés", "Invalid role" in str(_m), str(_m))
_o, _m = auth.add_user("zzz", "x", "administrator", "n", "")
chk("auth.add_user sin grupo → inglés", "must belong to a group" in str(_m), str(_m))
_o, _m = auth.add_group("")
chk("auth.add_group sin nombre → inglés", "required" in str(_m).lower(), str(_m))

# ── timeclock: los dos mensajes que se ven cada día ──
_o, _m = timeclock.clock_out("nadie-zzz", "cliente1")
chk("timeclock.clock_out sin fichaje abierto se EJECUTA", _o is False)
chk("...y el mensaje va en inglés",
    "no open clock in" in str(_m).lower(), str(_m))

# ⚠️ Los tres `d` que quedan como VARIABLE en timeclock siguen funcionando: se
# ejercitan llamando a las funciones que los usan.
# ⚠️ El 2º argumento es un DATETIME, no una cadena: pasándole texto devolvía []
# y parecía roto. Otro fallo del test, no del código.
from datetime import datetime as _dt                                # noqa: E402
_seg = timeclock._segmentos_dia("2026-08-30 20:00:00",
                                _dt(2026, 8, 31, 5, 0, 0))
chk("timeclock._segmentos_dia (usa `d` como variable) se EJECUTA", len(_seg) == 2,
    str(_seg))
_rs = timeclock.resumen_semana("dmoreno", "cliente1", "dmoreno")
chk("timeclock.resumen_semana se EJECUTA", isinstance(_rs, dict), str(type(_rs)))

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
