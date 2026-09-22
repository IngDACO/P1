# -*- coding: utf-8 -*-
"""v514 · EL AVANCE POR ACTIVIDAD.

Lo que protege:
  (a) ⚠️ que `StageProgress` esté en el lote de lectura: fuera de él, `registros()`
      devuelve None y el avance se acreditaría en la hoja sin que la app lo volviera a
      ver NUNCA, sin un solo error (v461, v507 — dos veces ya);
  (b) que el % de una etapa se pondere por el PESO de cada actividad y no por cuántas
      hay, y que sea escala-invariante como `compute_avance`;
  (c) ⚠️ que el número siga escribiéndose en `Activities.Progress`, que es lo que leen
      la curva S, el SPI, la cadena de v500 y la reclamación que se cobra;
  (d) ⚠️ que NO se acredite contra un catálogo distinto del que la obra selló: los
      órdenes se desplazan y el trabajo se colgaría de otra etapa;
  (e) que una obra anterior a v512 siga funcionando con la rejilla de siempre;
  (f) que solo se recalculen las etapas TOCADAS (criterio del guardado parcial, v499);
  (g) que si la escritura del avance falla, se DIGA — el crédito guardado con la etapa
      quieta es lo que haría dudar al usuario de su propio trabajo;
  (h) la fila posicional contra la cabecera (v363).
Todo EJECUTANDO, con la hoja sustituida: importar no ejecuta (v378).
"""
import ast
import io
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


def ok(q):
    global n_ok
    n_ok += 1
    print(f"  ok   {q}")


def fallo(q, d=""):
    fallos.append(q)
    print(f"  *** FALLO  {q}" + (f"  -> {d}" if d else ""))


def ck(q, real, esp):
    ok(q) if real == esp else fallo(q, f"{real!r} != {esp!r}")


def cerca(q, real, esp, tol=0.05):
    ok(q) if abs(float(real) - float(esp)) <= tol else fallo(q, f"{real!r} != {esp!r}")


def _fuente(f):
    return io.open(os.path.join(RAIZ, f), encoding="utf-8").read()


from core import hojas as H                                       # noqa: E402
from core import projects as P                                    # noqa: E402
from core import stage_progress as SP                             # noqa: E402
from core import stages as S                                      # noqa: E402

PRJ = {"ID": "PRJ-T", "Type": "Installation", "Name": "test",
       "StagePlanJSON": P.plan_nuevo("Installation", ())}


class _WS:
    """Hoja de mentira que se queda con lo que se le escribe."""

    def __init__(self):
        self.filas, self.parches = [], []

    def append_rows(self, filas, value_input_option=None):
        self.filas += [list(f) for f in filas]

    def batch_update(self, lote, value_input_option=None):
        self.parches += list(lote)


class _Reloj:
    class _T:
        def strftime(self, f):
            return "2026-09-22 10:00"

    def now(self, g):
        return self._T()


def _con(filas_credito, save_ok=True, fila_existente=None):
    """Sustituye hoja, caché y escritor. Devuelve (hoja_falsa, llamadas_a_save).

    ⚠️ Sin ejercitar el camino de ESCRITURA, las roturas que importan se escapan: fue
    exactamente lo que pasó en v510, donde cinco de doce pasaron por delante porque el
    guardián solo miraba la aritmética de lectura.
    """
    _hoja = _WS()
    _llamadas = []

    def _save(pid, cambios):
        _llamadas.append((pid, list(cambios)))
        return (save_ok, "ok" if save_ok else "la hoja no responde")

    SP._ws = lambda: _hoja
    SP.creditos = lambda pid, etapa=None: [
        r for r in filas_credito
        if etapa is None or int(float(r.get("StageOrder", 0))) == int(etapa)]
    SP._fila = lambda w, pid, et, ac: (fila_existente or (None, None))
    SP._invalidate = lambda: None
    SP.clock = _Reloj()
    P.save_field_progress = _save
    return _hoja, _llamadas


_orig = (SP._ws, SP.creditos, SP._fila, SP._invalidate, SP.clock, P.save_field_progress)


# ═════ 1 · la hoja esta en el lote ═══════════════════════════════════════════
print("\n[1] la hoja")
# ⚠️ Esto ha mordido DOS veces (v461 y v507): una hoja fuera del lote se escribe bien y
# se lee vacia para siempre, sin error. Es el primer chequeo a proposito.
ck("⚠️ «StageProgress» esta en HOJAS_LECTURA", SP.SHEET in H.HOJAS_LECTURA, True)
ck("la cabecera tiene las 10 columnas", len(SP.HEADERS), 10)
# La fila posicional que se escribe tiene que cuadrar con la cabecera (v363).
_t = ast.parse(_fuente("core/stage_progress.py"))
_ac = next(n for n in ast.walk(_t) if isinstance(n, ast.FunctionDef)
           and n.name == "acreditar")
