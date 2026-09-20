"""v454 — ningún camino puede crear una obra SIN actividades.

## El fallo, encontrado por accidente

Intentando verificar el titular «You are at» de una cotización, resultó que no se pintaba
**nunca**: la única obra creada desde una cotización (`PRJ-0016`, un Ripout) había nacido
con **CERO actividades**.

El avance es `Σ(peso·avance)/Σpeso` sobre las actividades, así que sin ninguna:
  1. la obra se queda **clavada en 0% para siempre**;
  2. el **campo no tiene dónde reportar** su trabajo;
  3. y el bloque «cotizado vs real» **nunca puede pintar su titular**, porque depende del
     avance — que fue lo que llevó hasta el fallo.

## La causa: media unificación (el patrón de v419)

La regla es de **v306** — *«los demás tipos nacen con UNA actividad genérica, no con cero»*
— y estaba aplicada **solo en el alta MANUAL** (`projects_ui`). El camino que crea la obra
al **aceptar una cotización** (`quotes.aceptar_y_crear_proyecto`, v354) se quedó sin ella:
dejaba `acts = None` para todo lo que no fuera Instalación.

⚠️ Es la misma forma de fallo que v419 (la ubicación unificada a medias) y v358 (el
archivado): **una regla aplicada a un camino y no al gemelo**. Por eso este guardián no
mira un sitio, mira LOS DOS.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
fallos = []


def chk(ok, msg):
    print(("  OK  " if ok else "  FALLO  ") + msg)
    if not ok:
        fallos.append(msg)


def _asigna_acts(fn):
    """Valores que la función llega a asignar a `acts` / `_acts`."""
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign):
            for t_ in n.targets:
                if getattr(t_, "id", "") in ("acts", "_acts"):
                    out.append(n.value)
    return out


print("== 1. Los DOS caminos de creación dan actividades ==")

_q = ast.parse((CORE / "quotes.py").read_text(encoding="utf-8"))
_acep = next((n for n in ast.walk(_q) if isinstance(n, ast.FunctionDef)
              and n.name == "aceptar_y_crear_proyecto"), None)
chk(_acep is not None, "se localiza `aceptar_y_crear_proyecto`")

_vals = _asigna_acts(_acep) if _acep else []
# ⚠️ Un `acts = None` suelto es EXACTAMENTE el fallo: la obra nace sin actividades.
_nones = [v for v in _vals if isinstance(v, ast.Constant) and v.value is None]
_listas = [v for v in _vals if isinstance(v, (ast.List, ast.Subscript))
           or (isinstance(v, ast.Tuple))]
chk(bool(_vals), f"la función asigna `acts` ({len(_vals)} veces)")
chk(bool(_listas), "…y al menos una rama le da una LISTA de actividades")

# La comprobación que de verdad importa: que exista una rama `else` que cubra el caso
# «no es Instalación». Sin ella, el tipo no-instalación se va con lo que hubiera (None).
_ifs = [n for n in ast.walk(_acep) if isinstance(n, ast.If)] if _acep else []
_con_else = [n for n in _ifs
             if n.orelse and any(
                 isinstance(x, ast.Assign)
                 and any(getattr(t_, "id", "") == "acts" for t_ in x.targets)
                 for x in ast.walk(ast.Module(body=n.orelse, type_ignores=[])))]
chk(bool(_con_else),
    "la rama que NO es Instalación también asigna actividades (era el fallo)")

print("\n== 2. Los dos caminos usan la MISMA actividad genérica ==")
_qs = (CORE / "quotes.py").read_text(encoding="utf-8")
_ps = (CORE / "projects_ui.py").read_text(encoding="utf-8")
chk('"nombre": "Execution"' in _qs, "quotes.py crea la actividad «Execution»")
chk('"nombre": "Execution"' in _ps, "projects_ui.py crea la MISMA «Execution»")
# ⚠️ Si divergieran, el histórico tendría dos nombres para lo mismo según por dónde se
# creó la obra — el fallo de los helpers divergentes de v323, aplicado a los datos.

print("\n== 3. …y ninguno la deja en español (migración de v453) ==")
for fn, src in (("quotes.py", _qs), ("projects_ui.py", _ps)):
    chk('"Ejecución"' not in src, f"{fn} no vuelve a «Ejecución» (la hoja está migrada)")

print("\n== 4. ⚠️ …pero la LOCALIZACIÓN interna SÍ va sin actividades ==")
# ⚠️ El alta de localización (`projects_ui`, v423) llama a `create_project` SIN
# `activities`, y eso es CORRECTO por diseño: una oficina o un almacén no tiene avance
# —por eso v422 le dio estado propio Abierta/Cerrada— y el campo ni siquiera ve la
# pestaña «Avance». Se afirma aquí para que nadie lo «arregle» creyendo que es el mismo
# fallo: auditando los tres caminos estuve a punto de hacerlo yo.
_a_pu = ast.parse((CORE / "projects_ui.py").read_text(encoding="utf-8"))
_altas = [n for n in ast.walk(_a_pu)
          if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "create_project"]
_sin_acts = [n for n in _altas if not any(k.arg == "activities" for k in n.keywords)]
chk(len(_altas) >= 2, f"projects_ui tiene los dos altas ({len(_altas)})")
chk(len(_sin_acts) == 1,
    f"exactamente UNA (la de localización) crea sin actividades ({len(_sin_acts)})")
_tipos = [k.value for n in _sin_acts for k in n.keywords
          if k.arg == "tipo" and isinstance(k.value, ast.Name)]
chk(bool(_tipos), "…y es la que recibe un `tipo` variable (el de TIPOS_INTERNOS)")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
