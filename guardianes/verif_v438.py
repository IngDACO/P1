"""Guardián de v438 — F1c: los DIAGRAMAS y las PLOMADAS, en inglés. Cierra F1.

Lo que protege:

 1. ⚠️ **Las CLAVES de `schedule_table` / `plumb_table` / `plumb_checks` siguen en
    español.** Las indexan `report.py` y `user_report.py` (`r["Actividad"]`,
    `r["Línea"]`, `r["Medida"]`…): traducirlas daría KeyError o una columna vacía.
 2. ⚠️ **Los NOMBRES de `schedule.ACTIVIDADES` NO se traducen.** Son DATO: se guardan
    en la hoja `Actividades` de cada proyecto, así que van con la migración del
    histórico, no aquí. Traducirlos dejaría los proyectos viejos en español y los
    nuevos en inglés, sin forma de casarlos.
 3. ⚠️ **El motor se importa con alias `_d`**, y ninguna variable puede llamarse así.
    En estos módulos `d` ya es una variable corriente (días, dicts) en 14 sitios, y
    Python marca el nombre local en el ÁMBITO ENTERO de la función: importar como
    `d` habría reventado las etiquetas con UnboundLocalError (el fallo de v437).
 4. Ningún `<text>` de los seis módulos queda en español.
 5. Los SVG se GENERAN y su texto sale en inglés (prueba funcional).
 6. ⚠️ Los SVG siguen sin `<defs>`/`<marker>`: svglib no los convierte y el diagrama
    desaparecería del PDF sin ningún error (regla v39).
"""
import ast
import re
import sys
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

MODS = ["core/plumb.py", "core/diagrams.py", "core/schedule.py",
        "core/rail_cut.py", "core/buffer_cut.py", "core/belting.py"]
ok = True
n = 0


def chk(t_, cond, det=""):
    global ok, n
    n += 1
    ok = ok and bool(cond)
    print(f"  {'OK  ' if cond else 'FALLO'} {t_}" + (f"  → {det}" if det and not cond else ""))


def sec(t_):
    print(f"\n{'─' * 70}\n{t_}\n{'─' * 70}")


# ── 1 ────────────────────────────────────────────────────────────
sec("1. Las CLAVES de las tablas siguen intactas (las indexan los informes)")
from core import schedule as SCH, plumb as PL                     # noqa: E402

_sch = SCH.build_schedule(4, date(2026, 1, 5), {})
_fila = SCH.schedule_table(_sch)[0]
chk("schedule_table conserva sus 5 claves",
    set(_fila) == {"Actividad", "Inicio", "Fin", "Duración (d)", "Peso (%)"}, str(set(_fila)))
_pl = PL.compute_plumb({"BKS": 1100, "RAIL": 62, "TKSW": 900, "LengthTemplate": 300,
                        "SF1": 40, "SF2": 40, "BSR": 1300, "BS": 1304,
                        "SG": 300, "TG": 60, "OMEGA_SIDE": "R"})
chk("plumb_table conserva sus 4 claves",
    set(PL.plumb_table(_pl)[0]) == {"Línea", "X inicial (mm)", "X final (mm)", "Desplazada"},
    str(set(PL.plumb_table(_pl)[0])))
chk("plumb_checks conserva sus 2 claves",
    set(PL.plumb_checks(_pl)[0]) == {"Medida", "Distancia (mm)"},
    str(set(PL.plumb_checks(_pl)[0])))
# ⚠️ y los informes tienen que seguir indexando ESAS claves
_ur = (RAIZ / "core" / "user_report.py").read_text(encoding="utf-8")
_idx = set(re.findall(r'r\["([^"]+)"\]', _ur))
chk("el informe del cliente indexa las claves que existen",
    {"Actividad", "Línea", "Medida"} <= _idx, str(sorted(_idx)))
