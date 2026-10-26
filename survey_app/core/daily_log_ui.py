# -*- coding: utf-8 -*-
"""El parte diario en pantalla: escribirlo (campo) y leerlo (admin) — v516.

⚠️ Esto se escribe en un MÓVIL, de pie, al final de la jornada. Lo que decide si se usa
o no es cuántos toques hay entre abrir la obra y haber guardado. Así que: una caja de
texto y un botón. Sin fecha que elegir (es hoy), sin categoría, sin adjuntos.

⚠️ La fecha se puede cambiar, pero está ESCONDIDA detrás de un desplegable cerrado. El
caso normal —escribo hoy lo de hoy— no paga el precio de un widget más, y el caso raro
—ayer no hubo cobertura— sigue siendo posible. Poner el selector siempre visible habría
invitado a tocarlo, y un parte con fecha equivocada es peor que uno sin fecha.
"""
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from core import clock, daily_log as DL, flash, theme
from core.i18n import t
from core.maps import literal_md

logger = logging.getLogger(__name__)


def _nombre(login) -> str:
    """El NOMBRE de una persona para mostrar (v559): salía el login («campo000»). El login
    sigue siendo la identidad para todo lo demás. Sin nombre, el login."""
    _u = str(login or "")
    try:
        from core import auth
        return auth.etiqueta_usuarios(auth.list_users()).get(_u, _u)
    except Exception:
        return _u


def _dmy(iso) -> str:
    """«2026-09-26» → «26/09/2026» (v559: los partes enseñaban la fecha en ISO)."""
    s = str(iso or "")
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
    return s


def _cuantos(n, d) -> str:
    """«1 log · 1 day covered» / «3 logs · 2 days covered» (v559: salía «1 logs»)."""
    _a = t("1 log") if n == 1 else t("{n} logs", n=n)
    _b = t("1 day covered") if d == 1 else t("{d} days covered", d=d)
    return f"{_a} · {_b}"


def _linea(r, puede_borrar, key_prefix, extra=None) -> None:
    """Un parte ya guardado: quién, cuándo y qué escribió. `extra` (v523) pinta debajo lo
    que la app leyó en él, antes del separador."""
    _autor = str(r.get("Author", "") or "—")
    _dia = str(r.get("Date", "") or "")
    _creado = str(r.get("Created", "") or "")
    # ⚠️ La hora solo se enseña si NO coincide con el día: «23/09 · 18:40» informa, pero
    # repetir la fecha dos veces en una línea de móvil solo gasta ancho.
    # ⚠️ Recortada a `hh:mm`: `Created` guarda SEGUNDOS para poder ordenar dos partes del
    # mismo minuto (ver `daily_log.partes`), pero a quien lee no le dicen nada.
    # ⚠️ v526 · Y cuando el parte es de OTRO día, la fecha de escritura va entera pero
    # sin segundos: salía «2026-09-29 16:35:28» (visto en producción).
    # ⚠️ v559 · las fechas en DD/MM/YYYY y el autor por su NOMBRE (salía
    # «2026-09-26 · campo000 · 2026-09-29 16:35»).
    _hora = (_creado[11:16] if _creado[:10] == _dia and len(_creado) >= 16
             else (f"{_dmy(_creado[:10])} {_creado[11:16]}".strip() if _creado else ""))
    st.markdown(
        theme.chip(f"{_dmy(_dia)} · {_nombre(_autor) if _autor != '—' else _autor}"
                   + (f" · {_hora}" if _hora else ""),
                   color=theme.GRIS_TXT),
        unsafe_allow_html=True)
    # ⚠️ v523 · Con sus saltos de línea: en Markdown un salto simple se come y el parte
    # salía en un solo párrafo, y la tarjeta de abajo cita LÍNEAS como prueba — quien
    # confirma tiene que poder encontrar «Installed header» en lo que escribió.
    st.markdown(str(r.get("Text", "")).replace("\n", "  \n"))
    if puede_borrar:
        if st.button(t(":material/delete: Delete"), key=f"{key_prefix}_del_{r.get('ID')}",
                     type="tertiary"):
            ok, msg = DL.borrar(r.get("ID"), _autor)
            (flash.exito if ok else flash.error)(msg)
            st.rerun()
    if extra is not None:
        # ⚠️ Lo de la app NUNCA tumba el parte: si algo falla leyéndolo, el campo tiene que
        # poder seguir escribiendo y viendo los suyos. Se dice en una línea y se sigue.
        try:
            extra()
        except Exception as e:
            logger.warning("daily_log_ui: propuestas de %s: %s", r.get("ID"), e)
            st.caption(t("The suggestions for this log are unavailable right now ({e}).", e=e))
    st.divider()


# ═════════════════════════════════════════════════════════════════
# v523 · Lo que la app leyó en el parte, para que su AUTOR confirme
# ═════════════════════════════════════════════════════════════════
# ⚠️ La regla del usuario (28/09/2026): «la app no asume nada sin consultar». Por eso:
#   · todo empieza DESMARCADO — la app sugiere, quien escribió el parte decide;
#   · nada se acredita hasta que pulsa «Confirmar»; «Nada que acreditar» lo cierra sin
#     tocar el avance;
#   · con varios ascensores, cada trozo va a la obra que ÉL elija de las suyas; lo que no
#     asigne no se propone en ningún sitio;
#   · «L3» primero se pregunta: ¿ascensor o planta?
_AVISO = {
    "incompleto": ":material/warning: The log says this is not finished yet.",
    "otro_dia": ":material/event: The log says this was done on another day.",
    # v607 · el agente lo leyó como hecho, pero el parte lo lista bajo «Issues/Pending».
    "bajo_pendiente": ":material/pending: Your log lists this under «Issues/Pending». Tick it "
                      "only if it was finished.",
}
_OTRA = "__otra__"


