import py_compile, pathlib, importlib, sys, re
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
mods = sorted((BASE / "core").glob("*.py"))
for p in mods:
    py_compile.compile(str(p), doraise=True)
py_compile.compile(str(BASE / "app.py"), doraise=True)

malos = []
sys.path.insert(0, str(BASE))
for p in mods:
    try:
        importlib.import_module("core." + p.stem)
    except Exception as e:
        malos.append((p.stem, repr(e)[:80]))
print(f"compilan e importan: {len(mods)-len(malos)}/{len(mods)} + app.py")
for m in malos:
    print("  FALLO", m)

src = (BASE / "core" / "roster_ui.py").read_text(encoding="utf-8")
for n in ("render_estado_vivo", "_plan_vs_real"):
    print(f"referencias residuales a {n}: {len(re.findall(n, src))}")
print("herramientas en la fila:", len(re.findall(r'\("(?:asignar|radar|cumpl|cat)",', src)))
print("_cumplimiento definida:", "def _cumplimiento(" in src)
ks = re.findall(r'key\s*=\s*["\']([^"\']+)["\']', src)
print("keys duplicadas:", sorted({k for k in ks if ks.count(k) > 1}) or "ninguna")
sys.exit(1 if malos else 0)