# ⚠️ Las CLAVES se quedan, pero los VALORES que van dentro SI se traducen — y eso no
# lo veia ningun chequeo: `LINE_NAMES` no vive dentro de un <text>, asi que la seccion
# 4 no lo miraba, y `plumb_svg` usa LINE_SHORT. Se comprueba el valor entregado.
_valen = " ".join(str(r["Línea"]) for r in PL.plumb_table(_pl))
_valen += " " + " ".join(str(r["Medida"]) for r in PL.plumb_checks(_pl))
_valen += " " + " ".join(PL.LINE_SHORT.values())
chk("los VALORES de las tablas de plomada están en inglés",
    not __import__("re").search(r"[áéíóúñÑ]|\b(plomo|pared|riel|izquierd\w+|derech\w+|teóric\w+)\b",
                                _valen, __import__("re").I), _valen[:110])

# ── 2 ────────────────────────────────────────────────────────────
sec("2. Los nombres de ACTIVIDADES son DATO y NO se traducen")
# se leen del cronograma REAL que produce build_schedule, no de una constante
# cuyo nombre yo suponga (la constante es `PHASES`, no `ACTIVIDADES` — regla v135)
_nom = [a["nombre"] for a in _sch["activities"]]
_txt_act = " ".join(str(x) for x in _nom)
# NO vale un `or` sobre unos pocos nombres: traducir UNO seguiria pasando porque otro
# casa. Y contar "cuantos parecen espanoles" tampoco: 5 de los 11 no llevan ni acento
# ni palabra funcional ("Brackets / soportes"), asi que el umbral daba FALLO con el
# codigo CORRECTO. Se exigen TRES nombres concretos, verbatim.
# ⚠️ CADUCADO Y ACTUALIZADO en v453 (regla v385). Este chequeo exigia que los
# nombres siguieran en ESPAÑOL, y estaba bien mientras la hoja `Actividades` los
# guardaba asi: traducir solo el codigo habria dejado los proyectos viejos en
# espanol y los nuevos en ingles SIN forma de casarlos. En v453 se hizo la
# migracion del historico (123 filas en 1 batch, verificadas leyendo), asi que la
# afirmacion se INVIERTE: ahora lo que hay que proteger es que NO vuelvan al
# espanol y que el codigo y la hoja digan lo MISMO.
# ⚠️ v515 · Los tres nombres eran de `PHASES`, borrada. Se DERIVAN del catálogo, que es
# de donde salen hoy (trampa nº16). No es tautológico: lo que se compara es el
# cronograma RENDERIZADO contra el catálogo, o sea que la tubería entera —`plan_de`,
# `filas_de_etapas`, `build_schedule`— conserva los nombres. Y se exigen TODOS, no tres:
# con la lista entera, traducir UNO ya no se cuela por detrás de otro que casa.
from core import stages as _ST438                                   # noqa: E402
_FIJOS = [e[2] for e in _ST438.etapas(_ST438.PISTA_INSTALL)]
_faltan_act = [x for x in _FIJOS if x not in _nom]
chk("están en inglés y casan con el histórico ya migrado (v453)",
    not _faltan_act, str(_faltan_act))
_ES_ACT = [x for x in _nom if any(c in x for c in "áéíóúñ")]
chk("...y ninguno quedó a medias", not _ES_ACT, str(_ES_ACT))
# ⚠️ el chequeo no puede correr en vacío
chk("...y el chequeo ve actividades de verdad", len(_nom) >= 8, f"{len(_nom)}")

# ── 3 ────────────────────────────────────────────────────────────
sec("3. El motor se importa como `_d` y nada lo tapa")
for m in MODS:
    src = (RAIZ / m).read_text(encoding="utf-8")
    tr = ast.parse(src)
    _imp = any(isinstance(x, ast.ImportFrom) and x.module == "core.i18n"
               and any(a.name == "d" and a.asname == "_d" for a in x.names)
               for x in tr.body)                      # ⚠️ a nivel de MÓDULO (v342)
    _tapa = [x.lineno for x in ast.walk(tr)
             if (isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and x.id == "_d")
             or (isinstance(x, ast.arg) and x.arg == "_d")]
    chk(f"{Path(m).name:16} importa `d as _d` a nivel de módulo y nada lo tapa",
        _imp and not _tapa, f"imp={_imp} tapa={_tapa}")
