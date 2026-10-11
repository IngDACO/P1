# -*- coding: utf-8 -*-
"""v523 · LA PANTALLA DONDE SE CONFIRMA LO QUE LA APP LEYÓ EN EL PARTE.

La regla del usuario (28/09/2026): «la app no asume nada sin consultar». Lo que protege:
  (a) ⚠️ que TODO empiece desmarcado y que se acredite EXACTAMENTE lo marcado — ni una
      casilla más, ni con el origen equivocado, ni sin el ID del parte en la nota (sin
      esa marca no se podrá medir nunca si la interpretación acierta);
  (b) ⚠️ que con varios ascensores cada trozo vaya solo a la obra que ÉL elija, que lo que
      no asigne no se proponga en ningún sitio, y que «L2» no se reparta hasta que diga
      si es un ascensor o un piso;
  (c) ⚠️ que separar la nota no convierta lo pendiente en propuesta (la cabecera
      «Pendings» viaja con cada trozo);
  (d) que el parte quede revisado SOLO si todo se escribió — si algo falla, la tarjeta
      sigue ahí — y que solo su AUTOR pueda revisarlo;
  (e) que la fila de `DailyLogs` siga cuadrando con la cabecera (v363) y que las dos
      columnas nuevas vayan al FINAL;
  (f) que lo propuesto sea siempre algo que `acreditar` acepta: se ejecuta la escritura
      REAL con la hoja sustituida, no una copia de su validación.
Todo EJECUTANDO (v378): la lógica contra el catálogo real y la tarjeta con `AppTest`,
marcando casillas y pulsando botones — importar no ejecuta nada.
"""
import ast
import datetime as _dt
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "campo000", "nombre": "Field Test",
                            "rol": "field", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    # Acepta el detalle y lo ignora: `(ok if cond else fallo)(q, det)` llama a las dos
    # con la misma firma (verif_v470, verif_v516).
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def sec(x):
    print("\n" + x)
    print("-" * 70)


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


from core import daily_log as DL                                  # noqa: E402
from core import parte_propuestas as PP                           # noqa: E402
from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402
from core.num import col_letter                                   # noqa: E402

PLAN = S.plan_de("Installation", ())
NOTA = ("Install day 12\nInstalled header\nShaft wiring done\nworked on the lights\n"
        "Pendings lifts to do:\ncube also needs to be installed")


def _en_plan(orden, nombre, plan=PLAN):
    """¿Está `nombre` en la etapa `orden` (posición 1-based del plan) de verdad?"""
    if not (1 <= orden <= len(plan)):
        return False
    e = plan[orden - 1]
    return (nombre in [a["nombre"] for a in e["actividades"]]
            or nombre in list(S.informativas(e.get("pista"), e.get("numero"))))


def _todas(p):
    """Todas las casillas que la pantalla ofrecería para UN destino."""
    out = [(f["orden"], f["actividad"]) for f in p["actividades"]]
    out += [(o["orden"], o["actividad"]) for e in p["etapas"] for o in e["opciones"]]
    out += [(o["orden"], o["actividad"]) for q in p["preguntas"] for o in q["opciones"]]
    return out


class _Reloj:
    """Formatea DE VERDAD (la lección de v516: un stub con cadena fija mide al stub)."""
    AHORA = _dt.datetime(2026, 9, 29, 17, 5, 9)

    def now(self, g=None):
        return self.AHORA

    def today(self, g=None):
        return self.AHORA.date()


# ═════════════════════════════════════════════════════════════════
sec("1. El contrato entre módulos")
chk("el origen de lo acreditado desde un parte es el MISMO texto en los dos módulos",
    SP.PARTE == PP.ORIGEN == "log", (SP.PARTE, PP.ORIGEN))
chk("...y no se confunde con lo marcado a mano", SP.PARTE != SP.MANUAL)
_V516 = ["ID", "Group", "ProjectID", "Date", "Author", "Text", "Source", "Created"]
chk("las 8 columnas de v516 siguen en su sitio (v363)", DL.HEADERS[:8] == _V516,
    DL.HEADERS[:8])
# ⚠️ v524 · `[8:10]` y no `[8:]`: `Proposals` va DETRÁS (la vigila verif_v524). Lo que
# importa aquí es el principio —las de v523 van tras las de v516—, no que sean las últimas.
chk("...y las dos nuevas van detrás", DL.HEADERS[8:10] == ["Reviewed", "ReviewedBy"],
    DL.HEADERS[8:])
# ⚠️ El nombre de la actividad basta para saber su etapa SOLO si no se repite en el plan.
for _tipo in P.TIPOS:
    try:
        _conds = tuple(c["nombre"] for p in S.pistas_de_tipo(_tipo)
                       for c in S.condicionales(p))
        _pl = S.plan_de(_tipo, _conds)
    except Exception as e:
        _pl = []
        if _tipo in (P.TIPO_INSTALACION, P.TIPO_RIPOUT, P.TIPO_RIPOUT_INST):
            fallo("el plan de «%s» no se puede construir" % _tipo, e)
        continue
    _nom = [a["nombre"] for e in _pl for a in e["actividades"]]
    _nom += [n for e in _pl for n in S.informativas(e.get("pista"), e.get("numero"))]
    if not _nom:
        continue
    _rep = sorted({n for n in _nom if _nom.count(n) > 1})
    chk("«%s»: ningún nombre de actividad se repite (%d nombres, con condicionales)"
        % (_tipo, len(_nom)), not _rep, _rep)

