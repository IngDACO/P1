# -*- coding: utf-8 -*-
"""v519 · LAS DECISIONES DEL USUARIO DEL 27/09/2026.

  1. «Roping» = belting ese día            → lo vigila `verif_v517`
  2. Cuatro actividades entran como INFORMATIVAS: se marcan, NO cuentan
  3. El desmontaje pesa 50/50 en una obra combinada (antes 14%)
  4. El parte diario no trabaja sin conexión, «de momento» → no hay código

Lo que protege:
  (a) ⚠️ que marcar una informativa NO MUEVA NINGÚN NÚMERO — ni la etapa, ni la obra.
      Probado con una etapa A MEDIAS: con la etapa vacía, 0 → 0 no demuestra nada;
  (b) ⚠️ que `acreditar` las acepte sin tocar `Activities.Progress` cuando son solo
      informativas, y que con una mezcla SOLO se toque la etapa de las que pesan;
  (c) ⚠️ que el 50/50 afecte SOLO a obras NUEVAS: una obra que selló el 14 se sigue
      midiendo con 14 — el reparto mueve el avance, y el avance es lo que se reclama;
  (d) ⚠️ el contrato de v514 que hasta hoy sostenía la disciplina: si cambia UN SOLO
      PESO sin subir `VERSION`, las obras existentes se medirían contra otro juego sin
      enterarse. Ahora hay una HUELLA de los pesos por versión;
  (e) que las informativas no choquen con una actividad con peso (compartiendo nombre,
      marcar una acreditaría la otra) y vivan en etapas que existen;
  (f) que el móvil las pinte SIN porcentaje y con el aviso de que no cuentan.
Todo EJECUTANDO, con la hoja sustituida: importar no ejecuta (v378).
"""
import ast
import hashlib
import io
import json
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    # ⚠️ Acepta el detalle y lo ignora: `(ok if cond else fallo)(msg, det)` llama a las
    # dos con la misma firma, y sin esto revienta justo cuando PASA (v470, v516).
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("\n" + x)
    print("-" * 70)


from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402

TR = S.EXCLUYENTES["demolicion"]["opciones"][0]
INST = S.plan_de("Installation", ())
INFO = {n for _v in S.INFORMATIVAS.values() for n in _v}
CON_PESO = {a[0] for _v in S.ACTIVIDADES.values() for a in _v}

# ═════════════════════════════════════════════════════════════════
sec("1. Las cuatro informativas están, y bien puestas")
chk("son las cuatro que decidió el usuario", len(INFO) == 4, sorted(INFO))
chk("`validar()` cuadra con ellas dentro", not S.validar(), S.validar())
chk("...ninguna comparte nombre con una actividad CON peso", not (INFO & CON_PESO),
    sorted(INFO & CON_PESO))
chk("...ninguna está en la tabla de pesos (van APARTE, no con peso cero)",
    not any(n in CON_PESO for n in INFO))
# ⚠️ Y la sonda de `validar` tiene que SABER ver un choque, o su «cuadra» no vale (nº12).
_orig = dict(S.INFORMATIVAS)
S.INFORMATIVAS[("install", 7)] = S.INFORMATIVAS[("install", 7)] + ["Install sills"]
chk("...y `validar` SÍ caza una informativa que choca con una con peso",
    any("share a name" in p for p in S.validar()), S.validar())
S.INFORMATIVAS.clear()
S.INFORMATIVAS.update(_orig)

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ Marcar una informativa NO mueve ningún número")
# ⚠️ Con la etapa A MEDIAS. La primera prueba que hice fue con la etapa vacía y dio
# «0,0% → 0,0%», que no demuestra NADA: una etapa vacía no se podía mover de ninguna forma.
_det0 = SP._sobre(INST, {})
_e7 = next(e for e in _det0 if e["numero"] == 7)
_o7 = _e7["orden"]
_medias = {(_o7, a["nombre"]): 100.0 for a in _e7["actividades"][:3]}
_con_info = dict(_medias)
_con_info.update({(_o7, a["nombre"]): 100.0 for a in _e7["informativas"]})
_a = next(e for e in SP._sobre(INST, _medias) if e["orden"] == _o7)["pct"]
_b = next(e for e in SP._sobre(INST, _con_info) if e["orden"] == _o7)["pct"]
chk("la etapa 7 está a medias antes de nada (%.1f%%)" % _a, 0 < _a < 100, _a)
chk("...y marcar sus dos informativas la deja EXACTAMENTE igual (%.1f → %.1f)" % (_a, _b),
    _a == _b, (_a, _b))
# ⚠️ Y la OBRA entera, que es lo que se reclama: todas las etapas iguales.
_todas_a = [e["pct"] for e in SP._sobre(INST, _medias)]
_todas_info = dict(_medias)
_todas_info.update({(e["orden"], a["nombre"]): 100.0
                    for e in _det0 for a in e["informativas"]})
