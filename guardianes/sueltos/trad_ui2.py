# -*- coding: utf-8 -*-
"""Segundo lote de v450: lo que quedaba de interfaz, documentos y constantes.

⚠️ Las CONSTANTES DE MÓDULO van en texto BASE, sin `t()`: se evalúan al importar y un
`t()` ahí queda congelado (seis veces ya). Sus CLAVES son el dato y no se tocan.
"""
import ast
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = {
    "_core/ausencias_ui.py": [
        # ⚠️ Asunto de CORREO: sale de la empresa → idioma BASE, no el de la pantalla
        # de quien lo dispara (regla v436). Por eso literal y no `t()`.
        ('f"CANCELADA — {cfg.get(\'nombre\', r.get(\'Tipo\'))}',
         'f"CANCELLED — {cfg.get(\'nombre\', r.get(\'Tipo\'))}', 1),
    ],
    "_core/prestart_ui.py": [
        ('"  ·  todo OK"', 't("  ·  all OK")', 1),
    ],
    "_core/tool_save_ui.py": [
        ('st.spinner("Guardando...")', 'st.spinner(t("Saving…"))', 1),
    ],
    "_core/plumb_ui.py": [
        ('f"centrado · holgura {disp.get(\'holgura_lado\', 0):.0f} mm/lado"',
         'f"{t(\'centred · clearance\')} {disp.get(\'holgura_lado\', 0):.0f} mm/side"', 1),
        ('"replanteo_plomadas.pdf"', '"plumb_setout.pdf"', 1),
    ],
    "_core/manuals.py": [
        ('f" · pág {h[\'page\']}"', 'f" · p. {h[\'page\']}"', 1),
    ],
    "_core/interpretation.py": [
        ('cortes if cortes else "Ninguno"', 'cortes if cortes else d("None")', 1),
    ],
    "_core/expenses.py": [
        ("f'GASTO ACUMULADO</text>'", "f'CUMULATIVE SPEND</text>'", 1),
        ("f' · {n} movimientos</text>'", "f' · {n} entries</text>'", 1),
    ],
    "_core/catalogo_ui.py": [
        # constante de módulo → texto BASE
        ('_TIPO_LBL = {CAT.PRODUCTO: ":material/inventory_2: producto",\n'
         '             CAT.SERVICIO: ":material/engineering: servicio"}',
         '_TIPO_LBL = {CAT.PRODUCTO: ":material/inventory_2: product",\n'
         '             CAT.SERVICIO: ":material/engineering: service"}', 1),
    ],
    "core/roster.py": [
        # ⚠️ Las CLAVES ("lun", "mie"…) son el dato con que se indexa el JSON del
        # roster y NO se tocan; solo cambian los nombres visibles.
        ('DIAS_LABEL = {"lun": "Lun", "mar": "Mar", "mie": "Mié", "jue": "Jue", "vie": "Vie",\n'
         '              "sab": "Sáb", "dom": "Dom"}',
         'DIAS_LABEL = {"lun": "Mon", "mar": "Tue", "mie": "Wed", "jue": "Thu", "vie": "Fri",\n'
         '              "sab": "Sat", "dom": "Sun"}', 1),
        ('"FORMACION": {"nombre": "Formación",', '"FORMACION": {"nombre": "Training",', 1),
        # ⚠️ De la paleta solo se GUARDA el hex (`_colmap[n]` → hex), así que el nombre
        # es puro display y se puede traducir sin tocar ningún dato.
        ('("Magenta",  "#e84393"), ("Naranja", "#e67e22"), ("Amarillo", "#f1c40f"),',
         '("Magenta",  "#e84393"), ("Orange",  "#e67e22"), ("Yellow",   "#f1c40f"),', 1),
        ('("Verde",    "#27ae60"), ("Cian",    "#00b5cc"), ("Azul",     "#2e6da4"),',
         '("Green",    "#27ae60"), ("Cyan",    "#00b5cc"), ("Blue",     "#2e6da4"),', 1),
        ('("Rosa",     "#f5a6c3"), ("Lila",    "#9b59b6"), ("Teal",     "#16a085"),',
         '("Pink",     "#f5a6c3"), ("Lilac",   "#9b59b6"), ("Teal",     "#16a085"),', 1),
        ('("Durazno",  "#f6b189"), ("Oliva",   "#7f8c8d"), ("Índigo",   "#34495e"),',
         '("Peach",    "#f6b189"), ("Olive",   "#7f8c8d"), ("Indigo",   "#34495e"),', 1),
        ('f"{n} persona(s) copiada(s)."', 'f"{n} " + t("person(s) copied.")', 1),
    ],
    "app.py": [
        ('st.spinner("Consultando…")', 'st.spinner(t("Searching…"))', 1),
    ],
}


def main():
    tot = 0
    for rel, cambios in CAMBIOS.items():
        if rel.startswith("_"):
            continue
        ruta = RAIZ / rel
        src = ruta.read_text(encoding="utf-8")
        for viejo, nuevo, veces in cambios:
            n = src.count(viejo)
            if n != veces:
                raise SystemExit(f"{rel}: {viejo[:60]!r} aparece {n}, esperaba {veces}")
            src = src.replace(viejo, nuevo)
            tot += veces
        ast.parse(src)
        io.open(ruta, "w", encoding="utf-8", newline="").write(src)
        print(f"  {rel:26} {sum(c[2] for c in cambios)}")
    print(f"\n{tot} textos traducidos")


if __name__ == "__main__":
    main()