def _asignables(usuario, grupo, pid) -> dict:
    """`{pid: etiqueta}` de las obras a las que puede ir un trozo del parte: las SUYAS.
    La del parte, primero. ⚠️ Etiqueta por ID (`etiqueta_proyectos`): dos ascensores de
    la misma torre se llaman igual y por nombre uno se volvería inalcanzable."""
    from core import projects as P
    try:
        proys = P.list_projects_for_field(usuario, grupo)
    except Exception as e:
        logger.warning("daily_log_ui._asignables: %s", e)
        proys = []
    _et = P.etiqueta_proyectos(proys)
    out = {str(pid): _et.get(str(pid), str(pid))}
    for p in proys:
        _i = str(p.get("ID", "") or "")
        if _i and _i not in out:
            out[_i] = _et.get(_i, _i)
    return out


def _version_app() -> str:
    """La versión del CÓDIGO que hizo las propuestas, para el registro de la revisión: el
    vocabulario cambia de una versión a otra, y un acierto medido sin saber con cuál no
    dice nada. Import perezoso (`home_ui` es la shell); si falla, vacío — nunca tumba."""
    try:
        from core import home_ui
        return home_ui._version()
    except Exception:
        return ""


def _prueba(item) -> None:
    """La línea del parte que respalda la propuesta, y sus avisos."""
    _txt = "  ·  ".join("“%s”" % p for p in (item.get("pruebas") or [])[:2])
    _extra = []
    if item.get("aviso") in _AVISO:
        _extra.append(t(_AVISO[item["aviso"]]))
    if item.get("cuenta") is False:
        _extra.append(t(":material/info: For the record only — it does not change the progress."))
    if _txt or _extra:
        st.caption("  \n".join([x for x in [_txt] + _extra if x]))


def _pintar(p, k, titulo=True) -> dict:
    """Las propuestas de UN destino. Devuelve lo MARCADO y, desde v524, lo que se ENSEÑÓ:
    `{"marcadas": [(orden, actividad)], "ofrecidas": [[tipo, orden, actividad, termino]],
    "hechas": [(orden, actividad)]}` — el registro que mide el acierto.
    ⚠️ Se anota AL PINTAR cada casilla, no se deduce después de `p`: lo que se guarda tiene
    que ser exactamente lo que vio quien confirmó, y dos listas armadas por separado
    acabarían diciendo cosas distintas (regla v361).
    `titulo=False` cuando encima ya va «→ obra»: repetir el rótulo en cada trozo es ruido."""
    tick, ofr, hechas = [], [], []

    def _ya(o):
        st.markdown(":green[:material/check_circle:] %s · %s"
                    % (o["actividad"], t("already credited")))
        hechas.append((o["orden"], o["actividad"]))

    if p["actividades"]:
        if titulo:
            st.markdown(t("**Activities your log mentions**"))
        for f in p["actividades"]:
            _et = "#%d · %s" % (f["orden"], f["etapa"])
            if f["hecha"]:
                _ya(f)
            else:
                ofr.append(["a", f["orden"], f["actividad"], f.get("termino", "")])
                if st.checkbox(f["actividad"], key="%s_a_%d_%s" % (k, f["orden"], f["actividad"]),
                               help=_et):
                    tick.append((f["orden"], f["actividad"]))
            _prueba(f)
    for _ie, e in enumerate(p["etapas"]):
        with st.expander(t(":material/checklist: Your log names «{e}» — which of these did "
                           "you finish?", e=e["termino"]), expanded=True, key="%s_exp_%d" % (k, _ie)):
            _prueba(e)
            for o in e["opciones"]:
                if o["hecha"]:
                    _ya(o)
                    continue
                ofr.append(["e", o["orden"], o["actividad"], e["termino"]])
                if st.checkbox(o["actividad"],
                               key="%s_e_%d_%s" % (k, o["orden"], o["actividad"])):
                    tick.append((o["orden"], o["actividad"]))
    for q in p["preguntas"]:
        st.markdown(t("**«{x}» can mean several things — which one was it?**", x=q["termino"]))
        st.caption(q.get("regla", ""))
        _prueba(q)
        for o in q["opciones"]:
            if o["hecha"]:
                _ya(o)
                continue
            ofr.append(["q", o["orden"], o["actividad"], q["termino"]])
            if st.checkbox("%s  ·  #%d %s" % (o["actividad"], o["orden"], o["etapa"]),
                           key="%s_q_%s_%d_%s" % (k, q["termino"], o["orden"], o["actividad"])):
                tick.append((o["orden"], o["actividad"]))
    if p["pendientes"]:
        with st.expander(t(":material/pending: Pending in your log — not credited ({n})",
                           n=len(p["pendientes"]))):
            for x in p["pendientes"]:
                st.caption("  ·  ".join("“%s”" % y for y in x["pruebas"]) or x["termino"])
    for x in p["retiradas"]:
        st.caption(":material/help: %s  \n%s" % (t(x["motivo"]), "  ·  ".join(
            "“%s”" % y for y in x["pruebas"])))
    if p["fuera"]:
        st.caption(t(":material/block: Mentioned, but not in this job's plan: {x}",
                     x=", ".join(sorted({f["actividad"] for f in p["fuera"]}))))
    _resto_agente(p)
    # ⚠️ Sin repetidos: la misma actividad puede salir en una etapa Y en una pregunta
    # («Lights»), y marcada en las dos el botón decía «3 marcadas» para 2 créditos.
    return {"marcadas": list(dict.fromkeys(tick)), "ofrecidas": ofr,
            "hechas": list(dict.fromkeys(hechas))}


