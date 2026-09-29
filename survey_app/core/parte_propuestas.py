# -*- coding: utf-8 -*-
"""Del parte diario a PROPUESTAS que el usuario confirma (v523).

## La regla que manda aquí

«La app no asume nada sin consultar con el usuario: el avance tiene que darse de forma
correcta. Con el tiempo, cuando la IA interprete mejor, se le dará más autonomía»
(el usuario, 28/09/2026). Así que este módulo **no escribe nada**. Recibe el texto del
parte, el plan SELLADO de la obra y lo ya acreditado, y devuelve lo que la pantalla tiene
que PREGUNTAR, ya cruzado:

  · cada actividad con su etapa en el ORDEN del plan — que es lo que entiende
    `stage_progress.acreditar`, no el número de etapa del catálogo;
  · si ya está hecha (no se vuelve a proponer: marcar lo marcado no informa);
  · la LÍNEA del parte que la respalda — la prueba que el usuario lee antes de marcar;
  · los avisos («el parte dice que no está terminado», «dice que fue otro día»).

Y convierte lo que el usuario marcó en la lista que espera `acreditar`, con el origen
`log` y el ID del parte en la nota. ⚠️ Esa marca no es burocracia: distinguir lo
acreditado desde un parte de lo marcado a mano es lo único que permitirá medir si la
interpretación acierta — y con esa medida se decidirá cuánta autonomía darle.

## Varios ascensores

Decisión del usuario: se PROPONE separar. `reparto` parte la nota por ascensor según lo
que el usuario haya asignado; lo que no asignó no se propone en ningún sitio. ⚠️ Y
conserva la cabecera «Pendings»: separar sin ella convertiría lo pendiente en propuesta.

## Lo que se enseñó y lo que se marcó (v524)

`registro` guarda, al revisar el parte, lo que la pantalla OFRECIÓ y lo que el usuario
MARCÓ; `acierto` lo cuenta. ⚠️ Sin esto solo se sabía lo aceptado (StageProgress con origen
`log`): la mitad de la cuenta. Y no se puede reconstruir después — el vocabulario cambia y
lo ya acreditado también —, así que cada parte revisado sin registro es un dato perdido.

Módulo HOJA: solo `vocabulario` y `stages`, sin Streamlit ni Sheets.
"""
import json

from core import vocabulario as V

# El `Source` en StageProgress de lo acreditado desde un parte (lo manual es «manual»).
ORIGEN = "log"

# v524 · Formato del registro de revisión (columna `Proposals` de DailyLogs). Si cambia su
# forma, se sube: `acierto` tiene que poder leer los viejos.
REGISTRO_V = 1
# ⚠️ Una celda de Sheets aguanta 50.000 caracteres: por encima, la escritura FALLA y el parte
# se quedaría sin revisar. Se recorta antes, y el recorte queda dicho en el propio registro.
_TOPE_REGISTRO = 45000


def _indice(plan) -> dict:
    """`nombre de actividad -> (orden, nombre de etapa, cuenta)` para ESTA obra.

    ⚠️ Los nombres son únicos en el catálogo (comprobado en v523: 0 repetidos entre las
    18 etapas), así que el nombre basta para saber la etapa sin adivinar. Si algún día se
    repitiera uno, `verif_v523` lo dice antes de que un crédito caiga en otra etapa.
    """
    from core import stages as S
    out = {}
    for i, e in enumerate(plan or [], start=1):
        for a in e.get("actividades") or []:
            out[str(a.get("nombre") if isinstance(a, dict) else a)] = (i, e.get("nombre", ""), True)
        for n in S.informativas(e.get("pista"), e.get("numero")):
            out.setdefault(n, (i, e.get("nombre", ""), False))
    return out