# ═════════════════════════════════════════════════════════════════
sec("2. Las propuestas, contra el catálogo REAL")
p = PP.propuestas(NOTA, PLAN, {})
_a = {f["actividad"]: f for f in p["actividades"]}
chk("propone «Install headers» por «Installed header»", "Install headers" in _a,
    list(_a))
if "Install headers" in _a:
    f = _a["Install headers"]
    chk("...en el ORDEN del plan, que es lo que entiende `acreditar`",
        _en_plan(f["orden"], "Install headers"), f["orden"])
    chk("...con la LÍNEA que la respalda", f["pruebas"] == ["Installed header"], f["pruebas"])
    chk("...sin hacer todavía", f["hecha"] is False)
_et = {e["termino"]: e for e in p["etapas"]}
chk("«shaft wiring» a secas → la etapa entera, como lista", "shaft wiring" in _et, list(_et))
if "shaft wiring" in _et:
    _ops = _et["shaft wiring"]["opciones"]
    chk("...con al menos 5 actividades", len(_ops) >= 5, len(_ops))
    chk("...todas de la etapa que dice", all(_en_plan(o["orden"], o["actividad"]) for o in _ops))
_q = {q["termino"]: q for q in p["preguntas"]}
chk("«lights» se PREGUNTA (cinco sitios posibles)", "lights" in _q, list(_q))
if "lights" in _q:
    chk("...con opciones de varias etapas, cada una en la suya",
        len({o["orden"] for o in _q["lights"]["opciones"]}) >= 3
        and all(_en_plan(o["orden"], o["actividad"]) for o in _q["lights"]["opciones"]))
chk("lo de «Pendings» se ENSEÑA como pendiente…",
    any("cube also needs to be installed" in x["pruebas"] for x in p["pendientes"]),
    p["pendientes"])
chk("...y no se propone", "Install electrical boxes" not in [a for _, a in _todas(p)])
chk("hay algo que confirmar", p["hay_algo"] is True)

# ⚠️ Toda casilla que la pantalla ofrezca tiene que ser aceptable para `acreditar`:
# se comprueba sobre un surtido de notas, no sobre una.
_NOTAS = [NOTA, "Bridged the landing door circuit", "Programmed the controller parameters",
          "Installed the switch light\nworked on the lights", "Shaft wiring done\nInstalled cable tray",
          "Started installing headers", "Installed headers yesterday", "car frame assembled",
          "Installed sills L1-L6, headers L1-L4"]
_ofrecidas = {x for n in _NOTAS for x in _todas(PP.propuestas(n, PLAN, {}))}
# Suelo contra el paso en vacío (trampa nº1), no una cifra a clavar: hoy son 16.
chk("el surtido ofrece bastantes casillas para que esto signifique algo (≥ 12)",
    len(_ofrecidas) >= 12, len(_ofrecidas))
chk("...y TODAS están en su etapa del plan", all(_en_plan(o, n) for o, n in _ofrecidas),
    [x for x in _ofrecidas if not _en_plan(*x)][:3])

# ⚠️ Cada «NO aparece X» lleva su control «X SÍ aparece cuando debe» (trampa nº1/nº12):
# sin él, un «no está» puede ser solo que nunca iba a estar.
chk("control: la lista de «shaft wiring» a secas SÍ incluye «Install cable tray»",
    "Install cable tray" in [o["actividad"] for e in
                             PP.propuestas("Shaft wiring done", PLAN, {})["etapas"]
                             for o in e["opciones"]])
chk("control: «worked on the lights» a secas SÍ ofrece «Switch light»",
    "Switch light" in [o["actividad"] for q in
                       PP.propuestas("worked on the lights", PLAN, {})["preguntas"]
                       for o in q["opciones"]])
chk("control: «Install headers» fuera de «Pendings» SÍ se propone",
    "Install headers" in [a for _, a in _todas(PP.propuestas("Install headers", PLAN, {}))])
chk("control: «L2 call button» SÍ propone «Call button wiring» (lo que se retiene existe)",
    "Call button wiring" in [a for _, a in _todas(PP.propuestas("L2 call button", PLAN, {}))])
p = PP.propuestas("Shaft wiring done\nInstalled cable tray", PLAN, {})
_suelta = [f["actividad"] for f in p["actividades"]]
_de_etapa = [o["actividad"] for e in p["etapas"] for o in e["opciones"]]
chk("una actividad nombrada suelta sale arriba…", "Install cable tray" in _suelta, _suelta)
chk("...y NO se repite dentro de la lista de su etapa",
    bool(_de_etapa) and "Install cable tray" not in _de_etapa, _de_etapa)
p = PP.propuestas("Installed the switch light\nworked on the lights", PLAN, {})
_suelta = [f["actividad"] for f in p["actividades"]]
_de_preg = [o["actividad"] for q in p["preguntas"] for o in q["opciones"]]
chk("«switch light» suelta…", "Switch light" in _suelta, _suelta)
chk("...no se repite entre las opciones de «lights»",
    bool(_de_preg) and "Switch light" not in _de_preg, _de_preg)

p = PP.propuestas("Bridged the landing door circuit", PLAN, {})
_b = [f for f in p["actividades"] if f["actividad"].startswith("Bridge landing door")]
chk("una informativa se propone marcada como que NO cuenta",
    len(_b) == 1 and _b[0]["cuenta"] is False, [(f["actividad"], f["cuenta"]) for f in p["actividades"]])
