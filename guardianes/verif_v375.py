"""GUARDIÁN v375 — el modal del Pre-Start deja de cerrarse solo.

⚠️ El fallo, visto EN PRODUCCIÓN y no en la mini-app: v374 consumía la bandera con
`pop`, así que el diálogo se pintaba en esa pasada y desaparecía en la siguiente. Y
en la app real siempre hay una pasada siguiente justo ahí: los cronómetros del
sidebar son `components.html` y al montarse disparan un rerun — y solo existen en
el estado «fichado», que es exactamente cuando el modal debe verse.

Ahora es una CONDICIÓN de estado: mientras se cumpla, cada pasada vuelve a llamar
al diálogo. Se prueban las 5 ramas llamando a la función REAL.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "jlopez", "grupo": "cliente1", "rol": "field"}

from core import timeclock_ui as TU, prestart as PS      # noqa: E402

ok = True
PID, NOM, G = "PRJ-0007", "Meriton Zetland — Torre A", "cliente1"

# Se sustituyen los diálogos por espías: interesa SI se llaman, no cómo se pintan.
# ⚠️ v403: son DOS. El título de un `st.dialog` va en el decorador, así que «falta la
# charla» y «fírmala» no pueden compartir función — y si aquí solo se espiara el
# primero, el caso nuevo pasaría desapercibido.
llamadas = []
firmas = []
TU._dialogo_prestart = lambda obra: llamadas.append(obra)
TU._dialogo_firmar = lambda obra, quien="": firmas.append(obra)


def escenario(nombre, estado, hecho_hoy, pendiente=None):
    llamadas.clear()
    firmas.clear()
    for k in [k for k in list(st.session_state.keys()) if k.startswith("_ps_")]:
        del st.session_state[k]
    st.session_state.update(estado)
    _orig, _origf = PS.hecho_hoy, PS.pendiente_de_firma
    PS.hecho_hoy = lambda pid, grupo="": hecho_hoy
    PS.pendiente_de_firma = lambda pid, grupo="", persona="": dict(pendiente or {})
    try:
        TU.aviso_prestart_pendiente(G)
    finally:
        PS.hecho_hoy, PS.pendiente_de_firma = _orig, _origf
    return list(llamadas)


print("== las 5 ramas de `aviso_prestart_pendiente` ==")
casos = [
    ("sin bandera (no se ha fichado)",      {},                                          False, 0),
    ("fichado y falta el pre-start",        {"_ps_aviso": {"pid": PID, "nombre": NOM}},  False, 1),
    ("⚠️ y en la pasada SIGUIENTE sigue",   {"_ps_aviso": {"pid": PID, "nombre": NOM}},  False, 1),
    ("descartado en esta sesión",           {"_ps_aviso": {"pid": PID, "nombre": NOM},
                                             f"_ps_visto_{PID}": True},                  False, 0),
    # ⚠️ CADUCADO Y ACTUALIZADO en v403 (regla v385, razón al lado): antes esto era
    # «hecho → no se abre nada», que era la conducta de v374. Ahora «hecho» no basta:
    # hay que distinguir si YO firmé. Si la charla está hecha y no consto en ella, el
    # aviso sigue — con el otro diálogo. El hueco que cerró v403 era justo este.
    ("hecho Y yo firmé",                    {"_ps_aviso": {"pid": PID, "nombre": NOM}},  True,  0),
]
for nombre, estado, hecho, esperado in casos:
    got = escenario(nombre, estado, hecho)
    bien = len(got) == esperado and not firmas
    ok &= bien
    print(f"   {'✓' if bien else '✗'} {nombre:<38} se abre: {len(got)} (esperado {esperado})")

# el caso NUEVO: hecha pero sin mi firma
_got = escenario("hecho y NO firmé", {"_ps_aviso": {"pid": PID, "nombre": NOM}}, True,
                 {"id": "PS-0009", "facilitador": "Ana Ruiz"})
_bien = len(_got) == 0 and len(firmas) == 1
ok &= _bien
print(f"   {'✓' if _bien else '✗'} {'hecho pero NO lo firmé':<38} "
      f"«falta»: {len(_got)} (esperado 0) · «firma»: {len(firmas)} (esperado 1)")

# ⚠️ Y que un fallo al consultar NO degrade al diálogo equivocado: decirle «no hay
# charla» a quien solo tenía que firmar le empuja a emitir un segundo documento.
firmas.clear()
llamadas.clear()
for _k in [k for k in list(st.session_state.keys()) if k.startswith("_ps_")]:
    del st.session_state[_k]
st.session_state["_ps_aviso"] = {"pid": PID, "nombre": NOM}
_o, _of = PS.hecho_hoy, PS.pendiente_de_firma


def _revienta(*a, **k):
    raise RuntimeError("fallo al consultar la firma")


PS.hecho_hoy = lambda pid, grupo="": True
PS.pendiente_de_firma = _revienta
try:
    TU.aviso_prestart_pendiente(G)
finally:
    PS.hecho_hoy, PS.pendiente_de_firma = _o, _of
_seguro = len(llamadas) == 0
ok &= _seguro
print(f"   {'✓' if _seguro else '‼️'} {'si la consulta falla, NO dice «falta la charla»':<38} "
      f"se abre «falta»: {len(llamadas)} (esperado 0)")

# ⚠️ La rama clave: DOS pasadas seguidas con el mismo estado deben abrirlo LAS DOS
# veces. Con el `pop` de v374 la segunda daba 0 — que es justo lo que se veía.
llamadas.clear()
for k in [k for k in list(st.session_state.keys()) if k.startswith("_ps_")]:
    del st.session_state[k]
st.session_state["_ps_aviso"] = {"pid": PID, "nombre": NOM}
_orig = PS.hecho_hoy
PS.hecho_hoy = lambda pid, grupo="": False
try:
    TU.aviso_prestart_pendiente(G)
    TU.aviso_prestart_pendiente(G)      # la pasada que provoca el components.html
    TU.aviso_prestart_pendiente(G)
finally:
    PS.hecho_hoy = _orig
_persiste = len(llamadas) == 3
ok &= _persiste
print(f"\n   {'✓' if _persiste else '‼️'} ⚠️ 3 pasadas seguidas → se abre {len(llamadas)}/3 "
      "(con el `pop` de v374 habría sido 1/3 y por eso se cerraba solo)")

# Descartar corta la insistencia, y volver a fichar la re-arma
TU._ps_descartar()
llamadas.clear()
_orig = PS.hecho_hoy
PS.hecho_hoy = lambda pid, grupo="": False
try:
    TU.aviso_prestart_pendiente(G)
finally:
    PS.hecho_hoy = _orig
_corta = len(llamadas) == 0 and st.session_state.get(f"_ps_visto_{PID}") is True
ok &= _corta
print(f"   {'✓' if _corta else '✗'} al descartar deja de salir, y queda marcado como visto")

# ── el código: la bandera NO se consume al mostrar ──
print("\n== el código ==")
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\timeclock_ui.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "aviso_prestart_pendiente")
cuerpo = ast.unparse(fn)
_sin_pop = "pop('_ps_aviso'" not in cuerpo.replace('"', "'") or "hecho_hoy" in cuerpo
_usa_get = "get('_ps_aviso')" in cuerpo.replace('"', "'")
ok &= _usa_get
print(f"   {'✓' if _usa_get else '‼️'} lee la bandera con `get`, no la consume con `pop`")
# la X del modal también descarta
_dlg = next(n for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.FunctionDef) and n.name == "_dialogo_prestart")
_dec = " ".join(ast.unparse(d) for d in _dlg.decorator_list)
_dismiss = "on_dismiss=_ps_descartar" in _dec
ok &= _dismiss
print(f"   {'✓' if _dismiss else '‼️'} cerrar con la X también descarta (`on_dismiss`), "
      "si no reaparecería para siempre")

# ── el literal `:material/` dentro de HTML crudo ──
print("\n== ⚠️ `:material/` dentro de `components.html` no es un icono, es texto ==")
_malas = []
for n in ast.walk(ast.parse(src)):
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("_chrono_mini", "_chronometer"):
        for a in n.args:
            if isinstance(a, (ast.Constant, ast.JoinedStr)) and ":material/" in ast.unparse(a):
                _malas.append(n.lineno)
ok &= not _malas
print(f"   {'✓' if not _malas else '‼️'} ninguna etiqueta de cronómetro lleva `:material/`: "
      f"{_malas or 'ok'}")

print("\n" + ("✅ v375 OK: el modal persiste entre pasadas, se descarta de las 3 formas y "
              "el cronómetro no enseña el literal" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
