# -*- coding: utf-8 -*-
"""Los dos rojos que salieron al DESCONGELAR los guardianes de informes.

Ninguno es una regresión, y los dos llevaban ahí desde que v456 los dejó SIN DATOS:
un guardián que no corre no envejece a la vista, envejece a oscuras.

· v437 exigía «Engineer in charge» en el bloque de firma, y **v459 lo renombró a
  «Head installer/s»** (petición del usuario: se elige de una lista, no se teclea).
  CADUCADO → se actualiza la afirmación con la razón escrita (regla v385), no se
  relaja: el bloque de firma sigue teniendo que salir en inglés.

· v448 tiene su PROPIA copia del barrido de mensajes en español y marcaba
  `'Ripout + Instalación'`, que es una **CLAVE de `i18n.VALORES`** — el español
  HEREDADO que el mapa traduce al mostrar, o sea DATO. Es el mismo falso positivo que
  ya se corrigió en v449; la exclusión se DERIVA del propio mapa.
"""
import ast
import io

# ── v437 ─────────────────────────────────────────────────────────────────────
P = "verif_v437.py"
s = io.open(P, encoding="utf-8").read()
VIEJO = ('        chk("la FIRMA sale en inglés",\n'
         '            all(k in _txt for k in ("PREPARED BY", "RECEIVED BY", '
         '"Engineer in charge")))\n')
NUEVO = ('        # ⚠️ CADUCADO en v459 y ACTUALIZADO (regla v385): decía «Engineer in\n'
         '        # charge», que v459 renombró a «Head installer/s». No se vio antes\n'
         '        # porque este guardián llevaba SIN DATOS desde v456 — un guardián que\n'
         '        # no corre envejece a oscuras. Lo que se protege no cambia: el bloque\n'
         '        # de firma sale en inglés.\n'
         '        chk("la FIRMA sale en inglés",\n'
         '            all(k in _txt for k in ("PREPARED BY", "RECEIVED BY",\n'
         '                                    "Head installer/s")))\n')
if s.count(VIEJO) != 1:
    raise SystemExit("v437: ancla %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v437.py: la firma se comprueba contra «Head installer/s» (v459)")

# ── v448 ─────────────────────────────────────────────────────────────────────
P = "verif_v448.py"
s = io.open(P, encoding="utf-8").read()
cand = [ln for ln in s.split("\n") if "_es_msg(s)" in ln and "for" in ln]
if len(cand) != 1:
    raise SystemExit("v448: %d lineas candidatas: %r" % (len(cand), cand[:2]))
viejo = cand[0]
nuevo = viejo.replace("_es_msg(s)", "_es_msg(s) and s not in _LEGADO_ES")
s = s.replace(viejo, nuevo)

# la exclusión, derivada del mapa (no una lista a mano)
ANCLA = "def _es_msg("
if s.count(ANCLA) != 1:
    raise SystemExit("v448: ancla de _es_msg %d" % s.count(ANCLA))
s = s.replace(ANCLA,
              "# ⚠️ Las CLAVES de `i18n.VALORES` son el español HEREDADO: DATO que el mapa\n"
              "# traduce al MOSTRAR (v442/v469), no mensajes. Se derivan del mapa en vez de\n"
              "# listarse, que es lo que se queda viejo. Mismo arreglo que en v449.\n"
              "from core import i18n as _i18n_legado                       # noqa: E402\n"
              "_LEGADO_ES = set(_i18n_legado.VALORES)\n\n\n"
              + ANCLA)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v448.py: el vocabulario heredado no cuenta como mensaje")