p = PP.propuestas("Started installing headers", PLAN, {})
chk("«started» lleva el aviso de incompleto",
    [f["aviso"] for f in p["actividades"]] == ["incompleto"], p["actividades"])
p = PP.propuestas("Installed headers yesterday", PLAN, {})
chk("«yesterday» lleva el aviso de otro día",
    [f["aviso"] for f in p["actividades"]] == ["otro_dia"], p["actividades"])
p = PP.propuestas("Pendings:\nInstall headers", PLAN, {})
chk("bajo «Pendings» no se propone NADA", not _todas(p) and p["hay_algo"] is False, _todas(p))
p = PP.propuestas("Removed the old machine", PLAN, {})
chk("quitar algo en una obra sin desmontaje: se pregunta, no se acredita",
    not _todas(p) and len(p["retiradas"]) == 1, (_todas(p), p["retiradas"]))

_o7 = next((f["orden"] for f in PP.propuestas("Installed header", PLAN, {})["actividades"]), 0)
p = PP.propuestas("Installed header", PLAN, {(_o7, "Install headers"): 100.0})
chk("lo ya acreditado sale como hecho", [f["hecha"] for f in p["actividades"]] == [True])
chk("...y si es lo único, no hay nada que confirmar", p["hay_algo"] is False)
p = PP.propuestas("Installed header", PLAN, {(_o7, "Install headers"): 40.0})
chk("un crédito parcial NO cuenta como hecho", [f["hecha"] for f in p["actividades"]] == [False])

# ═════════════════════════════════════════════════════════════════
sec("3. Lo marcado → lo que recibe `acreditar`")
c = PP.creditos([(7, "Install headers"), ("11", "Lights"), (7, "Install headers")], "LOG-0042")
chk("sin repetidos", len(c) == 2, c)
chk("...al 100% (el catálogo es binario, v514)", all(x["pct"] == 100.0 for x in c))
chk("...con el ID del parte en la nota", all(x["nota"] == "LOG-0042" for x in c))
chk("...y el orden como entero", [x["etapa"] for x in c] == [7, 11], c)
chk("nada marcado → nada", PP.creditos([], "LOG-1") == [] and PP.creditos(None, "LOG-1") == [])

# ⚠️ Y la ESCRITURA de verdad: `acreditar` con la hoja sustituida. Así lo que se prueba
# es su validación, no una copia que el guardián lleve aparte.


# ⚠️ v528 · Con el LIBRO de mentira compartido (`fixture_guardado`): desde v528 `acreditar`
# lee y escribe sus tres hojas en lote y ya no llama a `save_field_progress`, así que
# sustituir esa función no probaba nada. «El avance se recalcula» se mira ahora en lo que
# llega ESCRITO a `Activities.Progress`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixture_guardado as FG                                     # noqa: E402

_orig = {k: getattr(SP, k) for k in ("_records", "plan_de_obra", "version_desfasada",
                                     "clock")}
_m = None
try:
    SP._records = lambda: []
    SP.plan_de_obra = lambda prj: PLAN
    SP.version_desfasada = lambda prj: ""
    SP.clock = _Reloj()
    _m = FG.montar(SP, P, {"ID": "PRJ-9001"}, plan=PLAN)
    _w = _m.sp
    _todo = sorted(_ofrecidas)
    _ok, _msg = SP.acreditar("PRJ-9001", "cliente1", {"ID": "PRJ-9001"},
                             PP.creditos(_todo, "LOG-0042"), quien="campo000", origen=SP.PARTE)
    chk("`acreditar` ACEPTA todas las casillas del surtido (%d)" % len(_todo), _ok, _msg)
    _r = [dict(zip(SP.HEADERS, f)) for f in _w.nuevas]
    chk("...una fila por crédito, con tantas columnas como la cabecera",
        len(_r) == len(_todo) and all(len(f) == len(SP.HEADERS) for f in _w.nuevas),
        (len(_r), len(_todo)))
    chk("...con origen «log»", {x["Source"] for x in _r} == {"log"}, {x["Source"] for x in _r})
    chk("...y el ID del parte en la nota", {x["Note"] for x in _r} == {"LOG-0042"})
    _av = _m.escrituras_avance()
    chk("...y el avance de las etapas con peso se recalcula (una escritura)",
        len(_av) == 1 and len(_av[0]) >= 3, _av[:1])
finally:
    for k, v in _orig.items():
        setattr(SP, k, v)
    if _m is not None:
        _m.restaurar()

# ═════════════════════════════════════════════════════════════════
sec("4. Varios ascensores: se reparte SOLO lo que el usuario asignó")
TX = "lift 3 installed headers\nlift 1 installed sills\nL2 call button"
r = PP.reparto(TX, {"": "P1", "3": "P3", "1": "P1"}, sin_responder=["L2"])
chk("«L2» sin contestar: su línea no va a NINGUNA obra",
    all("L2 call button" not in v for v in r.values()), r)
chk("...y lo demás va a donde se asignó",
    r.get("P3") == "lift 3 installed headers" and r.get("P1") == "lift 1 installed sills", r)
r = PP.reparto(TX, {"": "P1", "3": "P3", "1": "P1"})
chk("«L2» es un piso → la línea va con las que no nombran ascensor",
    "L2 call button" in r.get("P1", ""), r)
