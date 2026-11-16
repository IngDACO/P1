# -*- coding: utf-8 -*-
"""v681 · Ciclo 4 → mejoras 1/3: el Survey y el informe del cliente.

Visto ejercitando el ciclo 4 en producción (PRJ-0045, plano y matriz de prueba de 12 paradas, Caso 1 con muro en la
parada 4 lado R) y decidido con el usuario el 16/11/2026:
- H1 · el PDF del cliente decía «Main action: shift the car block 18.0 mm to the right» con RL +18 y, debajo, «18.0 mm
  to the LEFT» (lo bueno: la app define RL+ = izquierda).
- H3 · «un muro limitante es aquel que no puede ser cortado»: si hace falta, se empuja la cabina hacia atrás hasta
  esquivarlo; los demás niveles sí se cortan; cortar lo menos posible; y (opción a) ninguna solución deja el muro por
  encima de su límite, vaya RL hacia donde vaya. El informe pedía «cut 17.0 mm on the right side» en el muro.
- H11 · WL/WR (y OL/OR) se miden hasta la LÍNEA del riel: el dibujo contaba un RAIL de más («Shaft width 1902»).
- H13 · reabrir el Survey desde la obra perdía la configuración (el muro volvía a «N»); H12 · y no llevaba al Survey.
- H2 · el informe archivado al guardar en una obra iba sin identidad; H12b · «Model —» siempre.
- H4 · «Limiting stop» 20 con 12 paradas: el muro se ignoraba en silencio. H5 · filas 0–11 frente a pisos 1–12.
- H16 · el historial del Survey guardaba el FB del barrido. Y de paso: el informe interno con frases en español, y el
  último piso del lado del controlador se cortaba contra el límite normal (el optimizador cuenta con −70 mm).
"""
import ast
import io
import os
import re
import sys

RAIZ = r"C:\Users\diego\P1\survey_app"
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
FALLOS = []


def chk(nombre, cond, detalle=""):
    print(("  OK    " if cond else "  FALLO ") + nombre + ("" if cond else f"\n          → {detalle!r}"[:700]))
    if not cond:
        FALLOS.append(nombre)


def sec(t):
    print("\n" + t)


def fuente(rel):
    return io.open(os.path.join(RAIZ, rel), encoding="utf-8").read()


import pandas as pd                                                                   # noqa: E402
from pypdf import PdfReader                                                           # noqa: E402
from core.calculations import calculate_limits, apply_offsets, analyze_matrix, validate_inputs  # noqa: E402
from core.optimizer import optimize                                                   # noqa: E402
from core.bs_logic import find_bs_step                                                # noqa: E402
from core.plumb import compute_plumb                                                  # noqa: E402
from core import interpretation as I, diagrams as DG, survey_calc as SC               # noqa: E402
from core.user_report import generate_user_report                                     # noqa: E402
from core.report import generate_report                                               # noqa: E402

COLS = ["WR", "FR", "OR", "WL", "FL", "OL"]
# La matriz de PRUEBA del ciclo 4 (sintética, `D:\CopeX\ciclos\ciclo4\matriz_c4.py`): el nivel 4 choca con el muro
M = [(99, 879, 402, 106, 874, 386), (98, 877, 405, 106, 867, 382), (103, 864, 390, 109, 854, 403),
     (110, 869, 419, 108, 879, 405), (105, 859, 392, 101, 861, 402), (109, 872, 385, 90, 867, 383),
     (103, 871, 396, 111, 855, 387), (102, 844, 403, 83, 865, 409), (93, 880, 379, 101, 853, 393),
     (96, 873, 380, 113, 869, 401), (115, 842, 385, 103, 857, 385), (111, 845, 400, 101, 851, 392)]


