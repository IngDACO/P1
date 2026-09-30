# -*- coding: utf-8 -*-
"""v533 · LO QUE DESTAPÓ CERRAR LOS PENDIENTES EN PRODUCCIÓN.

1. ⚠️ EL VEREDICTO DEL HEARTBEAT SE QUEDABA GUARDADO. Probando la expulsión de la sesión única
   EN PRODUCCIÓN (30/09/2026: se cambió el token de la cuenta de prueba en `Login`, como si
   otro dispositivo la tomara; la app expulsó — bien) se repuso el token y se recargó: la
   cookie restauró la sesión y la app la volvió a expulsar AL INSTANTE con el veredicto
   viejo, sin preguntar a la hoja. Una lectura de `Login` que una vez no trajera la fila
   dejaría a alguien fuera con su cookie buena hasta teclear la contraseña.
   → se olvida al EXPULSAR y al RESTAURAR desde la cookie.
2. La leyenda del dibujo de Buffers se pisaba con 1-3 buffers (visto en producción).
3. Una etapa que vuelve a 0% conservaba su «inicio real» (anotado en v527).

Lo que protege, EJECUTANDO:
  (a) ⚠️ el caso de producción: desplazado → False; token repuesto → tras olvidar, el siguiente
      heartbeat dice True. Y SIN olvidar el False sigue ahí (la sonda ve el fallo);
  (b) un hilo que termina DESPUÉS de olvidar no vuelve a meter su veredicto;
  (c) ⚠️ `render_login` real: restaurar desde la cookie olvida el veredicto viejo;
  (d) app.py olvida al expulsar, antes de quitar la sesión;
  (e) los SVG de Buffers, Belting y Rieles sin textos pisados (y la sonda ve uno cuando lo hay);
  (f) ⚠️ a 0% se borra el inicio real; por encima de 0 NO se toca.
"""
import ast
import html
import io
import os
import re
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

fallos, n_ok = [], 0


def ok(q):
    global n_ok
    n_ok += 1
    print("  ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("  FALLO %s%s" % (q, ("  -> " + str(det)) if det != "" else ""))


def chk(q, cond, det=""):
    (ok(q) if cond else fallo(q, det))


def sec(x):
    print("\n%s" % x)


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from streamlit.testing.v1 import AppTest                          # noqa: E402

import fixture_guardado as FG                                     # noqa: E402
from core import auth as A                                        # noqa: E402
from core import belting, buffer_cut, rail_cut                    # noqa: E402
from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402


# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ El veredicto del heartbeat no se queda guardado")


class _Login:
    """La hoja Login de mentira, con el token que tenga en cada momento."""

    def __init__(self, token, espera=0.0):
        self.token, self.espera = token, espera

    def get_all_records(self, numericise_ignore=None):
        time.sleep(self.espera)
        return [{"User": "u1", "SessionToken": self.token, "SessionTime": "1"}]

    def update_cell(self, f, c, v):
        pass


def _espera(u, tok, tope=6.0):
    t0 = time.time()
    while time.time() - t0 < tope:
        with A._HB_LOCK:
            h = (A._HB.get((u, tok)) or {}).get("hilo")
        if h is None:
            break
        time.sleep(0.05)
    return A.heartbeat_resultado(u, tok)


_ogl = A._get_login_ws
try:
    A._HB.clear()
    _lw = _Login("TOKEN-DE-OTRO")                 # otro dispositivo tomó la cuenta
    A._get_login_ws = lambda: (_lw, None)
    A.heartbeat_en_fondo("u1", "TOK")
    chk("desplazado → False (expulsar), como en producción", _espera("u1", "TOK") is False)
    _lw.token = "TOK"                             # el token vuelve a valer
    chk("⚠️ SIN olvidar, el False sigue guardado aunque la hoja ya diga otra cosa "
        "(la sonda ve el fallo de producción)", A.heartbeat_resultado("u1", "TOK") is False)
    A.heartbeat_olvidar("u1", "TOK")
    chk("⚠️ tras olvidar, ya no hay veredicto (None: no se expulsa)",
        A.heartbeat_resultado("u1", "TOK") is None, A.heartbeat_resultado("u1", "TOK"))
    A.heartbeat_en_fondo("u1", "TOK")
    chk("...y el siguiente heartbeat pregunta a la hoja y dice True", _espera("u1", "TOK") is True)
    A.heartbeat_olvidar("nadie", "X")
    chk("olvidar lo que no existe no revienta", True)

    # Un hilo lento: se olvida a mitad, y su veredicto (viejo) no puede entrar después.
    A._HB.clear()
    _lw2 = _Login("TOKEN-DE-OTRO", espera=0.8)
    A._get_login_ws = lambda: (_lw2, None)
    A.heartbeat_en_fondo("u1", "TOK")
    time.sleep(0.15)
    A.heartbeat_olvidar("u1", "TOK")
    time.sleep(1.2)
    chk("⚠️ un hilo que termina DESPUÉS de olvidar no vuelve a meter su veredicto",
        A.heartbeat_resultado("u1", "TOK") is None, A._HB)
    A._get_login_ws = lambda: (_Login("TOK"), None)
    A.heartbeat_en_fondo("u1", "TOK")
    chk("...y el flujo normal sigue apuntando el suyo", _espera("u1", "TOK") is True)
finally:
    A._get_login_ws = _ogl
    A._HB.clear()

# ── `render_login` de verdad: la restauración por cookie olvida ──
GUION_L = r'''
import sys
sys.path.insert(0, r"%s")
import streamlit as st
from core import auth as A, auth_ui as AU, session_cookie as SC
SC.load = lambda: ("u1", "TOK")
A.validate_session = lambda u, t: {"usuario": u, "rol": "field", "nombre": "U", "grupo": "g",
                                   "token": t}
if not st.session_state.get("_sembrado"):
    st.session_state["_sembrado"] = True
    with A._HB_LOCK:
        A._HB[("u1", "TOK")] = {"hilo": None, "ok": False, "t": 1.0}
st.markdown("DENTRO=%%s" %% AU.render_login())
st.markdown("VEREDICTO=%%r" %% (A.heartbeat_resultado("u1", "TOK"),))
''' % RAIZ
from core import session_cookie as _SC                            # noqa: E402
_o = (_SC.load, A.validate_session)
try:
    at = AppTest.from_string(GUION_L, default_timeout=60)
    at.run()
    _md = [m.value for m in at.markdown]
    chk("`render_login` real: la cookie restaura la sesión", "DENTRO=True" in _md,
        (_md, [e.value for e in at.exception][:1]))
    chk("⚠️ ...y olvida el veredicto viejo (no la expulsaría al instante)",
        "VEREDICTO=None" in _md, _md)
finally:
    (_SC.load, A.validate_session) = _o
    A._HB.clear()

# ── app.py: olvida al expulsar ──
_tapp = ast.parse(_fuente("app.py"))
_exp = [n for n in _tapp.body if isinstance(n, ast.If)
        and "heartbeat_resultado" in ast.unparse(n.test)]
_cuerpo = [ast.unparse(x) for x in (_exp[0].body if _exp else [])]
_i_olv = next((i for i, x in enumerate(_cuerpo) if x.startswith("heartbeat_olvidar(")), None)
_i_pop = next((i for i, x in enumerate(_cuerpo) if "session_state.pop('auth'" in x), None)
chk("app.py olvida el veredicto al expulsar, ANTES de quitar la sesión",
    _i_olv is not None and _i_pop is not None and _i_olv < _i_pop, _cuerpo)

# ═════════════════════════════════════════════════════════════════
sec("2. Los dibujos de las herramientas, sin textos pisados")
_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)