def _resto_agente(p) -> None:
    """v607 · Lo que solo el agente distingue, para que ningún trozo del parte quede sin
    decir qué pasó con él: lo EMPEZADO (no se acredita), los PROBLEMAS y lo que no es avance,
    con su motivo. En las propuestas del vocabulario estas claves no existen: no pinta nada."""
    _emp = p.get("empezadas") or []
    if _emp:
        st.caption(t(":material/pending: Started, not finished — not credited:") + "  \n"
                   + "  \n".join("“%s”" % literal_md(x["texto"]) for x in _emp))
    for x in p.get("problemas") or []:
        st.caption(t(":material/report: Something the office should know:") + "  \n“%s”%s" % (
            literal_md(x["texto"]), (" — %s" % literal_md(x["motivo"])) if x.get("motivo") else ""))
    _ap = p.get("aparte") or []
    if _ap:
        # ⚠️ Cerrado: en el corpus real (examen C) es la tercera clase más frecuente —cabeceras
        # del día, «Issues:», «No issues», viajes—, y abierto alargaba cada tarjeta en el móvil.
        # Sigue ahí, con su motivo: nada se ignora, pero no estorba.
        with st.expander(t(":material/info: Not progress on this job ({n})", n=len(_ap))):
            st.caption("  \n".join(
                "“%s”%s" % (literal_md(x["texto"]),
                            (" — %s" % literal_md(x["motivo"])) if x.get("motivo") else "")
                for x in _ap))


# ═════════════════════════════════════════════════════════════════
# v607 · El agente: lee el parte con el contexto de la obra (`parte_agente`)
# ═════════════════════════════════════════════════════════════════
# ⚠️ Regla de siempre: el agente PROPONE, el autor marca. Lo que cambia es QUIÉN lee el
# parte: un modelo con el plan sellado, lo acreditado y el documento del oficio, en vez de
# la lista de palabras. Si no puede (sin clave, error, tarda), la tarjeta sale como antes.
_LECT = "_ag_lecturas"          # {log_id: lectura} leídas en ESTA sesión
_FALLOS = "_ag_fallos"          # {log_id: (instante, motivo)}
_RELEER = "_ag_releer"          # la petición de «leer otra vez» que dejó el botón
# ⚠️ Un parte cuya lectura falló no se reintenta en cada recarga: cada intento puede tardar
# hasta ~40 s (tiempo máximo y un reintento) con la pantalla quieta.
_ESPERA_FALLO = 600

_MOTIVOS = {
    "timeout": "it took too long", "rate_limit": "too many requests right now",
    "connection": "no connection to the assistant", "auth": "the assistant's key was rejected",
    "refusal": "the assistant declined to read it", "json": "its answer could not be read",
    "max_tokens": "its answer was cut short", "max_rondas": "it already read this log {n} times",
}


def _motivo(m) -> str:
    from core import parte_agente as AG
    _m = str(m or "")
    if _m in _MOTIVOS:
        return t(_MOTIVOS[_m], n=AG.MAX_RONDAS)
    return t("an error from the assistant ({m})", m=_m or "?")


def _lectura(r, plan) -> dict:
    """La lectura del agente de este parte para este plan, si ya existe (de esta sesión o de
    la hoja), o `{}`. ⚠️ No llama al modelo: eso solo lo hacen `_leer_pendientes` y
    `_relectura`, arriba, antes de pintar."""
    from core import parte_agente as AG
    lid = str(r.get("ID", "") or "")
    texto = str(r.get("Text", "") or "")
    for reg in ((st.session_state.get(_LECT) or {}).get(lid), AG.de_json(r.get("Reading", ""))):
        if reg and AG.vigente(reg, texto, plan):
            return reg
    return {}


def _fallo(lid) -> str:
    """El motivo si la lectura de este parte falló hace poco, o ""."""
    _f = (st.session_state.get(_FALLOS) or {}).get(str(lid))
    return _f[1] if _f and time.time() - _f[0] < _ESPERA_FALLO else ""


def _apuntar(lecturas, fallos) -> None:
    """Lo leído, a la sesión y a la hoja (`Reading`); lo fallido, a la sesión. ⚠️ Si la hoja
    no lo guarda (cuota), la sesión sí: en esta sesión no se vuelve a pagar."""
    if lecturas:
        st.session_state.setdefault(_LECT, {}).update(lecturas)
        from core import parte_agente as AG
        ok, _n = DL.guardar_lecturas({k: AG.a_json(v) for k, v in lecturas.items()})
        if not ok:
            logger.warning("daily_log_ui: no se guardaron %d lecturas en la hoja", len(lecturas))
    if fallos:
        st.session_state.setdefault(_FALLOS, {}).update(
            {k: (time.time(), m) for k, m in fallos.items()})


def _plan_de(pid) -> list:
    """El plan contra el que se lee: el de la obra, si se puede acreditar contra él."""
    from core import projects as P
    from core import stage_progress as SP
    prj = P.get_project(pid) or {}
    if not SP.plan_de_obra(prj) or SP.version_desfasada(prj):
        return []
    return SP.plan_de_obra(prj)