def propuestas(texto, plan, mapa=None) -> dict:
    """Lo que la pantalla pregunta sobre un parte, ya cruzado con el plan y lo hecho.

    `plan` = `stage_progress.plan_de_obra(prj)`; `mapa` = `{(orden, actividad): pct}`.
    Devuelve `{actividades, etapas, preguntas, pendientes, retiradas, fuera, no_avance,
    hay_algo}`. Nada de esto se acredita: es lo que se le ENSEÑA al usuario.
    """
    lineas = str(texto or "").splitlines()
    idx = _indice(plan)
    mapa = mapa or {}

    def _hecha(o, n):
        try:
            return float(mapa.get((o, n), 0.0)) >= 100.0
        except (TypeError, ValueError):
            return False

    def _pruebas(nums):
        out = []
        for i in nums or []:
            if isinstance(i, int) and 0 <= i < len(lineas) and lineas[i].strip():
                if lineas[i].strip() not in out:
                    out.append(lineas[i].strip())
        return out

    r = V.buscar(texto, plan)

    acts, por_nombre = [], {}
    for c in r["candidatos"]:
        n = c["actividad"]
        if n not in idx:                      # no es de esta obra: la barandilla ya lo apartó
            continue
        ls = c.get("lineas") or [c.get("linea")]
        if n in por_nombre:                   # otra palabra para lo mismo: más pruebas, una fila
            _f = por_nombre[n]
            for p in _pruebas(ls):
                if p not in _f["pruebas"]:
                    _f["pruebas"].append(p)
            _f["aviso"] = _f["aviso"] or c.get("aviso", "")
            continue
        o, et, cuenta = idx[n]
        # `termino` (v524): qué palabra del vocabulario la trajo — lo que el registro guarda
        # para saber QUÉ término falla cuando una propuesta se rechaza.
        fila = {"orden": o, "etapa": et, "actividad": n, "cuenta": cuenta,
                "hecha": _hecha(o, n), "pruebas": _pruebas(ls),
                "aviso": c.get("aviso", ""), "fuente": c.get("fuente", ""),
                "termino": c.get("termino", "")}
        por_nombre[n] = fila
        acts.append(fila)
    _ya = set(por_nombre)

    etapas = []
    for e in r.get("etapas", []):
        o = next((i for i, x in enumerate(plan or [], start=1)
                  if x.get("pista") == e.get("pista") and x.get("numero") == e.get("numero")), None)
        if o is None:
            continue
        # ⚠️ Sin repetir lo que ya se propone suelto arriba: dos casillas para la misma
        # actividad en la misma nota harían dudar de cuál vale.
        ops = [{"orden": o, "etapa": e.get("etapa", ""), "actividad": n,
                "cuenta": idx.get(n, (o, "", True))[2], "hecha": _hecha(o, n)}
               for n in e.get("actividades") or [] if n not in _ya and n in idx]
        if not ops:
            continue
        etapas.append({"orden": o, "etapa": e.get("etapa", ""), "termino": e.get("termino", ""),
                       "opciones": ops, "aviso": e.get("aviso", ""),
                       "pruebas": _pruebas(e.get("lineas") or [e.get("linea")])})

    preguntas = []
    for a in r["ambiguos"]:
        ops = []
        for n in a.get("alternativas") or []:
            if n in idx and n not in _ya:
                o, et, cuenta = idx[n]
                ops.append({"orden": o, "etapa": et, "actividad": n, "cuenta": cuenta,
                            "hecha": _hecha(o, n)})
        if not ops:
            continue
        preguntas.append({"termino": a.get("termino", ""), "regla": a.get("regla", ""),
                          "opciones": ops, "pruebas": _pruebas([a.get("linea")])})

    out = {
        "actividades": acts,
        "etapas": etapas,
        "preguntas": preguntas,
        "pendientes": [{"termino": p.get("termino", ""), "actividades": p.get("actividades", []),
                        "pruebas": _pruebas([p.get("linea")])} for p in r.get("pendientes", [])],
        "retiradas": [{"termino": p.get("termino", ""), "motivo": p.get("motivo", ""),
                       "pruebas": _pruebas([p.get("linea")])} for p in r.get("retiradas", [])],
        "fuera": [{"actividad": c["actividad"], "termino": c.get("termino", "")}
                  for c in r.get("fuera_del_plan", [])],
        "no_avance": [{"termino": n.get("termino", ""), "motivo": n.get("motivo", "")}
                      for n in r.get("no_avance", [])],
    }
    # ⚠️ «Hay algo que CONFIRMAR»: una actividad o etapa o pregunta todavía sin hacer. Lo
    # demás (pendiente, retirada, fuera del plan) se enseña, pero no hay nada que marcar.
    out["hay_algo"] = any(not f["hecha"] for f in acts) \
        or any(not o["hecha"] for e in etapas for o in e["opciones"]) \
        or any(not o["hecha"] for q in preguntas for o in q["opciones"])
    return out