def solapes(svg, margen=2.0):
    """Pares de textos de la MISMA línea que se pisan (ancho ≈ caracteres × tamaño × 0,52)."""
    ts = []
    for attrs, cuerpo in _RE.findall(svg):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', attrs))
        if "transform" in a:
            continue
        try:
            x, y, fs = float(a.get("x", 0)), float(a.get("y", 0)), float(a.get("font-size", 10))
        except ValueError:
            continue
        t = html.unescape(re.sub(r"<[^>]+>", "", cuerpo)).strip()
        if not t:
            continue
        w = len(t) * fs * (0.58 if a.get("font-weight") == "bold" else 0.52)
        anc = a.get("text-anchor", "start")
        x0 = x - w if anc == "end" else (x - w / 2 if anc == "middle" else x)
        ts.append((x0, x0 + w, y, fs, t))
    out = []
    for i in range(len(ts)):
        for j in range(i + 1, len(ts)):
            a, b = ts[i], ts[j]
            if abs(a[2] - b[2]) < min(a[3], b[3]) * 0.7 \
                    and min(a[1], b[1]) - max(a[0], b[0]) > margen:
                out.append((round(a[2]), a[4][:30], b[4][:30]))
    return out


chk("la sonda SÍ ve dos textos que se pisan (trampa nº12)",
    len(solapes('<svg><text x="10" y="50" font-size="8">una frase bastante larga aqui</text>'
                '<text x="60" y="50" font-size="8">otra encima de la primera</text></svg>')) == 1)
chk("...y no acusa a dos que no se tocan",
    solapes('<svg><text x="10" y="50" font-size="8">corta</text>'
            '<text x="200" y="50" font-size="8">lejos</text></svg>') == [])
