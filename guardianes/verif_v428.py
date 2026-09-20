"""v428: ningún generador cuenta FILAS, y los que se borran no reciclan.

v427 arregló proyecto/cliente/gasto. Al barrer el resto apareció algo peor que el
reciclaje: **`roster._next_id` contaba FILAS** (`len(get_all_values()) - 1`), no el
máximo. Y `delete_trabajo` borra la fila de verdad cuando el trabajo no está asignado
en ningún roster.

⚠️ Estaba ROTO en producción: 4 filas con IDs `TRB-0002..TRB-0005`, así que el
siguiente alta emitía **TRB-0005**, que ya existía. Y `trabajos_idx` indexa por ID, o
sea que uno de los dos habría desaparecido del índice y las celdas del tablero
asignadas a él resolverían al trabajo equivocado —nombre y color de otro— sin ningún
error visible.

Lo que se protege:
  (a) ningún generador deriva el ID del NÚMERO DE FILAS;
  (b) los seis generadores de entidades que se borran Y se referencian saltan los IDs
      en uso (v427);
  (c) el caso concreto que estaba roto no puede volver.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def arbol(p: Path):
    src = p.read_text(encoding="utf-8")
    sin = tokenize.untokenize(
        [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
         if t.type != tokenize.COMMENT])
    return ast.parse(sin)


def cont(a, ln):
    m = None
    for n in ast.walk(a):
        if isinstance(n, ast.FunctionDef) and n.lineno <= ln <= (n.end_lineno or ln):
            if m is None or n.lineno > m.lineno:
                m = n
    return m


# ── (a) Nadie deriva un ID del número de filas ──────────────────────────────
print("== a) ningún ID sale de contar filas ==")
# El patrón roto: `len(...get_all_values()) - 1` dentro de un generador de ID.
_malos = []
for p in sorted(RAIZ.glob("core/*.py")):
    a = arbol(p)
    for n in ast.walk(a):
        if not (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "len"):
            continue
        # ¿el len() envuelve una lectura de la hoja?
        _dump = ast.dump(n)
        if "get_all_values" not in _dump and "get_all_records" not in _dump:
            continue
        f = cont(a, n.lineno)
        if f and ("next" in f.name.lower() and "id" in f.name.lower()):
            _malos.append(f"{p.name}:{n.lineno} ({f.name})")
chk("ningún `_next_*id*` usa `len(hoja)`", _malos, [])

# ── (b) Los generadores que importan saltan los IDs en uso ──────────────────
print("\n== b) los seis generadores saltan los IDs en uso ==")
ESPERADOS = {
    ("projects.py", "_next_project_id"): "PRJ-",
    ("projects.py", "create_grouping"):  "AGR-",   # el generador vive dentro
    ("clientes.py", "_next_id"):         "CLI-",
    ("expenses.py", "_next_id"):         "G-",
    ("credentials.py", "_next_id"):      "CR-",
    ("roster.py", "_next_id"):           "TRB-/ROS-",
    ("toolruns.py", "_next_id"):         "CAL-",
}
for (fich, nom), pref in ESPERADOS.items():
    a = arbol(RAIZ / "core" / fich)
    f = next((n for n in ast.walk(a)
              if isinstance(n, ast.FunctionDef) and n.name == nom), None)
    usa = f is not None and any(
        isinstance(n, ast.Call)
        and getattr(n.func, "attr", getattr(n.func, "id", "")) == "siguiente_id_libre"
        for n in ast.walk(f))
    chk(f"{fich}:{nom} ({pref})", usa)
    chk(f"   ...con respaldo si falla",
        f is not None and any(isinstance(n, ast.Try) for n in ast.walk(f)))

# ── (c) El caso concreto que estaba roto ────────────────────────────────────
print("\n== c) la colisión de trabajos no puede volver ==")
import streamlit as st                                              # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "g"}
from core import roster as R, hojas as H, timeclock as _TC          # noqa: E402


class _WS:
    """La hoja REAL que estaba rota: 4 filas con IDs 0002..0005."""
    def get_all_values(self):
        return [["ID", "Grupo"], ["TRB-0002", "g"], ["TRB-0003", "g"],
                ["TRB-0004", "g"], ["TRB-0005", "g"]]


_o = H.siguiente_id_libre
H.siguiente_id_libre = lambda pref, mx, propia="", ancho=4, tope=200: f"{pref}{mx+1:0{ancho}d}"
try:
    _r = R._next_id(_WS(), "TRB")
    chk("con 4 filas e IDs 0002..0005 emite TRB-0006, no TRB-0005", _r, "TRB-0006")
    chk("...o sea: NO colisiona con uno existente",
        _r in ("TRB-0002", "TRB-0003", "TRB-0004", "TRB-0005"), False)

    class _Hueco:
        """Un hueco en medio: 0001 y 0009. El siguiente debe ser 0010."""
        def get_all_values(self):
            return [["ID"], ["TRB-0001"], ["TRB-0009"]]
    chk("con huecos, sigue el MÁXIMO (no el conteo)",
        R._next_id(_Hueco(), "TRB"), "TRB-0010")

    class _Vacia:
        def get_all_values(self):
            return [["ID"]]
    chk("hoja vacía → el primero", R._next_id(_Vacia(), "TRB"), "TRB-0001")

    class _Rota:
        def get_all_values(self):
            raise RuntimeError("sin red")
    chk("si la hoja no se puede leer, no revienta",
        R._next_id(_Rota(), "TRB"), "TRB-0001")
finally:
    H.siguiente_id_libre = _o

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