def creditos(marcadas, log_id) -> list:
    """Lo que el usuario MARCÓ → la lista que espera `stage_progress.acreditar`.

    `marcadas` = pares `(orden, actividad)`. Al 100%: el catálogo es binario (v514). La
    nota lleva el ID del parte y `acreditar` recibe `origen=ORIGEN`: así se sabe de qué
    parte salió cada crédito, que es lo que permitirá medir el acierto.
    """
    out, vistos = [], set()
    for o, n in marcadas or []:
        k = (int(o), str(n))
        if k in vistos:
            continue
        vistos.add(k)
        out.append({"etapa": k[0], "actividad": k[1], "pct": 100.0, "nota": str(log_id)})
    return out


def lineas_de(texto, token, tambien=()) -> list:
    """Las líneas que irían con `token` SI fuera un ascensor: las que lo nombran y, si va
    solo en su línea («L2» como cabecera, igual que «Lift 3»), las que cuelgan de él.

    `token` es la clave de `ascensores`: «3» para «lift 3», el propio texto para «L2».
    """
    _t = str(token)
    _extra = () if _t.isdigit() else (_t,)
    a = V.ascensores(texto, tambien=tuple(tambien or ()) + _extra)
    return [l for l, claves in a.get("lineas", []) if _t in claves]


def propone_algo(lineas, plan) -> bool:
    """¿Proponen algo estas líneas, esté hecho o no? Para no PREGUNTAR por un «L2» o por
    un ascensor cuyas líneas no cambian nada («lift 2 was in use by builders»): una
    pregunta cuya respuesta no importa es fricción, y enseña a contestar sin leer.

    ⚠️ Sin lo acreditado A PROPÓSITO: lo hecho depende de la obra de DESTINO, que es
    justo lo que todavía no se sabe.
    """
    return bool(lineas) and propuestas("\n".join(lineas), plan, {})["hay_algo"]


def reparto(texto, asignacion, tambien=(), sin_responder=()) -> dict:
    """Parte la nota por ascensor según lo que el USUARIO asignó: `{destino: texto}`.

    `asignacion` = `{clave de ascensor: destino}`; la clave `""` son las líneas que no
    nombran ascensor (van a la obra del parte si el usuario no dice otra cosa). Una clave
    sin destino NO se propone en ningún sitio: sin su respuesta, no se decide.
    `tambien` = los nombres dudosos que el usuario confirmó como ascensor.
    `sin_responder` = los dudosos que TODAVÍA no contestó: lo que iría con ellos no va a
    ningún sitio hasta que conteste. ⚠️ Sin esto, «L2 call button» caía en la obra del
    parte como si «L2» fuera un piso — que es justo lo que se le está preguntando. ⚠️ Y no
    basta con la línea que lo NOMBRA: con «L2» solo en su línea, como cabecera, lo que va
    debajo también depende de la respuesta (`lineas_de`).

    ⚠️ Lo que iba bajo «Issues/Pendings» sigue siendo pendiente en CADA trozo: se repite
    la cabecera en el destino antes de su primera línea pendiente.
    """
    a = V.ascensores(texto, tambien=tambien)
    _sr = {str(x).strip() for x in (sin_responder or ()) if str(x).strip()}
    # ⚠️ Por TEXTO de línea: si la misma línea sale dos veces, se retienen las dos. En la
    # duda se retiene — el error seguro es no proponer, nunca proponer en otra obra.
    retener = {l for x in _sr for l in lineas_de(texto, x, tambien)}
    out, con_cabecera = {}, set()
    en_pendiente = False
    for l, claves in a.get("lineas", []):
        _ret = bool(_sr) and (l in retener or any(x.group(0) in _sr
                                                  for x in V._ASC_DUDOSO.finditer(l)))
        m = V._CABECERA_PENDIENTE.match(l)
        if m:
            en_pendiente = True
            l = m.group(1).strip()
            if not l or V._NADA.match(l):
                continue
        if _ret:
            continue
        for k in claves:
            d = asignacion.get(k)
            if not d:
                continue
            if en_pendiente and d not in con_cabecera:
                out.setdefault(d, []).append("Pending:")
                con_cabecera.add(d)
            if l not in out.setdefault(d, []):
                out[d].append(l)
    return {d: "\n".join(ls) for d, ls in out.items()}


