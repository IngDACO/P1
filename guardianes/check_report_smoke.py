# -*- coding: utf-8 -*-
"""Smoke de v448: GENERAR el informe ADMIN y leer su texto.

⚠️ La lección de v437 (el mismo informe, su hermano de cliente): un `NameError`
dentro del `try/except` del veredicto **no revienta nada** — se registra y sigue —,
así que hay que CAPTURAR el log del módulo además de mirar el PDF. Y la de v438: un
barrido del FUENTE no mide lo que se ve; solo el texto RENDERIZADO lo dice.
"""
import io
import json
import logging
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

import streamlit as st                                             # noqa: E402
st.session_state["auth"] = {"usuario": "verif", "rol": "administrator",
                            "grupo": "cliente1", "nombre": "verif"}

ok = True


def chk(t_, cond, det=""):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


from pypdf import PdfReader                                        # noqa: E402
from core import projects as P, report, schedule as SCH, survey_calc  # noqa: E402

_prj = next((x for x in P.list_projects("cliente1", incluir_archivados=True)
             if x.get("ParamsJSON") and x.get("MatrizJSON")), None)
# ⚠️ v474 · Si la demo no tiene ningún proyecto con survey (v456 la vació), se cae a un
# caso CONSTRUIDO en vez de salir SIN DATOS: la afirmación de este guardián llevaba
# versiones sin comprobarse. Se prefieren los datos REALES cuando los hay.
if _prj is None:
    import fixture_survey as _FIX
    if not _FIX.valido():
        print("‼️ el fixture no lo digiere el cálculo: no se puede afirmar nada")
        sys.exit(1)
    _prj = _FIX.proyecto()
    print("   (demo sin survey: se usa el caso construido `fixture_survey`)")

_par = json.loads(_prj["ParamsJSON"])
_mat = json.loads(_prj["MatrizJSON"])
# ⚠️ `recalcular` NO devuelve `survey_original`/`analysis`/`bs_result`: la firma
# real de `generate_report` pide 12 argumentos (regla v135, comprobada ejecutando).
# Se rehacen las piezas que faltan con las MISMAS funciones que usa `survey_calc`,
# para que el informe reciba exactamente lo que recibe en produccion.
_r = survey_calc.recalcular(_par, _mat)
if _r is None:
    print("⚠️ `recalcular` devolvio None: el chequeo no puede afirmar nada")
    sys.exit(1)
import pandas as _pd                                                # noqa: E402
from core.calculations import apply_offsets as _ao, analyze_matrix as _am  # noqa: E402
from core.bs_logic import find_bs_step as _bs                        # noqa: E402
from core.survey_calc import SURVEY_COLS as _SC                      # noqa: E402
# ⚠️ `_survey_table` indexa `df.columns`: el informe recibe DATAFRAMES, no listas
# de dicts (lo dijo el AttributeError, no la firma). `apply_offsets` si toma records.
_df = _pd.DataFrame(_mat)
_orig = _df
_adj = _pd.DataFrame(_ao(_df.to_dict("records"), _r["limits"]))
_ana = _am(_adj.to_dict("records"), _r["limits"],
           wall_limiting=bool(_r["all_params"].get("WALL_LIMITING")))
try:
    _bsr = _bs(_r["all_params"], _r["limits"])
except Exception as _e:
    _bsr = {}
_sch = SCH.build_schedule(int(_par.get("NS") or 2),
                          __import__("datetime").date(2026, 3, 2), {})
_ia = {"_ok": True, "parametros": "Geometry is consistent.",
       "estado_inicial": "Two levels are out of limit.",
       "desplazamientos": "Shift the block 6 mm.",
       "solucion_optima": "RL -6.0, FB 0.0.",
       "evasion_pared": "No limiting wall.",
       "bsr_vs_bs": "BSR matches BS.",
       "consideraciones": "Check the brackets."}


class _Cazador(logging.Handler):
    def __init__(self):
        super().__init__()
        self.msgs = []

    def emit(self, rec):
        self.msgs.append(rec.getMessage())


_caz = _Cazador()
_lg = logging.getLogger("core.report")
_lg.addHandler(_caz)
try:
    _pdf = report.generate_report(
        project_params=_r["all_params"], calculated=_r["limits"],
        survey_original=_orig, survey_adjusted=_adj, lim_map=_r["lim_map"],
        analysis=_ana,
        optimizer_result={"best": _r["best"], "solutions": [_r["best"]],
                          "log": [], "total": 0, "valid": 0},
        bs_result=_bsr, survey_cols=list(_SC),
        interpretation=_ia, schedule=_sch, plumb=_r.get("plumb"))
