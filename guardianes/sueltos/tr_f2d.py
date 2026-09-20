"""F2 (4/4) — REMATE. Los restos que el detector de español NO veía.

⚠️ Mi barrido de F2 usaba un detector de español (acentos + palabras funcionales) y dio
«0 restantes». Es FALSO: «Fichar», «Firma», «Iniciales», «Pendientes», «Sitios» o
«Mis ausencias» no llevan acento ni palabra funcional, así que pasaron por delante. Es
el mismo agujero que dejó «Planificado» en v438 y «Registrados» en el guardián de v439.
El barrido bueno es el de POSICIÓN: todo literal que llega a una función de display y NO
está envuelto en `t()`, y luego revisarlo a mano.

⚠️ Lo que NO se toca, aunque salga en ese barrido:
  · claves de dict y columnas de hoja: `f["entrada"]`, `r.get("Motivo")`, `x.get("Nombre")`,
    `"Ubicacion"`, `"usuario"`, `"nombre"`, `"tipo"`, `"horas"`, `"estado"`, `"ficho"`…
  · las keys de widget (`ps_invitados`) y los tokens `:material/…:` sin texto.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

# (viejo, nuevo, ¿todas las apariciones?)
R = {
    "core/timeclock_ui.py": [
        # sale 2 veces (el modal y el chip): las dos
        ('":material/health_and_safety: Hacerlo ahora"',
         't(":material/health_and_safety: Do it now")', True),
        ('":material/draw: Firmar ahora"', 't(":material/draw: Sign it now")', False),
        ('":material/draw: Firmar"', 't(":material/draw: Sign")', False),
        ('"###### :material/schedule: FICHAJE"',
         't("###### :material/schedule: TIME CLOCK")', False),
        ('f":material/check_circle: Fichar a {_a[\'etiqueta\']}",',
         'f"{t(\':material/check_circle: Clock in to\')} {_a[\'etiqueta\']}",', False),
        ('f":material/check_circle: Fichar a {_a[\'etiqueta\']} (your assignment for today)",',
         'f"{t(\':material/check_circle: Clock in to\')} {_a[\'etiqueta\']} '
         '{t(\'(your assignment for today)\')}",', False),
        ('":material/check_circle: Fichar"', 't(":material/check_circle: Clock in")', False),
        ('c2.time_input("Hora"', 'c2.time_input(t("Time")', False),
        ('"### :material/schedule: Fichaje"', 't("### :material/schedule: Time clock")', False),
        ('f"  ·  grupo **{grupo}**"', 'f"  ·  {t(\'group\')} **{grupo}**"', False),
        ('":material/sync: Cambiar"', 't(":material/sync: Switch")', False),
        # ⚠️ Cabeceras VISIBLES de la tabla de fichajes propios. Se traducen; lo que NO
        # se toca es `f["entrada"] / f["salida"] / f["horas"]`, que son claves del dato.
        ('"Entrada": f["entrada"]', 't("In"): f["entrada"]', False),
        ('"Salida": (f["salida"][11:16] if f["salida"] else "en curso")',
         't("Out"): (f["salida"][11:16] if f["salida"] else t("in progress"))', False),
        ('"Horas": f["horas"]', 't("Hours"): f["horas"]', False),
    ],
    "core/prestart_ui.py": [
        ('"Subcontratista, visita…"', 't("Subcontractor, visitor…")', False),
        ('"### :material/health_and_safety: Pre-Start diario"',
         't("### :material/health_and_safety: Daily Pre-Start")', False),
        ('"Necesita Google Sheets configurado (gcp_service_account + TIMECLOCK_SHEET_ID)."',
         't("Google Sheets must be configured '
         '(gcp_service_account + TIMECLOCK_SHEET_ID).")', False),
        ('"Notas generales"', 't("General notes")', False),
        ('":material/download: Descargar PDF"', 't(":material/download: Download PDF")', False),
        ('"#### :material/account_tree: Pre-Starts anteriores"',
         't("#### :material/account_tree: Previous Pre-Starts")', False),
        # ⚠️ Estos dos van CONCATENADOS (`"..." + d[...]`), así que el ancla tiene que
        # incluir la comilla de cierre: sin ella, envolver en `t(` deja el paréntesis
        # sin cerrar y el fichero no compila (lo cortó `ast.parse` antes de escribirlo).
        ('":material/description: Actividades: "',
         't(":material/description: Activities: ")', False),
        ('":material/description: Notas generales: "',
         't(":material/description: General notes: ")', False),
    ],
    "core/ausencias_ui.py": [
        ('"## :material/event_busy: Mis ausencias"',
         't("## :material/event_busy: My absences")', False),
        ('"Motivo (opcional)"', 't("Reason (optional)")', False),
        ('":material/send: Enviar solicitud"', 't(":material/send: Send request")', False),
        ('"#### :material/history: Mis solicitudes"',
         't("#### :material/history: My requests")', False),
        ('_kpi("Pendientes"', '_kpi(t("Pending")', False),
        # ⚠️ `x.get("Nombre")` es COLUMNA de la hoja y no se toca; «nadie» sí es etiqueta
        ('or "nadie")', 'or t("nobody"))', False),
        ('"Nota (opcional)"', 't("Note (optional)")', False),
        ('":material/check_circle: Aprobar"', 't(":material/check_circle: Approve")', False),
        ('":material/cancel: Rechazar"', 't(":material/cancel: Reject")', False),
    ],
    "core/route_ui.py": [
        ('f"de {_n_pers} persona{\'\' if _n_pers == 1 else \'s\'}"',
         'f"{t(\'of\')} {_n_pers} {t(\'person\') if _n_pers == 1 else t(\'people\')}"', False),
        ('f":material/location_on: Sitios\\n\\n{len(sitios)}\\n\\n"',
         'f"{t(\':material/location_on: Sites\')}\\n\\n{len(sitios)}\\n\\n"', False),
    ],
}

fallos = []
for rel, reps in R.items():
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv, todas in reps:
        if s.count(nv) >= 1 and s.count(o) == 0:
            continue                                   # ya aplicado
        if s.count(o) < 1 or (not todas and s.count(o) != 1):
            fallos.append(f"{rel} ({s.count(o)}x) {o[:72]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv, todas in reps:
        c = s.count(o)
        if c:
            s = s.replace(o, nv) if todas else s.replace(o, nv, 1)
            n += c if todas else 1
    ast.parse(s)                                       # no se escribe un fichero roto
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:26} {n} reemplazos")
print("OK")
