# -*- coding: utf-8 -*-
"""Tercer y último lote de v450.

⚠️ Incluye el TERCER mapa que traducía «vigente»→«vigente»: `credentials.status_label`.
Van tres en el mismo día (`_cumplimiento_equipo`, `auth_ui._ico` y este), los tres con
la misma forma — un diccionario propio hecho antes de que existiera `i18n.VALORES`,
que ya sabe traducir esos valores. Cuando el mismo fallo sale tres veces, el arreglo
es borrar la copia, no traducirla.
"""
import ast
import io
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = {
    "_core/tenant.py": [
        ('etiqueta: str = "Esto"', 'etiqueta: str = "This item"', 1),
    ],
    "_core/orders.py": [
        ('f"Orden {oid} registrada."', 'f"{t(\'Order\')} {oid} {t(\'recorded.\')}"', 1),
    ],
    "_core/plan_data.py": [
        ('f"{n}/{tot} parámetros"', 'f"{n}/{tot} {t(\'parameters\')}"', 1),
        ('("rail", "riel")', '("rail", t("rail"))', 1),
    ],
    "_core/projects_ui.py": [
        ('f" (hasta {_fin})"', 'f" ({t(\'until\')} {_fin})"', 1),
        ('{_horas:.1f} h</b> trabajadas</span>', '{_horas:.1f} h</b> {t("worked")}</span>', 1),
    ],
    "_core/auth_ui.py": [
        ('**{_nvc}** cred. vencida(s)', '**{_nvc}** {t("expired credential(s)")}', 1),
        # las tres celdas «sí» de las tablas de usuarios
        ('else ("sí" if (str(u.get("Email", "")).strip()', 'else (t("yes") if (str(u.get("Email", "")).strip()', 1),
        ('"Activo": "sí" if _activo(u) else "no",', '"Activo": t("yes") if _activo(u) else t("no"),', 1),
        ('"Contacto": "sí" if _cont_ok(u) else "falta",',
         '"Contacto": t("yes") if _cont_ok(u) else t("missing"),', 1),
    ],
    "_core/credentials.py": [
        # ⚠️ Tercer mapa propio del día que traducía «vigente»→«vigente».
        ('    return {"vigente": "vigente", "por_vencer": "por vencer",',
         '    return {"vigente": _etq("vigente"), "por_vencer": _etq("por_vencer"),', 1),
    ],
    "core/roster_ui.py": [
        ('("asignación" if len(items) == 1 else "asignaciones")',
         '(t("assignment") if len(items) == 1 else t("assignments"))', 1),
        ('("cumpl", ":material/fact_check: Cumplimiento")',
         '("cumpl", t(":material/fact_check: Compliance"))', 1),
    ],
    "core/survey_ui.py": [
        ('_FASE_RES: ":material/insights: Resultados e informes"',
         '_FASE_RES: t(":material/insights: Results and reports")', 1),
        ('f"{\':material/star: \' if is_best else \'\'}Solución {idx_sol+1} — RL = ',
         'f"{\':material/star: \' if is_best else \'\'}{t(\'Solution\')} {idx_sol+1} — RL = ', 1),
        ('"diagramas_posicionamiento.pdf"', '"positioning_diagrams.pdf"', 1),
    ],
    "core/quotes_ui.py": [
        ('" cotizados.")', '" " + t("quoted."))', 1),
        ('"Esta cotización"', 't("This quote")', 1),
        ('f"## :material/request_quote: Cotización Nº {c.get(\'Numero\', \'\')}"',
         'f"## :material/request_quote: {t(\'Quote No.\')} {c.get(\'Numero\', \'\')}"', 1),
        ('f"  ·  válida hasta {c.get(\'Validez\', \'\') or \'—\'}"',
         'f"  ·  {t(\'valid until\')} {c.get(\'Validez\', \'\') or \'—\'}"', 1),
        ('"### :material/compare_arrows: Cotizado vs. real — "',
         't("### :material/compare_arrows: Quoted vs. actual —") + " "', 1),
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
                raise SystemExit(f"{rel}: {viejo[:70]!r} aparece {n}, esperaba {veces}")
            src = src.replace(viejo, nuevo)
            tot += veces
        ast.parse(src)
        ruta.write_text(src, encoding="utf-8", newline="")
        print(f"  {rel:26} {sum(c[2] for c in cambios)}")
    print(f"\n{tot} textos traducidos")


if __name__ == "__main__":
    main()
