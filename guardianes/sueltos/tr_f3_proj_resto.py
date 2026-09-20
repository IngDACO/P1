"""F3 · projects_ui — los 35 trozos de f-string partidos entre líneas.

La herramienta los deja a mano a propósito (ver la cabecera de `aplicar.py`).

⚠️ Anclas de UNA LÍNEA: las multilínea fallan por la indentación de la continuación,
que hay que copiar al carácter y es donde se pierde el tiempo (20 de 27 no casaron al
primer intento). Cada fragmento del fuente vive en una sola línea, así que se cambia por
sí solo y la frase queda armada igual.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(r"C:\Users\diego\P1\survey_app\core\projects_ui.py")

R = [
    ('f"See {min(por_pagina, len(fotos) - n_ver)} más "',
     'f"See {min(por_pagina, len(fotos) - n_ver)} more "'),
    ('":material/event_available: Fin estimado: "',
     '":material/event_available: Estimated finish: "'),
    ('f"El proyecto se creó, pero no se guardaron los datos "',
     'f"The project was created, but the drawing data was "'),
    ('f"del plano: {e}")', 'f"not saved: {e}")'),
    ('f"Nueva factura con esta obra y su cliente ya "',
     'f"New invoice with this job and its client already "'),
    ('f"elegidos · pendiente {theme.dinero(_pf, 0)}"',
     'f"chosen · outstanding {theme.dinero(_pf, 0)}"'),
    ('f":material/receipt: **{_Tl.dinero(_tot, 0)}** sin facturar "',
     'f":material/receipt: **{_Tl.dinero(_tot, 0)}** not invoiced "'),
    ('f"Nueva factura con esta obra y su cliente ya elegidos · "',
     'f"New invoice with this job and its client already chosen · "'),
    ('f"pendiente {_Tb.dinero(_spf, 0)}"', 'f"outstanding {_Tb.dinero(_spf, 0)}"'),
    ('f":material/schedule: La fecha de fin planificada ya pasó y queda "',
     'f":material/schedule: The planned finish date has already passed and there is "'),
    ('f":material/schedule: **Sin avance todavía**: necesitas "',
     'f":material/schedule: **No progress yet**: you need "'),
    ('f"**{d[\'ritmo_nec\']:.1f} %/day** over the {d[\'dias_rest\']:.0f} días "',
     'f"**{d[\'ritmo_nec\']:.1f} %/day** over the {d[\'dias_rest\']:.0f} days "'),
    ('f"que quedan para llegar a la fecha.")', 'f"left to make the date.")'),
    ('f":material/schedule: You are running at **{d[\'ritmo_real\']:.1f} %/día** y necesitas "',
     'f":material/schedule: You are running at **{d[\'ritmo_real\']:.1f} %/day** and you need "'),
    ('f"**{d[\'ritmo_nec\']:.1f} %/día** para llegar a la fecha: "',
     'f"**{d[\'ritmo_nec\']:.1f} %/day** to make the date: "'),
    ('f"hay que **acelerar ×{d[\'factor\']:.1f}** over the "',
     'f"you have to **speed up ×{d[\'factor\']:.1f}** over the "'),
    ('f":material/schedule: You are running at **{d[\'ritmo_real\']:.1f} %/día** y con "',
     'f":material/schedule: You are running at **{d[\'ritmo_real\']:.1f} %/day** and at "'),
    ('f":material/schedule: You are running at **{d[\'ritmo_real\']:.1f} %/día**, justo el ritmo "',
     'f":material/schedule: You are running at **{d[\'ritmo_real\']:.1f} %/day**, exactly the "'),
    ('f"que hace falta ({d[\'ritmo_nec\']:.1f} %/day).")',
     'f"rate needed ({d[\'ritmo_nec\']:.1f} %/day).")'),
    ('f":red[:material/cancel:] **{x[\'nombre\']}** — sin empezar, "',
     'f":red[:material/cancel:] **{x[\'nombre\']}** — not started, "'),
    ('f"tocaba el {x[\'desde\'].strftime(\'%d/%m\')} ({x[\'dur\']:.0f} d)")',
     'f"it was due on {x[\'desde\'].strftime(\'%d/%m\')} ({x[\'dur\']:.0f} d)")'),
    ('":material/wrong_location: **Esta obra no está en el mapa.** Tiene "',
     '":material/wrong_location: **This job is not on the map.** It has an "'),
    ('f"dirección (*{prj.get(\'Ubicacion\')}*) pero no un punto, así que no "',
     'f"address (*{prj.get(\'Ubicacion\')}*) but no point, so it does not "'),
    ('"aparece en el mapa de Home ni en la Ruta del día. Ábrelo abajo y "',
     '"appear on the Home map or in the Day route. Open it below and "'),
    ('"pulsa **Buscar** para ubicarla.")', '"press **Search** to place it.")'),
    ('f"(lo fija el propietario en Grupos).")', 'f"(the owner sets it in Companies).")'),
    ('f"{len(_sel)} proyectos: cada cambio es una escritura "',
     'f"{len(_sel)} projects: each change is a write "'),
    ('"en la hoja; puede tardar unos segundos.")',
     '"to the sheet; it may take a few seconds.")'),
    ('":material/shopping_cart: Vas dentro de presupuesto, pero con las "',
     '":material/shopping_cart: You are within budget, but with the "'),
    ('f"**{_T.dinero(cp[\'comprometido\'], 0)} ya pedidos** el proyecto llega "',
     'f"**{_T.dinero(cp[\'comprometido\'], 0)} already ordered** the project reaches "'),
    ('f"a **{_T.dinero(cp[\'total_comp\'], 0)}**, "',
     'f"**{_T.dinero(cp[\'total_comp\'], 0)}**, "'),
    ('f":material/warning: **{T.dinero(abs(cc[\'sin_explicar\']))} sin explicar** "',
     'f":material/warning: **{T.dinero(abs(cc[\'sin_explicar\']))} unexplained** "'),
    ('"entre lo que deberías pagar y lo puesto en nóminas: trabajo aún sin "',
     '"between what you should be paying and what is in the payslips: work "'),
    ('"nómina, o nóminas editadas a mano.")',
     '"not yet paid, or payslips edited by hand.")'),
    ('f":material/info: Con un periodo acotado la cadena **no cierra por "',
     'f":material/info: With a narrow period the chain **cannot balance by "'),
    ('f"construcción**: las horas cuentan por el día trabajado y las nóminas "',
     'f"construction**: hours count by the day worked and payslips by the "'),
    ('f"por el periodo que cierran, así que caen en meses distintos. "',
     'f"period they close, so they fall in different months. "'),
    ('f"Los {T.dinero(abs(cc[\'sin_explicar\']))} de diferencia no son un "',
     'f"The {T.dinero(abs(cc[\'sin_explicar\']))} of difference is not a "'),
    ('f"descuadre — para conciliar de verdad, mira el periodo **Todo**.")',
     'f"discrepancy — to reconcile properly, look at the **All** period.")'),
    ('f":material/visibility_off: {len(_sin)} obra(s) sin movimiento "',
     'f":material/visibility_off: {len(_sin)} job(s) with no movement "'),
    ('"(sin costo ni facturación)"', '"(no cost and no invoicing)"'),
    ('f":material/business: **{T.dinero(tot_int, 0)}** de estructura "',
     'f":material/business: **{T.dinero(tot_int, 0)}** of overhead "'),
    ('"de compras) en "', '"of purchases) across "'),
    ('f"{len(_int_filas)} localización(es). **No se le carga a ninguna obra "',
     'f"{len(_int_filas)} location(s). **It is not charged to any job "'),
    ('"ni entra en el % consumido**, pero sí es costo del grupo y cuenta "',
     '"and does not count towards % used**, but it is a company cost and "'),
    ('"en el P&L.")', '"does count in the P&L.")'),
    ('f":material/help: **{T.dinero(_huer[\'total\'], 0)} en {_huer[\'n\']} compra(s) "',
     'f":material/help: **{T.dinero(_huer[\'total\'], 0)} across {_huer[\'n\']} purchase(s) "'),
    ('"sin proyecto** (o de un proyecto borrado). Cuentan en el costo del grupo, "',
     '"with no project** (or from a deleted project). They count towards the company "'),
    ('"pero no en el presupuesto de ninguna obra — asígnalas desde el recibo.")',
     '"cost, but not towards any job budget — assign them from the receipt.")'),
    ('f"{len(sin_pres)} proyecto(s) sin presupuesto: no hay contra qué comparar "',
     'f"{len(sin_pres)} project(s) with no budget: there is nothing to compare "'),
    ('"su gasto. Se define en el detalle del proyecto → :material/edit: Datos.")',
     '"their spend against. It is set in the project detail → :material/edit: Data.")'),
    ('f":material/error: **{tot_proy - tot_jorn:+.1f} h**: hay quien imputó a "',
     'f":material/error: **{tot_proy - tot_jorn:+.1f} h**: some people charged "'),
    ('f"obras MÁS horas que las de su jornada ({_n}). Fichó al proyecto sin "',
     'f"MORE hours to jobs than their workday ({_n}). They clocked in without "'),
    ('"abrir jornada, así que esas horas **se cargan al cliente y no entran en "',
     '"opening their workday, so those hours **are charged to the client and appear "'),
    ('"ninguna nómina**. Por eso «sin asignar» sale como «—»: no es calculable.")',
     '"in no payslip**. That is why «unallocated» shows «—»: it cannot be worked out.")'),
    ('f"**{pct_sina:.0f}%** de la jornada del grupo fue traslados y espera "',
     'f"**{pct_sina:.0f}%** of the company workday was travel and waiting "'),
    ('f"(sin asignar).{_extra} M.O. cargada = horas imputadas × tarifa de "',
     'f"(unallocated).{_extra} Labour charged = hours charged × each "'),
    ('"cada persona; no incluye los aportes de ley (ver Resumen → "',
     '"person rate; it does not include statutory contributions (see Summary → "'),
    ('"Conciliación).")', '"Reconciliation).")'),
    ('"<small>gastado</small>"', '"<small>spent</small>"'),
    ('f"{theme.dinero(filas.get(\'total\', 0))} — ⚠️ esto es costo de "',
     'f"{theme.dinero(filas.get(\'total\', 0))} — ⚠️ this is "'),
    ('"**estructura**: no se le carga a ninguna obra ni se le factura a nadie.")',
     '"**overhead**: it is not charged to any job and not invoiced to anyone.")'),
]

s = P.read_text(encoding="utf-8")
fallos = [o for o, n in R if s.count(o) != 1 and s.count(n) == 0]
if fallos:
    print(f"{len(fallos)} anclas no casan (cuenta ≠ 1):")
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
print(f"  projects_ui  {n} reemplazos a mano")
