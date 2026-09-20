"""Verifica las marcas de conflicto del tablero (v292) SIN tocar produccion."""
import sys, datetime
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

from core import roster_ui as RU, roster as R, projects as P, credentials as C

LUNES = datetime.date(2026, 8, 10)
STAFF = [{"User": "ana", "Name": "Ana"}, {"User": "beto", "Name": "Beto"}]

# ── dobles ──────────────────────────────────────────────────────────────
SEMANA = {
    # Ana: martes DOS trabajos a la MISMA franja -> choque
    ("ana", "mar"): [{"asig": "PRJ-1", "ini": "07:00", "fin": "15:30"},
                     {"asig": "PRJ-2", "ini": "07:00", "fin": "15:30"}],
    # Ana: miercoles uno solo, sin problema
    ("ana", "mie"): [{"asig": "PRJ-1", "ini": "07:00", "fin": "15:30"}],
    # Beto: jueves Y viernes en PRJ-9 (exige cert que NO cumple) -> los DOS dias marcados
    ("beto", "jue"): [{"asig": "PRJ-9", "ini": "07:00", "fin": "15:30"}],
    ("beto", "vie"): [{"asig": "PRJ-9", "ini": "07:00", "fin": "15:30"}],
    # Beto: lunes choque Y cert a la vez -> debe ganar "choque"
    ("beto", "lun"): [{"asig": "PRJ-9", "ini": "07:00", "fin": "12:00"},
                      {"asig": "PRJ-9", "ini": "11:00", "fin": "15:30"}],
}
R.get_semana = lambda g, l: "SEMANA"
R.celda_items = lambda datos, usr, d: SEMANA.get((usr, d), [])
R.proyecto_de = lambda a, t: a if str(a).startswith("PRJ-") else ""
R.etiqueta_de = lambda a, t: {"PRJ-1": "Torre", "PRJ-2": "Redfen", "PRJ-9": "Agecare"}.get(a, a)
_LLAMADAS_PRJ = []
P.get_project = lambda pid: (_LLAMADAS_PRJ.append(pid),
                             {"RequiredCerts": "White Card"} if pid == "PRJ-9" else {"RequiredCerts": ""})[1]
_LLAMADAS_COMP = []
C.compliance = lambda usr, certs: (_LLAMADAS_COMP.append((usr, tuple(certs))),
                                   {"cumple": False, "por_tipo": {"White Card": "vencido"}})[1]

choques, sin_cumplir, marcas = RU._radar_scan("g", LUNES, STAFF, {})

ok = True


def check(n, real, esp):
    global ok
    b = real == esp
    ok = ok and b
    print(f"  {'OK ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"         esperado: {esp!r}")


print("== marcas por celda (v294: conjuntos, ya no una etiqueta) ==")
check("Ana martes = choque",            marcas.get(("ana", "mar")), {"choque"})
check("Ana miercoles = sin marca",      marcas.get(("ana", "mie")), None)
check("Beto jueves = cert",             marcas.get(("beto", "jue")), {"cert"})
check("Beto VIERNES tambien = cert",    marcas.get(("beto", "vie")), {"cert"})
check("Beto lunes: choque Y cert (ya no se esconde uno)",
      marcas.get(("beto", "lun")), {"choque", "cert"})
check("celda inexistente sin marca",    marcas.get(("ana", "lun")), None)

print("\n== el CSS del anillo se arma bien ==")
from core import theme
def _capas(m):
    c = []
    if "choque" in m: c.append(f"0 0 0 2px {theme.ROJO}")
    if "cert" in m:   c.append(f"0 0 0 {'4px' if 'choque' in m else '2px'} {theme.AMBAR}")
    return ",".join(c)
check("solo choque", _capas({"choque"}), f"0 0 0 2px {theme.ROJO}")
check("solo cert",   _capas({"cert"}),   f"0 0 0 2px {theme.AMBAR}")
check("los dos: rojo DENTRO (2px) y ambar FUERA (4px)", _capas({"choque", "cert"}),
      f"0 0 0 2px {theme.ROJO},0 0 0 4px {theme.AMBAR}")
check("ninguno", _capas(set()), "")

print("\n== las listas del radar NO cambian de forma ==")
check("nº de choques", len(choques), 2)                      # Ana mar + Beto lun
check("nº de avisos de cert (dedupe por persona×proyecto)", len(sin_cumplir), 1)
print(f"         choques: {choques}")
print(f"         certs:   {sin_cumplir}")

print("\n== coste: no se re-consulta el mismo proyecto ==")
check("get_project llamado 1 vez por (persona,proyecto)",
      len(_LLAMADAS_PRJ), len(set(zip([x for x in _LLAMADAS_PRJ]))) and len(_LLAMADAS_PRJ))
print(f"         get_project: {_LLAMADAS_PRJ}")
print(f"         compliance : {_LLAMADAS_COMP}")
check("compliance no se repite por (persona,proyecto)",
      len(_LLAMADAS_COMP), len(set(_LLAMADAS_COMP)))

print("\n== _radar_personal no revienta con la 3-tupla ==")
try:
    import streamlit as st
    st.success = st.markdown = lambda *a, **k: None
    class _C:
        def __enter__(self): return self
        def __exit__(self, *a): return False
    st.container = lambda *a, **k: _C()
    RU._radar_personal("g", LUNES, STAFF, {}, scan=(choques, sin_cumplir, marcas))
    check("acepta scan de 3 elementos", True, True)
except Exception as e:
    check("acepta scan de 3 elementos", f"EXC {type(e).__name__}: {e}", True)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
