# -*- coding: utf-8 -*-
"""Lo que la interfaz PINTA y seguía en español (v450).

⚠️ Reglas que decidieron cada entrada:
  · constante de MÓDULO → texto BASE sin `t()` (un `t()` ahí se evalúa al importar y
    queda congelado; pasó cinco veces, v445-v449);
  · dentro de una función → `t()`;
  · lo que sale de la empresa (correo, PDF) → `d()`, idioma base siempre (v436);
  · si el valor se COMPARA, no se toca: se traduce el display con `format_func`.
"""
import ast
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = {
    "_core/projects_ui.py": [        # ya aplicado (prefijo _ = saltar)
        ('"Enviando alarma..."', 't("Sending alert…")', 1),
        ('"Preparando…"', 't("Preparing…")', 1),
        # _TIPO_LABEL: constante de módulo → texto base, sin t()
        ('"calculo": "Cálculos", "otro": "Otros"}', '"calculo": "Calculations", "otro": "Others"}', 1),
        ("f'{label}: {_MI('warning','#e0a021')} falta</span>')",
         "f'{label}: {_MI('warning','#e0a021')} {t(\"missing\")}</span>')", 1),
        ('"➕ Otro (escribir uno nuevo)"', 't("➕ Other (type a new one)")', 2),
        ('or "(vacío)"', 'or t("(empty)")', 2),
        ('" _(arrastrada)_"', 't(" _(carried over)_")', 1),
        # ⚠️ Centinela que se COMPARA (`ag_sel == "(ninguna)"`): se renombran los DOS
        # lados. Envolverlo en `t()` habría dejado la rama muerta (v442).
        ('"(ninguna)"', '"(none)"', 2),
        ('st.toast("Cambios guardados." + (f"  :material/send: {_sent} notificado(s)."',
         'st.toast(t("Changes saved.") + (f"  :material/send: {_sent} {t(\'notified\')}."', 1),
        ('»** — proyectada para "', '»** — expected "', 1),
        ('flash.exito(f"Agrupación creada ({res})"', 'flash.exito(f"{t(\'Grouping created\')} ({res})"', 1),
        ('f":material/calendar_month: **Hoy:** {_ets}{_n}"',
         'f"{t(\':material/calendar_month: **Today:**\')} {_ets}{_n}"', 1),
        ('":material/check_circle: **Todo facturado** ("',
         't(":material/check_circle: **Everything invoiced**") + " ("', 1),
        ('pie="oficina, almacén"', 'pie=t("office, warehouse")', 1),
        ('"— ninguna —"', 't("— none —")', 1),
        ('"Guardando..."', 't("Saving…")', 1),
        # ⚠️ «Ingreso estimado» y «Facturado» NO entran aquí: son CLAVES de columna que
        # el `disabled=[…]` lee por nombre. Van en `tabla.CABECERAS`, que traduce la
        # etiqueta sin tocar la clave.
        ('("venc", ":material/warning:", "Vencido"', '("venc", ":material/warning:", t("Overdue")', 1),
        ('"Esta localización"', 't("This location")', 1),
        ('":material/lock: cerrada"', 't(":material/lock: closed")', 2),
        ('{"": "Abierta",', '{"": t("Open"),', 1),
        ('P.INTERNO_CERRADA: "Cerrada",', 'P.INTERNO_CERRADA: t("Closed"),', 1),
        ('P.ARCHIVADO: "Archivada"}', 'P.ARCHIVADO: t("Archived")}', 1),
        ('":material/compare_arrows: Conciliación"', 't(":material/compare_arrows: Reconciliation")', 1),
        ('":material/pie_chart: Composición"', 't(":material/pie_chart: Breakdown")', 1),
    ],
    "_core/home_ui.py": [
        ('":red[:material/cancel:] vencida"', 't(":red[:material/cancel:] expired")', 1),
        ('f":red[mantenimiento vencido hace {e[\'dias\']} d]"',
         'f":red[{t(\'maintenance overdue by\')} {e[\'dias\']} d]"', 1),
        ('f":red[no devuelto hace {e[\'dias\']} d]"',
         'f":red[{t(\'not returned for\')} {e[\'dias\']} d]"', 1),
    ],
    "_core/auth_ui.py": [
        ('_fecha_input(c3, "Emisión"', '_fecha_input(c3, t("Issued")', 1),
        ('"— ningún grupo —"', 't("— no company —")', 1),
        ('"— ningún manual —"', 't("— no manual —")', 1),
        ('"Extrayendo texto e indexando…"', 't("Extracting text and indexing…")', 1),
        # ⚠️ mismo fallo que `_cumplimiento_equipo`: un mapa propio que traducía
        # «vigente»→«vigente». `etiqueta()` ya sabe hacerlo (v442).
        ('_ico = {"vencido": "vencido", "por_vencer": "por vencer", "vigente": "vigente"}',
         '_ico = {e: _etq(e) for e in ("vencido", "por_vencer", "vigente")}', 1),
    ],
    "_core/inventory_ui.py": [
        ('":orange[mantenimiento]"', 't(":orange[maintenance]")', 1),
        ('":red[dañado]"', 't(":red[damaged]")', 1),
        ('f":red[:material/build: Mantenimiento VENCIDO: {_pm}]"',
         'f":red[:material/build: {t(\'Maintenance OVERDUE\')}: {_pm}]"', 1),
        ('"Devolución esperada"', 't("Expected return")', 1),
        ('"Próximo mantenimiento"', 't("Next maintenance")', 3),
    ],
    "core/invoices_ui.py": [
        ('"Esta factura"', 't("This invoice")', 1),
        ('v + " · archivada"', 'v + " " + t("· archived")', 1),
        ('"(ninguno)"', '"(none)"', 2),          # centinela local, no se guarda
    ],
    "core/catalogo_ui.py": [
        ('"Este artículo"', 't("This item")', 1),
    ],
    "core/clientes_ui.py": [
        ('"sí"', 't("yes")', 1),
    ],
    "core/ausencias_ui.py": [
        ('"CANCELADA — "', '(t("CANCELLED —") + " ")', 1),
    ],
    "core/prestart_ui.py": [
        ('"·  todo OK"', 't("·  all OK")', 1),
    ],
    "core/tool_save_ui.py": [
        ('"Guardando..."', 't("Saving…")', 1),
    ],
    "core/plumb_ui.py": [
        ('"replanteo_plomadas.pdf"', '"plumb_setout.pdf"', 1),
    ],
    "core/tenant.py": [
        ('etiqueta: str = "Esto"', 'etiqueta: str = "This item"', 1),
    ],
    "core/manuals.py": [
        ('"· pág"', '"· p."', 1),
    ],
    "core/interpretation.py": [
        ('"Ninguno"', 'd("None")', 1),
    ],
    "core/expenses.py": [
        ('>GASTO ACUMULADO<', '>CUMULATIVE SPEND<', 1),
    ],
    "app.py": [
        ('"Consultando…"', 't("Searching…")', 1),
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
                raise SystemExit(f"{rel}: {viejo!r} aparece {n}, esperaba {veces}")
            src = src.replace(viejo, nuevo)
            tot += veces
        ast.parse(src)
        io.open(ruta, "w", encoding="utf-8", newline="").write(src)
        print(f"  {rel:26} {sum(c[2] for c in cambios)}")
    print(f"\n{tot} textos de interfaz traducidos")


if __name__ == "__main__":
    main()
