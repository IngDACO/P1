"""OCTAVA red: el argumento de display es un IfExp (a if c else b).

La red de POSICION (v440) mira si el argumento es un Constant sin t(); un
ternario NO es un Constant, asi que sus dos ramas pasan por delante sin que
salte nada — la trampa n30 otra vez, un ano despues.
"""
import ast, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app")
DISPLAY = {"write","markdown","caption","info","success","error","warning","title",
           "header","subheader","button","text","metric","toast","radio","selectbox",
           "checkbox","text_input","number_input","expander","tab","download_button",
           "form_submit_button","multiselect","text_area","date_input","time_input",
           "file_uploader","slider","toggle","popover","help","label","exito","aviso"}

def envuelto(n):
    return isinstance(n, ast.Call) and (
        getattr(n.func, "id", None) in ("t", "d", "_d", "_etq")
        or getattr(n.func, "attr", None) in ("t", "d", "etiqueta"))

hall = []
for f in sorted(BASE.rglob("*.py")):
    if ".venv" in str(f):
        continue
    try:
        arb = ast.parse(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    for n in ast.walk(arb):
        if not isinstance(n, ast.Call):
            continue
        nom = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
        if nom not in DISPLAY:
            continue
        # solo llamadas a st.* / flash.* (receptor), no logger
        rec = getattr(getattr(n.func, "value", None), "id", "")
        if rec not in ("st", "flash", "c1", "c2", "c3", "col", "cols", ""):
            continue
        for a in list(n.args) + [k.value for k in n.keywords if k.arg in ("label","help","body","text")]:
            if isinstance(a, ast.IfExp):
                for rama in (a.body, a.orelse):
                    if isinstance(rama, ast.Constant) and isinstance(rama.value, str) and len(rama.value) > 12:
                        hall.append((f.name, a.lineno, rama.value[:70]))
print(f"IfExp con rama literal SIN t(): {len(hall)}")
for h in hall:
    print(f"  {h[0]}:{h[1]}  {h[2]!r}")