# ⚠️ y NADIE puede importarlo como `d` pelado: `d` ya es variable en estos módulos
_malo = [m for m in MODS
         if re.search(r"^from core\.i18n import d\s*$",
                      (RAIZ / m).read_text(encoding="utf-8"), re.M)]
chk("ninguno lo importa como `d` pelado", not _malo, str(_malo))

# ── 4 ────────────────────────────────────────────────────────────
sec("4. Ningún <text> de los diagramas queda en español")
_ES = re.compile(r"[áéíóúñÑ]|\b(el|la|los|las|del|con|para|por|que|una|en|su|al|es|son|"
                 r"pared|riel|cabina|hueco|plomo|puerta|nivel|paradas|planta|vista|entre|"
                 r"corte|holgura|borde|revisar|piso|elevador|contrapeso|"
                 r"desplazamiento|apertura|ampliado|fondo|acceso|diseño|actividades|días)\b",
                 re.I)
_pat = re.compile(r">([^<>]*[a-záéíóúñA-ZÁÉÍÓÚÑ][^<>]*?)</text>")
_rest = []
for m in MODS:
    for i, l in enumerate((RAIZ / m).read_text(encoding="utf-8").splitlines(), 1):
        for c in _pat.findall(l):
            c2 = re.sub(r"\{[^}]*\}", "", c).strip()
            if c2 and _ES.search(c2):
                _rest.append(f"{Path(m).name}:{i} {c2[:40]!r}")
chk("0 etiquetas SVG en español", not _rest, str(_rest[:6]))
# ⚠️ el chequeo NO corre en vacío: tiene que haber <text> que mirar
_ntext = sum(len(_pat.findall((RAIZ / m).read_text(encoding="utf-8"))) for m in MODS)
chk("...y hay etiquetas SVG que vigilar", _ntext >= 30, f"{_ntext}")

# ── 5 · 6 ────────────────────────────────────────────────────────
sec("5-6. Los SVG se GENERAN, salen en inglés y svglib los sigue aceptando")
from core import diagrams as DG, rail_cut as RC, buffer_cut as BC, belting as BL  # noqa: E402
from core import calculations as CA                                # noqa: E402

_p = {"BKS": 1100, "RAIL": 62, "TKSW": 900, "SF1": 40, "SF2": 40, "BS": 1304,
      "BSR": 1300, "BT": 800, "FRAME": 30, "TS": 1750, "TK": 1400, "TKA": 50,
      "TKS": 30, "TSW": 100, "FS": 120, "OFFSET_CABIN": 0, "OFFSET_SIDE": "L",
      "SG": 300, "TG": 60, "OMEGA_SIDE": "R", "NS": 3, "WALL_LIMITING": False,
      # totales del survey: `calculate_limits` los exige para los offsets
      "WRT": 90, "FRT": 760, "ORT": 30, "WLT": 90, "FLT": 760, "OLT": 30}
_lim = CA.calculate_limits(_p)
_row = {"WR": 90, "FR": 760, "OR": 30, "WL": 90, "FL": 760, "OL": 30}
_lm = {c: _lim[f"LIMIT_{c}"] for c in ("WR", "FR", "OR", "WL", "FL", "OL")}
_best = {"rl": -5.5, "fb": 2.0, "fb_applied": 2.0, "total_off": 1,
         "matrix": [dict(_row), dict(_row), dict(_row)]}

