# -*- coding: utf-8 -*-
"""Prueba el guardián de v482 contra código ROTO.

Un guardián que solo aprueba no demuestra nada — y hay que incluir un CONTROL (un
cambio inocuo que debe pasar), o uno que grite con cualquier edición tampoco distingue.

⚠️ NUNCA se lanza en paralelo con la suite: modifica ficheros del árbol de trabajo
(la trampa que fabricó 7 rojos falsos en v455).

⚠️ Y las corridas van ESPACIADAS: el guardián hace una lectura real de Sheets y el
techo son 60/min, así que once seguidas se provocan un 429 y dan rojos que no existen
(trampa nº19). Pasó en la primera tanda: el CONTROL salió rojo por eso y en solitario
pasaba.
"""
import io
import os
import subprocess
import sys
import time

RAIZ = "C:\\Users\\diego\\P1\\survey_app"
GUARDIAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v482.py")

_NL = chr(10)   # ⚠️ nunca "\n" literal por heredoc: se convierte en un salto real

PICO_RELOJ = _NL.join([
    "    _cubos_pico = {}",
    "    for _t, _l, _k in evs:",
    "        _c = _cubos_pico.setdefault(int(_t // 60) * 60, {'lectura': 0, 'escritura': 0})",
    "        _c[_k] += 1",
    "    out['pico']['lectura'] = max([v['lectura'] for v in _cubos_pico.values()] or [0])",
    "    out['pico']['escritura'] = max([v['escritura'] for v in _cubos_pico.values()] or [0])",
    "    for i, (t0, _l, _k) in enumerate([]):",
])

ROTURAS = [
    ("hojas.py", "invalidar vuelve a limpiar TODOS los libros",
     _NL.join(["        if sid:", "            _lote.clear(sid)",
               "        else:", "            _lote.clear()"]),
     "        _lote.clear()"),
    ("hojas.py", "ignora el titulo y usa siempre el libro de la sesion",
     'sid = timeclock.sheet_id_para(titulo, grupo)',
     'sid = timeclock.sheet_id_para("Sheet1", grupo)'),
    ("projects.py", "un llamador vuelve a la llamada pelada",
     'hojas.invalidar("Projects")', 'hojas.invalidar()'),
    ("metrics.py", "clasifica por METODO (un batchGet por POST seria escritura)",
     _NL.join(['        if ":batchGet" in ep:', '            return "lectura"',
               '        return "escritura"']),
     '        return "escritura"'),
    ("metrics.py", "el pico se calcula por minutos de RELOJ, no deslizante",
     "    for i, (t0, _l, _k) in enumerate(evs):", PICO_RELOJ),
    ("metrics.py", "el contador propaga sus propias excepciones",
     _NL.join(["    except Exception:                       "
               "# noqa: BLE001 - jamás puede propagar", "        pass"]),
     _NL.join(["    except Exception:", "        raise"])),
    ("timeclock.py", "se quita el enganche del medidor",
     _NL.join(["                        _anotar_llamada(_m, _ep)",
               "                        return super().request(*a, **kw)"]),
     "                        return super().request(*a, **kw)"),
    ("auth_ui.py", "la sub-seccion de Cuota deja de despacharse (cae al else)",
     _NL.join(['    elif sec == "📈 Cuota":', "        _owner_cuota()", ""]), ""),
    ("home_ui.py", "la sub-seccion nueva se cuela la PRIMERA",
     _NL.join(['        ("🌐 Resumen",   ":material/dashboard: Summary"),',
               '        ("🏢 Grupos",    ":material/business: Groups"),']),
     _NL.join(['        ("📈 Cuota",     ":material/speed: API quota"),',
               '        ("🌐 Resumen",   ":material/dashboard: Summary"),',
               '        ("🏢 Grupos",    ":material/business: Groups"),'])),
    ("home_ui.py", "...o se queda DUPLICADA en la lista",
     '        ("📚 Manuales",  ":material/menu_book: Manuals"),',
     _NL.join(['        ("📚 Manuales",  ":material/menu_book: Manuals"),',
               '        ("📈 Cuota",     ":material/speed: API quota"),'])),
    # ── CONTROL: un cambio inocuo que DEBE seguir pasando ──
    ("metrics.py", "CONTROL: solo un comentario nuevo",
     "logger = logging.getLogger(__name__)",
     _NL.join(["logger = logging.getLogger(__name__)",
               "# comentario inocuo del control"])),
]


def corre(espera=8):
    time.sleep(espera)
    r = subprocess.run([sys.executable, GUARDIAN], cwd=RAIZ,
                       capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


print("verde de BASE antes de romper nada:", "OK" if corre(0) == 0 else "*** ROJO ***")
print("(si esto sale rojo, la tanda de abajo no prueba NADA — leccion v459)")
print("")

cazadas = escapadas = 0
for fich, que, viejo, nuevo in ROTURAS:
    ruta = os.path.join(RAIZ, "core", fich)
    orig = io.open(ruta, encoding="utf-8").read()
    if orig.count(viejo) < 1:
        print("  ??   %-56s ANCLA NO ENCONTRADA" % que[:56])
        escapadas += 1
        continue
    try:
        io.open(ruta, "w", encoding="utf-8", newline="").write(orig.replace(viejo, nuevo, 1))
        cod = corre()
    finally:
        io.open(ruta, "w", encoding="utf-8", newline="").write(orig)
    es_control = que.startswith("CONTROL")
    bien = (cod == 0) if es_control else (cod != 0)
    cazadas += 1 if bien else 0
    escapadas += 0 if bien else 1
    print("  %s %-56s (%s)" % ("ok  " if bien else "ESCAPA", que[:56],
                               "pasa" if cod == 0 else "rojo"))

print("")
print("%d correctas · %d mal" % (cazadas, escapadas))
sys.exit(0 if escapadas == 0 else 1)