# ═════════════════════════════════════════════════════════════════
# v524 · El registro de la revisión: lo ofrecido y lo marcado
# ═════════════════════════════════════════════════════════════════
def registro(por_destino, respuestas=None, ascensores=None, app="", nada=False) -> str:
    """Lo que la pantalla ENSEÑÓ y lo que el usuario MARCÓ al revisar un parte, en JSON.

    `por_destino` = `{obra: {"ofrecidas": [[tipo, orden, actividad, termino]],
    "marcadas": [(orden, actividad)], "hechas": [(orden, actividad)]}}` — lo que anota
    `daily_log_ui._pintar` al pintar cada casilla. `tipo`: «a» actividad propuesta suelta,
    «e» opción de la lista de una etapa, «q» opción de una pregunta.
    `respuestas` = `{«L2»: "lift" | "level" | None}`; `ascensores` = `{«3»: obra | None}`.
    `nada=True` = pulsó «Nothing to credit»: lo que tuviera marcado NO se acreditó, así que
    no se registra como aceptado.
    """
    dest = {}
    for d, x in (por_destino or {}).items():
        x = x or {}
        dest[str(d)] = {
            "ofrecidas": [list(o) for o in x.get("ofrecidas") or []],
            "marcadas": [] if nada else [[int(o), str(a)] for o, a in x.get("marcadas") or []],
            "hechas": [[int(o), str(a)] for o, a in x.get("hechas") or []],
        }
    out = {"v": REGISTRO_V, "app": str(app or ""), "nada": bool(nada), "destinos": dest,
           "dudosos": dict(respuestas or {}), "ascensores": dict(ascensores or {})}

    def _js(o):
        return json.dumps(o, ensure_ascii=False, separators=(",", ":"))

    s = _js(out)
    if len(s) > _TOPE_REGISTRO:
        # Primero sin los términos, que es lo más largo; lo que se ofreció y lo que se
        # marcó sigue entero, que es lo que mide `acierto`.
        for x in dest.values():
            x["ofrecidas"] = [o[:3] for o in x["ofrecidas"]]
        out["recortado"] = "terminos"
        s = _js(out)
    if len(s) > _TOPE_REGISTRO:
        out["destinos"] = {d: {k: len(v) for k, v in x.items()} for d, x in dest.items()}
        out["recortado"] = "cuentas"
        s = _js(out)
    return s


def leer_registro(s) -> dict:
    """El registro de una revisión, o `{}` si no hay o no se entiende (una celda editada a
    mano no puede tumbar a quien mide)."""
    try:
        d = json.loads(s) if isinstance(s, str) and s.strip() else {}
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def acierto(registros) -> dict:
    """Cuánto se acepta de lo que se propone, sobre registros de partes revisados.

    `{"partes", "nada", "a": {"ofrecidas", "marcadas"}, "e": {...}, "q": {...}}`. ⚠️ Los
    tres tipos se cuentan APARTE porque no significan lo mismo: una actividad propuesta
    suelta («a») es una afirmación de la app, y rechazarla es un error suyo; en la lista de
    una etapa («e») o en las opciones de una pregunta («q») casi todo queda sin marcar POR
    DISEÑO, y juntarlos hundiría la cifra sin que la app hubiera fallado en nada.
    """
    out = {t: {"ofrecidas": 0, "marcadas": 0} for t in ("a", "e", "q")}
    out["partes"] = out["nada"] = 0
    for r in registros or []:
        d = r if isinstance(r, dict) else leer_registro(r)
        if not d:
            continue
        out["partes"] += 1
        out["nada"] += bool(d.get("nada"))
        for x in (d.get("destinos") or {}).values():
            if not isinstance(x, dict) or not isinstance(x.get("ofrecidas"), list):
                continue                          # recortado a cuentas: no se puede cruzar
            marc = {(int(o), str(a)) for o, a in x.get("marcadas") or []}
            for of in x["ofrecidas"]:
                if not isinstance(of, list) or len(of) < 3 or of[0] not in ("a", "e", "q"):
                    continue
                out[of[0]]["ofrecidas"] += 1
                out[of[0]]["marcadas"] += (int(of[1]), str(of[2])) in marc
    return out