def base(**kw):
    p = {"TKSW": 1000, "BKS": 1600, "TKA": 100, "TKS": 35, "TSW": 100, "BGS": 850, "BKF1": 420, "BKF2": 430,
         "BS": 1854, "BT": 800, "BK": 1050, "TK": 1350, "TS": 1760, "SF1": 60, "SF2": 70, "SG": 320, "TG": 70,
         "BSR": 1840, "RAIL": 62, "OFFSET_CABIN": 0, "FRAME": 30, "OMEGA_SIDE": "R", "OFFSET_SIDE": "R", "FS": 140,
         "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R", "CTRL_IN_FRAME": False, "CTRL_SIDE": None,
         "NS": 12, "LengthTemplate": 600, "PROYECTO": "C4 — Harbour Lifts — Lift 4 (tools)",
         "CLIENTE": "C1 — Harbour Lifts", "UBICACION": "", "INGENIERO": "hjg,ujgjg", "MODELO": "ES1_R2"}
    p.update(kw)
    return p


def corre(p):
    df = pd.DataFrame([dict(zip(COLS, map(float, r))) for r in M])
    for c in COLS:
        p["%sT" % c] = float(df.iloc[-1][c])
    lim = calculate_limits(p)
    p.update(lim)
    adj = apply_offsets(df.to_dict("records"), lim)
    ana = analyze_matrix(adj, lim, wall_limiting=bool(p.get("WALL_LIMITING")))
    p.update(ana)
    lim.update(ana)
    opt = optimize(adj, lim, p)
    return {"p": p, "lim": lim, "adj": adj, "ana": ana, "opt": opt, "df": df,
            "lim_map": {c: lim[f"LIMIT_{c}"] for c in COLS}, "best": opt["best"]}


def pdf_txt(b):
    return re.sub(r"\s+", " ", "\n".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(b)).pages))


# ══════════════════════════════════════════════════════════════════════════════
sec("1. El optimizador: el muro limitante no se corta NUNCA (H3, opción a)")
R120, R140, R100 = corre(base(FS=120)), corre(base(FS=140)), corre(base(FS=100))
R_tope = corre(base(FS=140, TS=1720))                 # BC_CALC 20 < FS−TSW 40 → FB_MAX_BACK 0: no cabe empujar
b120, b140 = R120["best"], R140["best"]
chk("FS 120: hay solución (con v680 + la regla, sin `wall_evaded` con empuje 0, se quedaba SIN)", bool(b120))
if b120:
    chk("…el muro queda esquivado SIN empujar: su piso ya está FS−TSW por detrás (el caso 3 de v28/v29)",
        b120.get("wall_evaded") is True and b120.get("fb_extra_applied") is False,
        {k: b120.get(k) for k in ("rl", "fb", "fb_applied", "wall_evaded", "fb_extra_applied")})
    chk("…y su apertura no cuenta como fuera (23, no 31: ya no se corta el muro)", b120["total_off"] == 23
        and b120["off_by_col"].get("OR") == 11, (b120["total_off"], b120["off_by_col"]))
if b140:
    # ⚠️ v682 · CADUCADO A PROPÓSITO: las soluciones equivalentes (misma posición) se agrupan y queda la de mayor fb del
    # barrido, así que el empuje EXTRA es 13.0 (era 19.0, la de fb −3); la cabina, en el mismo sitio (16.0 hacia atrás).
    chk("FS 140: empuja 13.0 mm EXTRA hacia atrás para esquivarlo (16.0 aplicados)", b140.get("fb_extra_applied") is True
        and I.empuje_extra(b140) == 13.0 and b140["fb_applied"] == 16.0 and b140.get("wall_evaded") is True,
        (I.empuje_extra(b140), b140.get("fb_applied")))
chk("FS 100 (FS = TSW, sin sitio para empujar) y alejarse no basta (LIMIT_L 18 < 35): SIN solución",
    R100["best"] is None, R100["best"] and R100["best"]["rl"])
chk("⚠️ …descartando también los pasos que se ALEJAN del muro (RL > 0): hasta v680 solo yendo hacia él",
    any(s.get("skip_type") == "wall" and s["rl"] > 0 for s in R100["opt"]["step_log"]))
chk("FB_MAX_BACK 0: el empuje entero no cabe, no está esquivado → SIN solución (antes: empujaba lo que cupiera)",
    R_tope["best"] is None, R_tope["best"] and {k: R_tope["best"].get(k) for k in ("rl", "fb_applied", "wall_evaded")})
