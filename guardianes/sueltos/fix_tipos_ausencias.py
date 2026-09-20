# -*- coding: utf-8 -*-
"""⚠️ Quita el `t()` de `ausencias.TIPOS` — se congelaba al importar.

Lo cazó el guardián de v445 con el fallo recién cometido: `TIPOS` se construye a
nivel de módulo, así que `t("Annual leave")` se evalúa UNA vez, al importar, cuando
todavía no hay sesión. La constante guarda el texto BASE y la traducción se mueve a
donde se PINTA — el mismo criterio que `auth.SESION_OCUPADA` y que toda la
separación etiqueta/dato del módulo i18n.

⚠️ En los CORREOS el nombre se queda en base a propósito (regla v436): un aviso que
sale de la empresa no puede cambiar de idioma según cómo tenga la pantalla quien lo
dispara.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = Path(r"C:\Users\diego\P1\survey_app")

AU = R / "core/ausencias.py"
src = AU.read_text(encoding="utf-8")

for viejo, nuevo in (('{"nombre": t("Annual leave"), "estado_roster": "LEAVE",',
                      '{"nombre": "Annual leave", "estado_roster": "LEAVE",'),
                     ('{"nombre": t("Sick leave"), "estado_roster": "LEAVE",',
                      '{"nombre": "Sick leave", "estado_roster": "LEAVE",'),
                     ('{"nombre": t("Day off"), "estado_roster": "OFF",',
                      '{"nombre": "Day off", "estado_roster": "OFF",')):
    assert src.count(viejo) == 1, f"ancla: {viejo[:44]!r}"
    src = src.replace(viejo, nuevo, 1)

# helper para las pantallas
ANCLA = "# Horas que vale un día de ausencia PAGADA en la nómina."
HELPER = '''def nombre_tipo(tipo) -> str:
    """El nombre visible de un tipo de ausencia, en el idioma de la PANTALLA.

    ⚠️ La traducción va aquí y NO dentro de `TIPOS`: ese dict se construye al
    importar el módulo, cuando no hay sesión, así que un `t()` ahí quedaría
    congelado en el idioma de ese instante (el fallo de `auth.SESION_OCUPADA`,
    v445). `TIPOS` guarda el texto BASE, que es el dato; esto lo traduce al pintarlo.

    ⚠️ En los CORREOS no se usa: un aviso que sale de la empresa va en el idioma
    base, pase lo que pase (regla v436).
    """
    return t(str(TIPOS.get(str(tipo), {}).get("nombre", tipo)))


'''
assert src.count(ANCLA) == 1, "ancla del helper"
src = src.replace(ANCLA, HELPER + ANCLA, 1)
AU.write_text(src, encoding="utf-8")
print("ausencias.TIPOS: `t()` fuera + helper `nombre_tipo` añadido")

# ── las pantallas pasan a usar el helper (los correos NO) ──
UI = R / "core/ausencias_ui.py"
u = UI.read_text(encoding="utf-8")
PANTALLA = [
    ("return (f\"**{cfg.get('nombre', r.get('Tipo'))}** · {r.get('Desde')} → \"",
     "return (f\"**{AU.nombre_tipo(r.get('Tipo'))}** · {r.get('Desde')} → \""),
    ("tarj.append(_kpi(cfg[\"nombre\"], f\"{s['usados']:.0f}\",",
     "tarj.append(_kpi(AU.nombre_tipo(k), f\"{s['usados']:.0f}\","),
    ("tarj.append(_kpi(cfg[\"nombre\"], f\"{s['restantes']:.0f}\",",
     "tarj.append(_kpi(AU.nombre_tipo(k), f\"{s['restantes']:.0f}\","),
    ("format_func=lambda _k: f\"{AU.TIPOS[_k]['emoji']} {AU.TIPOS[_k]['nombre']}\")",
     "format_func=lambda _k: f\"{AU.TIPOS[_k]['emoji']} {AU.nombre_tipo(_k)}\")"),
]
for viejo, nuevo in PANTALLA:
    n = u.count(viejo)
    if n != 1:
        print(f"  ⚠️ {n} de {viejo[:56]!r}")
        continue
    u = u.replace(viejo, nuevo, 1)
    print(f"  OK  {viejo[:58]}")
UI.write_text(u, encoding="utf-8")
