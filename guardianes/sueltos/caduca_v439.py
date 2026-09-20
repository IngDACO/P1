"""Actualiza los 4 guardianes CADUCADOS por la traducción de F2 (regla v385).

⚠️ Caducado ≠ regresión. Se miró el código acusado ANTES de tocar nada: las cuatro
conductas siguen intactas y lo único que cambió es el IDIOMA, que se cambió a propósito.
Se reescribe la AFIRMACIÓN sobre el principio, con la razón al lado — nunca se relaja
para que deje de molestar.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent

R = {
 "verif_v307.py": [
  ('        return "🟢 fichado aquí"', '        return "🟢 clocked in here"'),
  ('        return "🔴 fichó en " + ", ".join(_noms[:2])',
   '        return "🔴 clocked in at " + ", ".join(_noms[:2])'),
  ('    return "⚠️ sin fichar"', '    return "⚠️ not clocked in"'),
  ('      "🟢 fichado aquí")\ncheck("fichó en OTRA obra"',
   '      "🟢 clocked in here")\ncheck("fichó en OTRA obra"'),
  ('      "🔴 fichó en Otra")', '      "🔴 clocked in at Otra")'),
  ('check("no ficha nada", _estado("PRJ-1", []), "⚠️ sin fichar")',
   'check("no ficha nada", _estado("PRJ-1", []), "⚠️ not clocked in")'),
  ('      "🟢 fichado aquí")\n', '      "🟢 clocked in here")\n'),
  # ⚠️ CADUCADO por v439 (i18n F2): el texto pasó al inglés a propósito. Lo que la
  # regla protege es que la tabla marque los TRES estados y los distinga; el EMOJI es
  # la parte estable, así que se comprueba por ahí y no por la palabra.
  ('for _t in ("🟢 fichado aquí", "⚠️ sin fichar", "🔴 fichó en "):',
   'for _t in ("🟢", "⚠️", "🔴"):'),
  ('check("...y con Estado", \'"Estado": _estado\' in _src)',
   '# ⚠️ CADUCADO por v439: la CLAVE del dict es dato y no se traduce, pero la columna\n'
   '# que se muestra sí. Se comprueba que el estado real llega a la fila.\n'
   'check("...y con Estado", ("_estado" in _src) and ("Estado" in _src or "Status" in _src))'),
 ],
 "verif_v308.py": [
  ('check("y tarjeta de la semana", \'_tarjeta("Esta semana"\' in _src)',
   '# ⚠️ CADUCADO por v439 (i18n F2): la etiqueta pasó al inglés vía t(). Lo que la\n'
   '# regla protege es que la tarjeta de la SEMANA exista (resumen_semana, v308).\n'
   'check("y tarjeta de la semana",\n'
   '      \'_tarjeta(t("This week")\' in _src or \'_tarjeta("Esta semana"\' in _src)'),
 ],
 "verif_v408.py": [
  ('            and "fírmalo arriba" in n.value):',
   '            and ("fírmalo arriba" in n.value\n'
   '                 # ⚠️ CADUCADO por v439 (i18n F2): el aviso pasó al inglés.\n'
   '                 or "sign it above" in n.value)):'),
 ],
 "verif_v430.py": [
  ('chk("la pantalla dice de qué periodo habla", "año de vacaciones va del" in _rma2)\n'
   'chk("...y avisa cuando lo está estimando", "no consta" in _rma2)',
   '# ⚠️ CADUCADO por v439 (i18n F2): los dos textos pasaron al inglés a propósito. Lo\n'
   '# que la regla protege es que la pantalla DIGA de qué periodo habla y AVISE cuando\n'
   'chk("la pantalla dice de qué periodo habla",\n'
   '    "año de vacaciones va del" in _rma2 or "Your leave year runs from" in _rma2)\n'
   '# lo está estimando por falta de fecha de alta (un saldo estimado que parece exacto\n'
   '# es peor que ninguno, v325/v433).\n'
   'chk("...y avisa cuando lo está estimando",\n'
   '    "no consta" in _rma2 or "is not on record" in _rma2)'),
 ],
}

fallos = []
for rel, reps in R.items():
    s = (AQUI / rel).read_text(encoding="utf-8")
    for o, nv in reps:
        if s.count(nv) >= 1 and s.count(o) == 0:
            continue
        if s.count(o) < 1:
            fallos.append(f"{rel}: {o[:70]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in R.items():
    p = AQUI / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o):
            s = s.replace(o, nv, 1)
            n += 1
    compile(s, rel, "exec")                    # no se escribe un guardián roto
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:18} {n} actualizaciones")
print("OK")
