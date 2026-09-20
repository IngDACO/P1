# -*- coding: utf-8 -*-
"""v498 · el TIPO de credencial que llega a la hoja es el que se eligió.

El fallo real (reportado por el usuario): el formulario llamaba a `credentials.add`
pasando **`t`**, que desde la migración de i18n es la FUNCIÓN de traducción, en el sitio
del tipo. `str(función)` no está vacío, así que la guarda del backend lo dejaba pasar y en
la hoja quedaba «<function t at 0x…>» como tipo de la credencial.

⚠️ Llevaba escondido desde que el tipo dejó de llamarse `t` (v189): en v350 ejercité
`credentials.add` DIRECTAMENTE y pasó, porque el fallo no está en la función sino en lo
que la pantalla le pasa. Por eso este guardián EJECUTA el formulario.

Lo que protege:
  (a) lo que llega a `add` es el tipo elegido, y es TEXTO;
  (b) «Other» manda lo que se escribió en «Specify the type», no la palabra «Other»;
  (c) el backend RECHAZA un tipo que no sea texto (para que la clase de fallo no escriba);
  (d) nadie más en el repo pasa la función `t` como argumento de datos.
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
G = "cliente1"
st.session_state["auth"] = {"usuario": "admin", "nombre": "admin",
                            "rol": "administrator", "grupo": G}

fallos, n_ok = [], 0


def ok(que):
    global n_ok
    n_ok += 1
    print(f"  ok   {que}")


def fallo(que, detalle=""):
    fallos.append(que)
    print(f"  *** FALLO  {que}" + (f"  -> {detalle}" if detalle else ""))


def ck(que, real, esperado):
    ok(que) if real == esperado else fallo(que, f"{real!r} != {esperado!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import auth_ui as AU, credentials as C                  # noqa: E402

# ═════ 1 · el formulario, EJECUTADO ══════════════════════════════════════════
print("\n[1] el formulario manda el TIPO elegido (no la función de traducción)")
LLAMADAS = []
_g = {}


class _Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _espia(nombre, fn):
    _g[nombre] = getattr(st, nombre)
    setattr(st, nombre, fn)


ELEGIDO = {"tipo": "White Card", "otro": ""}
_espia("markdown", lambda *a, **kw: None)
_espia("caption", lambda *a, **kw: None)
_espia("warning", lambda *a, **kw: None)
_espia("error", lambda *a, **kw: None)
_espia("info", lambda *a, **kw: None)
_espia("dataframe", lambda *a, **kw: None)
_espia("download_button", lambda *a, **kw: None)
_espia("expander", lambda *a, **kw: _Ctx())
_espia("form", lambda *a, **kw: _Ctx())
_espia("columns", lambda n, **kw: tuple(_Col() for _ in range(n if isinstance(n, int) else len(n))))
_espia("rerun", lambda *a, **kw: None)
_espia("file_uploader", lambda *a, **kw: None)
_espia("text_input", lambda label, *a, **kw: ELEGIDO["otro"] if "Specify" in str(label) else "N1")
_espia("date_input", lambda *a, **kw: None)
_espia("selectbox", lambda label, opciones, **kw: ELEGIDO["tipo"] if str(label).startswith("Type")
       else list(opciones)[0])
_espia("form_submit_button", lambda *a, **kw: True)
_espia("button", lambda *a, **kw: False)
_espia("metric", lambda *a, **kw: None)


class _Col:
    def text_input(self, label, *a, **kw):
        return "N1"

    def selectbox(self, label, opciones, **kw):
        return list(opciones)[0]

    def date_input(self, *a, **kw):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


_orig = (C.add, C.list_for, C.is_configured)
try:
    C.list_for = lambda u: []
    C.is_configured = lambda: True
    C.add = lambda *a, **kw: (LLAMADAS.append(a) or (True, "ok"))
    AU.render_credenciales("juan", G, editable=True, key_prefix="zz")
    ck("se llamó a add una vez", len(LLAMADAS), 1)
    _tipo = LLAMADAS[0][2] if LLAMADAS else None
    ck("...con el TIPO elegido", _tipo, "White Card")
    ck("...y es TEXTO (no la función de traducción)", isinstance(_tipo, str), True)

    # (b) «Other» manda lo que se escribió
    LLAMADAS.clear()
    ELEGIDO.update({"tipo": "Other", "otro": "  Asbestos awareness  "})
    AU.render_credenciales("juan", G, editable=True, key_prefix="zz")
    ck("«Other» manda lo que se escribió, no la palabra «Other»",
       LLAMADAS[0][2] if LLAMADAS else None, "Asbestos awareness")

    # «Other» sin escribir nada: se queda «Other» (no vacío)
    LLAMADAS.clear()
    ELEGIDO.update({"tipo": "Other", "otro": "   "})
    AU.render_credenciales("juan", G, editable=True, key_prefix="zz")
    ck("«Other» sin especificar se guarda como «Other»",
       LLAMADAS[0][2] if LLAMADAS else None, "Other")
finally:
    for n, f in _g.items():
        setattr(st, n, f)
    (C.add, C.list_for, C.is_configured) = _orig

# ═════ 2 · la guarda del backend ═════════════════════════════════════════════
print("\n[2] el backend no deja escribir un tipo que no sea texto")
_w = C._ws
try:
    C._ws = lambda: (_ for _ in ()).throw(AssertionError("no debería llegar a la hoja"))
    for valor, como in ((print, "una función"), (None, "None"), (123, "un número"), ("  ", "espacios")):
        r = C.add("u", G, valor)
        ck(f"rechaza {como}", (r[0], "type is required" in str(r[1])), (False, True))
finally:
    C._ws = _w

# ═════ 3 · nadie pasa la función `t` como dato ═══════════════════════════════
print("\n[3] en todo el repo: la función `t` no se pasa como argumento de datos")


def _sospechosos():
    out = []
    _vistos_comp = set()          # llamadas dentro de una comprensión que liga `t`
    for f in sorted(os.listdir(os.path.join(RAIZ, "core"))) + ["app.py"]:
        rel = os.path.join("core", f) if f != "app.py" else "app.py"
        if not rel.endswith(".py"):
            continue
        tr = ast.parse(_fuente(rel))
        for fn in [n for n in ast.walk(tr) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            # si `t` es variable de ESA función, ahí no es la de i18n
            loc = {tg.id for a in ast.walk(fn) if isinstance(a, ast.Assign)
                   for tg in a.targets if isinstance(tg, ast.Name)}
            loc |= {a.arg for a in fn.args.args}
            loc |= {a.target.id for a in ast.walk(fn)
                    if isinstance(a, ast.For) and isinstance(a.target, ast.Name)}
            # ⚠️ Una comprensión tiene ÁMBITO PROPIO (trampa nº3): su variable no es la
            # `t` de i18n, así que esas llamadas no son sospechosas.
            comprension = set()
            for comp in ast.walk(fn):
                if isinstance(comp, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                    for gen in comp.generators:
                        if isinstance(gen.target, ast.Name):
                            comprension.add(gen.target.id)
                    if "t" in comprension:
                        for c2 in ast.walk(comp):
                            _vistos_comp.add(id(c2))
            if "t" in loc:
                continue
            for c in ast.walk(fn):
                if not isinstance(c, ast.Call):
                    continue
                if id(c) in _vistos_comp:
                    continue
                for a in c.args:
                    if isinstance(a, ast.Name) and a.id == "t":
                        out.append(f"{rel}:{c.lineno}")
                for kw in c.keywords:
                    # `format_func=t` es legítimo: ahí la función ES el argumento
                    if (isinstance(kw.value, ast.Name) and kw.value.id == "t"
                            and kw.arg not in ("format_func", "key_func", "hash_funcs")):
                        out.append(f"{rel}:{c.lineno}")
    return out


ck("ninguna llamada pasa `t` como dato", _sospechosos(), [])
# ⚠️ la sonda, validada contra el caso conocido-malo (trampa nº12)
_tmp = os.path.join(RAIZ, "core", "_zz_sonda_v498.py")
try:
    io.open(_tmp, "w", encoding="utf-8").write(
        "from core.i18n import t\n\n\ndef f(u, g):\n    return C.add(u, g, t, 1)\n")
    ck("...y la sonda CAZA el fallo real reconstruido",
       any("_zz_sonda_v498" in s for s in _sospechosos()), True)
finally:
    os.remove(_tmp)

# ═════ 4 · el aviso de certificados, sin español suelto ══════════════════════
print("\n[4] el aviso de certificados al asignar, traducido")
_av = next(n for n in ast.walk(ast.parse(_fuente("core/projects_ui.py")))
           if isinstance(n, ast.FunctionDef) and n.name == "_avisar_asignados")
# ⚠️ El literal 'falta' TIENE que seguir estando: es el DATO con el que se compara. Lo que
# no puede haber es esa palabra ESCRITA en el texto que se pinta (dentro de una f-string).
_pintados = [v.value for js in ast.walk(_av) if isinstance(js, ast.JoinedStr)
             for v in js.values if isinstance(v, ast.Constant) and isinstance(v.value, str)]
ck("ya no PINTA «falta»/«vencido» a mano",
   [x for x in _pintados if "falta" in x or "vencido" in x], [])
ck("...y la comparación con el dato en español sigue ahí",
   "'falta'" in ast.unparse(_av), True)
ck("...y traduce el valor al pintarlo",
   "_etq(comp['por_tipo']" in ast.unparse(_av), True)

print("\n" + "=" * 70)
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
