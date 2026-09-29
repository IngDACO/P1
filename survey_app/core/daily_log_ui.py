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

import streamlit as st

from core import clock, daily_log as DL, flash, theme
from core.i18n import t

logger = logging.getLogger(__name__)


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
    _hora = _creado[11:16] if _creado[:10] == _dia and len(_creado) >= 16 else _creado
    st.markdown(
        theme.chip(f"{_dia} · {_autor}" + (f" · {_hora}" if _hora else ""),
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
    for e in p["etapas"]:
        with st.expander(t(":material/checklist: Your log names «{e}» — which of these did "
                           "you finish?", e=e["termino"]), expanded=True):
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
    # ⚠️ Sin repetidos: la misma actividad puede salir en una etapa Y en una pregunta
    # («Lights»), y marcada en las dos el botón decía «3 marcadas» para 2 créditos.
    return {"marcadas": list(dict.fromkeys(tick)), "ofrecidas": ofr,
            "hechas": list(dict.fromkeys(hechas))}


def _propuestas(r, pid, grupo, usuario, key_prefix) -> None:
    """La tarjeta de UN parte propio y sin revisar."""
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
    if not SP.plan_de_obra(prj) or SP.version_desfasada(prj):
        return

    plan0 = SP.plan_de_obra(prj)
    asc = V.ascensores(texto)
    # ⚠️ Solo se pregunta por un «L2» si lo que colgaría de él PROPONE algo: preguntar
    # algo cuya respuesta no cambia nada es fricción, y enseña a contestar sin leer.
    dudosos = [d for d in asc["dudosos"] if PP.propone_algo(PP.lineas_de(texto, d), plan0)]
    partir = asc["separar"] or bool(dudosos)
    tambien, asignacion = [], {"": str(pid)}
    ops = _asignables(usuario, grupo, pid) if partir else None
    # Vista previa: ¿hay algo que confirmar? Si no, no se pinta tarjeta. ⚠️ Si la nota se
    # va a repartir, sin lo acreditado: lo hecho depende de la obra de DESTINO, y con lo
    # de esta, un ascensor ya terminado aquí escondería el trabajo de otro.
    if not PP.propuestas(texto, plan0, {} if partir else SP.acreditado(pid))["hay_algo"]:
        return

    with st.container(border=True):
        st.markdown(t("##### :material/auto_awesome: What the app read in your log"))
        st.caption(t("Tick only what is true. Nothing is credited until you confirm."))
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
                    if PP.propone_algo(PP.lineas_de(texto, a, tambien), plan0)]
            if _rel:
                st.caption(t(":material/call_split: Your log talks about more than one lift. "
                             "Choose the job for each one — what you leave unchosen is not "
                             "proposed anywhere.") if len(asc2["ascensores"]) > 1 else
                           t(":material/call_split: Choose the job for {x} — until you do, "
                             "it is not proposed anywhere.",
                             x=", ".join("«%s»" % a for a in _rel)))
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
            # ⚠️ El destino se nombra también cuando es UNO solo pero no es esta obra:
            # «Install headers» a secas, debajo del parte de Lift 1, se leería como de Lift 1.
            _cab = len(destinos) > 1 or d != str(pid)
            if _cab:
                st.markdown("**→ %s**" % (ops or {}).get(d, d))
            por_destino[d] = _pintar(PP.propuestas(txt, plan, SP.acreditado(d)),
                                     "%s_%s" % (kp, d), titulo=not _cab)

        n = sum(len(v["marcadas"]) for v in por_destino.values())

        def _registro(nada):
            # ⚠️ Lo que se ENSEÑÓ y lo que se marcó, en la misma escritura que la revisión:
            # sin esto solo quedaba lo aceptado, y el acierto no se puede medir (v524).
            return PP.registro(por_destino, respuestas, elegidas, app=_version_app(),
                               nada=nada)

        c1, c2 = st.columns([3, 2])
        if c1.button(t(":material/done_all: Confirm the {n} ticked", n=n) if n
                     else t(":material/done_all: Confirm"), key="%s_ok" % kp,
                     type="primary", disabled=(n == 0), width="stretch"):
            _mias = _asignables(usuario, grupo, pid)
            errores = []
            for d, res in por_destino.items():
                ticks = res["marcadas"]
                if not ticks:
                    continue
                # ⚠️ Se vuelve a comprobar al escribir: solo a obras SUYAS.
                if d not in _mias:
                    errores.append(t("{x} is not one of your jobs.", x=d))
                    continue
                ok, msg = SP.acreditar(d, grupo, prjs[d], PP.creditos(ticks, lid),
                                       quien=usuario, origen=SP.PARTE)
                if not ok:
                    errores.append(msg)
            if errores:
                # ⚠️ No se marca revisado: si algo falló, la tarjeta tiene que seguir ahí.
                st.error(" · ".join(str(e) for e in errores))
            else:
                ok, msg = DL.marcar_revisado(lid, usuario, propuestas=_registro(False))
                (flash.exito if ok else flash.error)(
                    t("Credited {n} activities from your log.", n=n) if ok else msg)
                st.rerun()
        if c2.button(t("Nothing to credit"), key="%s_no" % kp, type="tertiary",
                     width="stretch"):
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
    st.caption(t(":material/task_alt: Proposals reviewed by {q} · {n} activities credited "
                 "from this log", q=str(r.get("ReviewedBy", "") or "—"), n=n))


def render_campo(pid, grupo, usuario, key_prefix="fld") -> None:
    """Lo que ve y usa quien está en la obra."""
    theme.section(t("Daily log"),
                  t("Write what you did today, in your own words."))

    _k = f"{key_prefix}_dl_txt_{pid}"
    _kf = f"{key_prefix}_dl_dia_{pid}"
    _hoy = clock.today(grupo)

    txt = st.text_area(
        t("What did you do today?"), key=_k, height=140,
        placeholder=t("e.g. Finished the bedplates on levels 3 and 4. Started running "
                      "the shaft wiring. Waiting on the landing door frames."),
        label_visibility="collapsed")

    # ⚠️ El contador solo aparece cuando ya se acerca al tope: enseñarlo desde el
    # carácter uno es ruido y le dice a quien escribe que hay un examen de longitud.
    if len(txt or "") > DL.MAX_TEXTO * 0.8:
        st.caption(t("{n} of {max} characters.", n=len(txt), max=DL.MAX_TEXTO))

    with st.expander(t("It is not for today"), icon=":material/event:"):
        dia = st.date_input(t("Day being reported"), value=_hoy, max_value=_hoy,
                            key=_kf, format="DD/MM/YYYY")
    if st.button(t(":material/save: Save the daily log"), key=f"{key_prefix}_dl_save_{pid}",
                 type="primary", width="stretch"):
        ok, msg = DL.crear(pid, grupo, txt, usuario, dia=dia)
        if ok:
            # ⚠️ La caja SOLO se vacía cuando la hoja confirmó. Si falla, el texto sigue
            # ahí: quien acaba de escribir doscientas palabras en un sótano no las
            # vuelve a escribir, deja de usar la pantalla (ver la nota de `daily_log`).
            st.session_state.pop(_k, None)
            flash.exito(t("Daily log saved."))
            st.rerun()
        else:
            st.error(msg)

    _mios = DL.partes(pid)
    if not _mios:
        st.caption(t("No daily logs yet for this job."))
        return
    st.markdown("")
    st.caption(t("{n} logs · {d} days covered", n=len(_mios),
                 d=DL.dias_cubiertos(pid)))
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
    if not _p:
        st.caption(t("The crew has not written any daily log for this job yet."))
        return
    st.caption(t("{n} logs · {d} days covered", n=len(_p), d=DL.dias_cubiertos(pid)))
    for r in _p[:25]:
        # v523 · El admin ve si el autor revisó las propuestas y cuánto acreditó desde el
        # parte. No confirma por él: quien no escribió el parte no sabe si fue así.
        _linea(r, False, key_prefix, extra=lambda r=r: _estado_revision(r, pid))
    if len(_p) > 25:
        st.caption(t("…and {n} older ones.", n=len(_p) - 25))