r = PP.reparto(TX, {"": "P1", "3": "P3", "1": "P1", "L2": "P2"}, tambien=["L2"])
chk("«L2» es un ascensor → va a SU obra", r.get("P2") == "L2 call button", r)
r = PP.reparto(TX, {"": "P1", "1": "P1"}, tambien=["L2"])
chk("un ascensor SIN obra elegida no se propone en ningún sitio",
    all("lift 3" not in v and "L2" not in v for v in r.values()) and set(r) == {"P1"}, r)
# ⚠️ «L2» solo en su línea es una CABECERA: lo de debajo depende de la respuesta igual que
# la línea que lo nombra. Retener solo esa línea dejaba lo de debajo en la obra del parte.
TXC = "L2\ninstalled headers\nlift 3 installed sills"
chk("`lineas_de`: con «L2» de cabecera, lo que cuelga de él",
    PP.lineas_de(TXC, "L2") == ["installed headers"], PP.lineas_de(TXC, "L2"))
chk("`lineas_de`: y con «lift 3», su línea",
    PP.lineas_de(TX, "3") == ["lift 3 installed headers"], PP.lineas_de(TX, "3"))
r = PP.reparto(TXC, {"": "P1", "3": "P3"}, sin_responder=["L2"])
chk("«L2» de cabecera sin contestar: lo de DEBAJO tampoco va a ninguna obra",
    "installed headers" not in r.get("P1", "") and r.get("P3") == "lift 3 installed sills", r)
r = PP.reparto(TXC, {"": "P1", "3": "P3"})
chk("control: contestado «piso», lo de debajo va a la obra del parte",
    "installed headers" in r.get("P1", ""), r)
chk("`propone_algo`: una línea que no propone nada → no hay nada que preguntar",
    PP.propone_algo(["L2 waiting on the scaffold"], PLAN) is False
    and PP.propone_algo([], PLAN) is False)
chk("...y una que sí, sí", PP.propone_algo(["L2 call button"], PLAN) is True)
_o7s = next((f["orden"] for f in PP.propuestas("Installed sills", PLAN, {})["actividades"]), 0)
chk("...esté ya hecho o no (lo hecho depende de la obra de DESTINO)",
    PP.propone_algo(["lift 3 installed sills"], PLAN) is True and _o7s > 0)
r = PP.reparto("lift 3 installed headers\nPendings:\nlift 3 installed sills\nlift 1 sills",
               {"": "P1", "3": "P3", "1": "P1"})
chk("la cabecera «Pending» viaja a CADA trozo que tenga pendientes",
    r.get("P3", "").splitlines() == ["lift 3 installed headers", "Pending:",
                                     "lift 3 installed sills"]
    and r.get("P1", "").splitlines() == ["Pending:", "lift 1 sills"], r)
# ⚠️ La línea pendiente tiene que ser una que SIN cabecera SÍ se propondría: con
# «lift 3 sills» (que no casa con nada) esta comprobación pasaba en vacío (trampa nº1).
chk("control: «lift 3 installed sills» suelta SÍ se propone",
    "Install sills" in [a for _, a in _todas(PP.propuestas("lift 3 installed sills", PLAN, {}))])
_p3 = PP.propuestas(r.get("P3", ""), PLAN, {})
chk("...así que el trozo separado NO convierte lo pendiente en propuesta",
    "Install sills" not in [a for _, a in _todas(_p3)]
    and "Install headers" in [a for _, a in _todas(_p3)], _todas(_p3))

# ═════════════════════════════════════════════════════════════════
sec("5. La revisión del parte (hoja sustituida)")


class _WSdl:
    def __init__(self, filas):
        self.filas = [list(f) for f in filas]
        self.lotes = []
        self.revienta = False

    def get_all_records(self, numericise_ignore=None):
        if self.revienta:
            raise RuntimeError("429 quota exceeded")
        return [dict(zip(DL.HEADERS, f + [""] * (len(DL.HEADERS) - len(f)))) for f in self.filas]

    def append_row(self, fila, value_input_option=None):
        self.filas.append(list(fila))

    def batch_update(self, datos, value_input_option=None):
        self.lotes.append(datos)


