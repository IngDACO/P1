"""¿Está cada CASO donde tiene que estar? (los totales no lo dicen)

Sembrar 38 asignaciones no sirve de nada si el solape no solapa o el sábado no está.
Aquí se comprueba caso por caso, leyendo lo que quedó en la hoja.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator", "nombre": "dmoreno"}

from core import clock, credentials as CR, roster as R            # noqa: E402

G = "cliente1"

# ⚠️ Este guardián afirma que la DEMO CONTIENE cada caso que la interfaz debe saber
# pintar. Si la demo está vacía a propósito (v456), no hay nada que afirmar: sale con
# código 2 = SIN DATOS, ni verde (sería un OK que no comprobó nada, trampa nº1) ni rojo
# (no hay nada roto). Vuelve a servir en cuanto se siembren datos otra vez.
from core import projects as _P                                   # noqa: E402
_DEMO_VACIA = not _P.list_projects(G, incluir_archivados=True, incluir_internos=True)

# ⚠️ CADUCÓ POR EL CALENDARIO, no por un cambio de código: miraba
# `lunes_de(today())`, así que se ponía rojo TODOS LOS LUNES — los casos sembrados
# viven en la semana en que se sembraron (2026-08-24), no en la que hoy sea actual.
# Un ancla sobre un blanco móvil no es una afirmación: lo que este chequeo quiere
# decir es «la demo CONTIENE cada caso que la interfaz tiene que saber pintar», así
# que se buscan en TODAS las semanas con datos y se dice en cuál está cada uno.
_SEMANAS = sorted({str(r.get("Semana", "")) for r in R._roster_records()
                   if str(r.get("Grupo", "")) == G and str(r.get("Semana", ""))})
_TODAS = {s: R.get_semana(G, s) for s in _SEMANAS}
LUNES = R.lunes_de(clock.today(G))
datos = R.get_semana(G, LUNES)
ok = True


def en_alguna(fn):
    """(hay_caso, semanas_donde) recorriendo todas las semanas sembradas."""
    donde = [s for s, d in _TODAS.items() if fn(d)]
    return bool(donde), donde


def check(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")


def _mins(t):
    hh, mm = str(t).split(":")
    return int(hh) * 60 + int(mm)


def _dobles(d):
    return [(u, dd) for u in d for dd in R.DIAS_TODOS
            if len([i for i in R.celda_items(d, u, dd)
                    if not i["asig"].startswith(("OFF", "LEAVE", "FORMACION"))]) > 1]


def _solapes(d):
    out = []
    for u in d:
        for dd in R.DIAS_TODOS:
            its = [i for i in R.celda_items(d, u, dd) if i["ini"] and i["fin"]]
            for x in range(len(its)):
                for y in range(x + 1, len(its)):
                    a, b = its[x], its[y]
                    if _mins(a["ini"]) < _mins(b["fin"]) \
                       and _mins(b["ini"]) < _mins(a["fin"]):
                        out.append((u, dd))
    return out


def _estados(d):
    return sorted({i["asig"] for u in d for dd in R.DIAS_TODOS
                   for i in R.celda_items(d, u, dd) if i["asig"] in R.ESTADOS})


def _sab(d):
    return [(u, i["asig"]) for u in d for i in R.celda_items(d, u, "sab")]


# ── la semana CONSTRUIDA (v474) ───────────────────────────────────────────────
# ⚠️ Antes esto salía SIN DATOS desde que v456 vació la demo. Los detectores de abajo
# son los mismos; lo que cambia es que ahora hay SIEMPRE una semana con cada caso, así
# que la afirmación pasa a ser sobre el CÓDIGO —que sabe leerlos— y no sobre lo que
# alguien haya sembrado. La forma es la de `get_semana`: {usuario: {dia: celda}}.
_FIX = {
    "ana": {  # dos obras el mismo día, y además SOLAPADAS
        "lun": {"items": [{"a": "PRJ-X1", "i": "07:00", "f": "12:00"},
                          {"a": "PRJ-X2", "i": "11:00", "f": "15:30"}]},
        "sab": {"items": [{"a": "PRJ-X1", "i": "", "f": ""}]},
    },
    "luis": {  # dos obras el mismo día SIN solaparse, y los tres estados
        "mar": {"items": [{"a": "PRJ-X1", "i": "07:00", "f": "11:00"},
                          {"a": "PRJ-X2", "i": "12:00", "f": "15:30"}]},
        "mie": {"items": [{"a": "OFF", "i": "", "f": ""}]},
        "jue": {"items": [{"a": "LEAVE", "i": "", "f": ""}]},
        "vie": {"items": [{"a": "FORMACION", "i": "", "f": ""}]},
    },
}
# una semana SIN ninguno de los casos, para validar que los detectores no inventan
_LIMPIA = {"ana": {"lun": {"items": [{"a": "PRJ-X1", "i": "07:00", "f": "15:30"}]}}}

print("== 0) los detectores, sobre una semana CONSTRUIDA ==")
check("ve las DOS obras en un mismo día", bool(_dobles(_FIX)), True)
check("ve el SOLAPE de verdad", bool(_solapes(_FIX)), True)
check("...y NO confunde dos turnos seguidos con un solape",
      [u for u, d in _solapes(_FIX)], ["ana"])
check("ve los tres ESTADOS", _estados(_FIX), ["FORMACION", "LEAVE", "OFF"])
check("ve el SÁBADO", bool(_sab(_FIX)), True)
print("   ¿y NO inventan sobre una semana limpia?")
check("   sin dobles", _dobles(_LIMPIA), [])
check("   sin solapes", _solapes(_LIMPIA), [])
check("   sin estados", _estados(_LIMPIA), [])
check("   sin sábado", _sab(_LIMPIA), [])

if _DEMO_VACIA or not _SEMANAS:
    print("\n(la demo está vacía: lo de abajo es sobre los datos sembrados y se omite)")
    print("\n" + ("✅ los detectores leen cada caso" if ok else "⚠️ REVISAR"))
    sys.exit(0 if ok else 1)

# 1 · alguien con DOS obras el mismo día
_hay, _donde = en_alguna(lambda d: _dobles(d))
check("hay un día con DOS asignaciones (vista del día, v387)", _hay, True)
print(f"         semanas: {_donde}")

# 2 · un SOLAPE de verdad
_hay, _donde = en_alguna(lambda d: _solapes(d))
check("hay un CHOQUE de turno (radar, v292)", _hay, True)
print(f"         semanas: {_donde}")

# 3 · OFF y Leave
_hay, _donde = en_alguna(lambda d: set(_estados(d)) >= {"LEAVE", "OFF"})
check("hay OFF y Leave (vista Libres)", _hay, True)
print(f"         semanas: {_donde}")

# 4 · sábado trabajado
_hay, _donde = en_alguna(lambda d: _sab(d))
check("hay SÁBADO trabajado (columna extra de v390)", _hay, True)
print(f"         semanas: {_donde}")

# 5 · la columna del sábado se abre sola EN ESA MISMA semana
#     ⚠️ No vale «en alguna»: el sábado tiene que abrirlo la semana que lo tiene.
check("`dias_con_datos` abre el sábado donde hay sábado",
      all("sab" in R.dias_con_datos(_TODAS[s]) for s in _donde) and bool(_donde), True)

# 6 · alguien sin asignar
from core import auth                                             # noqa: E402
campo = [str(u.get("Usuario")) for u in auth.list_users()
         if str(u.get("Rol")) == "campo" and str(u.get("Grupo")) == G]
_hay, _donde = en_alguna(
    lambda d: [u for u in campo
               if not any(R.celda_items(d, u, dd) for dd in R.DIAS_TODOS)])
check("alguien SIN asignar (cobertura / «sin plan»)", _hay, True)
print(f"         semanas: {_donde}")

# 7 · credenciales en los tres estados
est = {}
for u in campo:
    for c in CR.list_for(u):
        s = CR.status(str(c.get("Vencimiento", "")))
        est[s] = est.get(s, 0) + 1
check("credenciales en los TRES estados",
      sorted(k for k in est if k), ["por_vencer", "vencido", "vigente"])
print(f"         {est}")

# 8 · el trabajo de catálogo resuelve etiqueta y color
idx = R.trabajos_idx(G)
trab = [t for t in R.list_trabajos(G)]
check("los trabajos del catálogo resuelven en el índice",
      all(str(t.get("ID")) in idx for t in trab), True)

print("\n" + ("TODO OK — la app tiene qué enseñar en todas esas pantallas"
              if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
