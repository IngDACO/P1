# -*- coding: utf-8 -*-
"""Batería de roturas del arnés (01/11/2026): `verif_arnes` contra herramientas ROTAS.
Rompe GUARDIANES, no la app. ⚠️ Verde de BASE primero (v459) y NO en paralelo con la suite (v455):
`run_suite.py` y `anclas_lectura.py` se reescriben mientras dura.
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
ENV.pop("COPEX_CORTE", None)
G = "verif_arnes"
TOPE_S = 180
A = "arnes/sitecustomize.py"
S = "run_suite.py"
B = "baterias_afectadas.py"
T = "tanda.py"

ROTURAS = [
    ("⚠️ el corte deja de cortar", A,
     [("            os._exit(1)\n", "            pass\n")]),
    ("⚠️ el corte sale con 0: un rojo parecería verde", A,
     [("            os._exit(1)\n", "            os._exit(0)\n")]),
    ("⚠️ el corte también en las baterías", A,
     [("        if a and _es_fallo(a[0]) and _es_guardian():\n", "        if a and _es_fallo(a[0]):\n")]),
    ("⚠️ el recuento «FALLOS: 3» corta", A,
     [('    return t == "FALLO" or t.startswith(("FALLO ", "FALLO:"))\n', '    return t.startswith("FALLO")\n')]),
    ("el «*** FALLO» deja de reconocerse", A,
     [('    t = str(primero).lstrip(" \\n*")\n', '    t = str(primero).lstrip(" \\n")\n')]),
    ("el corte funciona sin pedirlo", A,
     [('if os.environ.get("COPEX_CORTE"):\n    _cortar', 'if True:\n    _cortar')]),
    ("⚠️ la red deja de apuntar", A,
     [("    http.client.HTTPConnection.putrequest = putrequest\n", "")]),
    ("⚠️ la suite lleva el corte", S,
     [('ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8",\n',
       'ENTORNO = {**os.environ, "PYTHONIOENCODING": "utf-8", "COPEX_CORTE": "1",\n')]),
    ("la suite pierde el arnés", S,
     [('(str(AQUI / "arnes"), os.environ.get("PYTHONPATH"))', '(os.environ.get("PYTHONPATH"),)')]),
    ("⚠️ pasarse del techo deja de ser rojo", S,
     [("if _ritmo > TECHO_HOJA:\n", "if _ritmo > TECHO_HOJA and False:\n    pass\nif False:\n")]),
    ("⚠️ el techo sube por encima de la cuota", S,
     [("TECHO_HOJA = 50\n", "TECHO_HOJA = 500\n")]),
    ("⚠️ la suite deja de guardar las lecturas", S,
     [('    ENTORNO["COPEX_CACHE_HOJA"] = tempfile.mkdtemp(prefix="suite_hoja_")\n', '    ENTORNO["COPEX_CACHE_HOJA"] = ""\n')]),
    ("⚠️ los datos reales se quedan en el disco", S,
     [('    atexit.register(shutil.rmtree, ENTORNO["COPEX_CACHE_HOJA"], ignore_errors=True)\n', "")]),
    ("la suite vuelve a correr de uno en uno", S,
     [("PROCESOS = 5\n", "PROCESOS = 1\n")]),
    ("un guardián se queda sin su tope de tiempo", S,
     [('errors="replace", timeout=240)', 'errors="replace")')]),
    ("⚠️ un 429 se guarda como si fuera el dato", A,
     [("            if r.status_code == 200:", "            if True:")]),
    ("⚠️ una escritura deja lo guardado como estaba", A,
     [("            _vaciar()\n", "            pass\n")]),
    ("⚠️ una escritura se contesta de la carpeta", A,
     [('        if request.method != "GET":\n', '        if False:\n')]),
    ("⚠️ se guarda cualquier host (el token incluido)", A,
     [("        if _host not in str(request.url):\n", "        if False:\n")]),
    ("⚠️ una carrera por guardar revienta la lectura", A,
     [("                except OSError:\n                    try:\n                        os.remove(tmp)\n"
       "                    except OSError:\n                        pass\n",
       "                except ZeroDivisionError:\n                    pass\n")]),
    ("⚠️ py_compile vuelve a escribir el .pyc", A,
     [("_compilar_en_memoria()\nif os.environ", "if os.environ")]),
    ("⚠️ un error de sintaxis deja de avisar", A,
     [("            if doraise:\n                raise err\n", "")]),
    ("lo guardado no se usa", A,
     [('            with open(f, "rb") as fh:\n                cuerpo = fh.read()\n',
       '            raise OSError("no")\n')]),
    ("sin las variables de la prueba, lo guardado se activa solo", A,
     [('if os.environ.get("COPEX_CACHE_HOJA"):\n    _guardar', 'if True:\n    _guardar')]),
    ("⚠️ el margen deja de contar", B,
     [("range(l0 - margen, l1 + margen + 1)", "range(l0, l1 + 1)")]),
    ("el salto final del ancla cuenta como otra línea", B,
     [('a.rstrip("\\n").count("\\n")', 'a.count("\\n")')]),
    ("⚠️ un borrado no marca ninguna línea", B,
     [("if n else (ini, ini + 1))", "if n else ())")]),
    ("cambiar la batería deja de seleccionarla", B,
     [('            motivos.append("se cambió la batería")\n', "            pass\n")]),
    ("⚠️ cambiar su guardián deja de seleccionarla", B,
     [('if g.startswith(("verif_", "check_")) and g in fuente]', 'if False]')]),
    ("⚠️ una batería NUEVA va con corte", T,
     [("    if not nueva:\n", "    if True:\n")]),
    ("una batería vieja va sin corte", T,
     [("    if not nueva:\n", "    if False:\n")]),
    ("⚠️ salir con 0 y una rotura escapada es «bien»", T,
     [('    return codigo != 0 or any(m in texto for m in _MALAS)\n', '    return codigo != 0\n')]),
    ("⚠️ las baterías se corren con la suite en rojo", T,
     [('            print("\\n⚠️ LA SUITE ESTÁ EN ROJO: no se corren las baterías.")\n            return 1\n',
       '            print("\\n⚠️ LA SUITE ESTÁ EN ROJO: no se corren las baterías.")\n')]),
    ("⚠️ las baterías dejan de compartir las lecturas", T,
     [('    os.environ["COPEX_CACHE_HOJA"] = _cache\n', "")]),
    ("⚠️ el código deja de compararse tras cada batería", T,
     [("        _t = distintos(h0, huella())\n", "        _t = []\n")]),
    ("⚠️ una batería con tiempo máximo", T,
     [("stdout=fh, stderr=subprocess.STDOUT)", "stdout=fh, stderr=subprocess.STDOUT, timeout=600)")]),
]
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo", T,
           [('_MALAS = ("ESCAPA",', '_MALAS = ("ESCAPA",  # (control)\n         ')])


def corre():
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRW, G + ".py")], cwd=RAIZ,
                           capture_output=True, env=ENV, timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return None
    return r.returncode == 0


def aplica(rel, cambios):
    p = os.path.join(SCRW, rel)
    bak = io.open(p, encoding="utf-8", newline="").read()
    txt = bak.replace("\r\n", "\n")
    for viejo, nuevo in cambios:
        if txt.count(viejo) != 1:
            return None, bak, p, "x%d: %s" % (txt.count(viejo), viejo[:50])
        txt = txt.replace(viejo, nuevo, 1)
    io.open(p, "w", encoding="utf-8", newline="").write(txt)
    return True, bak, p, ""


if __name__ == "__main__":
    if corre() is not True:
        print("⚠️ el guardian YA esta rojo: la tanda saldria «cazada» sin probar nada")
        sys.exit(1)
    print("0. Verde de base: ok")
    cazadas, malas = 0, []
    for desc, rel, cambios in ROTURAS:
        ok, bak, p, msg = aplica(rel, cambios)
        if ok is None:
            print("  ?? ancla %s: %s" % (desc, msg))
            malas.append(desc)
            continue
        try:
            r = corre()
        finally:
            io.open(p, "w", encoding="utf-8", newline="").write(bak)
        if r is False:
            cazadas += 1
            print("  ok    cazada: %s" % desc)
        else:
            print("  ESCAPA %s (%s)" % (desc, "COLGADA" if r is None else "verde"))
            malas.append(desc)
    desc, rel, cambios = CONTROL
    ok, bak, p, msg = aplica(rel, cambios)
    try:
        r = corre() if ok else None
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok   " if r is True else "ESCAPA", desc))
    if r is not True:
        malas.append(desc)
    if corre() is not True:
        print("⚠️ el guardian NO vuelve a verde tras restaurar")
        malas.append("restaurar")
    print("=== %d de %d roturas cazadas ===" % (cazadas, len(ROTURAS)))
    sys.exit(1 if malas else 0)