_od = {k: getattr(DL, k) for k in ("_ws", "_invalidate", "clock", "_next_id")}
try:
    h = _WSdl([["LOG-0001", "cliente1", "PRJ-9001", "2026-09-29", "juan", "x", "manual",
                "2026-09-29 09:00:00", "", ""],
               ["LOG-0002", "cliente1", "PRJ-9001", "2026-09-29", "ana", "y", "manual",
                "2026-09-29 10:00:00", "", ""]])
    DL._ws = lambda: h
    DL._invalidate = lambda: None
    DL.clock = _Reloj()
    DL._next_id = lambda recs: "LOG-0003"
    _ok, _lid = DL.crear("PRJ-9001", "cliente1", "Installed header", "juan")
    chk("`crear` escribe una fila tan larga como la cabecera (v363)",
        _ok and len(h.filas[-1]) == len(DL.HEADERS), (len(h.filas[-1]), len(DL.HEADERS)))
    chk("...con la revisión VACÍA (un parte nuevo está sin revisar)",
        h.filas[-1][8:10] == ["", ""], h.filas[-1][8:])
    chk("`revisado` dice que no", DL.revisado(dict(zip(DL.HEADERS, h.filas[-1]))) is False)

    _ok, _m = DL.marcar_revisado("LOG-0002", "juan")
    chk("otro que no es el autor NO puede revisarlo", not _ok and not h.lotes, _m)
    _ok, _m = DL.marcar_revisado("LOG-0002", "ana")
    chk("su autor sí", _ok, _m)
    _l = h.lotes[-1] if h.lotes else []
    _rng = [x["range"] for x in _l]
    # ⚠️ v524 · `[:2]`: la misma escritura lleva ahora también el registro (`Proposals`,
    # vigilado en verif_v524). Aquí se mira lo de v523: fecha y autor, en su sitio.
    chk("...escribe `Reviewed` y `ReviewedBy` en SUS columnas y en SU fila",
        _rng[:2] == ["%s3" % col_letter(DL.HEADERS.index("Reviewed") + 1),
                     "%s3" % col_letter(DL.HEADERS.index("ReviewedBy") + 1)], _rng)
    chk("...con la hora en segundos y quién",
        [x["values"] for x in _l][:2] == [[["2026-09-29 17:05:09"]], [["ana"]]],
        [x["values"] for x in _l])
    chk("`revisado` lo reconoce", DL.revisado({"Reviewed": "2026-09-29 17:05:09"}) is True)
    _ok, _m = DL.marcar_revisado("LOG-9999", "ana")
    chk("un parte que no existe no se marca", not _ok, _m)
    h.revienta = True
    _n = len(h.lotes)
    _ok, _m = DL.marcar_revisado("LOG-0001", "juan")
    chk("si la hoja falla, NO dice que revisó", not _ok and len(h.lotes) == _n, _m)
finally:
    for k, v in _od.items():
        setattr(DL, k, v)

_oc = SP.creditos
try:
    SP.creditos = lambda pid, etapa=None: [
        {"ProjectID": pid, "StageOrder": "7", "Activity": "Install headers", "Pct": "100",
         "Note": "LOG-0042", "Source": "log"},
        {"ProjectID": pid, "StageOrder": "11", "Activity": "Lights", "Pct": "0",
         "Note": "LOG-0042", "Source": "log"},
        {"ProjectID": pid, "StageOrder": "7", "Activity": "Install sills", "Pct": "100",
         "Note": "LOG-0042", "Source": "manual"},
        {"ProjectID": pid, "StageOrder": "7", "Activity": "Install frames", "Pct": "100",
         "Note": "LOG-0043", "Source": "log"}]
    _dp = SP.de_parte("PRJ-9001", "LOG-0042")
    chk("`de_parte`: solo lo que salió de ESE parte, con origen «log» y aún acreditado",
        [x["Activity"] for x in _dp] == ["Install headers"], [x["Activity"] for x in _dp])
finally:
    SP.creditos = _oc

# ═════════════════════════════════════════════════════════════════
sec("6. Estático: lo que la ejecución no alcanza")
_src = io.open("core/daily_log_ui.py", encoding="utf-8").read()
_t = ast.parse(_src)
_fn = {n.name: n for n in _t.body if isinstance(n, ast.FunctionDef)}


def _llama(fn, attr):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call)
            and (getattr(n.func, "attr", "") == attr or getattr(n.func, "id", "") == attr)]


chk("la vista del admin NO pinta la tarjeta (no confirma por el autor)",
    "render_admin" in _fn and not _llama(_fn["render_admin"], "_propuestas"))
# ⚠️ Al confirmar se vuelve a mirar que cada destino sea una obra SUYA, y ANTES de acreditar.
_pr = _fn.get("_propuestas")
_ok_dest = False
if _pr is not None:
    for n in ast.walk(_pr):
        if isinstance(n, ast.For):
            _ifs = [i for i, s in enumerate(n.body) if isinstance(s, ast.If)
                    and isinstance(s.test, ast.Compare)
                    and any(isinstance(o, ast.NotIn) for o in s.test.ops)
                    and getattr(s.test.comparators[0], "id", "") == "_mias"
                    and any(isinstance(x, ast.Continue) for x in s.body)]
            _acr = [i for i, s in enumerate(n.body) if _llama(s, "acreditar")]
            if _ifs and _acr and min(_ifs) < min(_acr):
                _ok_dest = True
chk("al confirmar se comprueba que el destino es una obra SUYA antes de `acreditar`",
    _ok_dest)
_c = [n for n in _llama(_pr, "acreditar")] if _pr is not None else []
chk("...y se acredita con `origen=SP.PARTE`",
    len(_c) == 1 and any(k.arg == "origen" and ast.unparse(k.value) == "SP.PARTE"
                         for k in _c[0].keywords), [ast.unparse(x) for x in _c])

# ═════════════════════════════════════════════════════════════════
sec("7. La tarjeta EJECUTADA (AppTest): marcar, confirmar, fallar, admin")
from streamlit.testing.v1 import AppTest                          # noqa: E402

