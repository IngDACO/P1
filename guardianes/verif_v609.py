# -*- coding: utf-8 -*-
"""v609 · EL MOTOR EN EL CATÁLOGO Y LA MIGRACIÓN A PROPÓSITO — decisión del usuario (27/10/2026):
«Vamos a crear esta actividad dentro de shaft climb & bedplates y le vamos a poner 5% que vamos a
tomar del 17% de install motor bedplate. También vamos a renombrar esta sección a shaft climb,
bedplate & motor».

Lo que protege:
  (a) el juego nuevo (`2026-10-27`): «Install motor (machine)» 5 % junto a «Install motor
      bedplate» 12 %, la etapa renombrada, y NADA más cambiado (comparado con el catálogo de
      antes, sacado de git en `bd4e406`);
  (b) ⚠️ el juego anterior es MIGRABLE de verdad: mismas etapas en el mismo orden, ninguna
      actividad quitada ni renombrada, y solo la etapa declarada cambia de pesos;
  (c) ⚠️ `migrar_catalogo` (con el libro sustituido, `fixture_guardado`): en UNA lectura y UNA
      escritura pasa el plan a la versión de hoy, renombra la etapa en el cronograma de la obra,
      recalcula esa etapa con lo acreditado y la obra con ella, y lo deja en la auditoría; se
      niega con un juego no migrable o un crédito que ya no existe, y no escribe nada entonces;
  (d) sin migrar, una obra del juego viejo sigue en solo lectura (lo de siempre); migrada, no.
"""
import json
import os
import subprocess
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "admin", "nombre": "Admin", "rol": "administrator",
                            "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


import fixture_guardado as FX                                     # noqa: E402

from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402

VIEJA, NUEVA = "2026-09-22", "2026-10-27"
NOMBRE_VIEJO, NOMBRE_NUEVO = "Shaft Climb & Bedplates", "Shaft Climb, Bedplate & Motor"

# El catálogo de ANTES, tal como estaba desplegado (v608, `bd4e406`): fijo, no HEAD.
_src = subprocess.run(["git", "show", "bd4e406:survey_app/core/stages.py"], cwd=RAIZ,
                      capture_output=True, text=True, encoding="utf-8").stdout
OLD = {}
exec(compile(_src, "stages_v608", "exec"), OLD)

# ═════════════════════════════════════════════════════════════════
sec("1. El juego nuevo")
chk("el catálogo de antes se pudo leer de git (la prueba vale)", OLD.get("VERSION") == VIEJA, OLD.get("VERSION"))
chk("versión nueva", S.VERSION == NUEVA, S.VERSION)
chk("la aritmética cuadra (cada etapa y cada pista suman 100)", S.validar() == [], S.validar())
_e6 = dict(((p, n), x) for p, n, x, _w in S.ETAPAS)
chk("la etapa se llama «Shaft Climb, Bedplate & Motor»", _e6.get(("install", 6)) == NOMBRE_NUEVO)
_a6 = S.actividades("install", 6)
_n6 = [a[0] for a in _a6]
chk("«Install motor bedplate» 17 → 12", dict((a[0], a[1]) for a in _a6).get("Install motor bedplate") == 12)
chk("«Install motor (machine)» 5 %, NO condicional, justo detrás del bedplate",
    ("Install motor (machine)", 5, False) in _a6
    and _n6.index("Install motor (machine)") == _n6.index("Install motor bedplate") + 1, _n6)
chk("el peso de la etapa en su pista NO cambia (13)", [w for p, n, _x, w in S.ETAPAS if (p, n) == ("install", 6)] == [13])

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ El juego anterior es migrable de verdad")
_m = S.MIGRABLES.get(VIEJA) or {}
chk("el juego anterior está en MIGRABLES", bool(_m))
chk("mismas etapas, en el MISMO orden (los créditos guardan el orden de etapa)",
    [(p, n) for p, n, _x, _w in S.ETAPAS] == [(p, n) for p, n, _x, _w in OLD["ETAPAS"]])
_old_n = {a[0] for v in OLD["ACTIVIDADES"].values() for a in v}
_new_n = {a[0] for v in S.ACTIVIDADES.values() for a in v}
chk("⚠️ ninguna actividad quitada ni renombrada (un crédito no puede quedar colgando)",
    _old_n <= _new_n, sorted(_old_n - _new_n))
