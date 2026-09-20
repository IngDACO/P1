# -*- coding: utf-8 -*-
"""QUINTA red: etiquetas de UNA palabra dentro de tuplas y dicts de display.

⚠️ Estas van A MANO, una a una, porque la misma cadena es DATO en otro sitio:
`"Credenciales"` y `"Alarmas"` son también nombres de hoja, y `"Proyectos"` /
`"Usuarios"` / `"Gastos"` conviven con los IDs de sub-pestaña `"📊 Proyectos"` /
`"👷 Usuarios"` / `"💰 Gastos"`, que **no se pueden tocar** (los compara `sub ==` y
los usan los deep-links, v232/v303). Un reemplazo global las mezclaría.

En cada tupla del resumen del día se traducen los elementos 3 (etiqueta) y 8 (nombre
visible de la sección) y se dejan intactos el 6 (clave de sección) y el 7 (ID de
sub-pestaña).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    # ── projects_ui · resumen del día: etiqueta (3º) y nombre visible (8º) ──
    ("core/projects_ui.py",
     '(\"vencidos\", \":material/block:\", \"Vencidos\", True, len(d[\"vencidos\"]),',
     '(\"vencidos\", \":material/block:\", \"Overdue\", True, len(d[\"vencidos\"]),'),
    ("core/projects_ui.py",
     '(\"cred\", \":material/badge:\", \"Credenciales\", False, len(d.get(\"cred_venc\", [])),',
     '(\"cred\", \":material/badge:\", \"Credentials\", False, len(d.get(\"cred_venc\", [])),'),
    ("core/projects_ui.py",
     '(\"alarmas\", \":material/notifications:\", \"Alarmas\", True, _al_n,',
     '(\"alarmas\", \":material/notifications:\", \"Alarms\", True, _al_n,'),
    ("core/projects_ui.py",
     '(\"sobrep\", \":material/payments:\", \"Sobre presup.\", False, '
     'len(d.get(\"sobre_presupuesto\", [])),',
     '(\"sobrep\", \":material/payments:\", \"Over budget\", False, '
     'len(d.get(\"sobre_presupuesto\", [])),'),
    # el botón «→ Ir a X»
    ("core/projects_ui.py",
     'if st.button(f\"\u2192 Ir a {secn}\", key=f\"go_{slug}\", type=\"primary\"):',
     'if st.button(f\"\u2192 {t(\'Go to\')} {secn}\", key=f\"go_{slug}\", type=\"primary\"):'),
    # ── projects_ui · etiquetas de tipo de documento (VALORES del dict) ──
    ("core/projects_ui.py",
     '_TIPO_LABEL = {\"plano\": \"Plano\", \"informe_cliente\": \"Client report\",',
     '_TIPO_LABEL = {\"plano\": \"Drawing\", \"informe_cliente\": \"Client report\",'),
    ("core/projects_ui.py",
     '\"foto\": \"Fotos\", \"certificado\": \"Certificados\",',
     '\"foto\": \"Photos\", \"certificado\": \"Certificates\",'),
    # ── projects_ui · composición del costo ──
    ("core/projects_ui.py",
     '_comp = [(x, y) for x, y in ((\"N\u00f3minas\", d[\"costo_nomina\"]),',
     '_comp = [(x, y) for x, y in ((\"Payroll\", d[\"costo_nomina\"]),'),
    # ── home_ui · etiquetas de tipo de resultado del buscador (VALORES) ──
    ("core/home_ui.py",
     '_ETQ = {\"proyecto\": \"Proyectos\", \"persona\": \"Personas\", '
     '\"trabajo\": \"Trabajos\"}',
     '_ETQ = {\"proyecto\": \"Projects\", \"persona\": \"People\", '
     '\"trabajo\": \"Jobs\"}'),
    # ── ausencias_ui · etiquetas de estado (VALORES; las claves son el dato) ──
    ("core/ausencias_ui.py",
     'return {AU.PENDIENTE: \"\U0001f7e1 pendiente\", AU.APROBADA: \"\U0001f7e2 aprobada\",',
     'return {AU.PENDIENTE: \"\U0001f7e1 pending\", AU.APROBADA: \"\U0001f7e2 approved\",'),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    assert viejo in src, f"ANCLA NO CASA en {rel}: {viejo[:70]!r}"
    assert src.count(viejo) == 1, f"ANCLA AMBIGUA ({src.count(viejo)}) en {rel}"
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:60]}")
print(f"\n{len(CAMBIOS)} cambios aplicados")
