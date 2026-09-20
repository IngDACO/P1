"""Actualiza los guardianes CADUCADOS por la traducción de F3 (regla v385).

⚠️ Caducado ≠ regresión. En los ONCE se miró el código acusado ANTES de tocar nada: las
conductas siguen intactas y lo único que cambió es el IDIOMA, a propósito. La afirmación
se reescribe aceptando el inglés (o anclándola a la parte estable), con la razón al lado.
Relajar un guardián porque molesta es taparse los ojos; esto es lo contrario: se conserva
lo que la regla protege y se le quita la dependencia del idioma, que nunca fue la regla.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
_CAD = "# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.\n"

R = {
 "verif_v311.py": [
  ('_withs.append(("alerts" in _txt, "Actividades" in _txt))',
   '# ⚠️ CADUCADO por v440 (i18n F3): la etiqueta pasó al inglés. Lo que la regla\n'
   '        # protege es que EXISTA una columna con las actividades enfrentada a las\n'
   '        # alarmas (v311), no cómo se llama.\n'
   '        _withs.append(("alerts" in _txt,\n'
   '                       "Actividades" in _txt or "Activities" in _txt))'),
 ],
 "verif_v313.py": [
  ('check("P&L: «Costos (lo que pagas)»", "Costos (lo que pagas)" in _src)',
   _CAD + 'check("P&L: «Costos (lo que pagas)»",\n'
   '      "Costos (lo que pagas)" in _src or "Costs (what you pay)" in _src)'),
  ('check("Gastos: «Costo cargado a obras»", "Costo cargado a obras" in _src)',
   'check("Gastos: «Costo cargado a obras»",\n'
   '      "Costo cargado a obras" in _src or "Cost charged to jobs" in _src)'),
  ('check("Rentabilidad: «Costo cargado»", \'"Costo cargado"\' in _src)',
   'check("Rentabilidad: «Costo cargado»",\n'
   '      \'"Costo cargado"\' in _src or \'"Cost charged"\' in _src)'),
 ],
 "verif_v321.py": [
  ('check("hay expander de «sin movimiento»", "sin movimiento" in _src)',
   _CAD + 'check("hay expander de «sin movimiento»",\n'
   '      "sin movimiento" in _src or "with no movement" in _src)'),
 ],
 "verif_v390.py": [
  ('check("el multiselect de días usa los visibles", \'"Aplicar a estos días", dias\' in _ttxt)',
   _CAD + '# Lo que protege es que el multiselect reciba `dias` (los VISIBLES), no R.DIAS.\n'
   'check("el multiselect de días usa los visibles",\n'
   '      \'"Aplicar a estos días", dias\' in _ttxt\n'
   '      or \'t("Apply to these days"), dias\' in _ttxt)'),
 ],
 "verif_v397.py": [
  ('check("...y sin pendiente sigue habiendo «Abrir»", \'elif st.button("Abrir →"\' in _t)',
   _CAD + 'check("...y sin pendiente sigue habiendo «Abrir»",\n'
   '      \'elif st.button("Abrir →"\' in _t or \'elif st.button(t("Open →")\' in _t)'),
 ],
 "verif_v420.py": [
  ('chk("se busca la ficha ya existente para reutilizarla",',
   _CAD + 'chk("se busca la ficha ya existente para reutilizarla",'),
 ],
 "verif_v423.py": [
  ('chk("«Costará al terminar» cuelga de si es interna",\n'
   '    _bajo_if_interno(_re, "Costará al terminar"))',
   _CAD + 'chk("«Costará al terminar» cuelga de si es interna",\n'
   '    _bajo_if_interno(_re, "Costará al terminar")\n'
   '    or _bajo_if_interno(_re, "Cost at completion"))'),
 ],
 "verif_v430.py": [
  ('chk("...y ve a quién le falta", "Sin fecha de alta" in _au)',
   _CAD + 'chk("...y ve a quién le falta",\n'
   '    "Sin fecha de alta" in _au or "With no start date" in _au)'),
 ],
}

fallos = []
for rel, reps in R.items():
    s = (AQUI / rel).read_text(encoding="utf-8")
    for o, n in reps:
        if s.count(n) >= 1 and s.count(o) == 0:
            continue
        if s.count(o) < 1:
            fallos.append(f"{rel}: {o.splitlines()[0][:76]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", f)
    sys.exit(1)

for rel, reps in R.items():
    p = AQUI / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o):
            s = s.replace(o, nv, 1)
            n += 1
    compile(s, rel, "exec")
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:18} {n} actualizados")
print("OK")
