# -*- coding: utf-8 -*-
"""v536 · UN DESPLIEGUE NUEVO NO PUEDE CORRER CON LOS MÓDULOS VIEJOS EN MEMORIA.

⚠️ Visto en producción el 06/10/2026: al desplegar v535, el Cloud ejecutó el `app.py` nuevo
—que llama a `estado_vivo.de_la_cuenta`, función nueva— con el `core.estado_vivo` de v534
todavía cargado en el proceso. Resultado: `AttributeError` en `app.py` línea 133 y la app
entera caída para cualquiera con sesión, hasta reiniciarla a mano. CLAUDE.md lo tenía como
«Settings → Reboot app» si el chip seguía viejo; esta vez no era un chip viejo, era la app
caída.

→ `app.py`, antes de importar nada de la app: si la versión del DISCO no es aquella con la
que se importaron los módulos (`core._VERSION_CARGADA`), descarta TODOS los `core.*` y
`extractors.*` y los vuelve a importar en esa misma pasada.

Lo que protege, EJECUTANDO el bloque real de `app.py` (extraído por AST) sobre un proceso
con módulos «viejos» simulados:
  (a) ⚠️ el caso de producción: módulos cargados SIN marca de versión (el proceso de v535) →
      se descartan y se vuelven a importar los del disco;
  (b) versión distinta → se descartan; misma versión → NO se toca nada (sin coste);
  (c) solo los de la app: `streamlit`, `pandas`… no se tocan;
  (d) el bloque va ANTES de cualquier `import core…` / `from core…` de `app.py`.
"""
import ast
import io
import os
import sys
import tempfile
import types

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def sec(x):
    print("\n%s" % x)


_src = io.open(os.path.join(RAIZ, "app.py"), encoding="utf-8").read()
_t = ast.parse(_src)

# ── El bloque real: desde la lectura de VERSION hasta la marca, tal cual está en app.py ──
_i0 = next((i for i, n in enumerate(_t.body) if isinstance(n, ast.Try)
            and "_V_DISCO" in ast.unparse(n)), None)
_i1 = next((i for i, n in enumerate(_t.body) if isinstance(n, ast.Assign)
            and ast.unparse(n).startswith("_core_pkg._VERSION_CARGADA")), None)
sec("1. El bloque está en app.py, y ANTES de importar nada de la app")
chk("se encontró el bloque (lectura de VERSION … marca de versión)",
    _i0 is not None and _i1 is not None and _i0 < _i1, (_i0, _i1))
_primero_core = next((i for i, n in enumerate(_t.body)
                      if isinstance(n, (ast.Import, ast.ImportFrom))
                      and (("core" in [a.name.split(".")[0] for a in n.names])
                           if isinstance(n, ast.Import)
                           else (n.module or "").split(".")[0] == "core")), None)
_import_core_pkg = next((i for i, n in enumerate(_t.body) if isinstance(n, ast.Import)
                         and [a.name for a in n.names] == ["core"]), None)
chk("⚠️ el primer import de la app es el del propio bloque (`import core as _core_pkg`), "
    "después de descartar: ningún `from core…` va antes",
    _primero_core is not None and _primero_core == _import_core_pkg and _i0 < _primero_core < _i1,
    (_primero_core, _import_core_pkg, _i0, _i1))

_bloque = ast.Module(body=_t.body[_i0:_i1 + 1], type_ignores=[]) if _i1 is not None else None
_codigo = compile(_bloque, "app.py[bloque v536]", "exec") if _bloque else None


def _proceso(version_disco, marca, extra=()):
    """Simula un proceso con módulos de la app ya cargados y corre el bloque real."""
    guardados = {m: sys.modules[m] for m in list(sys.modules)
                 if m in ("core", "extractors") or m.startswith(("core.", "extractors."))}
    for m in guardados:
        sys.modules.pop(m)
    viejo = types.ModuleType("core")
    viejo.__path__ = []
    if marca is not None:
        viejo._VERSION_CARGADA = marca
    sys.modules["core"] = viejo
    sys.modules["core.estado_vivo"] = types.ModuleType("core.estado_vivo")   # sin de_la_cuenta
    sys.modules["extractors.schindler"] = types.ModuleType("extractors.schindler")
    for m in extra:
        sys.modules[m] = types.ModuleType(m)
    d = tempfile.mkdtemp()
    io.open(os.path.join(d, "VERSION"), "w", encoding="utf-8").write(version_disco)
    ns = {"__file__": os.path.join(d, "app.py"), "__name__": "__main__", "sys": sys, "os": os}
    try:
        exec(_codigo, ns)
        res = {"core_nuevo": sys.modules.get("core") is not viejo,
               "marca": getattr(sys.modules.get("core"), "_VERSION_CARGADA", None),
               "ev_viejo": "core.estado_vivo" in sys.modules
               and not hasattr(sys.modules["core.estado_vivo"], "__file__"),
               "schindler_viejo": "extractors.schindler" in sys.modules
               and not hasattr(sys.modules["extractors.schindler"], "__file__"),
               "extra": [m for m in extra if m in sys.modules]}
    finally:
        for m in [m for m in list(sys.modules)
                  if m in ("core", "extractors") or m.startswith(("core.", "extractors."))]:
            sys.modules.pop(m)
        sys.modules.update(guardados)
        for m in extra:
            sys.modules.pop(m, None)
    return res


sec("2. ⚠️ Ejecutando el bloque real sobre un proceso con módulos viejos")
if _codigo is None:
    fallo("no hay bloque que ejecutar")
else:
    r = _proceso("v536", None)
    chk("⚠️ el caso de producción: módulos cargados SIN marca (el proceso de v535) → se "
        "descartan y se importa el `core` del disco", r["core_nuevo"] and not r["ev_viejo"], r)
    chk("...y queda marcado con la versión del disco", r["marca"] == "v536", r)
    r = _proceso("v537", "v536")
    chk("versión distinta → se descartan también los `extractors`",
        r["core_nuevo"] and not r["ev_viejo"] and not r["schindler_viejo"], r)
    r = _proceso("v536", "v536")
    chk("⚠️ MISMA versión → no se toca nada (ni coste, ni módulos nuevos a media sesión)",
        not r["core_nuevo"] and r["ev_viejo"] and r["schindler_viejo"], r)
    r = _proceso("v537", "v536", extra=("corealgo", "pandas_falso"))
    chk("solo se descartan los de la app (`core`, `extractors`): un módulo que solo EMPIEZA "
        "igual no se toca", r["extra"] == ["corealgo", "pandas_falso"], r)

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