def _leer_pendientes(pid, usuario, partes) -> None:
    """Lee con el agente los partes PROPIOS sin revisar que aún no tienen lectura.

    ⚠️ El primero SOLO y el resto en paralelo: llamadas simultáneas no comparten la caché del
    prompt (cada una la escribe y la paga, medido: US$0,05 por parte en paralelo frente a
    US$0,0065 leyendo de la caché), y el primero la deja escrita para los demás.
    """
    from core import parte_agente as AG
    from core import stage_progress as SP
    from core.i18n import idioma
    _k = AG.clave_api()
    if not AG.disponible(_k):
        return
    plan = _plan_de(pid)
    if not plan:
        return
    falta = [r for r in partes
             if str(r.get("Author", "")) == str(usuario) and not DL.revisado(r)
             and str(r.get("Text", "")).strip() and not _lectura(r, plan)
             and not _fallo(r.get("ID"))]
    if not falta:
        return
    mapa, idi = SP.acreditado(pid), idioma()

    def _uno(r):
        return str(r.get("ID", "")), AG.leer(str(r.get("Text", "")), plan, str(r.get("Date", "")),
                                            mapa, None, None, idi, _k)

    with st.spinner(t("The assistant is reading your log…") if len(falta) == 1
                    else t("The assistant is reading your {n} logs…", n=len(falta))):
        res = [_uno(falta[0])]
        if len(falta) > 1:
            with ThreadPoolExecutor(max_workers=4) as ex:
                res += list(ex.map(_uno, falta[1:]))
    _apuntar({lid: reg for lid, (reg, _m) in res if reg},
             {lid: m for lid, (reg, m) in res if not reg})


def _pedir_relectura(lid, claves) -> None:
    """`on_click` de «Read it again»: solo APUNTA lo que el autor escribió. La lectura —unos
    segundos— se hace arriba, antes de pintar la lista (trampa 37: una acción lenta dentro de
    un bloque con clave deja fantasmas)."""
    resp = []
    for linea, texto, k in claves:
        v = str(st.session_state.get(k, "") or "").strip()
        if v:
            resp.append({"linea": linea, "texto": texto, "respuesta": v[:500]})
    st.session_state[_RELEER] = {"lid": str(lid), "respuestas": resp}


def _relectura(pid, usuario, partes) -> None:
    """Atiende la petición de «Read it again»: una lectura NUEVA con la anterior y TODAS las
    respuestas del autor como datos (`parte_agente.leer`)."""
    pet = st.session_state.pop(_RELEER, None)
    if not pet:
        return
    if not pet.get("respuestas"):
        flash.aviso(t("Write what you meant first, then ask the assistant to read it again."))
        st.rerun()
    from core import parte_agente as AG
    from core import stage_progress as SP
    from core.i18n import idioma
    r = next((x for x in partes if str(x.get("ID", "")) == pet["lid"]), None)
    plan = _plan_de(pid)
    # ⚠️ Solo el AUTOR y solo sin revisar: como confirmar (v523).
    if r is None or str(r.get("Author", "")) != str(usuario) or DL.revisado(r) or not plan:
        return
    previa = _lectura(r, plan)
    if not previa:
        return
    with st.spinner(t("The assistant is reading your log again…")):
        reg, mot = AG.leer(str(r.get("Text", "")), plan, str(r.get("Date", "")),
                           SP.acreditado(pid), previa,
                           list(previa.get("respuestas") or []) + pet["respuestas"], idioma())
    if reg:
        _apuntar({pet["lid"]: reg}, {})
        flash.exito(t("The assistant read your log again with your answers."))
    else:
        # ⚠️ Lo escrito NO se pierde: las cajas llevan la ronda en la clave y la ronda no
        # avanzó, así que siguen con su texto para volver a intentarlo.
        flash.error(t("The assistant could not read it again ({m}). What you wrote is still "
                      "there: try again in a minute.", m=_motivo(mot)))
    st.rerun()


def _hablar(reg, lid, kp) -> None:
    """Lo que el agente no entendió, con una caja para contestar cada cosa, otra para decirle
    lo que se le escapó, y «Read it again». ⚠️ Es la parte de «preguntar» que pidió el
    usuario: antes, lo que la app no reconocía no se enseñaba y parecía ignorado."""
    from core import parte_agente as AG
    _ronda = int(reg.get("rondas", 1) or 1)
    claves = []
    _dudas = AG.sin_entender(reg)
    if _dudas:
        st.markdown(t("**Not understood — tell the assistant what you meant**"))
        for i, f in enumerate(_dudas):
            _k = "%s_ag%d_%d" % (kp, _ronda, i)
            st.text_input("“%s”" % literal_md(f.get("texto", "")), key=_k,
                          placeholder=f.get("pregunta") or t("What did you mean?"))
            claves.append((f.get("linea"), f.get("texto", ""), _k))
    _kg = "%s_ag%d_gen" % (kp, _ronda)
    with st.expander(t("Something missing or wrong? Tell the assistant"), icon=":material/chat:",
                     key="%s_ag_exp%d" % (kp, _ronda)):
        st.text_input(t("What it missed or got wrong"), key=_kg,
                      placeholder=t("e.g. «the motor» was the machine on the bedplate"))
    claves.append((0, "", _kg))
    if _ronda < AG.MAX_RONDAS:
        st.button(t(":material/refresh: Read it again with my answers"), key="%s_ag_releer" % kp,
                  on_click=_pedir_relectura, args=(lid, claves), width="stretch")
    else:
        st.caption(t(":material/info: The assistant has read this log {n} times. Tick what is "
                     "right here, and mark anything else in «Progress».", n=_ronda))


