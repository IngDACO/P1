# -*- coding: utf-8 -*-
"""El arnés de los guardianes hace lo que dice (01/11/2026). Vigila la suite en paralelo, el corte
al primer fallo y la selección de baterías: si una de estas cosas falla en silencio, lo que se
pierde es la garantía de todas las demás.

Las tres que más daño harían:
  · el corte activo en la SUITE, o «cazando» con un guardián que imprime FALLO y sale con 0;
  · una lectura de la hoja guardada mal: un 429 tomado por dato, o una lectura vieja tras escribir;
  · la selección dejándose una batería que ancla en lo cambiado.
"""
import ast
import http.client
import http.server
import io
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
ARNES = AQUI / "arnes"
n_ok, fallos = 0, []


def chk(q, c, d=""):
    global n_ok
    if c:
        n_ok += 1
        print("  ok    %s" % q)
    else:
        fallos.append(q)
        print("  FALLO %s %s" % (q, d))


def lanza(nombre, cuerpo, **env):
    """Corre `cuerpo` en un proceso nuevo como un fichero llamado `nombre`, con el arnés puesto."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, nombre)
        io.open(p, "w", encoding="utf-8").write(cuerpo)
        # ⚠️ Solo lo que pide esta prueba: la suite que la lanza trae sus propias variables
        e = {k: v for k, v in os.environ.items() if not k.startswith("COPEX_")}
        e.update({"PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(ARNES), **env})
        r = subprocess.run([sys.executable, p], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=e, timeout=60)
    return r.returncode, r.stdout


print("1. El corte")
_G = ('print("  ok   uno")\nprint("FALLOS: 3")\nprint("HAY FALLOS: 1")\nprint(%r)\n'
      'print("  ok   detras")\nraise SystemExit(0)\n')
for _m in ("  FALLO dos", "   FALLO dos", "  *** FALLO  dos", "  FALLO"):
    _c, _o = lanza("verif_zz.py", _G % _m, COPEX_CORTE="1")
    chk("%r termina el guardián, con ese FALLO ya impreso y código 1" % _m,
        _c == 1 and _m.strip() in _o and "detras" not in _o, (_c, _o))
_c, _o = lanza("check_zz.py", _G % "  FALLO dos", COPEX_CORTE="1")
chk("…también en un check_", _c == 1 and "detras" not in _o, (_c, _o))
_c, _o = lanza("verif_zz.py", _G % "  ok   nada", COPEX_CORTE="1")
chk("«FALLOS: 3» y «HAY FALLOS» NO cortan: son el recuento del final", _c == 0 and "detras" in _o, (_c, _o))
_c, _o = lanza("romper_zz.py", _G % "  FALLO dos", COPEX_CORTE="1")
chk("⚠️ en una BATERÍA no corta: imprime sus propios textos con «FALLO»", _c == 0 and "detras" in _o, (_c, _o))
_c, _o = lanza("verif_zz.py", _G % "  FALLO dos")
chk("sin `COPEX_CORTE`, el guardián llega al final", _c == 0 and "detras" in _o, (_c, _o))

print("\n2. La red")


class _Local(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *a):
        pass


    def do_POST(self):
        self.do_GET()


class _Contando(_Local):
    """Cuenta lo que llega de verdad. `/mal` contesta 429, como la cuota de Google."""
    llegadas = []

    def do_GET(self):
        _Contando.llegadas.append((self.command, self.path))
        cuerpo = ('{"n": %d}' % len(_Contando.llegadas)).encode("utf-8")
        self.send_response(429 if self.path == "/mal" else 200)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


_srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Local)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
_port = _srv.server_address[1]
_C = ("import http.client, urllib.request\n"
      "c = http.client.HTTPConnection('127.0.0.1', %d)\nc.request('GET', '/')\nc.getresponse().read()\n"
      "urllib.request.urlopen('http://localhost:%d/').read()\n") % (_port, _port)
with tempfile.TemporaryDirectory() as _d:
    _r = os.path.join(_d, "red.txt")
    _c, _o = lanza("verif_zz.py", _C, COPEX_RED=_r)
    _h = io.open(_r, encoding="utf-8").read().splitlines() if os.path.exists(_r) else []
_srv.shutdown()
chk("apunta cada petición con su host y método (http.client y urllib)",
    _h == ["127.0.0.1 GET", "localhost GET"], _h)

print("\n3. Las lecturas guardadas")
_srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Contando)
threading.Thread(target=_srv.serve_forever, daemon=True).start()
_port = _srv.server_address[1]
_L = ("import requests\nr = requests.%s('http://127.0.0.1:%d%s', timeout=20)\n"
      "print('RESP', r.status_code, r.json()['n'], r.ok, r.text)\n")
_lleg = _Contando.llegadas
with tempfile.TemporaryDirectory() as _d:
    _e = {"COPEX_CACHE_HOJA": _d, "COPEX_CACHE_HOST": "127.0.0.1"}
    _c, _o1 = lanza("verif_zz.py", _L % ("get", _port, "/ok"), **_e)
    _c, _o2 = lanza("verif_zz.py", _L % ("get", _port, "/ok"), **_e)
    chk("la 1ª lectura va a la red", _o1.startswith("RESP 200 1 True"), _o1)
    chk("⚠️ OTRO proceso, la misma lectura: no sale a la red y da lo mismo",
        len(_lleg) == 1 and _o2 == _o1, (_lleg, _o1, _o2))
    chk("en la carpeta hay esa lectura", len(os.listdir(_d)) == 1, os.listdir(_d))
    lanza("verif_zz.py", _L % ("get", _port, "/mal"), **_e)
    lanza("verif_zz.py", _L % ("get", _port, "/mal"), **_e)
    chk("⚠️ un 429 NO se guarda como si fuera el dato: el siguiente vuelve a pedir",
        _lleg.count(("GET", "/mal")) == 2, _lleg)
    _c, _o = lanza("verif_zz.py", _L % ("post", _port, "/x"), **_e)
    chk("⚠️ una escritura va a la red y vacía lo guardado", ("POST", "/x") in _lleg and not os.listdir(_d),
        (_lleg, os.listdir(_d)))
    lanza("verif_zz.py", _L % ("post", _port, "/x"), **_e)
    chk("…y nunca se contesta de la carpeta", _lleg.count(("POST", "/x")) == 2, _lleg)
    _c, _o = lanza("verif_zz.py", _L % ("get", _port, "/ok"), **_e)
    chk("…así que quien lee después de escribir ve lo escrito",
        _lleg.count(("GET", "/ok")) == 2 and not _o.startswith("RESP 200 1 "), _o)
_R = ("import os, requests\n"
      "def no(*a, **k):\n    raise PermissionError(5, 'Acceso denegado')\n"
      "os.replace = no\n" + _L)
with tempfile.TemporaryDirectory() as _d:
    _e = {"COPEX_CACHE_HOJA": _d, "COPEX_CACHE_HOST": "127.0.0.1"}
    _c, _o = lanza("verif_zz.py", _R % ("get", _port, "/carrera"), **_e)
    chk("⚠️ si Windows no deja guardarla, la lectura NO revienta: la respuesta sigue siendo buena",
        _c == 0 and _o.startswith("RESP 200"), (_c, _o))
    chk("…y no deja ficheros a medias", not os.listdir(_d), os.listdir(_d))
_n = len(_lleg)
with tempfile.TemporaryDirectory() as _d:
    lanza("verif_zz.py", _L % ("get", _port, "/otro"), COPEX_CACHE_HOJA=_d)
    lanza("verif_zz.py", _L % ("get", _port, "/otro"), COPEX_CACHE_HOJA=_d)
    chk("otro host no se guarda: solo la API de hojas (ni el token, que va por oauth2)",
        len(_lleg) == _n + 2 and not os.listdir(_d), (_lleg, os.listdir(_d)))
lanza("verif_zz.py", _L % ("get", _port, "/sin"))
lanza("verif_zz.py", _L % ("get", _port, "/sin"))
chk("sin `COPEX_CACHE_HOJA`, todo va a la red", _lleg.count(("GET", "/sin")) == 2, _lleg)
_srv.shutdown()


print("\n3b. py_compile, sin escribir")
with tempfile.TemporaryDirectory() as _d:
    _bien, _mal = os.path.join(_d, "bien.py"), os.path.join(_d, "mal.py")
    io.open(_bien, "w", encoding="utf-8").write("x = 1\n")
    io.open(_mal, "w", encoding="utf-8").write("def (:\n")
    _P = ("import py_compile, sys\nsys.dont_write_bytecode = True\n"
          "py_compile.compile(%r, doraise=True)\nprint('COMPILA')\n"
          "try:\n    py_compile.compile(%r, doraise=True)\n    print('NO AVISA')\n"
          "except py_compile.PyCompileError:\n    print('AVISA')\n") % (_bien, _mal)
    _c, _o = lanza("verif_zz.py", _P)
    chk("compila lo bueno", "COMPILA" in _o, (_c, _o))
    chk("⚠️ y sigue avisando de un error de sintaxis", "AVISA" in _o and "NO AVISA" not in _o, (_c, _o))
    chk("⚠️ sin escribir el .pyc: es lo que chocaba entre procesos en Windows",
        not os.path.exists(os.path.join(_d, "__pycache__")), os.listdir(_d))


print("\n4. run_suite.py")
_rs = io.open(AQUI / "run_suite.py", encoding="utf-8").read()
_arb = ast.parse(_rs)


def _valor(nombre):
    for n in _arb.body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == nombre:
            return n.value
    return None


_ent = ast.dump(_valor("ENTORNO"))
chk("el entorno de los guardianes lleva el arnés", "arnes" in _ent and "PYTHONPATH" in _ent)
chk("⚠️ la suite NO lleva el corte: un rojo tiene que enseñar TODOS sus fallos",
    "COPEX_CORTE" not in _rs)
chk("cada guardián corre con su fichero de red", '"COPEX_RED": red' in _rs)
_tech = ast.literal_eval(_valor("TECHO_HOJA"))
chk("el techo está por debajo de las 60 lecturas/min de la cuenta", 0 < _tech < 60, _tech)
_c = next((n for n in _arb.body if isinstance(n, ast.If) and "_ritmo" in ast.dump(n.test)), None)
chk("⚠️ pasarse del techo es ROJO", _c is not None and "_ritmo > TECHO_HOJA" in _rs
    and "rojo" in ast.dump(_c.body[0]), _c)
chk("⚠️ las lecturas se guardan", 'ENTORNO["COPEX_CACHE_HOJA"] = tempfile.mkdtemp(' in _rs)
chk("⚠️ …y se borran al acabar (son datos reales)",
    'atexit.register(shutil.rmtree, ENTORNO["COPEX_CACHE_HOJA"]' in _rs)
chk("varios procesos", "ThreadPoolExecutor(PROCESOS)" in _rs and ast.literal_eval(_valor("PROCESOS")) > 1)
chk("todo guardián sigue con su tope de 240 s", "timeout=240" in _rs)

print("\n5. La selección de baterías")
import baterias_afectadas as BA                                    # noqa: E402

_dif = ("--- a/survey_app/core/x.py\n+++ b/survey_app/core/x.py\n@@ -10 +10 @@ def f\n-a\n+b\n"
      "@@ -20,2 +20,3 @@\n-a\n-b\n+c\n+d\n+e\n@@ -30,4 +32,0 @@\n-a\n"
      "--- a/survey_app/core/ya.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-a\n")
chk("lee las líneas de un diff, borrados incluidos",
    BA.lineas_de_diff(_dif) == {"survey_app/core/x.py": {10, 20, 21, 22, 32, 33}}, BA.lineas_de_diff(_dif))
# Un caso REAL: la línea de un ancla conocida de romper_v573
_rel = "guardianes/run_suite.py"
_lin = next(i for i, l in enumerate(_rs.splitlines(), 1) if l == "        _h1 = _huella()")
_si = BA.cruzar({_rel: {_lin}})
chk("una batería que ancla en la línea cambiada SALE", "romper_v573" in _si, sorted(_si))
_si = BA.cruzar({_rel: {_lin + BA.MARGEN}})
chk("…y a `MARGEN` líneas también", "romper_v573" in _si, sorted(_si))
_no = BA.cruzar({_rel: {_lin + BA.MARGEN + 1}})
chk("…a una más, no (la sonda distingue)", "romper_v573" not in _no, sorted(_no))
chk("cambiar la batería la selecciona", "romper_v573" in BA.cruzar({"guardianes/romper_v573.py": {1}}))
chk("cambiar el guardián que corre la selecciona", "romper_v573" in BA.cruzar({"guardianes/verif_v573.py": {1}}))
chk("nada cambiado, ninguna", BA.cruzar({}) == {})

print("\n6. tanda.py")
import tanda as T                                                  # noqa: E402

_v, _n = T.entorno(False), T.entorno(True)
chk("una batería vieja va con corte", _v.get("COPEX_CORTE") == "1")
chk("⚠️ una batería NUEVA va SIN corte", "COPEX_CORTE" not in _n)
chk("las dos llevan el arnés", all(str(ARNES) in e["PYTHONPATH"] for e in (_v, _n)))
chk("salir con error es mal", T.salio_mal(1, "todo bien"))
for _t in ("  ESCAPA x", " COLGADA", "⚠️ el guardian YA esta rojo", "⚠️ ya falla en sano", "ABORTA"):
    chk("salir con 0 y %r es mal" % _t.strip(), T.salio_mal(0, _t))
chk("salir con 0 y todas cazadas es bien", not T.salio_mal(0, "=== 13 de 13 roturas cazadas ==="))
_a, _b = {"x/a.py": "1", "x/b.py": "2"}, {"x/a.py": "1", "x/b.py": "3", "x/c.py": "4"}
chk("la huella distingue lo cambiado y lo nuevo", T.distintos(_a, _b) == ["b.py", "c.py"], T.distintos(_a, _b))
chk("sin cambios, nada", T.distintos(_a, dict(_a)) == [])
_tx = io.open(AQUI / "tanda.py", encoding="utf-8").read()
chk("⚠️ la suite va ANTES que las baterías, y en rojo no se corren",
    _tx.index('correr("run_suite"') < _tx.index("BA.afectadas(base)") and "return 1" in _tx.split("BA.nuevas(base)")[0])
chk("⚠️ se compara el código tras CADA batería", "distintos(h0, huella())" in _tx)
chk("suite y baterías comparten las lecturas, y se borran",
    'os.environ["COPEX_CACHE_HOJA"] = _cache' in _tx and "atexit.register(shutil.rmtree, _cache" in _tx)
chk("⚠️ ninguna batería lleva tiempo máximo (cortarla deja roturas puestas)",
    "timeout" not in _tx.split('"""', 2)[2])

print("")
print("=== %d comprobaciones · %d fallos ===" % (n_ok + len(fallos), len(fallos)))
if fallos:
    sys.exit(1)
print("TODO OK")
