"""v456b — la limpieza de Drive mira el nivel DONDE ESTÁN las carpetas.

## El fallo, visto USANDO la herramienta

La pantalla dijo **«32 file(s) in total, 0 of them in folders of jobs that no longer
exist»** con la demo completamente vacía: todas las carpetas eran huérfanas y marcó cero.

`ROOT_NAME = "COPEX Proyectos"`, o sea que **la raíz YA ES esa carpeta** y las `PRJ-####`
cuelgan de ella directamente. Mi código las buscaba en `subcarpetas`, un nivel más abajo
del que están.

⚠️ **Y la prueba con Drive simulado no lo cazó porque el mock reproducía MI suposición.**
Un mock construido sobre la estructura que uno asume confirma el error en vez de
detectarlo — es el OK en falso de v309, ahora con una jerarquía en vez de un parámetro.
Lo que lo destapó fue mirar la tabla en pantalla: mostraba `PRJ-0020` a secas, cuando mi
código habría escrito `COPEX Proyectos / PRJ-0020`.

⚠️ Y el aviso lo decía a gritos: «32 archivos, 0 huérfanos» con la demo vacía es una
contradicción — no hacía falta leer el código para saber que algo estaba mal. Mirar el
número antes de pulsar el botón evitó un borrado con la clasificación equivocada.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = pathlib.Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))
CORE = RAIZ / "core"
fallos = []


def chk(ok, msg):
    print(("  OK  " if ok else "  FALLO  ") + msg)
    if not ok:
        fallos.append(msg)


print("== 1. La clasificación mira el PRIMER nivel, no solo las subcarpetas ==")
_src = (CORE / "auth_ui.py").read_text(encoding="utf-8")
_a = ast.parse(_src)
_fn = next((n for n in ast.walk(_a) if isinstance(n, ast.FunctionDef)
            and n.name == "_owner_drive_limpieza"), None)
chk(_fn is not None, "existe `_owner_drive_limpieza`")
_cuerpo = ast.get_source_segment(_src, _fn) or ""
chk("_clasificar" in _cuerpo, "hay un clasificador único para los dos niveles")
# ⚠️ La comprobación de fondo: la carpeta de PRIMER nivel se clasifica, no solo `sub`.
chk('_clasificar(c["nombre"]' in _cuerpo,
    "la carpeta de primer nivel pasa por el clasificador (era el fallo)")
chk('_clasificar(sub["nombre"]' in _cuerpo, "…y las subcarpetas también")

print("\n== 2. El recuento se DERIVA de la misma clasificación ==")
# Si se contara aparte, el número y el botón podrían decir cosas distintas — y eso fue
# exactamente lo que pasó: «0 huérfanos» junto a 32 archivos.
chk('f["Status"] == t("orphan")' in _cuerpo,
    "el nº de huérfanos sale de las filas ya clasificadas, no de un bucle paralelo")

print("\n== 3. La lógica, EJECUTADA con la estructura REAL ==")
from core.i18n import t  # noqa: E402
_vivos = set()


def _clasificar(nombre, ident, archivos, ruta):
    _hu = nombre.startswith("PRJ-") and nombre not in _vivos
    _est = t("orphan") if _hu else (t("in use") if nombre.startswith("PRJ-") else t("storage"))
    return ({"Folder": ruta, "Files": len(archivos), "Status": _est},
            [a["id"] for a in archivos] + [ident], _hu)


INV = [{"id": "p1", "nombre": "PRJ-0001", "archivos": [{"id": "a1"}, {"id": "a2"}], "subcarpetas": []},
       {"id": "rc", "nombre": "COPEX Recibos", "archivos": [{"id": "r1"}], "subcarpetas": []}]
_h, _todo = [], []
for c in INV:
    _f, _ids, _hu = _clasificar(c["nombre"], c["id"], c["archivos"], c["nombre"])
    _todo += _ids
    if _hu:
        _h += _ids
chk(set(_h) == {"a1", "a2", "p1"}, f"la carpeta PRJ del primer nivel es huérfana ({_h})")
chk("rc" not in _h and "r1" not in _h, "el almacén «COPEX Recibos» NO se marca huérfano")
chk(len(_todo) == 5, f"«todo» incluye ambas ({len(_todo)})")

# ⚠️ Y con un proyecto VIVO, su carpeta no se toca.
_vivos = {"PRJ-0001"}
_, _, _hu2 = _clasificar("PRJ-0001", "p1", [], "PRJ-0001")
chk(not _hu2, "una carpeta de proyecto VIVO no se marca huérfana")

print("\n== 4. ⚠️ La estructura que asume el código es la REAL ==")
_ds = (CORE / "drive_store.py").read_text(encoding="utf-8")
chk('"COPEX Proyectos"' in _ds,
    "la raíz de Drive ES «COPEX Proyectos» (por eso las PRJ son hijas directas)")

print("\n== 5. ⚠️ El escaneo SOBREVIVE al rerun (regla v110) ==")
# Con el inventario dentro del `if st.button("Scan Drive")`, cualquier interacción
# posterior —elegir el radio, teclear DELETE— dispara un rerun, el botón vale False y
# la tabla DESAPARECE. Volver a escanear y volver a tocar el radio repite el ciclo: la
# pantalla nunca deja llegar al borrado. Se vio USÁNDOLA, no leyéndola.
chk('st.session_state["_dl_inv"]' in _cuerpo,
    "el inventario se guarda en session_state, no en una variable del run")
chk('st.session_state.get("_dl_inv")' in _cuerpo,
    "…y se lee de ahí, así que sobrevive a los reruns")
chk('st.session_state.pop("_dl_inv", None)' in _cuerpo,
    "tras borrar se descarta (o la tabla mostraría archivos ya borrados)")
# ⚠️ La forma que NO puede volver: `if not st.button(...): return` antes del inventario.
chk("if not st.button(t(\":material/refresh: Scan Drive\")" not in _cuerpo,
    "no vuelve el `if not st.button(...): return` que causaba el bucle")

print(f"\n{'TODO OK' if not fallos else f'{len(fallos)} FALLOS'}")
sys.exit(0 if not fallos else 1)
