# -*- coding: utf-8 -*-
"""Cuarta red, tanda 1 (resto): f-strings a medio traducir en la interfaz.

⚠️ Este script va a FICHERO y no a un heredoc: por stdin, Python decodifica con la
codificación de la consola y un acento (`_líneas`) se convierte en U+FFFD, así que
el ancla no casa nunca. Es la trampa nº26 en su variante de encoding — la cuarta vez
que muerde esa familia.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

CAMBIOS = [
    ("core/payroll_ui.py",
     '_l\u00edneas = "\\n".join(f"- **{s[\'nombre\']}** ya tiene `{s[\'id\']}` del "',
     '_l\u00edneas = "\\n".join(f"- **{s[\'nombre\']}** already has `{s[\'id\']}` from "'),
    ("core/payroll_ui.py",
     'f"{s[\'desde\']} al {s[\'hasta\']}" for s in _sol)',
     'f"{s[\'desde\']} to {s[\'hasta\']}" for s in _sol)'),
    ("core/survey_ui.py",
     '+ (f" en: **{\', \'.join(_cols_off)}**." if _cols_off else "."))',
     '+ (f" in: **{\', \'.join(_cols_off)}**." if _cols_off else "."))'),
    ("core/survey_ui.py",
     'st.caption(f"Mostrando {len(_floors)} de {n_floors} pisos"',
     'st.caption(f"Showing {len(_floors)} of {n_floors} floors"'),
    ("core/tool_save_ui.py",
     'msg = f":green[:material/check_circle:] Guardado como **{res[\'id\']}** '
     'en {prj.get(\'Nombre\')}."',
     'msg = f":green[:material/check_circle:] Saved as **{res[\'id\']}** '
     'in {prj.get(\'Nombre\')}."'),
    ("core/auth_ui.py",
     '_linea = f":material/group: **{len(gente)}** personas \u00b7 '
     ':green[:material/check_circle:] **{_nact}** activos"',
     '_linea = f":material/group: **{len(gente)}** people \u00b7 '
     ':green[:material/check_circle:] **{_nact}** active"'),
    ("core/catalogo_ui.py",
     'f"  \u00b7  costo {T.dinero(CAT.costo_de(it, 1))}"',
     'f"  \u00b7  cost {T.dinero(CAT.costo_de(it, 1))}"'),
]

for rel, viejo, nuevo in CAMBIOS:
    f = R / rel
    src = f.read_text(encoding="utf-8")
    assert viejo in src, f"ANCLA NO CASA en {rel}: {viejo[:60]!r}"
    assert src.count(viejo) == 1, f"ANCLA AMBIGUA ({src.count(viejo)}) en {rel}"
    f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
    print(f"  OK  {rel}: {viejo[:52]}")
print(f"\n{len(CAMBIOS)} cambios aplicados")