_lst = next((n for n in ast.walk(_ac) if isinstance(n, ast.List)
             and len(n.elts) == len(SP.HEADERS)), None)
ck("⚠️ la fila que se escribe cuadra con la cabecera", _lst is not None, True)


# ═════ 2 · la aritmetica pondera por PESO ════════════════════════════════════
print("\n[2] el % de una etapa")
_a = [{"peso_en_etapa": 17, "pct": 100}, {"peso_en_etapa": 12, "pct": 0},
      {"peso_en_etapa": 71, "pct": 0}]
cerca("⚠️ pondera por peso, no por cuantas hay", SP.avance_de(_a), 17.0)
ck("...y contar por numero habria dado otra cosa", round(100.0 / 3, 1) != 17.0, True)
cerca("todo hecho = 100", SP.avance_de([{"peso_en_etapa": 5, "pct": 100},
                                        {"peso_en_etapa": 95, "pct": 100}]), 100.0)
cerca("nada hecho = 0", SP.avance_de([{"peso_en_etapa": 5, "pct": 0}]), 0.0)
# ⚠️ Todo lo que puede dividir por cero va ENVUELTO. Sin esto, quitar la guarda del
# denominador hace que el guardián REVIENTE con ZeroDivisionError en vez de denunciar, y
# la batería lo cuenta como «revienta, no cuenta»: la rotura se va de rositas. Es la
# sexta vez en este proyecto con el mismo patrón — un guardián que muere no denuncia.
# ⚠️ Y la primera versión de este arreglo envolvió solo UNA de las dos llamadas: el
# reventón seguía saliendo de la de al lado. Por eso va un helper y no un try suelto.
def _sin_morir(fn, *a):
    try:
        return fn(*a)
    except Exception as e:
        return "lanzo %r" % (e,)


ck("una lista vacia no lanza", _sin_morir(SP.avance_de, []), 0.0)
ck("...ni pesos a cero (no divide por cero)",
   _sin_morir(SP.avance_de, [{"peso_en_etapa": 0, "pct": 100}]), 0.0)
# ⚠️ Escala-invariante, igual que `projects.compute_avance`: añadir una actividad no
# puede hacer que el avance se DESPLOME de golpe por cambiar el denominador entero.
cerca("es escala-invariante (misma proporcion, mismo %)",
      SP.avance_de([{"peso_en_etapa": 34, "pct": 100}, {"peso_en_etapa": 166, "pct": 0}]),
      17.0)


# ═════ 3 · el detalle mezcla catalogo y hoja ═════════════════════════════════
print("\n[3] lo que ve la pantalla")
_con([])
_d = SP.detalle("PRJ-T", PRJ)
ck("salen las 14 etapas de la instalacion", len(_d), 14)
ck("...con sus 143 actividades", sum(len(e["actividades"]) for e in _d), 143)
ck("el orden va de 1 a N sin huecos",
   [e["orden"] for e in _d], list(range(1, len(_d) + 1)))
ck("sin creditos, todo a cero", {e["pct"] for e in _d}, {0.0})

# Un credito real, superpuesto al catalogo.
_con([{"StageOrder": "6", "Activity": "Install motor bedplate", "Pct": "100"}])
_d6 = next(e for e in SP.detalle("PRJ-T", PRJ) if e["orden"] == 6)
cerca("⚠️ acreditar el bedplate (17% de su etapa) da 17%", _d6["pct"], 17.0)
ck("...y solo esa actividad queda marcada",
   [a["nombre"] for a in _d6["actividades"] if a["pct"] >= 100],
   ["Install motor bedplate"])
ck("las demas etapas siguen en cero",
   {e["pct"] for e in SP.detalle("PRJ-T", PRJ) if e["orden"] != 6}, {0.0})
# ⚠️ Un credito de una actividad que YA NO esta en el plan no puede sumar: seria avance
# sin denominador, o sea un numero que no se puede explicar.
_con([{"StageOrder": "4", "Activity": "Install mirror", "Pct": "100"}])
_d4 = next(e for e in SP.detalle("PRJ-T", PRJ) if e["orden"] == 4)
cerca("⚠️ un credito de algo que no esta en el plan no suma", _d4["pct"], 0.0)