def _sin_agente(lid) -> None:
    """Cuando el agente está puesto pero NO pudo leer este parte: dicho, para que la lista de
    palabras no se tome por lo que leyó el agente. Sin agente (sin clave), nada que decir."""
    from core import parte_agente as AG
    _m = _fallo(lid)
    if _m and AG.disponible():
        st.caption(t(":material/info: The assistant could not read this log ({m}), so this comes "
                     "from the app's word list. It will try again in a few minutes.",
                     m=_motivo(_m)))


def _sin_plan(pid) -> str:
    """v586 · Por qué los partes de esta obra NO van a proponer avance: `"sin"`, la versión
    del plan si es de un catálogo anterior, o `""` si sí pueden.

    ⚠️ Hasta v585 la tarjeta se callaba (`return`) y el parte se guardaba sin más: el
    usuario escribió dos partes el 15/10 en obras sin plan y esperó a ver moverse la curva.
    Una localización interna no tiene avance: ahí no se dice nada.
    """
    from core import projects as P
    from core import stage_progress as SP
    prj = P.get_project(pid) or {}
    if P.es_interno(prj):
        return ""
    return SP.version_desfasada(prj) or ("" if SP.plan_de_obra(prj) else "sin")


def _nada_que_confirmar(p) -> None:
    """v586 · Un parte sin nada que CONFIRMAR lo dice: antes no salía nada debajo y no se
    sabía si la app lo había leído. `p` = `parte_propuestas.propuestas`."""
    if p["actividades"] or p["etapas"] or p["preguntas"]:
        st.caption(t(":material/task_alt: Everything this log mentions is already credited."))
        return
    if p["fuera"]:
        st.caption(t(":material/block: Mentioned, but not in this job's plan: {x}",
                     x=", ".join(sorted({f["actividad"] for f in p["fuera"]}))))
    if p["pendientes"]:
        st.caption(t(":material/pending: What your log lists as still to do is not credited ({n}).",
                     n=len(p["pendientes"])))
    for x in p["retiradas"]:
        st.caption(":material/help: %s" % t(x["motivo"]))
    for x in p["no_avance"]:
        st.caption(":material/info: %s" % t(x["motivo"]))
    _resto_agente(p)
    if not (p["fuera"] or p["pendientes"] or p["retiradas"] or p["no_avance"]
            or p.get("empezadas") or p.get("problemas") or p.get("aparte")):
        st.caption(t(":material/search_off: The app did not recognise any activity of this job "
                     "in this log. If something advanced, mark it in «Progress»."))


