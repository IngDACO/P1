# -*- coding: utf-8 -*-
"""v680 · Lo que la oficina lee JUSTO antes de responder: «responde solo a eso» (visto verificando v679 en producción).

La regla de v679 en la guía no bastó con una conversación larga: a «Who is planned on PRJ-0044 on Monday 23/11?» el
Management assistant añadió en producción «helper leader CI 1 is no longer on the list. The removal you confirmed took
them off.», y en el examen (`sueltos/examen_asistente_oficina.py … revisar2`) 3 de 3, una vez con un dato viejo («their
leave starts on 25/11», con esa ausencia cancelada). Con el recordatorio detrás de los resultados (donde v643 arregló el
idioma): 0 de 3; `revisar` 0 de 5; `confirmado`, lo que SÍ pregunta por un turno anterior, bien.

Aquí: el recordatorio va solo a la OFICINA, detrás del idioma, y la llamada le pasa el rol.
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

_of = CA._idioma_tras_datos("Who is planned on PRJ-0044 on Monday 23/11?", "administrator")
_ca = CA._idioma_tras_datos("Who is planned on PRJ-0044 on Monday 23/11?", "field")
_es = CA._idioma_tras_datos("¿quién está planificado el lunes en PRJ-0044?", "administrator")
_sin = CA._idioma_tras_datos("Who is planned on PRJ-0044 on Monday 23/11?")
chk("la oficina: cita la pregunta y le pide responder solo a eso, sin turnos anteriores",
    "«Who is planned on PRJ-0044 on Monday 23/11?»" in _of and "Answer only that question" in _of
    and "Do not bring up earlier turns of this conversation" in _of and "what was done on a card" in _of, _of)
chk("…y si la pregunta SÍ se refiere a algo anterior, que lo conteste con lo de hoy",
    "If the question itself refers to something earlier, answer it with today's data." in _of, _of)
chk("…detrás de lo del idioma, que sigue igual", _of.index("Do not comment on the language.") < _of.index("Answer only"))
chk("…también con el idioma por su nombre", "Answer only that question" in _es and "Spanish" in _es, _es)
chk("el campo no cambia (no se examinó con él), ni sin rol", "Answer only" not in _ca and "Answer only" not in _sin
    and _ca == _sin, (_ca, _sin))
_s = open(os.path.join(RAIZ, "core", "chat_agent.py"), encoding="utf-8").read()
chk("la llamada le pasa el rol de la sesión", '_idioma_tras_datos(ctx.get("pregunta", ""), ctx.get("rol", ""))' in _s)
_ex = open(r"C:\Users\diego\P1\guardianes\sueltos\examen_asistente_oficina.py", encoding="utf-8").read()
chk("el examen que lo mide sigue ahí (modo `revisar2`)", 'sys.argv[4:] == ["revisar2"]' in _ex and "_HIST_V678" in _ex)

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
sys.exit(1 if FALLOS else 0)
