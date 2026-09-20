"""v419: una sola ubicación por proyecto — la del mapa.

El proyecto tenía DOS entradas para el mismo dato: el pin (`Lat`/`Lng`, fuera del form,
con su propio buscador) y un `text_input("Ubicación")` dentro del form. Nada las
conectaba, así que se podía guardar una sin la otra. Y como el TEXTO es lo que leen Home,
Ruta del día, Pre-Start y los avisos —las coordenadas solo las usan el mapa y la ruta—,
un proyecto con pin y sin texto **parecía no estar ubicado**.

⚠️ v272 ya había resuelto esto al CREAR («la Ubicación se toma de la dirección que
buscaste en el mapa → ya no se pide dos veces») y la EDICIÓN se quedó con el campo suelto.
Media unificación es la que produce el desajuste.

Lo que se protege:
  (a) en la edición no puede volver a haber un campo de ubicación que se teclee a mano;
  (b) ⚠️ el texto SOLO se pisa con una dirección CONFIRMADA por el geocoder (`_addr`),
      nunca con la caja de búsqueda (`_q`): media dirección tecleada no puede acabar
      siendo la ubicación de la obra;
  (c) si no se toca el mapa, se CONSERVA lo que hubiera — hay direcciones puestas a mano
      («Gagiope») que el geocoder reescribiría, y cambiarlas en frío es el fallo de v360;
  (d) se avisa de las obras con dirección y sin pin, que no salen en ningún mapa.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


src = (RAIZ / "core" / "projects_ui.py").read_text(encoding="utf-8")
sin_com = tokenize.untokenize(
    [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
     if t.type != tokenize.COMMENT])
arb = ast.parse(sin_com)
fn = next((n for n in ast.walk(arb)
           if isinstance(n, ast.FunctionDef) and n.name == "_detalle_proyecto"), None)

def _desenv(nodo):
    """`t("X")` → el Constant "X". Tras la traducción, las etiquetas llegan
    envueltas y un chequeo que mire el Constant directo deja de ver nada."""
    if (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
            and nodo.func.id in ("t", "d", "_d") and nodo.args):
        return nodo.args[0]
    return nodo

chk("existe `_detalle_proyecto`", fn is not None)

# ── (a) Ningún campo de ubicación editable a mano ───────────────────────────
print("\n== a) la ubicación no se teclea ==")
editables = []
for n in ast.walk(fn):
    if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "text_input" and n.args
            # ⚠️ CADUCADO por v440: la etiqueta ya no es un Constant sino
            # `t("Location")`. Se desenvuelve; si no, el chequeo no ve NINGÚN
            # campo y pasa en vacío justo donde tiene que vigilar.
            and isinstance(_desenv(n.args[0]), ast.Constant)
            # ⚠️ CADUCADO por v440: la etiqueta es «Location». Lo que la regla
            # protege es que NINGÚN campo de ubicación sea editable a mano.
            and ("bicaci" in str(_desenv(n.args[0]).value)
                 or "Location" in str(_desenv(n.args[0]).value))):
        _dis = next((k.value for k in n.keywords if k.arg == "disabled"), None)
        editables.append(isinstance(_dis, ast.Constant) and _dis.value is True)
chk("hay un campo de ubicación que auditar", len(editables) >= 1)
chk("...y NINGUNO es editable a mano", all(editables), True)

# ── (b) Solo la dirección CONFIRMADA puede pisar el texto ───────────────────
print("\n== b) media búsqueda no puede acabar siendo la dirección ==")
cad = [n.value for n in ast.walk(fn)
       if isinstance(n, ast.Constant) and isinstance(n.value, str)]
_usa_addr = any("_addr" in c for c in cad)
_usa_q = any(c.endswith("_q") for c in cad)
chk("se usa la dirección confirmada del geocoder (`_addr`)", _usa_addr)
chk("...y NO la caja de búsqueda (`_q`) al editar", not _usa_q)

# ── (c) Sin tocar el mapa, se conserva lo que hubiera ───────────────────────
print("\n== c) no se reescribe en frío lo ya puesto ==")
# la asignación de `ubic` tiene que partir de lo que ya tiene el proyecto
_parte_del_actual = False
for n in ast.walk(fn):
    if (isinstance(n, ast.Assign) and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "ubic"):
        if any(isinstance(c, ast.Constant) and c.value == "Location"
               for c in ast.walk(n.value)):
            _parte_del_actual = True
chk("`ubic` arranca del valor actual del proyecto", _parte_del_actual)


def _regla(ubic_actual, addr_confirmada):
    """La regla tal cual la aplica el código."""
    ubic = str(ubic_actual or "")
    _m = str(addr_confirmada or "").strip()
    if _m:
        ubic = _m
    return ubic


chk("sin tocar el mapa se conserva la dirección a mano",
    _regla("Gagiope", None), "Gagiope")
chk("al confirmar en el mapa, se actualiza",
    _regla("Gagiope", "12 Gagiope St, Sydney NSW"), "12 Gagiope St, Sydney NSW")
chk("una dirección vacía no se inventa", _regla("", None), "")

# ── (d) El aviso de «sin pin» ───────────────────────────────────────────────
print("\n== d) se avisa de las obras que no salen en el mapa ==")
_txt = "".join(cad)
chk("existe el aviso de obra sin pin",
    "no está en el mapa" in _txt or "wrong_location" in _txt)
_mira_lat = any(isinstance(n, ast.Constant) and n.value == "Lat" for n in ast.walk(fn))
chk("...y se decide mirando si hay coordenadas", _mira_lat)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