def _propuestas(r, pid, grupo, usuario, key_prefix) -> None:
    """La tarjeta de UN parte propio y sin revisar."""
    from core import parte_agente as AG
    from core import parte_propuestas as PP
    from core import projects as P
    from core import stage_progress as SP
    from core import vocabulario as V
    lid = str(r.get("ID", "") or "")
    texto = str(r.get("Text", "") or "")
    kp = "%s_pp_%s" % (key_prefix, lid)
    prj = P.get_project(pid) or {}
    # ⚠️ Sin plan sellado (obra anterior a v512) o con el catálogo desfasado no hay contra
    # qué acreditar: no se propone nada que después `acreditar` rechazaría.
    # v586 · Lo DICE una vez, arriba del todo (`_sin_plan`), no debajo de cada parte.
    if not SP.plan_de_obra(prj) or SP.version_desfasada(prj):
        return

    plan0 = SP.plan_de_obra(prj)
    # v607 · Lo que leyó el agente, si lo leyó. Con lectura, TODO lo de abajo (ascensores,
    # reparto, destinos) sale de ella; sin lectura, del vocabulario, como hasta v606.
    reg = _lectura(r, plan0)

    def _props(txt, plan, mapa, lineas=None):
        if reg:
            return AG.propuestas(reg, plan, mapa, texto, lineas)
        return PP.propuestas(txt, plan, mapa)

    def _propone(lineas):
        if reg:
            return AG.propone_algo(reg, plan0, lineas, texto)
        return PP.propone_algo(lineas, plan0)

    asc = V.ascensores(texto)
    # ⚠️ Solo se pregunta por un «L2» si lo que colgaría de él PROPONE algo: preguntar
    # algo cuya respuesta no cambia nada es fricción, y enseña a contestar sin leer.
    dudosos = [d for d in asc["dudosos"] if _propone(PP.lineas_de(texto, d))]
    partir = asc["separar"] or bool(dudosos)
    tambien, asignacion = [], {"": str(pid)}
    ops = _asignables(usuario, grupo, pid) if partir else None
    # Vista previa: ¿hay algo que confirmar? Si no, no se pinta tarjeta. ⚠️ Si la nota se
    # va a repartir, sin lo acreditado: lo hecho depende de la obra de DESTINO, y con lo
    # de esta, un ascensor ya terminado aquí escondería el trabajo de otro.
    _prev = _props(texto, plan0, {} if partir else SP.acreditado(pid))
    # ⚠️ v607 · Con algo SIN ENTENDER también hay tarjeta: es donde se le contesta al agente.
    if not _prev["hay_algo"] and not (reg and AG.sin_entender(reg)):
        _nada_que_confirmar(_prev)      # v586 · antes, nada debajo
        if reg:
            _hablar(reg, lid, kp)
        else:
            _sin_agente(lid)
        return

    with st.container(border=True):
        st.markdown(t("##### :material/auto_awesome: What the assistant read in your log") if reg
                    else t("##### :material/auto_awesome: What the app read in your log"))
        st.caption(t("Tick only what is true. Nothing is credited until you confirm."))
        if not reg:
            _sin_agente(lid)
        destinos = {str(pid): texto}
        # v524 · Lo que contestó y eligió, para el registro de la revisión.
        respuestas, elegidas = {}, {}
        if ops is not None:
            sin_resp = []
            for d in dudosos:
                _r = st.radio(t("In your log, «{x}» is…", x=d), ["lift", "level"],
                              format_func=lambda o: t("a lift") if o == "lift" else t("a level/floor"),
                              index=None, horizontal=True, key="%s_dud_%s" % (kp, d))
                respuestas[d] = _r
                if _r == "lift":
                    tambien.append(d)
                elif _r is None:
                    sin_resp.append(d)
            if sin_resp:
                # ⚠️ Mientras no conteste, lo que nombra «L2» no se propone en NINGUNA obra:
                # dar por hecho que es un piso también sería decidir por él.
                st.caption(t(":material/help: Until you answer, the lines that mention {x} "
                             "are not proposed anywhere.",
                             x=", ".join("«%s»" % x for x in sin_resp)))
            asc2 = V.ascensores(texto, tambien=tambien)
            # ⚠️ Selector solo para el ascensor cuyas líneas proponen algo: «lift 2 was in
            # use by builders» no necesita obra. Lo que no tiene selector no se asigna, y lo
            # no asignado no se propone — con esas líneas, no había nada que proponer.
            _rel = [a for a in asc2["ascensores"]
                    if _propone(PP.lineas_de(texto, a, tambien))]
            # ⚠️ v525 · Y las líneas que NO nombran ascensor. Con la nota repartida, mandarlas
            # a la obra del parte era decidir por él (la 2B del usuario): «cleaned the pit»
            # puede ser de cualquiera de los dos. Selector propio, sin nada elegido, y solo
            # si PROPONEN algo — se miran juntas y en orden, para que una cabecera
            # «Pendings» siga mandando sobre lo que va debajo.
            _sin_rel, _sin_ev = False, []
            if asc2["separar"] or tambien:
                _l_sin = PP.lineas_de(texto, "", tambien)
                _p_sin = _props("\n".join(_l_sin), plan0, {}, _l_sin)
                _sin_rel = _p_sin["hay_algo"]
                for x in _p_sin["actividades"] + _p_sin["etapas"] + _p_sin["preguntas"]:
                    for l in x.get("pruebas") or []:
                        if l not in _sin_ev:
                            _sin_ev.append(l)
            if _rel or _sin_rel:
                if len(asc2["ascensores"]) > 1:
                    st.caption(t(":material/call_split: Your log talks about more than one "
                                 "lift. Choose the job for each one — what you leave "
                                 "unchosen is not proposed anywhere."))
                elif not _sin_rel:
                    st.caption(t(":material/call_split: Choose the job for {x} — until you "
                                 "do, it is not proposed anywhere.",
                                 x=", ".join("«%s»" % a for a in _rel)))
                else:
                    st.caption(t(":material/call_split: Choose the job for each part of "
                                 "your log — what you leave unchosen is not proposed "
                                 "anywhere."))
                # ⚠️ `index=None` + placeholder, no una opción `None` en la lista: con la
                # opción, Streamlit ponía la «×» de borrar sobre «— choose the job —», como
                # si ya hubiera algo elegido.
                _opts = list(ops) + [_OTRA]
                for a in _rel:
                    _lab = t("Lift {n}", n=a) if a.isdigit() else a
                    asignacion[a] = st.selectbox(
                        _lab, _opts, index=None, key="%s_dest_%s" % (kp, a),
                        placeholder=t("— choose the job —"),
                        format_func=lambda o: (t("Not one of my jobs") if o == _OTRA
                                               else ops.get(o, o)))
                    elegidas[a] = asignacion[a]
                if _sin_rel:
                    asignacion[""] = st.selectbox(
                        t("Lines that don't name a lift"), _opts, index=None,
                        key="%s_dest__sin" % kp, placeholder=t("— choose the job —"),
                        format_func=lambda o: (t("Not one of my jobs") if o == _OTRA
                                               else ops.get(o, o)))
                    if _sin_ev:
                        st.caption("  ·  ".join("“%s”" % l for l in _sin_ev[:3])
                                   + ("  …" if len(_sin_ev) > 3 else ""))
                    elegidas[""] = asignacion[""]
            if asc2["separar"] or tambien or sin_resp:
                destinos = PP.reparto(texto, {k: v for k, v in asignacion.items()
                                              if v and v != _OTRA},
                                      tambien=tambien, sin_responder=sin_resp)

        por_destino, prjs = {}, {}
        for d, txt in destinos.items():
            dprj = prj if d == str(pid) else (P.get_project(d) or {})
            prjs[d] = dprj
            plan = SP.plan_de_obra(dprj)
            if not plan or SP.version_desfasada(dprj):
                st.caption(t(":material/block: {x} has no stage plan to credit against.",
                             x=(ops or {}).get(d, d)))
                continue
            # v607 · Con la nota repartida, el agente solo enseña en cada destino los trozos
            # de SUS líneas (las que `reparto` le dio); sin repartir, la nota entera.
            _p = _props(txt, plan, SP.acreditado(d), None if txt == texto else txt.splitlines())
            # ⚠️ v525 · Un trozo sin NADA que enseñar no se pinta: «Install day 12» suelto,
            # repartido a la obra del parte, dejaba un «→ obra» sin nada debajo.
            if not any(_p.get(k) for k in ("actividades", "etapas", "preguntas", "pendientes",
                                           "retiradas", "fuera", "empezadas", "problemas",
                                           "aparte")):
                continue
            # ⚠️ El destino se nombra también cuando es UNO solo pero no es esta obra:
            # «Install headers» a secas, debajo del parte de Lift 1, se leería como de Lift 1.
            _cab = len(destinos) > 1 or d != str(pid)
            if _cab:
                st.markdown("**→ %s**" % (ops or {}).get(d, d))
            por_destino[d] = _pintar(_p, "%s_%s" % (kp, d), titulo=not _cab)

        n = sum(len(v["marcadas"]) for v in por_destino.values())
        if reg:
            _hablar(reg, lid, kp)

        def _registro(nada):
            # ⚠️ Lo que se ENSEÑÓ y lo que se marcó, en la misma escritura que la revisión:
            # sin esto solo quedaba lo aceptado, y el acierto no se puede medir (v524).
            # v607 · y QUIÉN lo leyó, para medir el agente aparte del vocabulario.
            return PP.registro(por_destino, respuestas, elegidas, app=_version_app(),
                               nada=nada, lector=("%s/p%s" % (reg.get("modelo", ""),
                                                              reg.get("prompt", "")))
                               if reg else "")

        c1, c2 = st.columns([3, 2])
        if c1.button(t(":material/done_all: Confirm the {n} ticked", n=n) if n
                     else t(":material/done_all: Confirm"), key="%s_ok" % kp,
                     type="primary", disabled=(n == 0), width="stretch"):
            _mias = _asignables(usuario, grupo, pid)
            errores = []
            # ⚠️ v528 · Se VE que está guardando (unos segundos con la pantalla quieta
            # hacían creer que el clic no había entrado).
            with st.spinner(t("Saving…")):
                for d, res in por_destino.items():
                    ticks = res["marcadas"]
                    if not ticks:
                        continue
                    # ⚠️ Se vuelve a comprobar al escribir: solo a obras SUYAS.
                    if d not in _mias:
                        errores.append(t("{x} is not one of your jobs.", x=d))
                        continue
                    # ⚠️ v525 · Con la fecha del PARTE: el trabajo se hizo el día que dice
                    # el parte, no el día en que se confirma (la 1A del usuario).
                    ok, msg = SP.acreditar(d, grupo, prjs[d], PP.creditos(ticks, lid),
                                           quien=usuario, origen=SP.PARTE,
                                           fecha=str(r.get("Date", "") or ""))
                    if not ok:
                        errores.append(msg)
                if not errores:
                    ok, msg = DL.marcar_revisado(lid, usuario, propuestas=_registro(False))
            if errores:
                # ⚠️ No se marca revisado: si algo falló, la tarjeta tiene que seguir ahí.
                st.error(" · ".join(str(e) for e in errores))
            else:
                (flash.exito if ok else flash.error)(
                    t("Credited {n} activities from your log.", n=n) if ok else msg)
                st.rerun()
        if c2.button(t("Nothing to credit"), key="%s_no" % kp, type="tertiary",
                     width="stretch"):
            with st.spinner(t("Saving…")):
                ok, msg = DL.marcar_revisado(lid, usuario, propuestas=_registro(True))
            (flash.exito if ok else flash.error)(msg)
            st.rerun()