APP = r'''
import datetime as _dt
import sys
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")
import streamlit as st
st.session_state.setdefault("auth", {"usuario": "campo000", "nombre": "Field Test",
                                     "rol": "field", "grupo": "cliente1"})
from core import clock, daily_log as DL, daily_log_ui as DLU
from core import projects as P, stage_progress as SP, stages as S
# v559 · los partes enseñan al autor y a quien revisó por su NOMBRE (`daily_log_ui._nombre`
# lee `auth.list_users`): se sustituye para no depender de la hoja real.
from core import auth as _A
_A.list_users = lambda *a, **k: [{"User": "campo000", "Name": "Field Test"}]

PLAN = S.plan_de("Installation", ())
HOY = "2026-09-29"
PRJS = {"PRJ-9001": "ZZ Test tower · Lift 1", "PRJ-9003": "ZZ Test tower · Lift 3",
        "PRJ-9002": "ZZ Other job"}
ss = st.session_state
ss.setdefault("_rev", {})
ss.setdefault("_cred", [])
ss.setdefault("_hecho", {"PRJ-9001": {(7, "Install sills"): 100.0}})
ss.setdefault("_falla", False)
ss.setdefault("_vista", "campo")
LOGS = [
    {"ID": "LOG-9009", "Author": "campo000", "Created": HOY + " 17:20:00",
     "Text": "lift 3 installed sills\nlift 1 installed sills"},
    {"ID": "LOG-9008", "Author": "campo000", "Created": HOY + " 17:15:00",
     "Text": "lift 2 was in use by the builders\nlift 1 installed sills\n"
             "lift 3 installed headers"},
    {"ID": "LOG-9007", "Author": "campo000", "Created": HOY + " 17:10:00",
     "Text": "L2 waiting on the scaffold\nInstalled header"},
    {"ID": "LOG-9006", "Author": "campo000", "Created": HOY + " 17:00:00",
     "Text": "Waiting on the scaffold all day"},
    {"ID": "LOG-9005", "Author": "campo000", "Created": HOY + " 16:55:00",
     "Text": "Installed header", "Reviewed": HOY + " 16:56:00", "ReviewedBy": "campo000"},
    {"ID": "LOG-9004", "Author": "campo000", "Created": HOY + " 16:50:00",
     "Text": "L3 installed headers"},
    {"ID": "LOG-9003", "Author": "campo000", "Created": HOY + " 16:40:00",
     "Text": "lift 3 installed headers\nlift 1 installed sills\nL2 call button"},
    {"ID": "LOG-9002", "Author": "campo000", "Created": HOY + " 16:30:00",
     "Text": "Install day 12\nInstalled header\nShaft wiring done\nworked on the lights\n"
             "Pendings lifts to do:\ncube also needs to be installed"},
    {"ID": "LOG-9001", "Author": "otro01", "Created": HOY + " 09:10:00",
     "Text": "Installed header\nShaft wiring done"},
]


def _partes(pid, autor=None, dia=None):
    out = []
    for r in LOGS:
        _r = dict(r, ProjectID="PRJ-9001", Date=HOY)
        if r["ID"] in ss["_rev"]:
            _r["Reviewed"], _r["ReviewedBy"] = HOY + " 17:30:00", ss["_rev"][r["ID"]]
        out.append(_r)
    return out


def _acreditar(pid, grupo, prj, creditos, quien="", origen=SP.MANUAL, fecha=None):
    # v525 · la pantalla pasa también la fecha del parte (la vigila verif_v525).
    ss["_cred"].append({"pid": pid, "quien": quien, "origen": origen, "fecha": fecha,
                        "creditos": [dict(c) for c in creditos]})
    if ss["_falla"]:
        return False, "boom: the sheet said no"
    for c in creditos:
        ss["_hecho"].setdefault(pid, {})[(c["etapa"], c["actividad"])] = 100.0
    return True, "ok"


def _revisar(lid, quien, propuestas=""):
    # v524 · la pantalla pasa también el registro de lo ofrecido y lo marcado.
    ss["_rev"][lid] = quien
    ss.setdefault("_reg", {})[lid] = propuestas
    return True, "Reviewed."


DL.partes = _partes
DL.dias_cubiertos = lambda pid: 1
DL.marcar_revisado = _revisar
DL.crear = lambda *a, **k: (True, "LOG-X")
clock.today = lambda grupo=None: _dt.date(2026, 9, 29)
P.get_project = lambda pid: {"ID": pid, "Name": PRJS.get(pid, pid), "Type": "Installation"}
P.list_projects_for_field = lambda u, g=None, incluir_internos=False: [
    {"ID": k, "Name": v} for k, v in PRJS.items()]
SP.plan_de_obra = lambda prj: PLAN
SP.version_desfasada = lambda prj: ""
SP.acreditado = lambda pid: dict(ss["_hecho"].get(pid, {}))
SP.acreditar = _acreditar
SP.de_parte = lambda pid, lid: [c for x in ss["_cred"] for c in x["creditos"]
                                if c["nota"] == lid and x["pid"] == pid]
if ss["_vista"] == "admin":
    DLU.render_admin("PRJ-9001", "cliente1", key_prefix="adm")
else:
    DLU.render_campo("PRJ-9001", "cliente1", "campo000", key_prefix="fld")
'''


def _app(**estado):
    at = AppTest.from_string(APP, default_timeout=90)
    for k, v in estado.items():
        at.session_state[k] = v
    return at.run()


def _cb(at, pre):
    return [c for c in at.checkbox if (c.key or "").startswith(pre)]


def _bt(at, key):
    return next((b for b in at.button if b.key == key), None)


def _txt(at):
    return [m.value for m in at.markdown] + [c.value for c in at.caption]


