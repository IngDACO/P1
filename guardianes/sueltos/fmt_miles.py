"""v399 · Separador de miles en las columnas de dinero.

Sustitucion LITERAL, sin regex y sin tocar indentacion: solo se inserta una coma
dentro de la cadena de formato. MEDIDO en vivo (mini-app + intercepcion de
`fillText`, que es lo unico que ve lo que glide pinta en su canvas):

    "$%d"    -> $0 $368 $980 $2960  $3305  $27882      (trunca)
    "$%,d"   -> $0 $368 $980 $2,960 $3,305 $27,882     (trunca IGUAL)
    "$%.2f"  -> $2960.00  $3305.76  $27882.67
    "$%,.2f" -> $2,960.00 $3,305.76 $27,882.67
    "$%.0f"  -> $2960     $3306     $27883             (redondea)
    "$%,.0f" -> $2,960    $3,306    $27,883

⚠️ Por eso `%d` NO se convierte a `%.0f`: uno trunca y el otro redondea, asi que
cambiarlo moveria cifras en pantalla. Cada formato conserva su semantica.
"""
import io
import pathlib
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
RESP = pathlib.Path(__file__).parent / "resp_v399"
RESP.mkdir(exist_ok=True)

CAMBIOS = [('format="$%d"',    'format="$%,d"'),
           ('format="$%.2f"',  'format="$%,.2f"'),
           ('format="$%.0f"',  'format="$%,.0f"')]

FICHEROS = ["catalogo_ui.py", "clientes_ui.py", "inventory_ui.py", "invoices_ui.py",
            "payroll_ui.py", "projects_ui.py", "quotes_ui.py"]

total = 0
for nom in FICHEROS:
    p = BASE / nom
    src = io.open(p, encoding="utf-8").read()
    shutil.copy2(p, RESP / nom)               # respaldo ANTES de escribir
    n_fich, det = 0, []
    for viejo, nuevo in CAMBIOS:
        n = src.count(viejo)
        if n:
            src = src.replace(viejo, nuevo)
            det.append(f"{viejo} x{n}")
            n_fich += n
    if n_fich:
        io.open(p, "w", encoding="utf-8", newline="").write(src)
    total += n_fich
    print(f"  {nom:<18} {n_fich:>2}   {' · '.join(det)}")

print(f"\nTOTAL sustituido: {total}")

# --- comprobaciones DESPUES de escribir -------------------------------------
ok = True


def check(nombre, real, esp):
    global ok
    b = real == esp
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {nombre}: {real!r}" +
          ("" if b else f"   esperado {esp!r}"))


todo = "".join(io.open(BASE / f, encoding="utf-8").read() for f in FICHEROS)
check("39 formatos de dinero convertidos", total, 39)
check("no queda ningun formato de dinero SIN coma",
      sum(todo.count(v) for v, _ in CAMBIOS), 0)
check("ninguna coma duplicada", todo.count("$%,,"), 0)
# ⚠️ los % de margen NO llevan separador (valores < 500): no se han tocado
check("los formatos de porcentaje siguen intactos", todo.count('format="%.1f%%"') > 0, True)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