_todas_b = [e["pct"] for e in SP._sobre(INST, _todas_info)]
chk("...y ninguna etapa de la obra cambia con TODAS las informativas marcadas",
    _todas_a == _todas_b, [(i + 1, x, y) for i, (x, y)
                           in enumerate(zip(_todas_a, _todas_b)) if x != y])
# ⚠️ La razón estructural, afirmada: `avance_de` no las recibe. Si alguien las metiera
# dentro de `actividades`, esto se pondría rojo antes de que ninguna cuenta se moviera.
chk("...porque NO están en `actividades`: van en su propia clave",
    all(not ({a["nombre"] for a in e["actividades"]} & INFO) for e in _det0))
chk("...y sí se ven, para poder marcarlas (3 en una instalación)",
    sum(len(e["informativas"]) for e in _det0) == 3,
    sum(len(e["informativas"]) for e in _det0))


# ═════════════════════════════════════════════════════════════════
sec("3. ⚠️ `acreditar` las acepta SIN tocar el avance guardado")


class _WS:
    def __init__(self):
        self.filas = []

    def append_rows(self, filas, value_input_option=None):
        self.filas += [list(f) for f in filas]

    def batch_update(self, lote, value_input_option=None):
        pass


class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-09-27 10:00"

    def now(self, g=None):
        return self._T()


_PRJ = {"ID": "PRJ-T", "Type": "Installation",
        "StagePlanJSON": P.plan_nuevo("Installation", ())}
_llamadas = []


def _stub():
    _h = _WS()
    SP._ws = lambda: _h
    SP._mapa = lambda pid: {}
    SP._fila = lambda w, pid, et, ac: (None, None)
    SP._invalidate = lambda: None
    SP.clock = _Reloj()
    P.save_field_progress = lambda pid, cambios: (_llamadas.append(list(cambios)) or
                                                  (True, "ok"))
    return _h


_h = _stub()
_ok, _msg = SP.acreditar("PRJ-T", "cliente1", _PRJ,
                         [{"etapa": _o7, "actividad": n, "pct": 100.0}
                          for n in S.informativas("install", 7)], quien="Bobo")
chk("acredita las dos informativas de la etapa 7", _ok, _msg)
chk("...y quedan GUARDADAS (el hecho se registra)", len(_h.filas) == 2, len(_h.filas))
# ⚠️ Lo que importa: sin actividad con peso no hay etapa tocada, así que NO se escribe
# `Activities.Progress`. Antes del arreglo se reescribía con el mismo número.
chk("...SIN llamar a `save_field_progress` (el avance no se toca)", not _llamadas,
    _llamadas)

_llamadas.clear()
_h = _stub()
_peso = _e7["actividades"][0]["nombre"]
_ok, _msg = SP.acreditar("PRJ-T", "cliente1", _PRJ,
                         [{"etapa": _o7, "actividad": _peso, "pct": 100.0},
                          {"etapa": _o7, "actividad": S.informativas("install", 7)[0],
                           "pct": 100.0}], quien="Bobo")
_solo = next(e for e in SP._sobre(INST, {(_o7, _peso): 100.0}) if e["orden"] == _o7)["pct"]
chk("con una MEZCLA, se toca solo la etapa de la que pesa", _ok and len(_llamadas) == 1,
    _llamadas)
chk("...y el número escrito es el de la que pesa SOLA (%.1f%%)" % _solo,
    bool(_llamadas) and _llamadas[0] == [{"orden": _o7, "avance": _solo}], _llamadas)

_llamadas.clear()
_stub()
_ok, _msg = SP.acreditar("PRJ-T", "cliente1", _PRJ,
                         [{"etapa": _o7, "actividad": "Program controller parameters",
                           "pct": 100.0}], quien="Bobo")
chk("una informativa en la etapa EQUIVOCADA se rechaza (es de la 14, no de la 7)",
    not _ok, _msg)

# ═════════════════════════════════════════════════════════════════
sec("4. ⚠️ El 50/50 solo afecta a obras NUEVAS")


def _rip(plan):
    return round(sum(e["peso"] for e in plan if e["pista"] == S.PISTA_RIPOUT), 2)


chk("el reparto por defecto es 50 (decisión del usuario)", S.PCT_RIPOUT_DEFECTO == 50.0,
    S.PCT_RIPOUT_DEFECTO)
_nuevo = json.loads(P.plan_nuevo("Ripout + Installation", (TR,)))
chk("una obra combinada NUEVA sella 50", _nuevo.get("pct_ripout") == 50.0,
    _nuevo.get("pct_ripout"))
chk("...y su plan da al desmontaje el 50%",
    _rip(SP.plan_de_obra({"Type": "Ripout + Installation",
                          "StagePlanJSON": json.dumps(_nuevo)})) == 50.0)
