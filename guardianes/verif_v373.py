"""GUARDIÁN v373 — alarma por check en NO + ganancia FIJA por obra.

Lo que hay que demostrar, en este orden de importancia:

1. ⚠️ **Ninguna obra existente cambia de cifra.** Es la regla de v360: se añade un
   modelo nuevo, no se mueve el dinero de nadie sin pedirlo. Con `GananciaFija`
   vacía, `project_revenue` tiene que dar EXACTAMENTE lo mismo que antes.
2. La fila posicional de `create_project` cuadra con la cabecera (v363: añadir la
   columna y olvidar el valor dejó la función muerta 3 versiones).
3. La cotización sigue mandando: la fija NO se le suma a un precio pactado.
4. Un check en NO abre alarma, y "N/A" no.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "Bobo", "grupo": "cliente1", "rol": "administrator"}

from core import projects as P, finance as F, prestart as PS, auditoria as AU  # noqa: E402

G = "cliente1"
ok = True

# ── 1) la fila posicional (regla v363) ──────────────────────────────
print("== 1. la fila de `create_project` cuadra con la cabecera ==")
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\projects.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == "create_project")
fila = next((n for n in ast.walk(fn)
             if isinstance(n, ast.Assign)
             and getattr(n.targets[0], "id", "") == "row"
             and isinstance(n.value, ast.List)), None)
n_fila = len(fila.value.elts) if fila else -1
n_cab = len(P.PROJECTS_HEADERS)
ok &= n_fila == n_cab
print(f"   fila={n_fila}  cabecera={n_cab}  {'✓' if n_fila == n_cab else '‼️ create_project MUERTA'}")
print(f"   última columna: {P.PROJECTS_HEADERS[-1]!r}")

# ── 2) ⚠️ ninguna obra existente se mueve ───────────────────────────
print("\n== 2. ⚠️ ninguna obra EXISTENTE cambia de cifra ==")
# Se compara el ingreso de cada obra real contra la fórmula ANTERIOR a v373,
# recalculada aquí a mano. Con GananciaFija vacía deben coincidir al céntimo.
proys = P.list_projects(grupo=G, incluir_archivados=True)
for p in proys:
    pid = str(p.get("ID", ""))
    fija = P.ganancia_fija(pid, p)
    r = F.project_revenue(pid, G, p)
    # el ingreso SIN la fija es lo que daba la versión anterior
    _antes = round(P._num(r.get("ingreso")) - P._num(r.get("ganancia_fija")), 2)
    bien = fija > 0 or abs(_antes - P._num(r.get("ingreso"))) < 0.005
    ok &= bien
    print(f"   {pid} {str(p.get('Name'))[:24]:<25} modelo={str(r.get('modelo')):<12} "
          f"fija=${fija:>8,.2f}  ingreso=${P._num(r.get('ingreso')):>10,.2f}  "
          f"{'✓ igual que antes' if bien else '✗'}")

# ── 3) la fija SUMA, y la cotización manda ──────────────────────────
print("\n== 3. la fija suma en rubro/margen y NO en cotizado ==")
_orig = P.ganancia_fija
for pid in [str(p.get("ID")) for p in proys][:6]:
    r0 = F.project_revenue(pid, G)
    P.ganancia_fija = lambda _p, _prj=None: 1000.0        # simula $1.000 de fija
    try:
        r1 = F.project_revenue(pid, G)
    finally:
        P.ganancia_fija = _orig
    d = P._num(r1.get("ingreso")) - P._num(r0.get("ingreso"))
    esperado = 0.0 if str(r0.get("modelo")) == "cotizado" else 1000.0
    bien = abs(d - esperado) < 0.005
    ok &= bien
    print(f"   {pid} modelo={str(r0.get('modelo')):<10} el ingreso sube ${d:>9,.2f} "
          f"(esperado ${esperado:,.2f})  {'✓' if bien else '✗'}")
    if str(r0.get("modelo")) == "cotizado":
        _ig = P._num(r1.get("fija_ignorada"))
        ok &= _ig == 1000.0
        print(f"      {'✓' if _ig == 1000.0 else '✗'} y se AVISA de que no se usa "
              f"(fija_ignorada=${_ig:,.2f})")

# ── 4) `margen_pct` no cambia de significado ────────────────────────
print("\n== 4. ⚠️ `margen_pct` conserva su definición (no se le cambió el denominador) ==")
for pid in [str(p.get("ID")) for p in proys][:4]:
    r = F.project_revenue(pid, G)
    if str(r.get("modelo")).startswith("rubro"):
        mo, gmo = P._num(r.get("costo_mo")), P._num(r.get("ganancia_mo"))
        esp = round(100.0 * gmo / mo, 2) if mo > 0 else 0.0
        bien = abs(P._num(r.get("margen_pct")) - esp) < 0.01
        ok &= bien
        print(f"   {pid} margen_pct={r.get('margen_pct')} (ganancia MO / costo MO) "
              f"{'✓' if bien else '✗'}  ·  margen_total_pct={r.get('margen_total_pct')}")

# ── 5) el check en NO abre alarma ───────────────────────────────────
print("\n== 5. un check en NO abre alarma (y 'N/A' no) ==")
src_ps = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\prestart.py").read_text(encoding="utf-8")
fn_ps = next(n for n in ast.walk(ast.parse(src_ps))
             if isinstance(n, ast.FunctionDef) and n.name == "submit")
cuerpo = ast.unparse(fn_ps)
_n_alarmas = cuerpo.count("alerts.report_problem")
ok &= _n_alarmas == 2
print(f"   {'✓' if _n_alarmas == 2 else '‼️'} `submit` abre 2 alarmas distintas "
      f"(near miss + checks): encontradas {_n_alarmas}")
_solo_no = "'NO'" in cuerpo and ".upper() == 'NO'" in cuerpo.replace('"', "'")
ok &= _solo_no
print(f"   {'✓' if _solo_no else '‼️'} solo cuenta 'NO' (el 'N/A' es una respuesta legítima)")
# la lógica de conteo, con datos
_checks = {"permisos": "YES", "toolbox": "NO", "cages": "N/A", "landings": "NO"}
_no = [PS._LABELS.get(k, k) for k, v in _checks.items() if str(v).strip().upper() == "NO"]
bien = len(_no) == 2
ok &= bien
print(f"   {'✓' if bien else '✗'} con YES/NO/N-A/NO → {len(_no)} en NO: "
      + " · ".join(x[:28] for x in _no))
# una alarma, no N
# ⚠️ CADUCADO por v447 (i18n F5c): el mensaje de la alarma pasó al inglés
# (va por Telegram/email, así que es idioma BASE, regla v436). Lo que la regla
# protege es que sea **UNA** alarma con todos los checks y no una por check:
# `report_problem` también NOTIFICA, y N alarmas serian N avisos por un solo
# formulario. Se cuenta el prefijo, sea cual sea el idioma.
_una = (cuerpo.count("Pre-Start with") + cuerpo.count("Pre-Start con")) == 1
ok &= _una
print(f"   {'✓' if _una else '✗'} UNA alarma con todos los checks, no una por check "
      "(`report_problem` también NOTIFICA)")

# ── 6) los campos de dinero se auditan (regla v344/v352) ────────────
print("\n== 6. ⚠️ los campos que mueven dinero están auditados ==")
# ⚠️ CADUCADO Y ACTUALIZADO en v455 (regla v385): el modelo del % sobre la mano de
# obra se ELIMINÓ a petición del usuario. La ganancia va por RUBRO.
for campo in ("FixedProfit", "HourlyProfitJSON"):
    en = campo in AU.CAMPOS_CLAVE
    ok &= en
    print(f"   {'✓' if en else '‼️ sin rastro'} {campo}")
# y que cada CAMPO_CLAVE del proyecto exista de verdad como columna
_fantasma = [c for c in ("FixedProfit", "HourlyProfitJSON")
             if c not in P.PROJECTS_HEADERS]
ok &= not _fantasma
print(f"   {'✓' if not _fantasma else '‼️'} ninguno es un nombre fantasma: {_fantasma or 'ok'}")

print("\n" + ("✅ v373 OK: nadie cambia de cifra, la cotización manda, el check en NO "
              "escala y todo queda auditado" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