_viol = []
for nom, R in (("120", R120), ("140", R140), ("100", R100), ("tope", R_tope)):
    _lim_or, _lim_fr = R["lim"]["LIMIT_OR"], R["lim"]["LIMIT_FR"]
    _fs_tsw = R["p"]["FS"] - R["p"]["TSW"]
    for s in R["opt"]["all_solutions"]:
        m4 = s["matrix"][3]
        if m4["OR"] > _lim_or + 1e-6 and not (s.get("wall_evaded") and m4["FR"] - _lim_fr >= _fs_tsw - 1e-3):
            _viol.append((nom, s["rl"], s["fb"], m4["OR"]))
        if s["fb_applied"] > R["lim"]["FB_MAX_BACK"] + 1e-6:          # empujar más de lo que cabe detrás
            _viol.append((nom, "fb", s["fb_applied"], R["lim"]["FB_MAX_BACK"]))
chk("⚠️ ninguna solución válida deja el muro por encima de su límite sin esquivarlo DE VERDAD", not _viol, _viol[:4])
chk("FS 140: los pasos que se ALEJAN del muro (RL > 0) y no lo libran también se esquivan empujando, no se descartan",
    any(s["rl"] > 0 and s.get("wall_evaded") and s.get("status") == "VALID" for s in R140["opt"]["step_log"]))
chk("FS 120: hacia el muro más de FRAME se descarta (apertura tapada) también si ya estaba esquivado sin empujar",
    any(s.get("skip_type") == "frame_opening" for s in R120["opt"]["step_log"]))
chk("sin muro (Caso 2) nada cambia: la solución sale y no lleva `wall_evaded`",
    bool(corre(base(WALL_LIMITING=False))["best"]) and not corre(base(WALL_LIMITING=False))["best"].get("wall_evaded"))

# ══════════════════════════════════════════════════════════════════════════════
sec("2. Los cortes, lo que «queda» y los textos de la app")
for nom, R in (("FS 120", R120), ("FS 140", R140)):
    b, lim, p = R["best"], R["lim"], R["p"]
    cps = I.cortes_por_piso(lim, b, p)
    chk(f"{nom}: el muro (piso 4, derecha) NO es un corte", not any(c["piso"] == 4 and c.get("cortar_OR_mm") for c in cps),
        [c for c in cps if c["piso"] == 4])
    chk(f"{nom}: …los demás pisos sí (11)", len([c for c in cps if c.get("cortar_OR_mm")]) == 11, len(cps))
    chk(f"{nom}: sonda validada: sin los parámetros, el piso 4 SÍ saldría (lo que hacía hasta v680)",
        any(c["piso"] == 4 and c.get("cortar_OR_mm") for c in I.cortes_por_piso(lim, b)))
    f = I.hechos({"limits": lim, "analysis": R["ana"], "optimizer_result": R["opt"], "survey_adj": R["adj"]}, p)
    q = [x["column"] for x in f["solution"]["still_out_of_limit"]]
    chk(f"{nom}: «still out of limit» sin OR/OL (se cortan, o el muro se esquiva)", q and set(q) <= {"WR", "WL", "FR", "FL"}, q)
    chk(f"{nom}: los hechos dicen el muro: parada 4, RIGHT, no se corta", (f["solution"].get("limiting_wall") or {}).get("cut")
        is False and f["solution"]["limiting_wall"]["stop"] == 4 and f["solution"]["limiting_wall"]["side"] == "RIGHT",
        f["solution"].get("limiting_wall"))
    td = I.texto_desplazamientos(f)
    chk(f"{nom}: los desplazamientos no repiten las aperturas como «still out»", "the space at the" not in td, td)
    if nom == "FS 140":
        # v682 · CADUCADO A PROPÓSITO: los mm del desplazamiento hacia atrás, no la parte «extra» (cambiaba entre equivalentes)
        chk("FS 140: «This front-back shift (16.0 mm towards the REAR) clears the limiting wall at floor 4 (right side), "
            "which is not cut»", "This front-back shift (16.0 mm towards the REAR) clears the limiting wall at floor 4 "
            "(right side), which is not cut." in td, td)
    else:
        chk("FS 120: «is not cut: at that floor the car is already far enough towards the rear»",
            "is not cut: at that floor the car is already far enough towards the rear to clear it" in td, td)