chk("...y la única nueva es la del motor", _new_n - _old_n == {"Install motor (machine)"}, _new_n - _old_n)
_cambian = sorted(k for k in S.ACTIVIDADES if S.ACTIVIDADES[k] != OLD["ACTIVIDADES"].get(k))
chk("⚠️ solo cambian los pesos de las etapas que MIGRABLES recalcula", _cambian == sorted(_m.get("etapas") or []),
    (_cambian, _m.get("etapas")))
_ren = {k: v for k, v in _m.get("renombres", {}).items()}
chk("los renombres declarados son los de verdad",
    all(dict(((p, n), x) for p, n, x, _w in OLD["ETAPAS"])[k] == v[0] and _e6[k] == v[1] for k, v in _ren.items())
    and len(_ren) == sum(1 for (p, n, x, _w), (_p2, _n2, x2, _w2) in zip(OLD["ETAPAS"], S.ETAPAS) if x != x2))
chk("las informativas no cambian", S.INFORMATIVAS == OLD["INFORMATIVAS"])


# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ migrar_catalogo (libro sustituido)")


def _prj(pid, tipo, version=VIEJA, cond=()):
    return {"ID": pid, "Group": "cliente1", "Name": "ZZ " + pid, "Type": tipo, "Progress": "0",
            "Status": "In progress", "ManualStatus": "",
            "StagePlanJSON": json.dumps({"version": version, "tipo": tipo, "condicionales": list(cond),
                                         "pct_ripout": 50.0})}


_E6 = ["Install rings to top", "Install car rails to top", "Install CW rails to top",
       "Install motor bedplate", "Install single bedplate", "Seal machine room / shaft penetrations"]


def _montar(prj, orden6, extra_cred=()):
    _plan = SP.plan_de_obra(dict(prj, StagePlanJSON=json.dumps(dict(json.loads(prj["StagePlanJSON"]), version=NUEVA))))
    cred = [{"ID": "SP-%d" % i, "StageOrder": str(orden6), "Activity": n, "Pct": "100", "WorkDate": "2026-10-1%d" % i}
            for i, n in enumerate(_E6)] + list(extra_cred)
    acts = {i: {"Name": (NOMBRE_VIEJO if i == orden6 else e["nombre"]), "Weight": str(e["peso"]),
                "Progress": ("100" if i == orden6 else "0"),
                "ActualStartDate": ("2026-10-10" if i == orden6 else ""),
                "ActualEndDate": ("2026-10-15" if i == orden6 else "")}
            for i, e in enumerate(_plan, start=1)}
    return FX.montar(SP, P, prj, creditos=cred, actividades=acts, plan=_plan)


_inst = _prj("PRJ-T1", "Installation")
chk("ANTES de migrar, una obra del juego viejo está en solo lectura", SP.version_desfasada(_inst) == VIEJA)
m = _montar(_inst, 6)
try:
    ok_, msg = SP.migrar_catalogo("PRJ-T1", "cliente1", _inst, quien="owner")
    _ae = m.actividades_escritas()
    _ob = m.obra_escrita()
    chk("migra", ok_, msg)
    chk("⚠️ UNA lectura y UNA escritura (como `acreditar`)", m.cuenta() == {"leer": 1, "escribir": 1, "append": 0}, m.cuenta())
    chk("⚠️ la etapa, recalculada con lo acreditado: 100 → 95 (el motor, sin marcar, pesa 5)",
        float((_ae.get(6) or {}).get("Progress", -1)) == 95.0, _ae.get(6))
    chk("...y como ya no está completa, pierde su fin real (la regla de siempre)",
        (_ae.get(6) or {}).get("ActualEndDate") == "", _ae.get(6))
    chk("el cronograma de la obra lleva el nombre NUEVO de la etapa", (_ae.get(6) or {}).get("Name") == NOMBRE_NUEVO)
    chk("no toca las otras etapas", set(_ae) == {6}, sorted(_ae))
    _pj = json.loads(_ob.get("StagePlanJSON", "{}"))
    chk("el plan de la obra pasa a la versión de hoy y lo demás no cambia",
        _pj == dict(json.loads(_inst["StagePlanJSON"]), version=NUEVA), _pj)
    chk("el avance de la obra se recalcula con la etapa nueva", "Progress" in _ob and float(_ob["Progress"]) > 0, _ob)
    chk("⚠️ queda en la auditoría, con la acción que lo explica",
        len(m.auditado) == 1 and m.auditado[0][1].get("accion") == "catalogue %s -> %s" % (VIEJA, NUEVA)
        and "StagePlanJSON" in m.auditado[0][0][2], m.auditado)
    chk("...y lo dice, con las dos versiones", VIEJA in msg and NUEVA in msg, msg)
    chk("ninguna fila AJENA tocada (la fila 2 de cada hoja es de otra obra)",
        all(FX._a1(a1)[0] != 2 for h in ("Activities", "Projects") for a1, _v in m._escritas(h)))