def _estado_revision(r, pid) -> None:
    """Una línea: si su autor ya revisó las propuestas y cuántas acreditó desde ahí."""
    if not DL.revisado(r):
        return
    from core import stage_progress as SP
    try:
        n = len(SP.de_parte(pid, r.get("ID")))
    except Exception:
        n = 0
    _q = str(r.get("ReviewedBy", "") or "")
    st.caption(t(":material/task_alt: Proposals reviewed by {q} · {n} activities credited "
                 "from this log", q=_nombre(_q) if _q else "—", n=n))


def render_campo(pid, grupo, usuario, key_prefix="fld", ir_avance=None) -> None:
    """Lo que ve y usa quien está en la obra. `ir_avance` (v586): lo que hace el botón que
    lleva a «Progress» cuando la obra no tiene plan (sin él, no hay botón)."""
    theme.section(t("Daily log"),
                  t("Write what you did today, in your own words."))
    _sp = _sin_plan(pid)
    if _sp:
        st.caption(t(":material/info: This job has no stage plan, so the app cannot suggest "
                     "progress from your logs. They are kept; mark what advanced in «Progress».")
                   if _sp == "sin" else
                   t(":material/info: This job's stage plan is from an older catalogue ({v}), so "
                     "the app does not suggest progress from your logs. Mark it in «Progress».",
                     v=_sp))
        if ir_avance is not None:
            st.button(t(":material/trending_up: Go to Progress"), key=f"{key_prefix}_dl_ir_av_{pid}",
                      type="tertiary", on_click=ir_avance)

    _k = f"{key_prefix}_dl_txt_{pid}"
    _kf = f"{key_prefix}_dl_dia_{pid}"
    _kv = f"{key_prefix}_dl_vaciar_{pid}"
    _hoy = clock.today(grupo)

    # ⚠️ v529 · La caja se VACÍA asignando "" ANTES de pintarla, en la pasada que sigue a un
    # guardado que la hoja confirmó. Hasta v528 se hacía `pop` de su clave: el servidor
    # quedaba en "" pero el NAVEGADOR seguía enseñando el texto, porque Streamlit solo le
    # manda el valor nuevo (`set_value`) cuando el código lo ASIGNA. Visto en producción el
    # 29/09: el parte guardado y el texto todavía en la caja, invitando a guardarlo otra
    # vez. AppTest no lo veía porque lee el valor del SERVIDOR; `verif_v529` mira el
    # `set_value`, que es lo que recibe el navegador.
    if st.session_state.pop(_kv, False):
        st.session_state[_k] = ""

    txt = st.text_area(
        t("What did you do today?"), key=_k, height=140,
        placeholder=t("e.g. Finished the bedplates on levels 3 and 4. Started running "
                      "the shaft wiring. Waiting on the landing door frames."),
        label_visibility="collapsed")

    # ⚠️ El contador solo aparece cuando ya se acerca al tope: enseñarlo desde el
    # carácter uno es ruido y le dice a quien escribe que hay un examen de longitud.
    if len(txt or "") > DL.MAX_TEXTO * 0.8:
        st.caption(t("{n} of {max} characters.", n=len(txt), max=DL.MAX_TEXTO))

    with st.expander(t("It is not for today"), icon=":material/event:", key=f"{key_prefix}_exp_otrodia_{pid}"):
        dia = st.date_input(t("Day being reported"), value=_hoy, max_value=_hoy,
                            key=_kf, format="DD/MM/YYYY")
    if st.button(t(":material/save: Save the daily log"), key=f"{key_prefix}_dl_save_{pid}",
                 type="primary", width="stretch"):
        with st.spinner(t("Saving…")):
            ok, msg = DL.crear(pid, grupo, txt, usuario, dia=dia)
        if ok:
            # ⚠️ La caja SOLO se vacía cuando la hoja confirmó. Si falla, el texto sigue
            # ahí: quien acaba de escribir doscientas palabras en un sótano no las
            # vuelve a escribir, deja de usar la pantalla (ver la nota de `daily_log`).
            # v529 · Se vacía en la pasada siguiente, ANTES de pintarla (ver arriba):
            # asignar la clave de un widget ya pintado en esta pasada revienta.
            st.session_state[_kv] = True
            flash.exito(t("Daily log saved."))
            st.rerun()
        else:
            st.error(msg)

    _mios = DL.partes(pid)
    if not _mios:
        st.caption(t("No daily logs yet for this job."))
        return
    st.markdown("")
    st.caption(_cuantos(len(_mios), DL.dias_cubiertos(pid)))
    # v607 · ANTES de pintar la lista: lo que pidió «Read it again» y los partes propios que
    # el agente todavía no leyó (solo los que se van a enseñar).
    _relectura(pid, usuario, _mios[:10])
    _leer_pendientes(pid, usuario, _mios[:10])
    _hoy_txt = _hoy.strftime("%Y-%m-%d")
    for r in _mios[:10]:
        # Borrar solo lo PROPIO y solo lo de hoy — el módulo lo vuelve a comprobar;
        # aquí es para no ofrecer un botón que va a decir que no (v499).
        _puede = (str(r.get("Author", "")) == str(usuario)
                  and str(r.get("Date", "")) == _hoy_txt)
        # v523 · Lo que la app leyó: tarjeta para confirmar en los partes PROPIOS sin
        # revisar; en el resto, solo el estado de la revisión.
        _mio = str(r.get("Author", "")) == str(usuario)
        _linea(r, _puede, key_prefix,
               extra=(lambda r=r: _propuestas(r, pid, grupo, usuario, key_prefix))
               if (_mio and not DL.revisado(r)) else (lambda r=r: _estado_revision(r, pid)))
    if len(_mios) > 10:
        st.caption(t("…and {n} older ones.", n=len(_mios) - 10))