chk("la nota del muro bajo la matriz, en los tres estados",
    "the 16.0 mm shift towards the rear clears it" in I.texto_muro(I.muro_de(R140["p"]), b140)   # v682
    and "already far enough towards the rear" in I.texto_muro(I.muro_de(R120["p"]), b120)
    and "stays within its limit" in I.texto_muro({"stop": 4, "side": "R"}, {"wall_evaded": False}))
_lc = {"LIMIT_OR": 401.0, "LIMIT_OL": 401.0}
_bc = {"matrix": [{"OR": 380.0, "OL": 380.0}, {"OR": 351.0, "OL": 380.0}]}
chk("controlador en el marco (R): el último piso se corta contra 401 − 70 (20.0 mm), como cuenta el optimizador",
    I.cortes_por_piso(_lc, _bc, {"CTRL_IN_FRAME": True, "CTRL_SIDE": "R"}) == [{"cortar_OR_mm": 20.0, "piso": 2}],
    I.cortes_por_piso(_lc, _bc, {"CTRL_IN_FRAME": True, "CTRL_SIDE": "R"}))
chk("…y sin controlador, ninguno", I.cortes_por_piso(_lc, _bc, {}) == [])
_sp, _usp = " ".join(I.SYSTEM_PROMPT.split()), " ".join(I.USER_SYSTEM_PROMPT.split())   # el prompt parte líneas
chk("el prompt: el muro nunca se corta y WR/WL van a la línea del riel",
    "it is NEVER cut" in _sp and "wall to the rail line" in _sp and "is NEVER cut" in _usp
    and "never list it as a cut" in _usp, _sp[:300])

# ══════════════════════════════════════════════════════════════════════════════
sec("3. El PDF del cliente")


def informe(R, best=None):
    b = best or R["best"]
    opt = dict(R["opt"], best=b)
    f = I.hechos({"limits": R["lim"], "analysis": R["ana"], "optimizer_result": opt, "survey_adj": R["adj"]}, R["p"])
    iu = {"resumen": "Summary.", "desplazamientos": I.texto_desplazamientos(f), "cortes": I.texto_cortes(f),
          "implementacion": "Steps.", "verificacion": "Checks.", "_ok": True}
    pl = compute_plumb({k: R["p"][k] for k in ("BKS", "RAIL", "TKSW", "LengthTemplate", "SF1", "SF2", "BSR", "BS")},
                       survey_disp={"rl": b["rl"], "fb": b["fb_applied"]})
    return pdf_txt(generate_user_report(R["p"], R["lim"], opt, R["lim_map"], COLS, iu, plumb=pl))


tx = informe(R140)
chk("⚠️ H1: RL −25 → «Main action: … 25.0 mm to the right» (decía «to the left»)",
    re.search(r"Main action: shift the car block 25\.0 mm to the right and 16\.0 mm to the rear", tx),
    re.findall(r"Main action:.{0,90}", tx))
chk("…y el apartado de desplazamientos lo MISMO («25.0 mm to the RIGHT»)", "Lateral: 25.0 mm to the RIGHT." in tx)
_b18 = dict(b140, rl=18.0)
tx18 = informe(R140, _b18)
chk("⚠️ H1: con RL +18 → «18.0 mm to the left» (decía «to the right»)",
    re.search(r"Main action: shift the car block 18\.0 mm to the left", tx18), re.findall(r"Main action:.{0,90}", tx18))
chk("H3: ningún «Floor 4: cut … right side» en el PDF", not re.search(r"Floor 4: cut[^.]*right side", tx),
    re.findall(r"Floor 4: cut[^.]*\.", tx))
chk("H3: la nota del muro bajo la matriz (v682: con el desplazamiento aplicado)", "Floor 4, right side: limiting wall. "
    "It is not cut: the 16.0 mm shift towards the rear clears it." in tx, re.findall(r"Floor 4, right side[^.]*\.[^.]*\.", tx))
