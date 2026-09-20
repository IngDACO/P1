"""Segunda tanda de guardianes CADUCADOS por F3 (regla v385).

Mismo criterio: se miró el código acusado y las conductas están intactas; solo cambió el
idioma. Se acepta el inglés y se deja escrita la razón.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
_C = "# ⚠️ CADUCADO por v440 (i18n F3): el texto pasó al inglés a propósito.\n"

R = {
 "verif_v397.py": [
  ('    and "Facturar" in n.value and "material/receipt_long" in n.value)',
   '    and ("Facturar" in n.value or "Invoice" in n.value)\n'
   '    and "material/receipt_long" in n.value)'),
 ],
 "verif_v419.py": [
  ('            and "bicaci" in str(n.args[0].value)):',
   '            # ⚠️ CADUCADO por v440: la etiqueta es «Location». Lo que la regla\n'
   '            # protege es que NINGÚN campo de ubicación sea editable a mano.\n'
   '            and ("bicaci" in str(n.args[0].value)\n'
   '                 or "Location" in str(n.args[0].value))):'),
 ],
 "verif_v420.py": [
  ('    any("Ya existía" in c or "ya existía" in c.lower() for c in cad))',
   '    any("Ya existía" in c or "ya existía" in c.lower()\n'
   '        or "already existed" in c.lower() for c in cad))'),
 ],
 "verif_v423.py": [
  ('chk("«Presupuesto» también", _bajo_if_interno(_re, "Presupuesto"))',
   _C + 'chk("«Presupuesto» también",\n'
   '    _bajo_if_interno(_re, "Presupuesto") or _bajo_if_interno(_re, "Budget"))'),
  ('chk("y el titular tiene su propia rama para estructura",\n'
   '    _bajo_if_interno(_re, "estructura"))',
   'chk("y el titular tiene su propia rama para estructura",\n'
   '    _bajo_if_interno(_re, "estructura") or _bajo_if_interno(_re, "overhead"))'),
 ],
 "verif_v425.py": [
  ('chk("«Gasto de estructura» solo si hay estructura",\n'
   '    _condicionado(_rge, "Gasto de estructura"))',
   _C + 'chk("«Gasto de estructura» solo si hay estructura",\n'
   '    _condicionado(_rge, "Gasto de estructura")\n'
   '    or _condicionado(_rge, "Overhead spend"))'),
  ('chk("«En estructura» (horas) solo si hay estructura",\n'
   '    _condicionado(_rgh, "En estructura"))',
   'chk("«En estructura» (horas) solo si hay estructura",\n'
   '    _condicionado(_rgh, "En estructura") or _condicionado(_rgh, "On overhead"))'),
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
