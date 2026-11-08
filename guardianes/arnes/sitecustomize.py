# -*- coding: utf-8 -*-
"""El arnés de los guardianes. Python importa `sitecustomize` solo al arrancar, y esta carpeta entra
en PYTHONPATH SOLO cuando lanzan `run_suite.py` o `tanda.py`: sin ellos no existe. Así tres cosas
valen para los 400 ficheros de guardianes y baterías sin tocar ni uno.

1. `COPEX_RED=<fichero>`: apunta cada petición HTTP que sale de verdad del proceso.
   ⚠️ Lo medido el 01/11/2026 desmintió lo que decía la documentación: no eran 16 guardianes los que
   leían la hoja real, eran 110 (1351 peticiones), casi todos solo por arrancar (`clock` lee los
   grupos). Y 9 de los que se creían lectores no la leen.
2. `COPEX_CACHE_HOJA=<carpeta>`: la lectura de una hoja se pide a Google UNA vez por tanda y los
   demás procesos la toman de esa carpeta. Sin esto, correr en paralelo eran ~180 lecturas/min contra
   un techo de 60 que comparte la app en producción (la misma cuenta de servicio). Una escritura
   vacía la carpeta: quien lee después de escribir ve lo escrito.
   ⚠️ Son datos reales: la carpeta va fuera del repo y se borra al acabar. El token de acceso NO se
   guarda (solo los GET de la API de hojas).
3. `COPEX_CORTE=1`: un guardián termina en su primer «FALLO» (con ese FALLO ya impreso). Una rotura
   cazada ya no corre el resto del guardián.
   ⚠️ Solo en un guardián: la batería que lo lanza imprime sus propios textos con «FALLO».
   ⚠️ Una batería NUEVA va SIN corte (`tanda.py`): es donde se prueba que el guardián SALE con
   código de error. Con el corte, uno que imprimiera «FALLO» y saliera con 0 —verde en la suite—
   parecería cazar la rotura.
4. Siempre: ⚠️ una prueba no escribe de verdad ni avisa a nadie. Escribir en Sheets o Drive, Telegram y correo se
   paran aquí, y cada intento queda en `COPEX_RED` como BLOQUEADA (`run_suite.py` lo pone en ROJO). Lo destapó
   el examen del Management assistant (v643): una rotura de `romper_v623` quitaba una validación y el guardián
   llegaba a `alerts.report_problem` real. 4 pasadas, 4 alarmas en cliente1 y aviso a 5 cuentas.
   ⚠️ Solo donde entra el arnés: una batería suelta sin este PYTHONPATH no lo lleva.
"""
import os
import sys
import threading
import time

# ⚠️ v658 · Windows (o el antivirus, que abre el fichero recién escrito) puede tener el registro bloqueado
# un instante. Sin reintentar, la línea se perdía EN SILENCIO: provocado con el fichero bloqueado 1 s, se
# perdían las 8 de verif_v643 y el hijo seguía diciendo «parado». Una BLOQUEADA perdida es un intento de
# escritura que la suite no ve. Lo destapó un rojo de esa comprobación en la tanda de v658 (1 de ~20).
_REINTENTOS = 100         # × 50 ms = 5 s


def _anotar(fichero, linea):
    for _ in range(_REINTENTOS):
        try:
            with open(fichero, "a", encoding="utf-8") as f:
                f.write(linea)
            return True
        except OSError:
            time.sleep(0.05)
    sys.stderr.write("arnés: NO se pudo apuntar en %s: %s" % (fichero, linea))
    return False


def _es_guardian():
    return os.path.basename(sys.argv[0] if sys.argv else "").startswith(("verif_", "check_"))


def _apuntar_red(fichero):
    import http.client
    _real = http.client.HTTPConnection.putrequest
    # ⚠️ Con cerrojo: dos hilos del mismo proceso pisaban la línea del otro y salían hosts que no
    # existen («is.com», el trozo final de «…googleapis.com»).
    _cerrojo = threading.Lock()

    def putrequest(self, method, url, *a, **k):
        with _cerrojo:
            _anotar(fichero, "%s %s\n" % (self.host, method))
        return _real(self, method, url, *a, **k)

    http.client.HTTPConnection.putrequest = putrequest


