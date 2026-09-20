"""Prueba `verif_v440.py` contra código ROTO (regla v410).

Cada rotura es un fallo REAL que ya se cometió en esta tanda. Si el guardián sigue verde,
está ciego. Respaldo → rompo → corro → restauro (siempre, aunque reviente).
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
GUARD = Path(__file__).parent / "verif_v440.py"

ROTURAS = [
    # ⚠️ la clave del formulario pasaría a depender del idioma → se pierde el estado
    ("una CLAVE de widget se traduce", "core/clientes_ui.py",
     'st.form("cli_nuevo")', 'st.form(t("new_client"))'),

    # ⚠️ `st.data_editor` devolvería una columna que nadie sabe leer
    ("una CLAVE de column_config se traduce", "core/invoices_ui.py",
     '{"Importe": st.column_config', '{t("Amount"): st.column_config'),

    # ⚠️ el fallo de v437/v439/quotes_ui: `t` local rompe la función entera
    ("una función vuelve a tapar `t`", "core/quotes_ui.py",
     "    _tot = Q.totales(lineas, _num(c.get(\"ImpuestoPct\")))",
     "    t = Q.totales(lineas, _num(c.get(\"ImpuestoPct\")))"),

    # ⚠️ «Guardar» no lleva acento ni palabra funcional: lo tiene que cazar el barrido
    #    por POSICIÓN, no el detector de español
    ("una etiqueta vuelve al español sin acentos", "core/inventory_ui.py",
     't(":material/save: Save changes")', '":material/save: Guardar cambios"'),

    ("una etiqueta larga vuelve al español", "core/payroll_ui.py",
     't("Net pay")', '"Neto a pagar"'),

    ("el motor deja de importarse a nivel de módulo", "core/catalogo_ui.py",
     "from core.i18n import t", "# from core.i18n import t"),
]


def corre():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode


print("guardián sobre el código SANO...")
if corre() != 0:
    print("  ⚠️ ya falla en sano — no tiene sentido seguir")
    sys.exit(1)
print("  OK (verde)\n")

ok = True
for i, (titulo, rel, viejo, nuevo) in enumerate(ROTURAS, 1):
    p = RAIZ / rel
    bak = p.with_suffix(p.suffix + ".bak_r440")
    shutil.copy2(p, bak)
    try:
        s = p.read_text(encoding="utf-8")
        if s.count(viejo) < 1:
            print(f"  {i}. ⚠️ ANCLA NO CASA — la rotura no se aplicó: {titulo}")
            ok = False
            continue
        p.write_text(s.replace(viejo, nuevo, 1), encoding="utf-8")
        rc = corre()
        print(f"  {i}. {'CAZADA' if rc else '⚠️ NO LA VE':12} {titulo}")
        ok = ok and rc != 0
    finally:
        shutil.copy2(bak, p)
        bak.unlink()

print(f"\nguardián tras restaurar: {'verde' if corre() == 0 else '⚠️ ROJO'}")
print(f"{len(ROTURAS)} roturas — " + ("las caza TODAS" if ok else "HAY CIEGAS"))
sys.exit(0 if ok else 1)