chk("H11: el glosario, WR/WL hasta la línea del riel", "Distance from the right / left wall to the rail line" in tx)
chk("H12b: el modelo en la cabecera (ES1_R2)", "ES1_R2" in tx)

# ══════════════════════════════════════════════════════════════════════════════
sec("4. Los dibujos: entre LÍNEAS de riel (H11)")
_iso = DG.shaft_iso_svg(R140["p"], R140["lim"], b140, 12, R140["lim_map"])
_w1 = b140["matrix"][0]["WL"] + 1600 + 62 + b140["matrix"][0]["WR"]
chk(f"isométrica: «Shaft width {_w1:.0f} mm» = WL + BKS + RAIL + WR (era + 2·RAIL)", f">{_w1:.0f} mm<" in _iso,
    re.findall(r">(\d+) mm<", _iso)[:3])
_fila = {"WL": 91.0, "WR": 101.0, "FL": 850.0, "FR": 850.0, "OL": 401.0, "OR": 401.0}   # la posición de DISEÑO
_svg = DG.floor_plan_svg(R140["p"], R140["lim"], _fila, 0, R140["lim_map"], n_floors=12)
_hueco = re.search(r'<rect x="[\d.]+" y="[\d.]+" width="([\d.]+)" height="([\d.]+)" fill="none" stroke="#1f2937" '
                   r'stroke-width="2.2"/>', _svg)
_marcos = [float(x) for x in re.findall(r'<rect x="[\d.]+" y="[\d.]+" width="([\d.]+)" height="5" fill="#8a94a6"/>', _svg)]
if _hueco:
    _w, _h = float(_hueco.group(1)), float(_hueco.group(2))
    _esc = _w / (91 + 1662 + 101)
    chk("planta, en la posición de diseño: el hueco mide WL + BKS + RAIL + WR = 1854 = BS (no 1916)",
        abs(_w / _h - 1854 / 1760) < 0.002, (_w, _h, _w / _h, 1854 / 1760))
    chk("…y los marcos de la puerta, FRAME (30 mm) cada uno: OL/OR se miden desde la línea del riel (antes 30 + 31)",
        len(_marcos) == 2 and all(abs(m - 30 * _esc) < 0.15 for m in _marcos), (_marcos, 30 * _esc))
else:
    chk("planta: se localiza el rectángulo del hueco", False, _svg[:300])

# ══════════════════════════════════════════════════════════════════════════════
sec("5. El informe interno (el del correo)")
_ta = pdf_txt(generate_report(R140["p"], R140["lim"], R140["df"], pd.DataFrame(R140["adj"]), R140["lim_map"], R140["ana"],
                              R140["opt"], find_bs_step(1840, 1854, R140["lim"]["LIMIT_ZB"], R140["lim"]["LIMIT_OB"]),
                              COLS, interpretation={k: "x" for k in I.INTERPRETATION_SCHEMA}))
chk("columnas CUT OR / CUT OL también con muro (Caso 1), en la CABECERA de la tabla (no solo en la nota)",
    bool(re.search(r"OR\s+CUT OR\s+WL\s+FL\s+OL\s+CUT OL", _ta)), re.findall(r".{0,30}CUT OR.{0,40}", _ta)[:2])
chk("la regla del muro, en inglés", "Limiting wall: stop 4, side R. It is never cut" in _ta, re.findall(r".{0,40}Limiting wall.{0,80}", _ta)[:3])
chk("la nota del muro", "Floor 4, right side: limiting wall" in _ta)
_esp = [w for w in ("Pared limitante", "Parada limitante", "Lado offset", "Offset cabina", "No aplica", "paso 0.5",
                    "FB aplic.", "Estado", "offset lado", "Omega lado", "ultimo nivel") if w in _ta]
chk("sin restos en español (salían «Pared limitante?», «Lado offset cabina», «paso 0.5 mm», «FB aplic.», «Estado»…)",
    not _esp, _esp)