def render_admin(pid, grupo, key_prefix="adm") -> None:
    """Lo que ve quien lleva la obra desde la oficina. Solo lectura: el parte es de
    quien lo escribió, y un admin corrigiéndolo destruiría lo único que lo hace valer."""
    _p = DL.partes(pid)
    theme.section(t("Daily logs"),
                  t("What the crew reported, in their own words."))
    _sp = _sin_plan(pid)
    if _sp:
        st.caption(t(":material/info: This job has no stage plan, so the crew's daily logs "
                     "cannot suggest progress: it is marked by hand in «Progress».")
                   if _sp == "sin" else
                   t(":material/info: This job's stage plan is from an older catalogue ({v}), so "
                     "the crew's daily logs do not suggest progress.", v=_sp))
    if not _p:
        st.caption(t("The crew has not written any daily log for this job yet."))
        return
    st.caption(_cuantos(len(_p), DL.dias_cubiertos(pid)))
    for r in _p[:25]:
        # v523 · El admin ve si el autor revisó las propuestas y cuánto acreditó desde el
        # parte. No confirma por él: quien no escribió el parte no sabe si fue así.
        _linea(r, False, key_prefix, extra=lambda r=r: _estado_revision(r, pid))
    if len(_p) > 25:
        st.caption(t("…and {n} older ones.", n=len(_p) - 25))
