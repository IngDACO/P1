# -*- coding: utf-8 -*-
"""Prueba el guardián de v450 contra código ROTO.

⚠️ Un guardián que solo se ejecuta sobre el código sano no demuestra nada: aprueba.
Cada rotura reproduce un fallo REAL de esta versión o de las anteriores.
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ROTURAS = [
    ("core/tabla.py", '"Cliente": "Client",', '',
     "se cae una cabecera del mapa → vuelve a pintarse «Cliente»"),
    ("core/tabla.py", 'out[c] = st.column_config.Column(t(base))', 'pass',
     "cfg deja de poner etiqueta → todas las cabeceras vuelven a la clave"),
    ("core/credentials.py", 'return _etq(_e) if _e else "—"',
     'return _e or "—"',
     "status_label devuelve el DATO crudo → «vencido» en pantalla"),
    ("core/inventory_ui.py", '_EST_LBL = {"disponible": ":green[available]"',
     '_EST_LBL = {"disponible": t(":green[available]")',
     "t() dentro de una constante de módulo → se congela al importar"),
    ("core/projects_ui.py", '_PER = {"Este mes": "This month"',
     '_PER = {"This month": "This month"',
     "se traduce la opción que se compara → rama MUERTA (v442)"),
    ("core/quotes_ui.py", 'return f"{_EST_ICONO.get(str(est), \'\')} {_etq(str(est))}".strip()',
     'return f"{_EST_ICONO.get(str(est), \'\')} {est}".strip()',
     "el chip de cotización vuelve a pintar el estado en crudo"),
    ("core/auth_ui.py", '_ico = {e: _etq(e) for e in ("vencido", "por_vencer", "vigente")}',
     '_ico = {"vencido": "vencido", "por_vencer": "por vencer", "vigente": "vigente"}',
     "vuelve el mapa espejo hecho a mano"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v450.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(RAIZ))
    return r.returncode


cazadas = 0
for rel, viejo, nuevo, desc in ROTURAS:
    ruta = RAIZ / rel
    orig = ruta.read_text(encoding="utf-8")
    if orig.count(viejo) != 1:
        print(f"  ?? ancla no única ({orig.count(viejo)}): {desc}")
        continue
    ruta.write_text(orig.replace(viejo, nuevo), encoding="utf-8", newline="")
    try:
        rc = corre()
    finally:
        ruta.write_text(orig, encoding="utf-8", newline="")   # ⚠️ SIEMPRE se restaura
    print(("  CAZADA  " if rc != 0 else "  ESCAPA  ") + desc)
    cazadas += (rc != 0)

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
print("verificando que el código quedó restaurado…")
sys.exit(0 if cazadas == len(ROTURAS) and corre() == 0 else 1)
