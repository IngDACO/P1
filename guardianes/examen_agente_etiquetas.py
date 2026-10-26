# -*- coding: utf-8 -*-
"""Etiquetas del EXAMEN A del agente del parte (v607): los 4 partes de prueba que escribió el
usuario en PRJ-0034 (cliente1, cuenta campo000 — datos de prueba, sin nombres reales).

⚠️ Escritas ANTES de correr el agente por primera vez, contra el plan sellado de PRJ-0034
(«Ripout + Installation», 18 etapas, 163 actividades). Como en v522: si se corrigen después
de ver lo que contesta, el examen ya no mide nada.

Una entrada por TROZO del parte:
  tipo  = «hecho»     → trabajo terminado: lo esperado es una propuesta (o una pregunta) con
                        alguna de `ok`;
          «empezado»  → empezado, sin terminar: NO debe proponerse como hecho nada de `mal`;
          «pregunta»  → lo correcto es PREGUNTAR: `ok` = las opciones que tienen que estar.
  ok    = actividades (nombre exacto) que cuentan como acierto.
  mal   = actividades que, propuestas como HECHAS, serían un error seguro.
"""
ETIQUETAS_A = {
    # «installed bedplate»: el plan tiene dos bedplates; sin más contexto se pregunta.
    "LOG-0001": [
        ("pregunta", "bedplate", {"Install motor bedplate", "Install single bedplate"}, set()),
    ],
    # «Installed yoke, platform, walls, and ceiling, start climbi g the shaft»
    "LOG-0002": [
        ("hecho", "yoke", {"Install yoke/base, level it"}, set()),
        ("hecho", "platform", {"Install platform (cradle)"}, set()),
        ("hecho", "walls", {"Build cabin (walls)"}, {"Prep cabin walls"}),
        ("hecho", "ceiling", {"Install cabin ceiling (roof)"}, set()),
        ("empezado", "climbi g the shaft", set(),
         {"Install rings to top", "Install car rails to top", "Install CW rails to top"}),
    ],
    # «Isntalled the tank / Finished with rails cabin and cw / Isntalled the motor»
    "LOG-0003": [
        ("hecho", "tank", {"Install CW tank"}, set()),
        ("hecho", "rails cabin", {"Install car rails to top", "Install first 2 car rails"}, set()),
        ("hecho", "cw", {"Install CW rails to top", "Install first 2 CW rails"}, set()),
        # El motor definitivo va sobre el bedplate; el plan no tiene «Install motor»: o se
        # pregunta o se dice fuera del plan. «Spin motor» (hacerlo girar) sería un error.
        ("pregunta", "motor", {"Install motor bedplate"}, {"Spin motor", "Mount tirak"}),
    ],
    # «Installed sills, frames, headers, grourguards, panels and tunned em all. And did door wiring»
    "LOG-0004": [
        ("hecho", "sills", {"Install sills"}, {"Install cabin sill", "Prep sills"}),
        ("hecho", "frames", {"Install frames"}, set()),
        ("hecho", "headers", {"Install headers"},
         {"Prep landing door headers", "Install cabin header (mechanical)"}),
        ("hecho", "grourguards", {"Groutguarding (fire-rated)"}, set()),
        ("hecho", "panels", {"Install door panels"}, {"Prep cabin panels", "Prep doors (panels/blades, frames)"}),
        ("hecho", "tunned em all", {"Tune doors"}, set()),
        ("hecho", "door wiring", {"Door locks"}, set()),
    ],
}
