# -*- coding: utf-8 -*-
"""⚠️ Regla v410: el guardián de v446, probado contra código ROTO."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).parent
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

ROTURAS = [
    ("core/interpretation.py", "You are a senior engineer specialising",
     "Eres un ingeniero senior especialista en", "el prompt del informe ADMIN vuelve al espanol"),
    ("core/interpretation.py", '"parametros":          "Analysis of the shaft',
     '"parameters":          "Analysis of the shaft',
     "se traduce una CLAVE del schema (se guarda en InterpJSON)"),
    # ATENCION: el prefijo se PRODUCE en interpretation y se COMPARA en report:
    # traducir solo uno deja la deteccion de «la IA fallo» sin casar, en silencio.
    ("core/report.py", 'text.startswith("[Interpretation unavailable")',
     'text.startswith("[Interpretacion no disponible")',
     "el comparador del prefijo de la IA se desincroniza"),
    ("core/report.py", '_d("2. CAR DIMENSIONS")', '_d("2. DIMENSIONES DE CABINA")',
     "una cabecera del informe vuelve al espanol"),
    ("core/chat_agent.py", "Responde SIEMPRE en ingles tecnico claro".replace("ingles", "inglés").replace("tecnico", "técnico"),
     "Responde siempre en español técnico claro",
     "el asistente vuelve a responder en espanol"),
    ("core/admin_digest.py", 't("Open alarms:")', '"Alarmas abiertas:"',
     "un texto del radar vuelve al espanol"),
    # ⚠️ v515: el ancla decia '"Montaje de rieles (guías)"' y apuntaba a
    # `schedule.py`. Llevaba muerta desde v453, que es cuando esos nombres se migraron
    # al ingles: la rotura pretendia TRADUCIR un nombre espanol que ya no existia. Ahora
    # los nombres viven en el catalogo y la rotura va al reves, que es el riesgo de hoy.
    ("core/stages.py", '(PISTA_INSTALL, 6, "Shaft Climb & Bedplates", 13)',
     '(PISTA_INSTALL, 6, "Montaje de rieles (guías)", 13)',
     "se traduce un nombre de ETAPA (es dato de la hoja)"),
]


def corre():
    r = subprocess.run([sys.executable, str(AQUI / "verif_v448.py")], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


rc = corre()
print(f"código SANO → {'OK' if rc == 0 else 'FALLA'}")
if rc != 0:
    sys.exit(1)

cazadas = ancladas = 0
for rel, viejo, nuevo, desc in ROTURAS:
    f = RAIZ / rel
    src = f.read_text(encoding="utf-8")
    if viejo not in src:
        print(f"  ⚠️ ANCLA NO CASA en {rel}: {viejo.splitlines()[0][:46]!r}")
        continue
    ancladas += 1
    bak = f.with_suffix(".py.bak_r448")
    shutil.copy2(f, bak)
    try:
        f.write_text(src.replace(viejo, nuevo, 1), encoding="utf-8")
        cazada = corre() != 0
        cazadas += cazada
        print(f"  {'CAZADA     ' if cazada else '✗ SE ESCAPÓ'}  {desc}")
    finally:
        shutil.copy2(bak, f)
        bak.unlink()

fin = corre() == 0
print(f"\ncódigo RESTAURADO → {'OK' if fin else 'FALLA'}")
print(f"{cazadas}/{ancladas} roturas cazadas ({len(ROTURAS)} intentadas)")
sys.exit(0 if (cazadas == ancladas == len(ROTURAS) and fin) else 1)