def _guardar_lecturas(carpeta):
    import hashlib
    import requests
    import requests.adapters
    _real = requests.adapters.HTTPAdapter.send
    _host = os.environ.get("COPEX_CACHE_HOST") or "sheets.googleapis.com"

    def _vaciar():
        for n in os.listdir(carpeta):
            try:
                os.remove(os.path.join(carpeta, n))
            except OSError:
                pass

    def send(self, request, *a, **k):
        if _host not in str(request.url):
            return _real(self, request, *a, **k)
        if request.method != "GET":
            r = _real(self, request, *a, **k)
            _vaciar()
            return r
        f = os.path.join(carpeta, hashlib.sha1(str(request.url).encode("utf-8")).hexdigest())
        try:
            with open(f, "rb") as fh:
                cuerpo = fh.read()
        except OSError:
            r = _real(self, request, *a, **k)
            if r.status_code == 200:          # ⚠️ un 429 o un 500 no se guarda como si fuera el dato
                tmp = "%s.%d.%d" % (f, os.getpid(), threading.get_ident())
                # ⚠️ Windows rechaza reemplazar un fichero que otro proceso tiene abierto. Dos que
                # pidan lo mismo a la vez es lo normal al empezar, y sin esto la LECTURA reventaba:
                # 2 guardianes en rojo después de 3 pasadas limpias, por pura suerte. Si no se
                # puede guardar da igual: la respuesta ya está aquí y otro la guardó o la guardará.
                try:
                    with open(tmp, "wb") as fh:
                        fh.write(r.content)
                    os.replace(tmp, f)
                except OSError:
                    try:
                        os.remove(tmp)
                    except OSError:
                        pass
            return r
        r = requests.Response()
        r.status_code, r._content, r._content_consumed = 200, cuerpo, True
        r.url, r.request, r.connection, r.encoding = request.url, request, self, "utf-8"
        r.headers["Content-Type"] = "application/json; charset=UTF-8"
        return r

    requests.adapters.HTTPAdapter.send = send


def _es_escritura(metodo, url) -> bool:
    """¿Cambia algo de verdad o avisa a alguien? Las lecturas y el token de acceso, no: sin ellos no arranca nada."""
    u = str(url)
    if "api.telegram.org" in u:
        return True
    if str(metodo).upper() in ("GET", "HEAD"):
        return False
    return "sheets.googleapis.com" in u or "googleapis.com/drive" in u or "googleapis.com/upload" in u


def _sin_escrituras():
    import smtplib
    import requests.adapters
    import requests.exceptions
    _real = requests.adapters.HTTPAdapter.send
    _fichero = os.environ.get("COPEX_RED")

    def _parar(host, metodo):
        if _fichero and not _anotar(_fichero, "%s %s BLOQUEADA\n" % (host, metodo)):
            # ⚠️ v658 · sin el apunte la suite no vería el intento: que el proceso salga en rojo él mismo
            sys.stdout.write("arnés: un intento de escribir (%s %s) que no se pudo apuntar\n" % (metodo, host))
            sys.stdout.flush()
            os._exit(1)   # (no es la salida del corte: romper_arnes ancla en aquella)
        return "arnés: una prueba no escribe de verdad ni avisa a nadie (%s %s)" % (metodo, host)

    def send(self, request, *a, **k):
        if _es_escritura(request.method, request.url):
            raise requests.exceptions.ConnectionError(_parar(str(request.url).split("/")[2], request.method))
        return _real(self, request, *a, **k)

    def correo(self, *a, **k):
        raise OSError(_parar("smtp", "SMTP"))

    requests.adapters.HTTPAdapter.send = send
    smtplib.SMTP.__init__ = correo
    smtplib.SMTP_SSL.__init__ = correo


def _compilar_en_memoria():
    """`py_compile.compile` SIEMPRE escribe el .pyc y, a diferencia de un `import`, revienta si no
    puede: con varios procesos a la vez, Windows rechaza reemplazarlo si otro lo tiene abierto
    (33 guardianes lo usan, y lo que quieren saber es si compila, no el .pyc)."""
    import py_compile

    def compilar(file, cfile=None, dfile=None, doraise=False, *a, **k):
        try:
            with open(file, "rb") as f:
                compile(f.read(), dfile or file, "exec", dont_inherit=True)
        except (SyntaxError, ValueError) as e:
            err = py_compile.PyCompileError(e.__class__, e, dfile or file)
            if doraise:
                raise err
            sys.stderr.write(err.msg + "\n")
        return None

    py_compile.compile = compilar


def _es_fallo(primero):
    """«  FALLO x», «   FALLO», «  *** FALLO  x»; NO «FALLOS: 3» ni «HAY FALLOS»: esas son el recuento
    del final y ahí el guardián ya termina solo."""
    t = str(primero).lstrip(" \n*")
    return t == "FALLO" or t.startswith(("FALLO ", "FALLO:"))


def _cortar_en_fallo():
    import builtins
    _real = builtins.print

    def print_(*a, **k):
        _real(*a, **k)
        if a and _es_fallo(a[0]) and _es_guardian():
            try:
                sys.stdout.flush()
            except Exception:                                    # noqa: BLE001
                pass
            os._exit(1)

    builtins.print = print_


_compilar_en_memoria()
if os.environ.get("COPEX_RED"):
    _apuntar_red(os.environ["COPEX_RED"])
if os.environ.get("COPEX_CACHE_HOJA"):
    _guardar_lecturas(os.environ["COPEX_CACHE_HOJA"])
if os.environ.get("COPEX_CORTE"):
    _cortar_en_fallo()
_sin_escrituras()         # ⚠️ El último: envuelve a `_guardar_lecturas`, y lo parado no le llega