at = _app()
chk("la pantalla se pinta sin excepción", not at.exception, [e.value for e in at.exception][:1])
_cards = [k for k in ("LOG-9009", "LOG-9008", "LOG-9007", "LOG-9006", "LOG-9005", "LOG-9004",
                      "LOG-9003", "LOG-9002", "LOG-9001")
          if _bt(at, "fld_pp_%s_ok" % k) is not None]
chk("tarjeta en los partes PROPIOS y sin revisar que tienen algo — y en ninguno más",
    _cards == ["LOG-9009", "LOG-9008", "LOG-9007", "LOG-9004", "LOG-9003", "LOG-9002"], _cards)
_todas_cb = _cb(at, "fld_pp_")
# ⚠️ La cifra se DERIVA de la lógica (trampa nº16), no se clava: la tarjeta tiene que
# ofrecer exactamente lo que `propuestas` saca — ni una casilla perdida ni una de más.
_esp = len(_todas(PP.propuestas(NOTA, PLAN, {})))
chk("la tarjeta ofrece EXACTAMENTE las casillas que salen de `propuestas` (%d)" % _esp,
    _esp >= 10 and len(_cb(at, "fld_pp_LOG-9002_")) == _esp,
    (len(_cb(at, "fld_pp_LOG-9002_")), _esp))
# ⚠️ No se pregunta lo que no cambia nada.
chk("«L2 waiting on the scaffold»: NO se pregunta si «L2» es ascensor o piso",
    not [r for r in at.radio if r.key == "fld_pp_LOG-9007_dud_L2"])
chk("...y lo demás del parte se propone en su obra, sin más",
    "fld_pp_LOG-9007_PRJ-9001_a_7_Install headers" in [c.key for c in at.checkbox])
_s8 = sorted(s.key for s in at.selectbox if (s.key or "").startswith("fld_pp_LOG-9008_dest_"))
chk("«lift 2 was in use by the builders»: sin selector de obra para el 2 (solo 1 y 3)",
    _s8 == ["fld_pp_LOG-9008_dest_1", "fld_pp_LOG-9008_dest_3"], _s8)
# ⚠️ Lo hecho depende de la obra de DESTINO: en PRJ-9001 los sills ya están, pero en el
# ascensor 3 no. Con lo de esta obra, la tarjeta ni salía y el trabajo de lift 3 se perdía.
_s9 = sorted(s.key for s in at.selectbox if (s.key or "").startswith("fld_pp_LOG-9009_dest_"))
chk("sills ya hechos en ESTA obra no esconden los de lift 3: hay tarjeta, y obra para cada uno",
    _s9 == ["fld_pp_LOG-9009_dest_1", "fld_pp_LOG-9009_dest_3"], _s9)
chk("⚠️ TODAS empiezan DESMARCADAS", all(c.value is False for c in _todas_cb),
    [c.key for c in _todas_cb if c.value][:3])
_b = _bt(at, "fld_pp_LOG-9002_ok")
chk("«Confirmar» desactivado mientras no haya nada marcado",
    _b is not None and _b.proto.disabled is True)
chk("el parte se enseña con sus SALTOS de línea",
    any("Installed header  \nShaft wiring done" in x for x in _txt(at)))
# ⚠️ CADUCADO por v559: quien revisó sale por su NOMBRE (antes el login «campo000»).
chk("el parte revisado enseña su estado, no la tarjeta",
    any("Proposals reviewed by Field Test" in x for x in _txt(at)))
chk("«L2» sin contestar: «Call button wiring» no se propone en su tarjeta",
    not [c for c in _cb(at, "fld_pp_LOG-9003_") if c.key.endswith("Call button wiring")],
    [c.key for c in _cb(at, "fld_pp_LOG-9003_")])
chk("...y se le dice por qué", any("Until you answer" in x and "«L2»" in x for x in _txt(at)))
chk("ascensores sin obra elegida: nada propuesto todavía en la tarjeta de varios",
    not _cb(at, "fld_pp_LOG-9003_"), [c.key for c in _cb(at, "fld_pp_LOG-9003_")])

# ── marcar tres (una repetida en dos sitios) y confirmar ──
K2 = "fld_pp_LOG-9002_PRJ-9001"
for _k in ("%s_a_7_Install headers" % K2, "%s_e_11_Lights" % K2, "%s_q_lights_11_Lights" % K2):
    _c = [c for c in at.checkbox if c.key == _k]
    if not _c:
        fallo("no aparece la casilla %s" % _k)
    else:
        _c[0].check()
at.run()
_b = _bt(at, "fld_pp_LOG-9002_ok")
chk("tres marcas de DOS actividades → «Confirm the 2 ticked»",
    _b is not None and "Confirm the 2 ticked" in _b.proto.label and _b.proto.disabled is False,
    _b.proto.label if _b is not None else None)
if _b is not None:
    _b.click()
    at.run()
_cr = at.session_state["_cred"] if "_cred" in at.session_state else []
chk("`acreditar` recibe UNA llamada, para la obra del parte", len(_cr) == 1
    and _cr[0]["pid"] == "PRJ-9001", _cr)
if _cr:
    chk("...con EXACTAMENTE lo marcado",
        sorted((c["etapa"], c["actividad"]) for c in _cr[0]["creditos"])
        == [(7, "Install headers"), (11, "Lights")], _cr[0]["creditos"])
    chk("...con origen «log» y el ID del parte en la nota",
        _cr[0]["origen"] == "log" and {c["nota"] for c in _cr[0]["creditos"]} == {"LOG-9002"},
        _cr[0])
    chk("...y quién lo confirmó", _cr[0]["quien"] == "campo000")
