"""Prueba el guardián de v461 contra código ROTO.

⚠️ NO lanzar mientras corre la suite: este script modifica ficheros del árbol de
trabajo y los restaura al terminar, así que cualquier cosa que lea el código a la
vez obtiene basura (trampa de v455).
"""
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUARDIAN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "verif_v461.py")
os.chdir(RAIZ)   # los ficheros que se rompen viven en el repo

ROTURAS = [
    ("core/hojas.py", '    "CorreccionesFichaje",', "",
     "la hoja sale del lote: leería vacía en silencio (v353)"),
    ("core/correcciones.py", "            PENDIENTE, clock.now(grupo).strftime(timeclock.FMT), \"\", \"\", \"\",",
     "            PENDIENTE, clock.now(grupo).strftime(timeclock.FMT), \"\", \"\",",
     "la fila posicional pierde un valor (v363)"),
    ("core/timeclock.py", '        if horas != "":',
     "        if False:",
     "corregir_fichaje deja de escribir Horas"),
    ("core/correcciones.py",
     '    ok2, msg2 = _set(cid, {"Estado": REVERTIDA, "RevisadoPor": str(revisor or ""),',
     '    ok2, msg2 = _set(cid, {"Estado": REVERTIDA, "RevisadoPor": str(revisor or "") or timeclock.corregir_fichaje.__name__,',
     "(control: cambio inocuo que NO debe romper nada)"),
    ("core/correcciones.py", '    ok2, msg2 = _set(cid, {"ValorNuevo": nuevo.strftime(timeclock.FMT),',
     "    ok2, msg2 = _set(cid, {",
     "ajustar deja de reescribir ValorNuevo: el rastro mentiría"),
    ("core/timeclock_ui.py", "logger = logging.getLogger(__name__)", "",
     "se pierde el logger de módulo (NameError latente, v370)"),
    ("core/home_ui.py", '        ("⏱ Correcciones", ":material/schedule_send: Time fixes"),',
     '        ("⏱ Time fixes", ":material/schedule_send: Time fixes"),',
     "el ID se traduce y la comparación no: RAMA MUERTA (v442/v449)"),
    ("core/correcciones_ui.py", "         theme.AMBAR if pend else theme.AZUL),",
     "         None),",
     "el acento del KPI vuelve a poder ser None"),
    ("core/correcciones.py", '        return hojas.siguiente_id_libre(SHEET, "COR", n + 1)',
     '        return "COR-%04d" % len(usados)',
     "el ID se deriva del NÚMERO de filas (el fallo real de v428)"),
    ("core/correcciones_ui.py", '        _nota = st.text_input(t("Note (optional)"), key=f"cor_nota_{_id}")',
     '        _nota = st.text_input("Nota (opcional)", key=f"cor_nota_{_id}")',
     "una etiqueta se queda sin t()"),
    ("core/timeclock_ui.py", "                    correcciones.registrar(", "                    _ = (",
     "cerrar una sesión olvidada deja de avisar al admin"),
]

tmp = tempfile.mkdtemp(prefix="romper_v461_")
cazadas = escapadas = 0
for fichero, viejo, nuevo, desc in ROTURAS:
    src = open(fichero, encoding="utf-8").read()
    if src.count(viejo) < 1:
        print("[?]  ANCLA NO ENCONTRADA - %s (%s)" % (desc, fichero))
        print("     ⚠️ una rotura sobre código que no existe no prueba nada")
        escapadas += 1
        continue
    resp = os.path.join(tmp, os.path.basename(fichero))
    shutil.copy2(fichero, resp)
    open(fichero, "w", encoding="utf-8").write(src.replace(viejo, nuevo, 1))
    r = subprocess.run([sys.executable, GUARDIAN], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    shutil.copy2(resp, fichero)
    control = desc.startswith("(control")
    if control:
        marca = "[OK]  control pasa (como debe)" if r.returncode == 0 else "[!!]  el control FALLA"
        if r.returncode != 0:
            escapadas += 1
        else:
            cazadas += 1
    elif r.returncode != 0:
        marca = "[OK]  CAZADA"
        cazadas += 1
    else:
        marca = "[!!]  SE ESCAPÓ"
        escapadas += 1
    print("%s - %s" % (marca, desc))
    if r.returncode != 0 and not control:
        for ln in r.stdout.splitlines():
            if ln.strip().startswith("FALLO"):
                print("        " + ln.strip())

print("")
print("cazadas: %d · escapadas: %d" % (cazadas, escapadas))
r = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True)
print("git diff tras restaurar (debe estar vacío salvo lo mío):")
print(r.stdout or "  (sin cambios)")
sys.exit(1 if escapadas else 0)