SVGS = {
    "floor_plan":  lambda: DG.floor_plan_svg(_p, _lim, _row, 0, _lm, False, None,
                                             is_last=False, rl=-5.5, fb=2.0, n_floors=3),
    "shaft_iso":   lambda: DG.shaft_iso_svg(_p, _lim, _best, 3, _lm),
    "plumb":       lambda: PL.plumb_svg(_pl),
    "plumb_iso":   lambda: PL.plumb_iso_svg(_pl),
    "plumb_card":  lambda: PL.plumb_card_svg(_pl),
    "plumb_det":   lambda: PL.plumb_detail_svg(_pl),
    "schedule":    lambda: SCH.schedule_svg(_sch),
    # ⚠️ firmas LEÍDAS con inspect.signature, no supuestas (regla v135: me equivoqué
    # en las tres a la primera — compute_case1 lleva lfkk/lfgk delante, buffer_cut_svg
    # recibe el RESULTADO y no el hkp, y belting_svg toma solo la lista).
    "rail_caso1":  lambda: RC.rail_cut_svg(
        RC.compute_case1(2915.0, 2693.0, 2, 2, [12000.0, 12000.0]), 1, 2, 2),
    "rail_caso2":  lambda: RC.rail_cut_svg(
        # compute_case2 devuelve una LISTA y rail_cut_svg espera un dict: la UI real
        # lo envuelve en {"elevadores": res} (leido de rail_cut_ui.py:218, no supuesto)
        {"elevadores": RC.compute_case2(
            2915.0, 2693.0, [{"RZ": 120.0, "RO": 118.0, "RF": 90.0, "RB": 92.0}],
            "encima")}, 2),
    "buffer":      lambda: BC.buffer_cut_svg(BC.compute_buffer_cut(70.0, [55.0, 70.0, 80.0])),
    "belting":     lambda: BL.belting_svg(BL.compute_belting(85, 14045, [120.0, 85.0])),
}
ESPERA = {
    "floor_plan": ["FLOOR", "FRONT WALL — ACCESS", "SHAFT REAR", "Plan · top view"],
    "shaft_iso":  ["SHAFT ISOMETRIC VIEW", "Shaft width", "Car block"],
    "plumb":      ["FRONT WALL", "CHECK ON SITE", "X origin: left real wall"],
    "plumb_card": ["between the two plumb lines", "SET-OUT CARD"],
    "plumb_det":  ["SET-OUT DETAIL"],
    "schedule":   ["SCHEDULE AND PROGRESS", "Planned", "Actual", "days", "activities"],
    "rail_caso1": ["RAIL CUTTING", "standard stack", "trims the 1st rail"],
    "rail_caso2": ["Car", "Counterweight", "illustrative heights, not to scale"],
    "buffer":     ["BUFFER CUTTING", "CAR STICKER", "no cut"],
    "belting":    ["top floor", "Car", "position at enlarged scale"],
}
# ⚠️ El SVG del cronograma lleva los NOMBRES DE ACTIVIDAD, que son DATO y siguen en
# español a propósito (sección 2). Excluirlos NO es relajar el chequeo: es no medir
# aquí lo que otra sección afirma que debe seguir así.
_EXCL = {nom for nom in _nom}
try:
    from svglib.svglib import svg2rlg
except Exception:
    svg2rlg = None

import io                                                          # noqa: E402
for nom, gen in SVGS.items():
    try:
        svg = gen()
    except Exception as e:
        chk(f"{nom:12} se genera", False, f"{type(e).__name__}: {e}")
        continue
    txts = [re.sub(r"\{[^}]*\}", "", c).strip() for c in _pat.findall(svg)]
    malos = [t for t in txts if t and _ES.search(t) and t not in _EXCL]
    chk(f"{nom:12} sin español en su texto ({len(txts)} etiquetas)", not malos, str(malos[:4]))
    # ⚠️ Chequeo POSITIVO: "Planificado" no lleva acento ni palabra funcional, asi que
    # el detector de espanol no lo veia. Se exige que el ingles ESPERADO este ahi.
    if nom in ESPERA:
        _falta = [k for k in ESPERA[nom] if k not in svg]
        chk(f"{nom:12} trae su texto en inglés", not _falta, str(_falta))
    # ⚠️ regla v39: sin <defs>/<marker>, o svglib no lo convierte y desaparece del PDF
    chk(f"{nom:12} sigue sin <defs>/<marker>",
        "<marker" not in svg and "<defs" not in svg)
    if svg2rlg is not None:
        try:
            dib = svg2rlg(io.BytesIO(svg.encode("utf-8")))
            chk(f"{nom:12} svglib lo convierte", dib is not None)
        except Exception as e:
            chk(f"{nom:12} svglib lo convierte", False, f"{type(e).__name__}: {e}")

print(f"\n{'=' * 70}\n{n} comprobaciones — " + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
