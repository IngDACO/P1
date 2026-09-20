# -*- coding: utf-8 -*-
"""Cuarta red, tanda 3: los 18 de `projects_ui` (f-strings a medio traducir).

Anclajes de UNA línea (v440). Se afirma que cada uno existe y es ÚNICO antes de
sustituir: un parche que no comprueba que se aplicó, miente (v361).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
F = Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")

CAMBIOS = [
    ('st.caption(f"Showing **{len(vis)}** de {len(entries)} files.")',
     'st.caption(f"Showing **{len(vis)}** of {len(entries)} files.")'),
    ('f"{len(nuevos)} person(s) in {r[\'semanas\']} semana(s){_oc}.")',
     'f"{len(nuevos)} person(s) in {r[\'semanas\']} week(s){_oc}.")'),
    ('msgs.append(f":material/calendar_month: Planificador: {r[\'llenadas\']} day(s) assigned to "',
     'msgs.append(f":material/calendar_month: Planner: {r[\'llenadas\']} day(s) assigned to "'),
    ('f"del {a.get(\'Desde\')} al {a.get(\'Hasta\')}"',
     'f"from {a.get(\'Desde\')} to {a.get(\'Hasta\')}"'),
    ('st.warning(f":material/mail: Notified {n} de {len(usuarios)}. '
     'The rest have no contact details.")',
     'st.warning(f":material/mail: Notified {n} of {len(usuarios)}. '
     'The rest have no contact details.")'),
    ('_hc1.markdown(f"**Cartera \u2014 {len(_proys_f)} de {len(proys)}**"',
     '_hc1.markdown(f"**{t(\'Portfolio\')} \u2014 {len(_proys_f)} of {len(proys)}**"'),
    ('_dia_txt  = (f"d\u00eda {_hoy_real} de {_tot}" if _hoy_real <= _tot',
     '_dia_txt  = (f"day {_hoy_real} of {_tot}" if _hoy_real <= _tot'),
    ('else f"d\u00eda {_hoy_real} \u2014 {_hoy_real - _tot} more than the {_tot} planificados")',
     'else f"day {_hoy_real} \u2014 {_hoy_real - _tot} more than the {_tot} planned")'),
    ('f"(en {d[\'proximo\'][\'faltan\']:.0f} days).")',
     'f"(in {d[\'proximo\'][\'faltan\']:.0f} days).")'),
    ('f"**{_fecha}**" + (f", con **{_d:.0f} days behind**." if _d else',
     'f"**{_fecha}**" + (f", with **{_d:.0f} days behind**." if _d else'),
    ('+ (f" con {_n} elevador(es)." if _n else',
     '+ (f" with {_n} lift(s)." if _n else'),
    ('st.markdown(f"**Cartera \u2014 {len(proys)} proyecto(s)**"',
     'st.markdown(f"**{t(\'Portfolio\')} \u2014 {len(proys)} project(s)**"'),
    ('+ (f"  \u00b7  :green[:material/check_circle:] {len(aheads)} adelantado(s)" if aheads else ""))',
     '+ (f"  \u00b7  :green[:material/check_circle:] {len(aheads)} ahead" if aheads else ""))'),
    ('"El " + f"{rev[\'margen_pct\']:g}%" + " follows from that price.")',
     '"The " + f"{rev[\'margen_pct\']:g}%" + " follows from that price.")'),
    ('_l = (f"Llevas **{_T.dinero(cp[\'total\'], 0)}** de {_T.dinero(pres, 0)}"',
     '_l = (f"You have spent **{_T.dinero(cp[\'total\'], 0)}** of {_T.dinero(pres, 0)}"'),
    ('f" \u00b7 **{cp[\'pct\']}% consumido**")',
     'f" \u00b7 **{cp[\'pct\']}% used**")'),
    ('+ (f"  \u00b7  margen {_mrg:.0f}%" if _mrg is not None else ""))',
     '+ (f"  \u00b7  {t(\'margin\')} {_mrg:.0f}%" if _mrg is not None else ""))'),
    ('("sinmar", ":material/percent:", "No margin", f"{len(_sinmar)} obras", False,',
     '("sinmar", ":material/percent:", "No margin", f"{len(_sinmar)} jobs", False,'),
    ('st.caption(f"\u2026 y {len(regs) - 10} more.")',
     'st.caption(f"\u2026 and {len(regs) - 10} more.")'),
    ('pie=f"de {len(locs)}" if len(locs) != len(_abiertas) else "abiertas"),',
     'pie=f"of {len(locs)}" if len(locs) != len(_abiertas) else t("open")),'),
]

src = F.read_text(encoding="utf-8")
for viejo, nuevo in CAMBIOS:
    assert viejo in src, f"ANCLA NO CASA: {viejo[:72]!r}"
    assert src.count(viejo) == 1, f"ANCLA AMBIGUA ({src.count(viejo)}): {viejo[:60]!r}"
    src = src.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo[:64]}")
F.write_text(src, encoding="utf-8")
print(f"\n{len(CAMBIOS)} cambios aplicados")
