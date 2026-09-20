# -*- coding: utf-8 -*-
"""`verif_sim_f` deja de depender de que la demo esté sembrada.

⚠️ Este guardián afirmaba «la DEMO CONTIENE cada caso», que es una afirmación sobre
los DATOS, no sobre el código — así que con la demo vacía (v456) no había nada que
decir y salía SIN DATOS. Se reorienta a lo que sí sobrevive y además es más útil:
**que las funciones del roster SEPAN LEER cada caso** (dos obras el mismo día, un
solape real, los estados y el sábado). Los detectores son los mismos; lo que cambia es
que la semana se construye en vez de buscarse.

⚠️ Y cada detector se valida contra su contrario: sobre una semana SIN el caso tiene
que devolver vacío. Sin eso, un detector roto que devolviera siempre algo pasaría —
que es justo el «OK en vacío» que el mecanismo de SIN DATOS existía para no fingir.
"""
import ast
import io

P = "verif_sim_f.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''from core import projects as _P                                   # noqa: E402
if not _P.list_projects(G, incluir_archivados=True, incluir_internos=True):
    print("⚠️ la demo está vacía: no hay casos que verificar")
    sys.exit(2)
'''

NUEVO = '''from core import projects as _P                                   # noqa: E402
_DEMO_VACIA = not _P.list_projects(G, incluir_archivados=True, incluir_internos=True)
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)

# la parte que recorre las semanas SEMBRADAS solo tiene sentido si hay datos
VIEJO2 = '''_SEMANAS = sorted({str(r.get("Semana", "")) for r in R._roster_records()
                   if str(r.get("Grupo", "")) == G and str(r.get("Semana", ""))})
assert _SEMANAS, "no hay ni una semana con datos: el chequeo no puede afirmar nada"
'''
NUEVO2 = '''_SEMANAS = sorted({str(r.get("Semana", "")) for r in R._roster_records()
                   if str(r.get("Grupo", "")) == G and str(r.get("Semana", ""))})
'''
if s.count(VIEJO2) != 1:
    raise SystemExit("ancla 2 no unica: %d" % s.count(VIEJO2))
s = s.replace(VIEJO2, NUEVO2)

# y el bloque nuevo: la semana CONSTRUIDA, delante de los casos
ANCLA = "# 1 · alguien con DOS obras el mismo día"
BLOQUE = '''# ── la semana CONSTRUIDA (v474) ───────────────────────────────────────────────
# ⚠️ Antes esto salía SIN DATOS desde que v456 vació la demo. Los detectores de abajo
# son los mismos; lo que cambia es que ahora hay SIEMPRE una semana con cada caso, así
# que la afirmación pasa a ser sobre el CÓDIGO —que sabe leerlos— y no sobre lo que
# alguien haya sembrado. La forma es la de `get_semana`: {usuario: {dia: celda}}.
_FIX = {
    "ana": {  # dos obras el mismo día, y además SOLAPADAS
        "lun": {"items": [{"asig": "PRJ-X1", "ini": "07:00", "fin": "12:00"},
                          {"asig": "PRJ-X2", "ini": "11:00", "fin": "15:30"}]},
        "sab": {"items": [{"asig": "PRJ-X1", "ini": "", "fin": ""}]},
    },
    "luis": {  # dos obras el mismo día SIN solaparse, y los tres estados
        "mar": {"items": [{"asig": "PRJ-X1", "ini": "07:00", "fin": "11:00"},
                          {"asig": "PRJ-X2", "ini": "12:00", "fin": "15:30"}]},
        "mie": {"items": [{"asig": "OFF", "ini": "", "fin": ""}]},
        "jue": {"items": [{"asig": "LEAVE", "ini": "", "fin": ""}]},
        "vie": {"items": [{"asig": "FORMACION", "ini": "", "fin": ""}]},
    },
}
# una semana SIN ninguno de los casos, para validar que los detectores no inventan
_LIMPIA = {"ana": {"lun": {"items": [{"asig": "PRJ-X1", "ini": "07:00", "fin": "15:30"}]}}}

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
    print("\\n(la demo está vacía: lo de abajo es sobre los datos sembrados y se omite)")
    print("\\n" + ("✅ los detectores leen cada caso" if ok else "⚠️ REVISAR"))
    sys.exit(0 if ok else 1)

# 1 · alguien con DOS obras el mismo día'''

if s.count(ANCLA) != 1:
    raise SystemExit("ancla 3 no unica: %d" % s.count(ANCLA))
s = s.replace(ANCLA, BLOQUE)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_sim_f.py: semana construida + detectores validados en las dos direcciones")