# ═════ 4 · obras sin plan y con plan viejo ═══════════════════════════════════
print("\n[4] las obras que no usan el catalogo")
ck("una obra anterior a v512 no tiene plan", SP.plan_de_obra({"ID": "viejo"}), [])
ck("...ni una con el plan ilegible",
   SP.plan_de_obra({"ID": "x", "StagePlanJSON": "{roto"}), [])
ck("la version al dia no se marca", SP.version_desfasada(PRJ), "")
ck("⚠️ una version distinta SI se marca",
   SP.version_desfasada({"StagePlanJSON": '{"version":"2020-01-01"}'}), "2020-01-01")


# ═════ 5 · ⚠️ lo que de verdad se ESCRIBE ════════════════════════════════════
print("\n[5] acreditar")
_hoja, _llam = _con([])
_ok, _msg = SP.acreditar("PRJ-T", "cliente1", PRJ,
                         [{"etapa": 6, "actividad": "Install motor bedplate",
                           "pct": 100}], quien="Bobo")
ck("se acredita", _ok, True)
ck("...escribiendo UNA fila", len(_hoja.filas), 1)
_f = _hoja.filas[0] if _hoja.filas else []
ck("...con todas las columnas", len(_f), len(SP.HEADERS))
ck("...la obra correcta", _f[SP.HEADERS.index("ProjectID")] if _f else "?", "PRJ-T")
ck("...la etapa correcta", _f[SP.HEADERS.index("StageOrder")] if _f else "?", "6")
ck("...y quien lo marco", _f[SP.HEADERS.index("UpdatedBy")] if _f else "?", "Bobo")

# ⚠️ LO QUE MAS IMPORTA: que el numero llegue a `Activities.Progress`. Si no, todo lo
# de abajo —curva S, SPI, cadena, reclamacion— seguiria viendo la obra parada.
ck("⚠️ se escribe el avance de la etapa en Activities", len(_llam), 1)
_cam = _llam[0][1] if _llam else []
ck("...solo la etapa TOCADA", [c["orden"] for c in _cam], [6])
cerca("...con el % calculado, no con el de la casilla",
      _cam[0]["avance"] if _cam else -1, 17.0)

# Solo las tocadas: acreditar en la 6 no puede reescribir las otras trece.
_hoja, _llam = _con([])
SP.acreditar("PRJ-T", "cliente1", PRJ,
             [{"etapa": 1, "actividad": "Receive toolbox", "pct": 100},
              {"etapa": 1, "actividad": "Receive Inex kit", "pct": 100}], quien="Bobo")
ck("dos creditos de la misma etapa = UNA sola escritura de avance",
   [c["orden"] for c in (_llam[0][1] if _llam else [])], [1])

# ⚠️ Si la escritura del avance falla, se DICE. El credito quedo guardado y la etapa
# quieta: sin aviso, el usuario veria su trabajo registrado y el avance sin moverse.
_hoja, _llam = _con([], save_ok=False)
_ok2, _msg2 = SP.acreditar("PRJ-T", "cliente1", PRJ,
                           [{"etapa": 6, "actividad": "Install motor bedplate",
                             "pct": 100}], quien="Bobo")
ck("⚠️ si el avance no se puede escribir, NO dice que todo fue bien", _ok2, False)
ck("...y el mensaje lo explica", "could not be updated" in str(_msg2), True)


# ═════ 6 · lo que NO se puede acreditar ══════════════════════════════════════
print("\n[6] lo que se rechaza")
_hoja, _llam = _con([])
_ok3, _m3 = SP.acreditar("PRJ-T", "cliente1", PRJ,
                         [{"etapa": 4, "actividad": "Install mirror", "pct": 100}])
ck("⚠️ algo que no esta en el plan de ESTA obra se rechaza", _ok3, False)
ck("...y no se escribe nada", len(_hoja.filas), 0)
_ok4, _m4 = SP.acreditar("PRJ-T", "cliente1", PRJ,
                         [{"etapa": 99, "actividad": "Lo que sea", "pct": 100}])
ck("una etapa que no existe tampoco", _ok4, False)

_hoja, _llam = _con([])
_ok5, _m5 = SP.acreditar("PRJ-VIEJA", "cliente1", {"ID": "PRJ-VIEJA"},
                         [{"etapa": 1, "actividad": "x", "pct": 100}])