finally:
    m.restaurar()
_mig = dict(_inst, StagePlanJSON=_ob.get("StagePlanJSON", _inst["StagePlanJSON"]))
chk("DESPUÉS de migrar, la obra ya no está en solo lectura", SP.version_desfasada(_mig) == "")

# Ripout + Installation: la etapa de instalación 6 es la 10 de la obra.
_comb = _prj("PRJ-T2", "Ripout + Installation", cond=("Rip out mechanical components - traction",))
_comb_n = dict(_comb, StagePlanJSON=json.dumps(dict(json.loads(_comb["StagePlanJSON"]), version=NUEVA)))
_o = next(i for i, e in enumerate(SP.plan_de_obra(_comb_n), start=1)
          if e["pista"] == "install" and e["numero"] == 6)
m = _montar(_comb, _o)
try:
    ok_, msg = SP.migrar_catalogo("PRJ-T2", "cliente1", _comb)
    _ae = m.actividades_escritas()
    chk("una obra combinada: se toca SU etapa (la %d), no la 6 de la lista" % _o,
        ok_ and set(_ae) == {_o} and float(_ae[_o]["Progress"]) == 95.0 and _ae[_o]["Name"] == NOMBRE_NUEVO, (_o, _ae))
finally:
    m.restaurar()

_rip = _prj("PRJ-T3", "Ripout", cond=("Rip out mechanical components - traction",))
m = FX.montar(SP, P, _rip, plan=SP.plan_de_obra(dict(_rip, StagePlanJSON=json.dumps(
    dict(json.loads(_rip["StagePlanJSON"]), version=NUEVA)))))
try:
    ok_, msg = SP.migrar_catalogo("PRJ-T3", "cliente1", _rip)
    chk("un desmontaje solo (sin esa etapa): pasa de versión y no toca su cronograma",
        ok_ and not m.actividades_escritas()
        and json.loads(m.obra_escrita().get("StagePlanJSON", "{}")).get("version") == NUEVA, (msg, m.actividades_escritas()))
finally:
    m.restaurar()

for _etq, _pp, _extra in (("ya en la versión de hoy", _prj("PRJ-T4", "Installation", version=NUEVA), ()),
                          ("de un juego que NO es migrable", _prj("PRJ-T5", "Installation", version="2020-01-01"), ()),
                          ("con un crédito que el juego de hoy no tiene", _prj("PRJ-T6", "Installation"),
                           ({"ID": "SP-X", "StageOrder": "6", "Activity": "Actividad que ya no existe", "Pct": "100"},))):
    m = _montar(_pp, 6, extra_cred=_extra)
    try:
        ok_, msg = SP.migrar_catalogo(_pp["ID"], "cliente1", _pp)
        _esc = [x for x in m.libro.llamadas if x[0].startswith("escribir")]
        if _etq == "ya en la versión de hoy":
            chk("⚠️ %s: no hace nada (ni lee)" % _etq, ok_ and not _esc and not m.libro.llamadas, (msg, m.libro.llamadas))
        else:
            chk("⚠️ %s: se NIEGA y no escribe nada" % _etq, not ok_ and not _esc, (msg, _esc))
    finally:
        m.restaurar()

# ═════════════════════════════════════════════════════════════════
sec("4. El agente del parte ve la actividad nueva")
from core import parte_agente as AG                               # noqa: E402
_t, _c = AG.plan_en_codigos(S.plan_de("Installation", ()))
chk("el plan que lee el agente lleva «Install motor (machine)» con su código",
    any(v[2] == "Install motor (machine)" for v in _c.values()) and "Install motor (machine)" in _t)
chk("...y la clave de las lecturas cambia con el plan (los partes sin revisar se releen)",
    AG.clave("x", S.plan_de("Installation", ())) != AG.clave("x", OLD["plan_de"]("Installation", ())))

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