# ⚠️ La obra VIEJA: su plan selló 14 el día que nació. Tiene que seguir en 14 — si leyera
# el defecto de hoy, su avance cambiaría sin que nadie tocara nada en obra, y la próxima
# reclamación saldría distinta de la anterior.
_viejo = dict(_nuevo, pct_ripout=14.0)
chk("una obra que selló 14 se sigue midiendo con 14",
    _rip(SP.plan_de_obra({"Type": "Ripout + Installation",
                          "StagePlanJSON": json.dumps(_viejo)})) == 14.0,
    _rip(SP.plan_de_obra({"Type": "Ripout + Installation",
                          "StagePlanJSON": json.dumps(_viejo)})))
chk("...y una instalación no reparte nada", _rip(INST) == 0.0)

# ═════════════════════════════════════════════════════════════════
sec("5. ⚠️ Si cambia un PESO, tiene que cambiar `VERSION`")
# El contrato de v514: la obra sella la versión del juego de pesos con la que nació, y
# `version_desfasada` la deja en solo lectura si el catálogo cambió. Pero eso solo
# funciona si quien cambia un peso SUBE la versión — y hasta hoy eso lo sostenía la
# disciplina. Con esta huella, cambiar un peso sin subirla es un ROJO.
# ⚠️ Las INFORMATIVAS no entran en la huella: no llevan peso, y por eso v519 no subió la
# versión. Comprobado contra el HEAD anterior: huella idéntica.
HUELLAS = {"2026-09-22": "7240bebb83ccab8f"}


def huella():
    datos = {"etapas": [list(e) for e in S.ETAPAS],
             "actividades": {"%s/%s" % k: [list(a) for a in v]
                             for k, v in sorted(S.ACTIVIDADES.items())}}
    return hashlib.sha256(json.dumps(datos, sort_keys=True).encode("utf-8")).hexdigest()[:16]


chk("la versión de hoy tiene su huella registrada (%s)" % S.VERSION, S.VERSION in HUELLAS,
    "añade la huella de %s a HUELLAS con la razón del cambio" % S.VERSION)
chk("...y los pesos casan con ella: nadie cambió un peso sin subir la versión",
    HUELLAS.get(S.VERSION) == huella(),
    "huella %s ≠ registrada %s" % (huella(), HUELLAS.get(S.VERSION)))
# ⚠️ La sonda tiene que ver un cambio de UNA décima, o no protege lo que dice (nº12).
_k = next(iter(sorted(S.ACTIVIDADES)))
_bak = list(S.ACTIVIDADES[_k])
S.ACTIVIDADES[_k] = [(_bak[0][0], _bak[0][1] + 0.1, _bak[0][2])] + _bak[1:]
chk("...y la huella SÍ cambia con una décima de peso", huella() != HUELLAS["2026-09-22"])
S.ACTIVIDADES[_k] = _bak
# ⚠️ Y que las informativas NO la mueven: si la movieran, añadir una obligaría a subir la
# versión y bloquearía obras cuyo avance no ha cambiado.
_bak_i = dict(S.INFORMATIVAS)
S.INFORMATIVAS[("install", 1)] = ["Algo informativo de prueba"]
chk("...y añadir una informativa NO la mueve", huella() == HUELLAS["2026-09-22"])
S.INFORMATIVAS.clear()
S.INFORMATIVAS.update(_bak_i)

# ═════════════════════════════════════════════════════════════════
sec("6. El móvil las pinta sin porcentaje y avisando")
_ui = io.open("core/stage_progress_ui.py", encoding="utf-8").read()
_a = ast.parse(_ui)
# ⚠️ Por AST, no buscando en el fichero: el aviso va partido en DOS literales seguidos
# («…ticking these does » + «not change the progress.») y buscar la frase en el texto
# fuente daba rojo con el aviso puesto. Python une los literales adyacentes en UNA
# constante; el AST la ve entera (trampa nº2: el texto del fuente no es lo que corre).
_consts = [n.value for n in ast.walk(_a)
           if isinstance(n, ast.Constant) and isinstance(n.value, str)]
chk("hay un aviso de que no cambian el avance",
    any("does not change the progress" in c for c in _consts))
# ⚠️ Sus casillas NO llevan porcentaje: una casilla con «0.0%» al lado de las que pesan
# parecería un error; una sin número, con el aviso, dice lo que es.
_cb = [n for n in ast.walk(_a) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "checkbox"]
_sin_pct = [n for n in _cb if n.args and isinstance(n.args[0], ast.Subscript)]
chk("la casilla informativa es el NOMBRE a secas, sin porcentaje", len(_sin_pct) == 1,
    len(_sin_pct))
chk("...y entran en lo que se guarda (si no, marcarlas no haría nada)",
    'list(e["actividades"]) + list(_info)' in _ui)

print("")
print("=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "HAY FALLOS" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