# ══════════════════════════════════════════════════════════════════════════════
sec("6. La parada del muro que no existe (H4) y la configuración al reabrir (H13)")
_v = {"BKS": 1, "TKSW": 1, "TS": 1, "TK": 1, "SF1": 1, "SF2": 1, "RAIL": 1, "BSR": 1}
chk("la parada 20 con 12 paradas para el cálculo", any("does not exist" in x for x in
    validate_inputs(dict(_v, WALL_LIMITING=True, WALL_STOP=20, NS=12))))
chk("…la 12 con 12, no; y sin muro, tampoco", not any("does not exist" in x for x in
    validate_inputs(dict(_v, WALL_LIMITING=True, WALL_STOP=12, NS=12)) + validate_inputs(dict(_v, WALL_STOP=20, NS=12))))
_c = SC.cfg_de_params({"WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R", "OMEGA_SIDE": "L", "OFFSET_SIDE": "L",
                       "CTRL_IN_FRAME": False, "CTRL_SIDE": None})
chk("cfg_de_params: la configuración de la obra → los controles", _c == {
    "cfg_omega_side": "L", "cfg_offset_side": "L", "cfg_wall_yn": "Y", "cfg_wall_stop": 4, "cfg_wall_side": "R",
    "cfg_ctrl_yn": "N"}, _c)
chk("…con «True» en texto también (Excel o una hoja vieja)", SC.cfg_de_params({"WALL_LIMITING": "True"}) == {"cfg_wall_yn": "Y"})
_su = fuente("core/survey_ui.py")
_ts = ast.parse(_su)
chk("la importación del Excel usa la MISMA equivalencia", any(isinstance(n, ast.Call) and getattr(n.func, "id", "") ==
    "cfg_de_params" for n in ast.walk(_ts)) and 'if cfg.get("OMEGA_SIDE")  in ("R", "L"): _cfg' not in _su)
import streamlit as st                                                                # noqa: E402
from core import projects_ui as PU                                                    # noqa: E402
for _k in ("_cfg_pendiente_sv", "pl_prj_sv"):
    st.session_state.pop(_k, None)
PU._cargar_en_survey("PRJ-0045", {"ID": "PRJ-0045", "Name": "C4 — Obra", "Group": "g"}, "g",
                     {"BSR": 1840.0, "NS": 12, "WALL_LIMITING": True, "WALL_STOP": 4, "WALL_SIDE": "R"},
                     [{c: 0.0 for c in COLS}] * 12)
chk("⚠️ H13: reabrir deja la configuración pendiente para el Survey (el muro, su parada y su lado)",
    (st.session_state.get("_cfg_pendiente_sv") or {}).get("cfg_wall_yn") == "Y"
    and st.session_state["_cfg_pendiente_sv"].get("cfg_wall_stop") == 4, st.session_state.get("_cfg_pendiente_sv"))
chk("H12: …y la obra elegida en el Survey", st.session_state.get("pl_prj_sv") == "C4 — Obra (PRJ-0045)",
    st.session_state.get("pl_prj_sv"))
_pu = fuente("core/projects_ui.py")
_reb = _pu.split('if st.button(t(":material/sync: Load this project into the Survey")')[1][:900]
chk("H12: «Load this project into the Survey» LLEVA al Survey (y ya no dice «Go to Survey»)",
    '_admin_nav_pending"] = ("herramientas", "📐 Survey")' in _reb and "st.rerun()" in _reb
    and "Go to **:material/architecture: Survey**" not in _reb, _reb[:400])

# ══════════════════════════════════════════════════════════════════════════════
sec("7. En el Survey: identidad, modelo, historial y columnas de corte")
chk("H12b: el cálculo pone MODELO, y la obra elegida lo da", 'all_params["MODELO"]        = st.session_state.get("modelo", "")'
    in _su and 'st.session_state["modelo"]    = str(_prj_sv.get("Model", ""))' in _su)