chk("el parte queda revisado por su autor",
    at.session_state["_rev"].get("LOG-9002") == "campo000", dict(at.session_state["_rev"]))
chk("...y su tarjeta desaparece", _bt(at, "fld_pp_LOG-9002_ok") is None)

# ── varios ascensores: contestar «L2», elegir obras, confirmar ──
_r = [r for r in at.radio if r.key == "fld_pp_LOG-9003_dud_L2"]
chk("se pregunta si «L2» es ascensor o piso, SIN respuesta por defecto",
    len(_r) == 1 and _r[0].value is None)
if _r:
    _r[0].set_value("lift")
    at.run()
_sel = {s.key: s for s in at.selectbox if (s.key or "").startswith("fld_pp_LOG-9003_dest_")}
chk("un selector de obra por ascensor (3, 1 y L2), vacíos",
    sorted(_sel) == ["fld_pp_LOG-9003_dest_1", "fld_pp_LOG-9003_dest_3",
                     "fld_pp_LOG-9003_dest_L2"] and all(s.value is None for s in _sel.values()),
    {k: s.value for k, s in _sel.items()})
if len(_sel) == 3:
    _sel["fld_pp_LOG-9003_dest_3"].set_value("PRJ-9003")
    _sel["fld_pp_LOG-9003_dest_1"].set_value("PRJ-9001")
    at.run()
_k3 = [c.key for c in _cb(at, "fld_pp_LOG-9003_")]
chk("lift 3 → propuesto en SU obra", "fld_pp_LOG-9003_PRJ-9003_a_7_Install headers" in _k3, _k3)
chk("L2 sin obra → no se propone en ningún sitio",
    not [k for k in _k3 if k.endswith("Call button wiring")], _k3)
chk("lo ya acreditado en lift 1 no se vuelve a ofrecer como casilla",
    not [k for k in _k3 if k.endswith("Install sills")], _k3)
chk("...pero SÍ se enseña, como ya acreditado (no desaparece sin más)",
    any("Install sills" in x and "already credited" in x for x in _txt(at)))
chk("cada trozo lleva el nombre de su obra",
    any("→ ZZ Test tower · Lift 3" in x for x in _txt(at))
    and any("→ ZZ Test tower · Lift 1" in x for x in _txt(at)))

# ── un solo ascensor que no es esta obra: también se nombra ──
_r = [r for r in at.radio if r.key == "fld_pp_LOG-9004_dud_L3"]
if _r:
    _r[0].set_value("lift")
    at.run()
    _s = [s for s in at.selectbox if s.key == "fld_pp_LOG-9004_dest_L3"]
    if _s:
        _s[0].set_value("PRJ-9003")
        at.run()
_n4 = [m.value for m in at.markdown]
chk("«L3» a otra obra, aunque sea el único destino, sale con su nombre",
    "fld_pp_LOG-9004_PRJ-9003_a_7_Install headers" in [c.key for c in _cb(at, "fld_pp_LOG-9004_")]
    and sum(1 for x in _n4 if x.strip() == "**→ ZZ Test tower · Lift 3**") >= 2,
    [c.key for c in _cb(at, "fld_pp_LOG-9004_")])

# ── «Nada que acreditar» ──
_n0 = len(at.session_state["_cred"])
_bn = _bt(at, "fld_pp_LOG-9003_no")
if _bn is not None:
    _bn.click()
    at.run()
chk("«Nothing to credit» revisa el parte SIN acreditar nada",
    at.session_state["_rev"].get("LOG-9003") == "campo000"
    and len(at.session_state["_cred"]) == _n0, (dict(at.session_state["_rev"]), _n0))

# ── si `acreditar` falla, el parte NO queda revisado ──
at2 = _app(_falla=True)
_c = [c for c in at2.checkbox if c.key == "%s_a_7_Install headers" % K2]
if _c:
    _c[0].check()
    at2.run()
_b = _bt(at2, "fld_pp_LOG-9002_ok")
if _b is not None:
    _b.click()
    at2.run()
chk("con la hoja diciendo que no: se enseña el error",
    any("boom" in e.value for e in at2.error), [e.value for e in at2.error])
chk("...el parte NO se marca revisado", "LOG-9002" not in at2.session_state["_rev"],
    dict(at2.session_state["_rev"]))
chk("...y la tarjeta sigue ahí", _bt(at2, "fld_pp_LOG-9002_ok") is not None)

# ── la vista del admin ──
at3 = _app(_vista="admin", _rev={"LOG-9002": "campo000"})
chk("admin: ninguna casilla ni botón de propuestas",
    not [w for w in list(at3.checkbox) + list(at3.button) if "_pp_" in (w.key or "")],
    [w.key for w in list(at3.checkbox) + list(at3.button) if "_pp_" in (w.key or "")])
# ⚠️ CADUCADO por v559: por su NOMBRE, no el login.
chk("...pero sí ve quién revisó",
    any("Proposals reviewed by Field Test" in c.value for c in at3.caption))

print("")
print("=" * 70)
if fallos:
    print("%d comprobaciones — %d FALLOS" % (n_ok + len(fallos), len(fallos)))
    for f in fallos:
        print("   · %s" % f)
    sys.exit(1)
print("%d comprobaciones — TODO OK" % n_ok)
