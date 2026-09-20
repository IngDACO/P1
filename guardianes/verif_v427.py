"""v427: un ID borrado NO se recicla mientras algo siga apuntando a él.

Los 13 generadores de la app hacen `max(los vivos) + 1`, así que borrar la fila con
el ID más alto libera ese número y el siguiente alta lo reutiliza — arrastrando los
huérfanos del anterior.

⚠️ No es teórico. En el ciclo de negocio de v426, dos facturas de una prueba vieja
apuntaban a `PRJ-0017`; al recrear ese ID, la obra nueva **heredó $1.000 de
facturación ajena** y su pendiente bajó de $4.000 a $3.000.

Lo que se protege:
  (a) las tres entidades que se BORRAN y se REFERENCIAN (proyecto, cliente, gasto)
      emiten su ID saltando los que otra hoja usa;
  (b) la comprobación mira todas las hojas MENOS la propia (si no, ningún ID vivo
      podría emitirse) e INCLUYE `Auditoria`, que es donde queda constancia de lo
      borrado;
  (c) degrada al comportamiento de siempre si la lectura falla: un problema de red
      no puede impedir dar de alta;
  (d) el barrido tiene tope: nada de colgarse buscando un hueco.
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


def fn(a, nombre):
    return next((n for n in ast.walk(a)
                 if isinstance(n, ast.FunctionDef) and n.name == nombre), None)


# ── (a) Los generadores que importan ────────────────────────────────────────
print("== a) las entidades que se borran Y se referencian saltan el ID ==")
CASOS = {
    ("projects.py", "_next_project_id"): "PRJ-",
    ("clientes.py", "_next_id"): "CLI-",
    ("expenses.py", "_next_id"): "G-",
}
for (fich, nom), pref in CASOS.items():
    f = fn(arbol(RAIZ / "core" / fich), nom)
    llama = any(isinstance(n, ast.Call)
                and getattr(n.func, "attr", getattr(n.func, "id", "")) == "siguiente_id_libre"
                for n in ast.walk(f or ast.Module(body=[], type_ignores=[])))
    chk(f"{fich}:{nom} ({pref}) usa `siguiente_id_libre`", llama)
    # ⚠️ y conserva el `max+1` como respaldo dentro de un except: si la comprobación
    # falla, se crea igual (ver (c)).
    _fb = any(isinstance(n, ast.Try) for n in ast.walk(f))
    chk(f"   ...con respaldo si la comprobación falla", _fb)

# ── (b) Qué hojas mira ──────────────────────────────────────────────────────
print("\n== b) mira las otras hojas, no la suya, y cuenta la Auditoría ==")
_h = arbol(RAIZ / "core" / "hojas.py")
_ir = fn(_h, "ids_referenciados")
chk("existe `ids_referenciados`", _ir is not None)
_lits = {c.value for c in ast.walk(_ir) if isinstance(c, ast.Constant)
         and isinstance(c.value, str)}
chk("incluye `Auditoria` (donde queda lo borrado)", "Auditoria" in _lits)

# ⚠️ Que la EXCLUSIÓN de la hoja propia funcione NO se puede comprobar buscando el
# nombre `propia_l`: sigue existiendo (se asigna arriba) aunque se borre la
# comparación, así que el chequeo pasaba con el filtro ROTO. Se ejercita de verdad,
# con el libro simulado. Lo destapó probarlo contra el código roto.
import streamlit as _st                                             # noqa: E402
_st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "g"}
from core import hojas as _H                                        # noqa: E402


class _LibroFalso:
    """Dos hojas: `Projects` (donde el ID vive) e `Invoices` (donde lo referencian).

    ⚠️ v465: los titulos van en INGLES porque el codigo ya los pide asi. Con los
    nombres viejos, `_existentes` no casaba, el lote salia vacio y este chequeo
    daba un FALLO que no existia — el andamio caducado, no la afirmacion.
    """
    DATOS = {"Projects": [["ID"], ["PRJ-0500"], ["PRJ-0501"]],
             "Invoices": [["ID", "LineasJSON"],
                          ["FAC-1", '[{"proyecto_id":"PRJ-0500"}]']]}

    def values_batch_get(self, rangos):
        out = []
        for r in rangos:
            t = r.strip("'")
            out.append({"range": f"'{t}'!A1:Z9", "values": self.DATOS.get(t, [])})
        return {"valueRanges": out}


# ⚠️ Se parchea TAMBIÉN `sheet_id_para`: resolver el libro de verdad necesita los
# secrets, que se buscan relativos al CWD (v19). Corriendo el guardián fuera de
# `survey_app` lanzaba, el `except` devolvía vacío y el chequeo daba un FALLO que no
# existía. Un guardián no puede depender del directorio desde el que se lance.
from core import timeclock as _TC                                   # noqa: E402
_ol, _oe, _os = _H._libro, _H._existentes, _TC.sheet_id_para
_H._libro = lambda sheet_id="": _LibroFalso()
_H._existentes = lambda sheet_id="": {"projects", "invoices"}
# ⚠️ `titulo_real` consultaria el indice del libro REAL (y sin secrets lanzaria):
# aqui el libro falso ya usa los nombres nuevos, asi que es la identidad.
_otr = _TC.titulo_real
_TC.titulo_real = lambda title="", sheet_id="": title
_TC.sheet_id_para = lambda title="", grupo=None: "libro-falso"
try:
    _sin = _H.ids_referenciados("PRJ-", propia="Projects")
    chk("excluye la hoja propia: solo ve el ID que OTRA hoja referencia",
        sorted(_sin), ["PRJ-0500"])
    _con = _H.ids_referenciados("PRJ-", propia="")
    chk("...y sin excluirla vería también el que solo vive ahí",
        sorted(_con), ["PRJ-0500", "PRJ-0501"])
finally:
    _H._libro, _H._existentes, _TC.sheet_id_para = _ol, _oe, _os
    _TC.titulo_real = _otr
_sl = fn(_h, "siguiente_id_libre")
chk("existe `siguiente_id_libre`", _sl is not None)
chk("...con tope de barrido (no se cuelga)",
    any(k.arg == "tope" for k in _sl.args.kwonlyargs + _sl.args.args)
    or "tope" in [a.arg for a in _sl.args.args])

# ── Comportamiento, con la función REAL ─────────────────────────────────────
print("\n== y la regla funciona ==")
import streamlit as st                                               # noqa: E402
st.session_state["auth"] = {"usuario": "v", "rol": "administrator", "grupo": "g"}
from core import hojas                                               # noqa: E402

_orig = hojas.ids_referenciados
try:
    # El caso REAL de v426: PRJ-0017 borrado pero aún referenciado por dos facturas.
    hojas.ids_referenciados = lambda pref, propia="", sheet_id="": {"PRJ-0017"}
    chk("salta el ID que aún se referencia",
        hojas.siguiente_id_libre("PRJ-", 16, propia="Proyectos"), "PRJ-0018")
    chk("...y si no hay referencias, no salta nada",
        (setattr(hojas, "ids_referenciados", lambda *a, **k: set())
         or hojas.siguiente_id_libre("PRJ-", 16, propia="Proyectos")), "PRJ-0017")
    # varios seguidos ocupados
    hojas.ids_referenciados = lambda *a, **k: {"PRJ-0017", "PRJ-0018", "PRJ-0019"}
    chk("salta TODOS los ocupados seguidos",
        hojas.siguiente_id_libre("PRJ-", 16, propia="Proyectos"), "PRJ-0020")
    # el ancho se respeta (G- va a 5 dígitos)
    hojas.ids_referenciados = lambda *a, **k: {"G-00014"}
    chk("respeta el ancho de cada prefijo",
        hojas.siguiente_id_libre("G-", 13, propia="Gastos", ancho=5), "G-00015")

    # ── (c) Degrada si la lectura falla ─────────────────────────────────────
    print("\n== c) si la comprobación falla, se crea igual ==")
    def _revienta(*a, **k):
        raise RuntimeError("sin red")
    hojas.ids_referenciados = _revienta
    try:
        _r = hojas.siguiente_id_libre("PRJ-", 16, propia="Proyectos")
        chk("...devuelve el siguiente sin más", _r, "PRJ-0017")
    except Exception as e:
        chk(f"...no propaga la excepción ({e})", False)

    # ── (d) Tope del barrido ────────────────────────────────────────────────
    print("\n== d) con todo ocupado no se cuelga ==")
    hojas.ids_referenciados = lambda *a, **k: {f"PRJ-{n:04d}" for n in range(1, 9999)}
    _r = hojas.siguiente_id_libre("PRJ-", 16, propia="Proyectos", tope=50)
    chk("sale del bucle y devuelve algo", _r.startswith("PRJ-"))
    chk("...tras agotar el tope", _r, "PRJ-0067")
finally:
    hojas.ids_referenciados = _orig

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