except TypeError as e:
    # ⚠️ Regla v135: si la firma no es la que supongo, se DICE, no se adivina.
    import inspect
    print(f"  ⚠️ firma distinta: {e}")
    print(f"     real: {inspect.signature(report.generate_report)}")
    sys.exit(1)
finally:
    _lg.removeHandler(_caz)

chk(f"el informe ADMIN se genera ({len(_pdf) // 1024} KB)", len(_pdf) > 20000)
chk("nada se cayó a un `except` (log del módulo vacío)", not _caz.msgs, str(_caz.msgs))

_txt = " ".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(_pdf)).pages)
for esp in ("PARÁMETROS DE ENTRADA", "LÍMITES GEOMÉTRICOS", "MATRIZ SURVEY",
            "Interpretación", "Reporte generado", "Lado del Omega"):
    chk(f"ya no dice «{esp}»", esp not in _txt)
for ing in ("INPUT PARAMETERS", "GEOMETRIC LIMITS", "SURVEY MATRIX",
            "Interpretation", "Automatically generated report", "Omega side"):
    chk(f"y sí «{ing}»", ing in _txt)

# ⚠️ Y la lección de v438: un barrido del FUENTE se dejó CINCO etiquetas; lo que
# mide de verdad es el texto RENDERIZADO. Se buscan restos de español en el PDF.
import re as _re                                                   # noqa: E402
import unicodedata as _u                                           # noqa: E402


def _sin(x):
    return "".join(c for c in _u.normalize("NFD", x.lower())
                   if _u.category(c) != "Mn")


_ES = {"de", "la", "el", "los", "las", "del", "por", "para", "con", "sin", "que",
       "una", "unos", "unas", "segun", "cada", "sobre", "entre", "hasta", "desde",
       "limite", "limites", "matriz", "calculo", "parametros", "pisos", "paso",
       "pasos", "valores", "hueco", "cabina", "pared", "riel", "rieles"}
# ⚠️ EXCLUSIÓN DELIBERADA: los nombres de ACTIVIDAD del cronograma son DATO — se
# guardan en la hoja `Activities`, así que traducirlos dejaría los proyectos viejos en
# español y los nuevos en inglés, sin forma de casarlos. Van con la migración del
# histórico, no con la traducción (v438).
# ⚠️ v515: salían de `schedule.PHASES`, que se BORRÓ. Ahora del CATÁLOGO, que es donde
# viven. Con el `getattr(..., [])` de antes este conjunto habría quedado VACÍO y las
# actividades del informe habrían empezado a contarse como texto sin traducir: un rojo
# en falso, que es la otra cara de la trampa nº30.
from core import stages as _ST2                                    # noqa: E402
_ACTIV = {_sin(e[2]) for e in _ST2.ETAPAS}
_ACTIV |= {_sin(a[0]) for _v in _ST2.ACTIVIDADES.values() for a in _v}
_ACTIV |= {_sin(str(a.get("nombre", ""))) for a in _sch.get("activities", [])}

_malas = []
for _ln in _txt.splitlines():
    if _sin(_ln.strip()) in _ACTIV:
        continue                       # nombre de actividad: es DATO
    _p = set(_re.findall(r"[a-záéíóúñ]+", _sin(_ln)))
    if len(_p & _ES) >= 2:
        _malas.append(_ln.strip()[:72])
chk("0 líneas con español en el PDF RENDERIZADO (salvo nombres de actividad)",
    not _malas, f"{len(_malas)}: {_malas[:4]}")
# ⚠️ La exclusión se AFIRMA, no se da por hecha: si ningún nombre de actividad apareciera
# en el PDF, la lista de arriba no estaría excluyendo nada y el «0 líneas» de antes sería
# un paso en vacío (trampa nº1). La etiqueta decía «siguen en español» desde antes de la
# migración de v453; se corrige aquí porque un rótulo que miente sobre lo que mide invita
# a leer verde donde no lo hay.
chk("...y los nombres de actividad SÍ llegan al PDF (o la exclusión no excluiría nada)",
    bool(_ACTIV) and any(_sin(l.strip()) in _ACTIV for l in _txt.splitlines()),
    f"{len(_ACTIV)} nombres")
# ⚠️ Un «0» no vale si la sonda no ve el caso malo (trampa nº12).
chk("...y la sonda SABE ver una línea española",
    len({"de", "la", "limite"} & set(_re.findall(r"[a-záéíóúñ]+",
                                                 _sin("valores de la matriz limite")))) >= 2)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