ck("⚠️ una obra sin plan no se acredita", _ok5, False)
# ⚠️ Y por EL MOTIVO correcto. Solo con `_ok5 is False` la comprobación pasaba aunque se
# quitara la guarda del plan: sin plan, la lista de actividades válidas queda vacía, así
# que el rechazo llegaba igual pero por «no está en el plan». Un chequeo que acierta por
# el motivo equivocado no protege lo que dice proteger, y la rotura se escapó.
ck("...y el mensaje dice que es por NO TENER plan",
   "no stage plan" in str(_m5), True)
ck("...sin escribir nada", len(_hoja.filas), 0)

# ⚠️ Catalogo distinto del que la obra sello: los ordenes se desplazan y el trabajo se
# colgaria de otra etapa. Se niega a escribir.
_hoja, _llam = _con([])
_ok6, _m6 = SP.acreditar("PRJ-V", "cliente1",
                         {"ID": "PRJ-V", "Type": "Installation",
                          "StagePlanJSON": '{"version":"2020-01-01","tipo":"Installation"}'},
                         [{"etapa": 1, "actividad": "Receive toolbox", "pct": 100}])
ck("⚠️ con el catalogo desfasado NO se acredita", _ok6, False)
ck("...y no se escribe nada", len(_hoja.filas), 0)
ck("...y el mensaje nombra las dos versiones",
   "2020-01-01" in str(_m6) and S.VERSION in str(_m6), True)

# Los porcentajes absurdos se recortan, no se guardan tal cual.
_hoja, _llam = _con([])
SP.acreditar("PRJ-T", "cliente1", PRJ,
             [{"etapa": 6, "actividad": "Install motor bedplate", "pct": 500}])
ck("un pct de 500 se recorta a 100",
   _hoja.filas[0][SP.HEADERS.index("Pct")] if _hoja.filas else "?", "100.0")


# ═════ 7 · la pantalla ═══════════════════════════════════════════════════════
print("\n[7] lo que se ve")
_ui = _fuente("core/stage_progress_ui.py")
_tu = ast.parse(_ui)
_llamadas_ui = {getattr(n.func, "attr", "") for n in ast.walk(_tu)
                if isinstance(n, ast.Call)}
ck("la pantalla acredita por el modulo, no escribe por su cuenta",
   "acreditar" in _llamadas_ui, True)
ck("...y lee el detalle de ahi mismo", "detalle" in _llamadas_ui, True)
# ⚠️ Un guardado por ETAPA: marcar una casilla no puede escribir. Con 143 casillas,
# escribir a cada clic es un 429 garantizado a media obra (la leccion de v511).
ck("⚠️ el guardado va tras un boton, no en la casilla",
   "st.button(" in _ui and "st.checkbox(" in _ui, True)
# ⚠️ Solo lo que cambio, no las 24 filas de la etapa.
ck("...y solo manda lo que cambio", "!= _marcas[" in _ui, True)
ck("la version desfasada deja la pantalla en SOLO LECTURA",
   "editable = False" in _ui, True)
_pu = _fuente("core/projects_ui.py")
ck("el campo cae a la rejilla vieja si la obra no tiene plan",
   "if not _SPU.render(pid, grupo, prj, key_prefix=\"fld\"):" in _pu, True)

# ⚠️ Borrar una obra tiene que llevarse sus creditos: viven en OTRA hoja, asi que
# `delete_project` no los tocaba y quedaban filas huerfanas apuntando a algo que ya no
# existe. No da error — ensucia el libro para siempre. Lo destapo el ejercicio contra la
# hoja real, donde hubo que borrarlas a mano para que la foto final cuadrara.
_tp = ast.parse(_fuente("core/projects.py"))
_dp = next((n for n in ast.walk(_tp) if isinstance(n, ast.FunctionDef)
            and n.name == "delete_project"), None)
assert _dp is not None, "no existe delete_project"
_sdp = ast.unparse(_dp)
ck("⚠️ borrar una obra se lleva sus creditos de etapa",
   "stage_progress" in _sdp and "delete_rows" in _sdp, True)
ck("...sin impedir el borrado si eso falla (try/except)",
   any(isinstance(n, ast.Try) for n in ast.walk(_dp)), True)

print("\n" + "=" * 70)
(SP._ws, SP.creditos, SP._fila, SP._invalidate, SP.clock, P.save_field_progress) = _orig
print(f"{n_ok + len(fallos)} comprobaciones — " + ("TODO OK" if not fallos else "HAY FALLOS"))
sys.exit(1 if fallos else 0)
