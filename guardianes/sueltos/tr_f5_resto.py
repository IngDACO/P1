"""Los trozos de f-string PARTIDOS entre líneas — a mano, con anclas de UNA línea.

⚠️ Anclas de una sola línea: las multilínea obligan a copiar la indentación de la
continuación al carácter, y en v440 20 de 27 no casaron al primer intento.
`ast.parse` antes de escribir; si el ancla no casa, no se escribe nada.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
 "core/payroll_ui.py": [
   ('f"- **{r[\'nombre\']}** el {r[\'fecha\']}: fichó {r[\'fichadas\']:g} h, "',
    'f"- **{r[\'nombre\']}** on {r[\'fecha\']}: clocked {r[\'fichadas\']:g} h, "'),
   ('f"así que su ausencia paga {r[\'pagadas\']:g} h (no la jornada entera)"',
    'f"so their absence pays {r[\'pagadas\']:g} h (not the whole working day)"'),
   ('+ ("\n\n…y otros más." if len(_rec) > 12 else ""))',
    '+ ("\n\n…and more." if len(_rec) > 12 else ""))'),
 ],
 "core/roster_ui.py": [
   ('f"con trabajo ese día ({\', \'.join(con[:3])})"',
    'f"with work that day ({\', \'.join(con[:3])})"'),
   ('if con else f"Quitar el {lbl.lower()} of this week")):',
    'if con else f"Remove {lbl.lower()} from this week")):'),
   ('f"asignado a {plan_lbl} · fichado en jornada pero "',
    'f"assigned to {plan_lbl} · clocked in for the workday but "'),
   ('f"SIN imputar obra{_ahora(usr)}"))',
    'f"with NO job charged{_ahora(usr)}"))'),
   ('_leyenda = [f":material/schedule: la hora solo aparece si difiere del turno "',
    '_leyenda = [f":material/schedule: the time only shows when it differs from the shift "'),
 ],
 "core/survey_ui.py": [
   ('f"mm** (altura del diente desde la espalda, del catálogo)."',
    'f"mm** (tooth height from the back, from the catalogue)."'),
   ('f"** detectado pero **no está en el catálogo de Rieles**. "',
    'f"** was detected but **it is not in the Rails catalogue**. "'),
   ('f"Ingresa RAIL a mano o agrégalo al catálogo.")',
    'f"Enter RAIL by hand or add it to the catalogue.")'),
   ('f":red[:material/block:] **No se puede generar el informe sin la "',
    'f":red[:material/block:] **The report cannot be generated without the "'),
   ('f"interpretación IA.**\n\nReason: "',
    'f"AI interpretation.**\n\nReason: "'),
   ('f":green[:material/check_circle:] NUMBER OF STOPS del plano → NS = **{_ns}**."',
    'f":green[:material/check_circle:] NUMBER OF STOPS from the drawing → NS = **{_ns}**."'),
 ],
}

fallos, hechos = [], 0
for rel, pares in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for viejo, nuevo in pares:
        if s.count(viejo) != 1:
            fallos.append(f"{rel}: ({s.count(viejo)}x) {viejo[:70]}")
            continue
        s = s.replace(viejo, nuevo, 1)
        n += 1
    try:
        ast.parse(s)
    except SyntaxError as e:
        fallos.append(f"{rel}: NO COMPILA {e}")
        continue
    p.write_text(s, encoding="utf-8")
    hechos += n
    print(f"  {rel:26} {n} a mano")

print(f"\n{hechos} hechas")
if fallos:
    print("⚠️ ANCLAS QUE NO CASAN (no prueban nada, hay que mirarlas):")
    for f in fallos:
        print("   ", f)
    sys.exit(1)
