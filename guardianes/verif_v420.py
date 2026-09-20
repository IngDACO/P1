"""v420: se puede dar de alta un cliente SIN salir de la cotización.

Antes, si el cliente era nuevo había que irse a Contactos, crearlo y volver a empezar la
cotización. Y peor: si NO había ningún cliente, la pantalla hacía `return` — o sea que el
primer presupuesto de un cliente nuevo era imposible sin pasar antes por otra sección.
Cotizar es lo PRIMERO que se hace con un cliente nuevo: pedir la ficha de antemano es el
orden al revés.

Lo que se protege:
  (a) la pantalla no puede volver a cerrarse cuando no hay clientes;
  (b) ⚠️ la ficha se crea ANTES que la cotización y, si falla, la cotización NO se crea:
      el `ClienteID` es lo que usa `aceptar_y_crear_proyecto` (v354) para que la obra
      nazca con su cliente — sin él, facturarla después no encuentra la ficha (v357);
  (c) un nombre duplicado REUTILIZA la ficha existente en vez de dejar al usuario con la
      cotización escrita y sin poder guardarla (`create_cliente` no admite duplicados por
      grupo, así que dentro del grupo ese nombre es UNO);
  (d) las keys del formulario se limpian: si no, la siguiente cotización abre con el
      cliente anterior ya tecleado y es fácil enlazarla al equivocado.
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


src = (RAIZ / "core" / "quotes_ui.py").read_text(encoding="utf-8")
sin_com = tokenize.untokenize(
    [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
     if t.type != tokenize.COMMENT])
arb = ast.parse(sin_com)
fn = next((n for n in ast.walk(arb)
           if isinstance(n, ast.FunctionDef) and n.name == "_nueva"), None)
chk("existe `_nueva`", fn is not None)
cad = [n.value for n in ast.walk(fn)
       if isinstance(n, ast.Constant) and isinstance(n.value, str)]
todo = "".join(cad)

# ── (a) La pantalla no se cierra por no haber clientes ──────────────────────
print("\n== a) sin clientes, la pantalla sigue sirviendo ==")
chk("ya no manda a Contactos y se rinde",
    "Créalos en" not in todo and "No hay clientes" not in todo)
# ⚠️ CADUCADO por v440 (i18n F3): la opción pasó a «New client».
chk("hay una opción para dar de alta aquí",
    any(("Nuevo cliente" in c or "New client" in c) for c in cad))

# ── (b) La ficha, antes que la cotización ──────────────────────────────────
print("\n== b) la ficha se crea ANTES, y si falla no hay cotización ==")
_crear = [n for n in ast.walk(fn)
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
          and n.func.attr == "create_cliente"]
chk("se da de alta el cliente desde aquí", len(_crear) >= 1)
_qcrear = [n for n in ast.walk(fn)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "crear" and isinstance(n.func.value, ast.Name)
           and n.func.value.id == "Q"]
chk("...y sigue habiendo UNA sola creación de cotización", len(_qcrear), 1)
chk("el alta del cliente va ANTES que la de la cotización",
    _crear[0].lineno < _qcrear[0].lineno if (_crear and _qcrear) else False)
# tiene que haber una salida (return) si no se puede resolver el cliente
_returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return)]
chk("hay salidas que abortan sin crear la cotización", len(_returns) >= 2)

# ── (c) y (d) ──────────────────────────────────────────────────────────────
print("\n== c) un nombre duplicado no deja al usuario tirado ==")
# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.
chk("se busca la ficha ya existente para reutilizarla",
    any("Ya existía" in c or "ya existía" in c.lower()
        or "already existed" in c.lower() for c in cad))
_incl = any(isinstance(k, ast.keyword) and k.arg == "incluir_inactivos"
            for n in ast.walk(fn) if isinstance(n, ast.Call) for k in n.keywords)
chk("...mirando también entre las inactivas", _incl)

print("\n== d) el formulario no se hereda en la siguiente cotización ==")
_keys = ("cot_new_cli_nom", "cot_new_cli_cto", "cot_new_cli_tel", "cot_new_cli_mail")
_limpia = [k for k in _keys if any(k == c for c in cad)]
chk("las keys del cliente nuevo existen", len(_limpia), 4)

# ⚠️ Por BLOQUE de limpieza, no por número de apariciones. La primera versión pedía
# «cada key ≥ 2 veces» y eso lo pasaba el código con la limpieza BORRADA de uno de los
# dos sitios (crear el widget + limpiar en el otro sitio ya suman 2). Hay DOS salidas
# del formulario —cancelar y guardar— y las dos tienen que limpiar: si solo lo hace una,
# por el otro camino el nombre del cliente anterior sigue ahí. Lo destapó probar el
# guardián contra el código roto.
_bloques = []
for n in ast.walk(fn):
    if not isinstance(n, ast.For):
        continue
    _pops = [x for x in ast.walk(n)
             if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
             and x.func.attr == "pop"]
    if not _pops:
        continue
    _en = {c.value for c in ast.walk(n.iter)
           if isinstance(c, ast.Constant) and isinstance(c.value, str)}
    _bloques.append(_en)
chk("hay DOS salidas del formulario que limpian (cancelar y guardar)",
    len(_bloques), 2)
chk("...y las dos limpian TODAS las keys del cliente nuevo",
    all(set(_keys) <= b for b in _bloques), True)
print(f"         keys por bloque: {[len(set(_keys) & b) for b in _bloques]} de 4")

# ── Comportamiento ─────────────────────────────────────────────────────────
print("\n== y la regla funciona ==")
from core import clientes as C                                     # noqa: E402


def resolver(cli_sel, nuevo, fichas, crear):
    if cli_sel != "➕ Nuevo cliente":
        return {"ID": "C-1", "Nombre": cli_sel}, None
    nom = str(nuevo.get("nombre", "")).strip()
    if not nom:
        return None, "El nombre del cliente es obligatorio."
    ok_c, res = crear(nom)
    if ok_c:
        return {"ID": res, "Nombre": nom}, None
    ya = next((x for x in fichas if C._norm(x.get("Nombre")) == C._norm(nom)), None)
    if not ya:
        return None, f"No se pudo crear el cliente: {res}"
    return ya, None


F = [{"ID": "C-9", "Nombre": "ACME Pty Ltd"}]
chk("cliente nuevo → se enlaza por su ID",
    resolver("➕ Nuevo cliente", {"nombre": "Obra SL"}, F, lambda n: (True, "C-42"))[0],
    {"ID": "C-42", "Nombre": "Obra SL"})
chk("sin nombre → no se crea nada",
    resolver("➕ Nuevo cliente", {"nombre": " "}, F, None)[1],
    "El nombre del cliente es obligatorio.")
chk("duplicado (aunque cambie may/min) → reutiliza la ficha",
    resolver("➕ Nuevo cliente", {"nombre": "acme PTY ltd"}, F,
             lambda n: (False, "Ya existe"))[0]["ID"], "C-9")
chk("fallo real del alta → aborta, sin cotización huérfana",
    resolver("➕ Nuevo cliente", {"nombre": "X"}, [], lambda n: (False, "sin conexión"))[0],
    None)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
