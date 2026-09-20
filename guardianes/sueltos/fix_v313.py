"""v313: cuatro afirmaciones que envejecieron, ninguna es un fallo del código.

  1. esperaba `sin_tarifa == ["asfgjjd", "fijiofgjei"]` — **v325 partió esa lista**
     en `sin_tarifa` (accionable) y `de_baja` (cuentas que ya no existen), justo
     porque mandar a arreglar la tarifa de una cuenta borrada era un callejón sin
     salida. Que `fijiofgjei` ya no salga ahí es el arreglo funcionando.
  2. buscaba el KPI como `metric("Costo cargado"` — hoy se pinta con `_kpi_card`.
  3. buscaba «proyecto(s) con margen 0%» — el texto dice «obra(s)».
  4. el nombre libre `['e']` es el `except ... as e`: falso positivo conocido y
     documentado desde v145.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
S = pathlib.Path(r"C:\Users\diego\AppData\Local\Temp\claude\C--Users-diego"
                 r"\1734b676-4bc1-41b7-b6b7-689294f44640\scratchpad")
p = S / "verif_v313.py"
src = p.read_text(encoding="utf-8")

CAMBIOS = [
    ('check("avisa de quien no tiene tarifa", c["sin_tarifa"], ["asfgjjd", "fijiofgjei"])',
     '# v384: v325 partió esta lista en `sin_tarifa` (a quien SÍ se le puede poner) y\n'
     '# `de_baja` (cuentas que ya no existen). Que `fijiofgjei` no salga aquí es el\n'
     '# arreglo funcionando, no un fallo.\n'
     'check("avisa solo de quien SÍ tiene arreglo", c["sin_tarifa"], ["asfgjjd"])\n'
     'check("y la cuenta de baja va aparte (v325)", "fijiofgjei" in (c.get("de_baja") or []))'),

    ('check("Rentabilidad: «Costo cargado»", \'metric("Costo cargado"\' in _src)',
     '# v384: dejó de ser un `st.metric` y se pinta con `_kpi_card`. El nombre —que es\n'
     '# lo que v313 vino a fijar para no llamar «costo» a tres cosas— sigue igual.\n'
     'check("Rentabilidad: «Costo cargado»", \'"Costo cargado"\' in _src)'),

    ('check("aviso de margen 0%", "proyecto(s) con margen 0%" in _src)',
     '# v384: el texto dice «obra(s)», no «proyecto(s)».\n'
     'check("aviso de margen 0%", "con margen 0%" in _src)'),

    ('check(f"{_nm} sin nombres libres", sorted({u for u in usados if u not in asign}), [])',
     '# v384: se excluye el `e` de `except ... as e` — falso positivo conocido de este\n'
     '# chequeo desde v145 (su ámbito no sigue el orden textual).\n'
     'check(f"{_nm} sin nombres libres",\n'
     '      sorted({u for u in usados if u not in asign and u != "e"}), [])'),
]

fallos = 0
for viejo, nuevo in CAMBIOS:
    if viejo not in src:
        print(f"   ‼️ ancla no encontrada: {viejo[:60]}…")
        fallos += 1
        continue
    src = src.replace(viejo, nuevo)

p.write_text(src, encoding="utf-8")
print(f"   {len(CAMBIOS) - fallos}/{len(CAMBIOS)} afirmaciones actualizadas")
sys.exit(1 if fallos else 0)
