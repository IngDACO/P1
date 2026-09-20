"""F4 · survey_ui — los trozos de f-string partidos entre líneas.

⚠️ Anclas de UNA LÍNEA (lección de projects_ui: las multilínea obligan a copiar la
indentación de la continuación al carácter y 20 de 27 no casaron). `ast.parse` antes de
escribir.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(r"C:\Users\diego\P1\survey_app\core\survey_ui.py")

R = [
    ('"Pulsa **:material/play_arrow: Calcular** para regenerar diagramas e informes.")',
     '"Press **:material/play_arrow: Calculate** to regenerate diagrams and reports.")'),
    ('f"**FB máx. hacia atrás:** {limits.get(\'FB_MAX_BACK\', 0):.2f} mm"',
     'f"**FB max. backwards:** {limits.get(\'FB_MAX_BACK\', 0):.2f} mm"'),
    ('f":green[:material/check_circle:] Found **{len(all_solutions)} solución(es) óptima(s)** con "',
     'f":green[:material/check_circle:] Found **{len(all_solutions)} optimal solution(s)** with "'),
    ('f"Omitidos por límite físico (RL/FB): {len(skip_phys)}  |  "',
     'f"Skipped for physical limit (RL/FB): {len(skip_phys)}  |  "'),
    ('f"Omitidos por pared: {len(skip_wall)}  |  "',
     'f"Skipped for the wall: {len(skip_wall)}  |  "'),
    ('f"Omitidos por apertura tapada: {len(skip_frame)}"',
     'f"Skipped for a blocked opening: {len(skip_frame)}"'),
    ('f"Rango: **{bs_result[\'range\']}**  |  Zone: **{bs_result[\'range_name\']}**"',
     'f"Range: **{bs_result[\'range\']}**  |  Zone: **{bs_result[\'range_name\']}**"'),
    ('f"frontal (fb) = **{best[\'fb_applied\']:.1f} mm**."',
     'f"front (fb) = **{best[\'fb_applied\']:.1f} mm**."'),
    ("** pero \"", "** but \""),
    ('f"(dif {_bs[\'dif\']:+.0f} mm). El encaje usa (BSR−BS)/2, así que con este "',
     'f"(diff {_bs[\'dif\']:+.0f} mm). The fit uses (BSR−BS)/2, so with this "'),
    ('f"desajuste los plomos quedan mal ubicados. Revisa BS, SF1, SF2, BKS o RAIL."',
     'f"mismatch the plumb points end up in the wrong place. Check BS, SF1, SF2, BKS or RAIL."'),
    ('"Los informes **requieren** la interpretación IA. Verifica que "',
     '"The reports **require** the AI interpretation. Check that "'),
    ('"`ANTHROPIC_API_KEY` esté configurada en los **Secrets de Streamlit Cloud**."',
     '"`ANTHROPIC_API_KEY` is configured in the **Streamlit Cloud Secrets**."'),
    ('f":green[:material/check_circle:] {_n_sv} valor(es) tomados del plano del proyecto. "',
     'f":green[:material/check_circle:] {_n_sv} value(s) taken from the project drawing. "'),
    ('"Revísalos y completa los medidos en obra.")',
     '"Check them and fill in the ones measured on site.")'),
    ('"— ajusta RAIL si el catálogo no lo tiene.")',
     '"— adjust RAIL if the catalogue does not have it.")'),
    ('f"Motivo: {interp_usr.get(\'_error\', interp.get(\'_error\', \'no disponible\'))}.\\n\\n"',
     'f"Reason: {interp_usr.get(\'_error\', interp.get(\'_error\', \'not available\'))}.\\n\\n"'),
    ('"Configura `ANTHROPIC_API_KEY` en los Secrets de Streamlit Cloud y vuelve a calcular."',
     '"Configure `ANTHROPIC_API_KEY` in the Streamlit Cloud Secrets and calculate again."'),
    ('f":material/warning: The project has **NS = {_ns_prj}** y este survey "',
     'f":material/warning: The project has **NS = {_ns_prj}** and this survey has "'),
    ('f"**NS = {_ns_sv}**. Revisa cuál es el correcto: el "',
     'f"**NS = {_ns_sv}**. Check which one is right: the "'),
    ('"cronograma del proyecto se calculó con el suyo.")',
     '"project schedule was worked out with its own.")'),
    ('f"Project **{_pc[\'id\']} · {_pc[\'nombre\']}** actualizado con "',
     'f"Project **{_pc[\'id\']} · {_pc[\'nombre\']}** updated with "'),
    ('"este survey.")', '"this survey.")'),
]

s = P.read_text(encoding="utf-8")
fallos = [o for o, n in R if s.count(o) != 1 and s.count(n) == 0]
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print(f"   ({s.count(f)}x) {f[:104]}")
    sys.exit(1)

n = 0
for o, nv in R:
    if s.count(o) == 1:
        s = s.replace(o, nv, 1)
        n += 1
ast.parse(s)
P.write_text(s, encoding="utf-8")
print(f"  survey_ui  {n} reemplazos a mano")