_guarda = _su.split('key="sv_save_prj"')[1]
_i_upd, _i_att = _guarda.find('ap.update({"PROYECTO": str(_prj.get("Name", ""))'), _guarda.find("attach_survey(")
chk("⚠️ H2: al guardar, la identidad de la OBRA DE DESTINO, antes de adjuntar y de archivar el informe",
    0 <= _i_upd < _i_att and '"MODELO": str(_prj.get("Model", ""))' in _guarda[:_i_att], (_i_upd, _i_att))
chk("H16: el historial guarda el FB APLICADO", '"fb": _best.get("fb_applied", _best.get("fb"))' in _guarda)
chk("H3: la tabla de la solución lleva CUT OR/OL en los dos casos, de `cortes_por_piso` (con el muro fuera)",
    "_cpp(limits, sol, all_params)" in _su and 'if not wall_limiting_:\n                        lor_v' not in _su)
chk("…y dice lo del muro", "_txm(_mdf(all_params), sol)" in _su)

# ══════════════════════════════════════════════════════════════════════════════
sec("8. AppTest: la configuración al reabrir, la parada imposible y las filas 1…NS")
from streamlit.testing.v1 import AppTest                                              # noqa: E402

GUION = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
import pandas as pd
from core import estado_vivo, plan_ui, survey_ui as S
st.session_state["auth"] = {"rol": "field", "usuario": "u", "nombre": "U", "grupo": "g"}
plan_ui.P.is_configured = lambda: True
plan_ui._proyecto_fichado = lambda a: None
plan_ui.P.list_projects_for_field = lambda *a, **k: []
S.init_state()
estado_vivo.pasada()
_s = st.session_state.pop("sembrar", None)
if _s:
    for _k, _v in _s.items():
        st.session_state[_k] = _v
    st.session_state["survey_df"] = pd.DataFrame({c: [float(i) for i in range(12)] for c in S.SURVEY_COLS})
S.render_survey_tab("field", "g")
''' % RAIZ


def at_con(sembrar):
    a = AppTest.from_string(GUION, default_timeout=120)
    a.session_state["sembrar"] = sembrar
    a.run()
    return a


a = at_con({"ns": 12, "_cfg_pendiente_sv": {"cfg_wall_yn": "Y", "cfg_wall_stop": 4, "cfg_wall_side": "L",
                                            "cfg_omega_side": "L"}})
chk("sin excepción", not a.exception, [e.value for e in a.exception][:1])
_r = {x.key: x.value for x in a.radio}
_n = {x.key: x.value for x in a.number_input}
chk("⚠️ H13: lo pendiente llega a los controles: muro Y, parada 4, lado L, omega L",
    _r.get("cfg_wall_yn") == "Y" and _n.get("cfg_wall_stop") == 4 and _r.get("cfg_wall_side") == "L"
    and _r.get("cfg_omega_side") == "L", (_r, _n.get("cfg_wall_stop")))
_ed = [d for d in a.dataframe if list(getattr(d.value, "columns", [])) == COLS]
chk("H5: la matriz se pinta con las filas 1…12", bool(_ed) and list(_ed[0].value.index)[:2] == [1, 2]
    and list(_ed[0].value.index)[-1] == 12, list(_ed[0].value.index)[:3] if _ed else "sin tabla")
chk("…y la guardada sigue con su índice de siempre (0…11)", list(a.session_state["survey_df"].index)[:2] == [0, 1]
    and len(a.session_state["survey_df"]) == 12)
a = at_con({"ns": 12, "cfg_wall_yn": "Y", "cfg_wall_stop": 20, "cfg_wall_side": "R"})
_err = " | ".join(e.value for e in a.error)
chk("⚠️ H4: «Stop 20 does not exist: the survey has 12 stops.» junto al campo", "Stop 20 does not exist: the survey has "
    "12 stops." in _err, _err)
a = at_con({"ns": 12, "cfg_wall_yn": "Y", "cfg_wall_stop": 12, "cfg_wall_side": "R"})
chk("…con la 12, nada", "does not exist" not in " | ".join(e.value for e in a.error))

print()
print(f"=== {('TODO OK' if not FALLOS else str(len(FALLOS)) + ' FALLO(S)')} ===")
sys.exit(1 if FALLOS else 0)
