# -*- coding: utf-8 -*-
"""v679 · El Management assistant responde solo a lo que se le pide ahora (visto verificando v678).

En producción, al preparar la tarjeta de liberar el tablero de helper leader CI 1, añadió por su cuenta «One thing from
my last answer needs correcting…» sobre una respuesta del ciclo 3 que era CIERTA entonces (el tablero lo cambió después
la prueba de Assign). En el examen real (`sueltos/examen_asistente_oficina.py … revisar`), al pedirle solo una tarea
comentó 2 de 2 la aprobación de un turno anterior (y una vez repitió un dato que ya no valía). Con la regla nueva: 0 de 5,
y 0 de 1 al repetir lo que la app contestó al confirmar; lo que SÍ se le pregunta de un turno anterior lo sigue
contestando («close the alert it created»).

Aquí: la regla está en el texto que recibe la OFICINA (el que arma `get_chat_response`), no en el del campo, y no
contradice la de las notas «[I pressed Confirm…]».
"""
import os
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:600]))
    if not cond:
        FALLOS.append(nombre)


from core import chat_agent as CA                                         # noqa: E402

_of, _ca = CA._PERSONA["office_tools"], CA._PERSONA["field_tools"]
REGLA = ("Responde SOLO a lo que te pide ahora. No comentes, repitas ni corrijas por tu cuenta lo que se dijo o se hizo "
         "en turnos anteriores, ni lo que la app contestó al confirmar (la persona ya lo ha visto): era cierto con los "
         "datos de entonces. Si te lo pregunta, contesta con lo de ahora.")
chk("la oficina tiene la regla, entera", REGLA in _of, _of[-1500:])
chk("…detrás de «la conversación puede venir de otros días» (las dos van juntas)",
    _of.find("La conversación puede venir de otros días") < _of.find("Responde SOLO a lo que te pide ahora") != -1)
chk("…y sigue la de las notas «[I pressed Confirm…]»: lo que dicen pasó de verdad",
    "«[I pressed Confirm»" in _of and "lo que dicen pasó de verdad" in _of)
# ⚠️ v687 · CADUCADO A PROPÓSITO: el campo también la tiene (el 17/11, con la sesión de campo, el Field assistant se
# «corrigió» de una respuesta del domingo 15/11, cierta entonces). Lo vigila verif_v687.
chk("v687 · el campo también la tiene, entera", REGLA in _ca, _ca[-1500:])
# lo que de verdad le llega al modelo: el texto fijo que arma `get_chat_response` para la oficina
_s = open(os.path.join(RAIZ, "core", "chat_agent.py"), encoding="utf-8").read()
chk("la oficina recibe `office_tools` (y el campo, `field_tools`)",
    '_PERSONA["field_tools" if rol == "field" else "office_tools"]' in _s)
_ex = open(r"C:\Users\diego\P1\guardianes\sueltos\examen_asistente_oficina.py", encoding="utf-8").read()
chk("el examen que lo mide sigue ahí (modo `revisar`)", 'sys.argv[4:] == ["revisar"]' in _ex and "_HIST_C3" in _ex)

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
sys.exit(1 if FALLOS else 0)