_H = [100, 130, 120, 95, 110, 105]
_malos = {}
for n in range(1, 7):
    _c = {
        "buffers": buffer_cut.buffer_cut_svg(buffer_cut.compute_buffer_cut(120, _H[:n])),
        "belting": belting.belting_svg(belting.compute_belting(85, 14045, _H[:n])),
        "rieles caso 1": rail_cut.rail_cut_svg(
            rail_cut.compute_case1(1200, 900, 2, 3, [21000 + 100 * k for k in range(n)]),
            caso=1, n2500=2, n5000=3),
        "rieles caso 2": rail_cut.rail_cut_svg(
            {"elevadores": rail_cut.compute_case2(
                1200, 900, [{"RZ": 300, "RO": 320, "RF": 250, "RB": 260}] * n, "encima")},
            caso=2),
    }
    for k, s in _c.items():
        if "<text" not in s:
            _malos["%s n=%d" % (k, n)] = "SIN TEXTOS (no se midió nada)"
        elif solapes(s):
            _malos["%s n=%d" % (k, n)] = solapes(s)
chk("⚠️ Buffers, Belting y Rieles de 1 a 6 elevadores: ningún texto pisa a otro",
    not _malos, _malos)
_b1 = buffer_cut.buffer_cut_svg(buffer_cut.compute_buffer_cut(120, [100]))
chk("la nota de escala de Buffers sigue en el dibujo (en su propia línea)",
    "not to scale" in _b1 and len(set(re.findall(r'<text x="[\d.]+" y="([\d.]+)"',
                                                 _b1[_b1.rfind("<rect"):]))) >= 2, "")

# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ A 0% no hay inicio real")
_cab = P.ACTIVITIES_HEADERS
_recs = [{"ProjectID": "P", "Order": "1", "Progress": "40", "ActualStartDate": "2026-09-26",
          "ActualEndDate": ""},
         {"ProjectID": "P", "Order": "2", "Progress": "100", "ActualStartDate": "2026-09-20",
          "ActualEndDate": "2026-09-25"},
         {"ProjectID": "P", "Order": "3", "Progress": "0", "ActualStartDate": "",
          "ActualEndDate": ""}]
from core.num import col_letter                                   # noqa: E402
_LS = col_letter(P._ACOL["ActualStartDate"])
_LE = col_letter(P._ACOL["ActualEndDate"])


def _escrito(cambios):
    lote, _a = P._lote_avance(_recs, "P", cambios, "2026-09-30")
    return {x["range"]: x["values"][0][0] for x in lote}


_e = _escrito([{"orden": 1, "avance": 0}])
chk("⚠️ la actividad 1 vuelve a 0% → se BORRA su inicio real", _e.get(_LS + "2") == "", _e)
_e = _escrito([{"orden": 2, "avance": 0}])
chk("...y una al 100% que vuelve a 0% pierde inicio Y fin",
    _e.get(_LS + "3") == "" and _e.get(_LE + "3") == "", _e)
_e = _escrito([{"orden": 1, "avance": 60}])
chk("⚠️ por encima de 0 el inicio NO se toca (control)", (_LS + "2") not in _e, _e)
_e = _escrito([{"orden": 3, "avance": 0}])
chk("sin inicio que borrar no se escribe nada de más", (_LS + "4") not in _e, _e)
_e = _escrito([{"orden": 3, "avance": 30}])
chk("...y al arrancar se sigue fechando hoy, como siempre", _e.get(_LS + "4") == "2026-09-30",
    _e)


# La cadena entera: acreditar y desacreditar con el libro de mentira.
class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-09-30 10:00" if "%H" in f else "2026-09-30"

    def now(self, g=None):
        return self._T()


PRJ = {"ID": "PRJ-T", "Group": "cliente1", "Type": "Installation", "Name": "t",
       "StagePlanJSON": P.plan_nuevo("Installation", ()), "Progress": "0",
       "Status": "Planned", "ManualStatus": ""}
_plan = SP.plan_de_obra(PRJ)
_a7 = _plan[6]["actividades"][0]["nombre"]
_oc, _orc = SP.clock, SP._records
SP.clock, SP._records = _Reloj(), (lambda: [])
m = FG.montar(SP, P, PRJ)
try:
    SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": 7, "actividad": _a7, "pct": 100}],
                 quien="u", fecha="2026-09-26")
    _f7 = next(r for r in m.acts.registros() if r["ProjectID"] == "PRJ-T" and r["Order"] == "7")
    chk("al acreditar, la etapa empieza el día del trabajo", _f7["ActualStartDate"] == "2026-09-26",
        _f7)
    SP.acreditar("PRJ-T", "cliente1", PRJ, [{"etapa": 7, "actividad": _a7, "pct": 0}], quien="u")
    _f7 = next(r for r in m.acts.registros() if r["ProjectID"] == "PRJ-T" and r["Order"] == "7")
    chk("⚠️ al desmarcarlo todo, la etapa queda a 0% y SIN inicio real (el caso de PRJ-0015)",
        float(_f7["Progress"]) == 0.0 and _f7["ActualStartDate"] == "", _f7)
finally:
    m.restaurar()
    SP.clock, SP._records = _oc, _orc

print("\n" + "=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos),
                                 "TODO OK" if not fallos else "%d FALLOS" % len(fallos)))
sys.exit(1 if fallos else 0)
