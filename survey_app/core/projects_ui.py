"""
UI del panel de administración de proyectos (rol administrador).
Navegación con st.radio (NO st.tabs) para evitar mezcla de contenido.
"""
import logging

from core.i18n import t, etiqueta as _etq
from datetime import timedelta

import pandas as pd
import streamlit as st

from core import flash
import streamlit.components.v1 as components

from core import tenant
from core import projects as P
from core import auth
from core import drive_store
from core import notify
from core import alerts
from core import maps
from core.schedule import schedule_svg, schedule_svg_alto
from core import toolruns
from core import tool_save_ui
from core import credentials
from core import plan_data
from core import timeclock

# Opción neutra de los selectores de proyecto: sin ella, `st.selectbox`
# devuelve el primer elemento y se abre un proyecto que nadie eligió.
_VACIO = "— choose a project —"
from core import ui_common as ui
from core import clock
from core import tabla

logger = logging.getLogger(__name__)


def _alerts_section(pid, grupo, project_name="", allow_report=False):
    """Alarmas abiertas del proyecto + resolver; si allow_report, el campo puede reportar."""
    if not alerts.is_configured():
        return
    usuario = st.session_state.get("auth", {}).get("usuario", "")
    abiertas = alerts.list_alerts(pid, "abierta")
    st.markdown(f"**{':red[:material/notifications:] ' + str(len(abiertas)) if abiertas else ':material/notifications:'} Alerts**")
    if abiertas:
        for al in abiertas:
            emo = ":red[:material/error:]" if str(al.get("Tipo")) == "problema" else ":blue[:material/info:]"
            c = st.columns([6, 1])
            c[0].write(f"{emo} _{al.get('Fecha')}_ · **{al.get('CreadoPor')}**: {al.get('Mensaje')}")
            if c[1].button(":material/check_circle:", key=f"resolv_{al.get('ID')}", help=t("Mark as resolved")):
                ok, msg = alerts.resolve_alert(al.get("ID"), usuario)
                if ok:
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.caption(t("No open alerts."))
    if allow_report:
        with st.expander(t(":material/report: Report a problem to the administrator")):
            msg = st.text_area(t("Describe the problem or issue on site"), key=f"rep_{pid}")
            if st.button(t("Send alert"), key=f"repb_{pid}"):
                if not msg.strip():
                    st.error(t("Describe the problem."))
                else:
                    with st.spinner(t("Sending alert…")):
                        ok, res = alerts.report_problem(pid, grupo, msg.strip(), usuario, project_name)
                    (flash.exito if ok else st.error)("Alert sent to the administrator." if ok else res)
                    if ok:
                        st.rerun()


# Colores de estado para las píldoras/barras (bg suave, texto oscuro de la misma familia)
_ESTADO_COLOR = {
    "En progreso": ("#e6f1fb", "#185fa5", "#2e6da4"),
    "Planificado": ("#f1f0ec", "#5f5e5a", "#888780"),
    "Completado":  ("#eaf3de", "#3b6d11", "#639922"),
    "En pausa":    ("#faeeda", "#854f0b", "#ba7517"),
    "Cancelado":   ("#fcebeb", "#a32d2d", "#e24b4a"),
    "Archivado":   ("#eef1f5", "#6b7280", "#9aa7b8"),
}


def _estado_colors(est):
    return _ESTADO_COLOR.get(est, ("#f1f0ec", "#5f5e5a", "#888780"))


# ══════════════════════════════════════════════════════════════════════
# CENTRO DE CONTROL DEL GRUPO — cabecera con marca + KPIs
# ══════════════════════════════════════════════════════════════════════
def _delays(proys) -> dict:
    """{pid: días de retraso} (proyección SPI). Delega en core.projects.delays_for."""
    return P.delays_for(proys)


def _aheads(proys) -> dict:
    """{pid: días de adelanto} (proyección SPI)."""
    return P.aheads_for(proys)


def _kpis(grupo=None) -> dict:
    """Métricas de salud del grupo (1 lectura de cada hoja, todo cacheado)."""
    proys   = P.list_projects(grupo=grupo)
    horas   = P.project_hours_bulk(grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    ids     = {str(p.get("ID", "")) for p in proys}
    activos = [p for p in proys if str(p.get("Estado", "")) not in ("Completado", "Cancelado")]
    avances = [P._num(p.get("Avance")) for p in proys]
    return {
        "total":   len(proys),
        "activos": len(activos),
        "avg":     round(sum(avances) / len(avances)) if avances else 0,
        "riesgo":  len(P.delays_of_group(grupo)),
        "alarmas": sum(v for k, v in alarmas.items() if k in ids),
        "horas":   round(sum(horas.get(str(p.get("ID", "")), 0.0) for p in proys)),
    }


def _kpi_card(label, value, color=None, pie=None, var=None):
    """Tarjeta KPI — delega en el SISTEMA DE DISEÑO (`core/theme.py`, v283) para que
    las ~20 tarjetas repartidas por la app hablen el mismo idioma visual.

    `color` tiñe el valor y el borde de acento. `pie` es una línea de contexto
    (v303). `var` (v341) es la variación contra el periodo anterior:
    `{dif, pct, mejor}` de `finance.variacion` — se pinta como ▲/▼ con su %.
    Las tres firmas viejas siguen valiendo: los parámetros nuevos son opcionales.
    """
    from core import theme
    _acc = color or theme.AZUL                    # borde: el color vivo, no es texto
    # ⚠️ v328: el VALOR sí es texto, así que pasa por `texto_seguro`. Con AMBAR el
    # importe salía a 2.85:1 sobre blanco.
    _seg = theme.texto_seguro(color)
    _val = f"color:{_seg};" if color else ""
    _sub = ""
    if var and var.get("pct") is not None:
        # ⚠️ El color lo decide `mejor`, que NO siempre es "subió": en un costo,
        # subir es peor. Quien llama pasa el sentido correcto.
        _c = theme.VERDE if var.get("mejor") else theme.ROJO
        _f = "▲" if var["dif"] > 0 else ("▼" if var["dif"] < 0 else "=")
        _sub = (f'<div class="sub" style="color:{theme.texto_seguro(_c)}">'
                f'{_f} {abs(var["pct"]):.0f}% vs. periodo anterior</div>')
    elif pie:
        _sub = f'<div class="sub">{theme._esc(pie)}</div>'
    return (
        f'<div class="cpx-kpi" style="--cpx-accent:{_acc};min-width:104px;">'
        f'<div class="lbl">{theme._esc(label)}</div>'
        f'<div class="val" style="{_val}">{theme._esc(value)}</div>'
        f'{_sub}</div>'
    )


def _MI(name, color="", size="1.05em"):
    """Icono Material DENTRO de HTML (st.markdown unsafe_allow_html / tarjetas).
    El directivo `:material/x:` NO renderiza dentro de un <div>, pero la fuente que
    Streamlit ya carga sí, vía font-family inline. color='' → hereda del contenedor."""
    _c = f"color:{color};" if color else ""
    return (f"<span style=\"font-family:'Material Symbols Rounded';font-size:{size};"
            f"vertical-align:-2px;{_c}\">{name}</span>")


def render_group_header(grupo: str):
    """Banda de marca del grupo + resumen del día (centro de control del admin).

    ⚠️ Los KPIs ya NO se pintan aquí (v303): se mudaron a `render_kpis`, que HOME
    llama dentro de la columna del mapa. Tres números estirados a lo ancho de la
    pantalla era justo lo que la hacía verse vacía. La BANDA no se toca: el nombre
    de la empresa cliente es lo que el admin quiere ver resaltado al entrar.
    """
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);'
        'padding:14px 18px;border-radius:12px;display:flex;align-items:center;gap:12px;'
        'margin-bottom:14px;">'
        f'<span style="line-height:1;">{_MI("business", "#fff", "26px")}</span>'
        '<div style="min-width:0;">'
        f'<div style="color:#fff;font-size:21px;font-weight:800;line-height:1.1;">{grupo}</div>'
        # ⚠️ v327: era #b0c8e8 → 3.2:1 contra el extremo CLARO del degradado de la
        # banda. Los otros 5 usos de ese tono (PDF, email, cajetín) van sobre el azul
        # OSCURO, donde da 9.1:1, así que solo se cambia este. #e2ecf9 → 4.58:1.
        # El nombre de la empresa (blanco, 5.47:1) no se toca: es lo que hay que resaltar.
        '<div style="color:#e2ecf9;font-size:13px;margin-top:2px;">Company control centre</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    if not P.is_configured():
        return
    _resumen_del_dia(grupo)


def _kpi_pies(k: dict) -> tuple:
    """Los 3 pies de contexto de las tarjetas KPI, a partir del dict de `_kpis`.

    Aparte para que se pueda VERIFICAR sin montar la UI: el chequeo de que ningún pie
    se sale de los 93 px útiles llama a esta función, no a una copia de su lógica
    (una copia puede pasar el test mientras la pantalla dice otra cosa).
    """
    _act, _rie, _tot = k["activos"], k["riesgo"], k["total"]
    if not _act:
        _sub_act = f"of {_tot} in total" if _tot else "none yet"
    elif not _rie:
        _sub_act = "all up to date"
    elif _rie >= _act:                      # todos los activos van retrasados
        _sub_act = f"all {_act} behind"
    else:
        _sub_act = f"{_rie} behind"
    # ⚠️ "media de N obras" mide 94 px con N de 2 cifras → NO cabe, por 1 px. "de N obras" = 59.
    # Los pies ingleses se MIDIERON igual (v441): el tope es de ANCHO, no de caracteres.
    _sub_avg = ("no progress yet" if not k["avg"]
                else f"of {_act} job" + ("s" if _act != 1 else ""))
    # ⚠️ MEDIDOS (v441): "nobody clocked in" da 98 px y "across the company" 106, sobre
    # 93 útiles — los dos se salían. Estos dos caben con margen (67 y 79).
    _sub_hor = "no hours yet" if not k["horas"] else "company-wide"
    return _sub_act, _sub_avg, _sub_hor


def render_kpis(grupo: str):
    """Las 3 métricas del portafolio, como tarjetas KPI CLICKEABLES (v199/v283).

    v303 — cada una gana una TERCERA línea de contexto. Una caja grande con un solo
    número se ve vacía, y encogerla no lo arregla: solo la hace una caja pequeña
    vacía. El dato del pie ya lo calculaba `_kpis` (`total`, `riesgo`) y se estaba
    tirando desde v197 → **cero lecturas nuevas de Sheets**.

    ⚠️ El pie tiene **93 px útiles** (medidos: tarjeta de 124 px − 28 de padding − borde),
    y el límite es de ANCHO, no de caracteres: `media de 12 obras` y `los 12 en retraso`
    tienen los mismos 17 caracteres y miden 94 px y 84 px. Por eso el pie se escribe
    corto Y el CSS lleva `nowrap`+elipsis (theme.py): si algún día uno no cabe, se
    recorta en vez de saltar a 2 líneas y descuadrar la fila de tarjetas.
    Cada pie nuevo hay que MEDIRLO en el navegador y añadirlo a `verif_v303.py`.
    ⚠️ "en retraso" sale aquí Y en el indicador «En retraso» del resumen. Es
    deliberado (aquí es contexto del número, allí es un filtro accionable), pero es
    el único número que se repite en HOME: si se añade otro pie, que no sea de los
    9 indicadores.
    """
    if not P.is_configured():
        return
    k = _kpis(grupo)
    _act, _hor = k["activos"], k["horas"]
    _sub_act, _sub_avg, _sub_hor = _kpi_pies(k)

    m1, m2, m3 = st.columns(3)
    if m1.button(f":material/folder: Active\n\n{_act}\n\n{_sub_act}",
                 key="cpxkpi_activos", width="stretch"):
        _ir_a("proyectos", "📊 Proyectos")
    if m2.button(f":material/trending_up: Progress\n\n{k['avg']}%\n\n{_sub_avg}",
                 key="cpxkpi_avance", width="stretch"):
        _ir_a("proyectos", "📊 Proyectos")
    if m3.button(f":material/schedule: Hours\n\n{_hor} h\n\n{_sub_hor}",
                 key="cpxkpi_horas", width="stretch"):
        _ir_a("finanzas", "⏱ Horas")


def _ir_a(seccion, sub_label=None):
    """Salta a una sección (y sub-pestaña) del admin. Lo lee home_ui._aplicar_nav_pending
    en el siguiente run (antes de instanciar los radios). Usado por los elementos ACTIVOS."""
    st.session_state["_admin_nav_pending"] = (seccion, sub_label)
    st.rerun()


def _resumen_del_dia(grupo: str):
    """Resumen del día — estructura fija + elementos ACTIVOS (v199): cada indicador es
    un botón; al clickearlo muestra sus 'cuáles' + un botón para ir a la sección a actuar.
    La lectura de IA va en su propio desplegable, bajo demanda.

    ⚠️ El 2º campo de cada tupla es el **ID** de la sub-pestaña (`home_ui._SUBSECCIONES`),
    y el ID lleva EMOJI a propósito (v232: el display con icono Material es otra cosa).
    Hasta v303 aquí había displays (`":material/bar_chart: Proyectos"`) que no eran ID de
    nada: `_seccion_proyectos` compara `sub == "📊 Proyectos"` por igualdad literal, así
    que «→ Ir a Proyectos» caía en el `else` y **abría Agrupaciones**; «→ Ir a Gastos»
    abría Horas. Si tocas estos strings, cópialos de `_SUBSECCIONES`, no del sidebar.
    """
    from core import admin_digest
    try:
        d = admin_digest.group_digest(grupo)
    except Exception:
        return

    _al_n = sum(a["n"] for a in d["alarmas"])
    # slug, icono, etiqueta, urgente, count, sección, sub_pestaña, nombre_sección, detalle()
    inds = [
        ("retrasos", ":material/error:", "Behind schedule", True, len(d["retrasos"]),
         "proyectos", "📊 Proyectos", "Projects",
         lambda: ", ".join(f"{r['nombre']} ({r['dias']}d)" for r in d["retrasos"][:15])),
        ("vencidos", ":material/block:", "Overdue", True, len(d["vencidos"]),
         "proyectos", "📊 Proyectos", "Projects",
         lambda: ", ".join(f"{v['nombre']} ({v['fin']})" for v in d["vencidos"][:15])),
        ("porvencer", ":material/event:", "Due soon", False, len(d["por_vencer"]),
         "proyectos", "📊 Proyectos", "Projects",
         lambda: ", ".join(f"{v['nombre']} ({v['dias']}d)" for v in d["por_vencer"][:15])),
        ("sinasig", ":material/engineering:", "Unassigned", False, len(d["sin_asignar"]),
         "proyectos", "📊 Proyectos", "Projects",
         lambda: ", ".join(s["nombre"] for s in d["sin_asignar"][:15])),
        ("sincont", ":material/contact_page:", "No contact details", False, len(d["campo_sin_contacto"]),
         "planificacion", "👷 Usuarios", "Users",
         lambda: ", ".join(d["campo_sin_contacto"][:15])),
        ("cred", ":material/badge:", "Credentials", False, len(d.get("cred_venc", [])),
         "planificacion", "👷 Usuarios", "Users",
         lambda: ", ".join(f"{c['tipo']}·{c['usuario']} ({c['dias']}d)"
                           for c in d.get("cred_venc", [])[:15])),
        ("alarmas", ":material/notifications:", "Alarms", True, _al_n,
         "proyectos", "📊 Proyectos", "Projects",
         lambda: ", ".join(f"{a['nombre']} ({a['n']})" for a in d["alarmas"][:15])),
        ("near", ":material/health_and_safety:", "Near miss", False, len(d["near_miss"]),
         "proyectos", "📊 Proyectos", "Projects",
         lambda: ", ".join(f"{n['proyecto']} ({n['fecha']})" for n in d["near_miss"][:15])),
        ("sobrep", ":material/payments:", "Over budget", False, len(d.get("sobre_presupuesto", [])),
         "finanzas", "💰 Gastos", "Expenses",
         lambda: f"{len(d.get('sobre_presupuesto', []))} project(s) over budget"),
    ]
    _urg = sum(c for (_s, _i, _l, u, c, *_r) in inds if u)
    _tot = sum(c for (_s, _i, _l, _u, c, *_r) in inds)

    # v303: el estado sube al TÍTULO del desplegable. Gana dos cosas: deja de gastar
    # una línea entera dentro del bloque (que el usuario veía demasiado alto) y se
    # sigue leyendo aunque el resumen esté plegado.
    # ⚠️ Verificado en vivo que el markdown de color SÍ se aplica en el label de un
    # expander (`:red[...]` → rgb(255,108,108) en el <summary>).
    _p = "" if _tot == 1 else "s"
    if _tot == 0:
        _titulo = ":material/notifications: Today's summary — :green[all in order]"
    elif _urg:
        _titulo = (f":material/notifications: Today's summary — "
                   f":red[{_urg} urgent] · {_tot} pending{_p}")
    else:
        _titulo = (f":material/notifications: Today's summary — "
                   f":orange[{_tot} pending{_p}]")

    with st.expander(_titulo, expanded=True, key="cpxresumen"):
        # colorear cada botón-indicador por severidad (clase st-key-<key>, v169)
        # + v303: bajarlos de ~52 a ~35 px (medido). Son 3 filas → ~50 px menos, sin
        # tocar la estructura fija (v196) ni los nombres visibles (v200).
        # + v304: los HUECOS entre filas. Medido el bloque entero (246 px), la mitad era
        # envoltorio: 46 px de huecos verticales. ⚠️ Va acotado a `.st-key-cpxresumen`
        # (por eso el expander lleva `key`): la misma regla suelta apretaría TODOS los
        # desplegables de la app.
        _css = ["<style>",
                # ⚠️ v326: era `min-height:0`, que dejaba estos botones en 32 px —
                # por debajo del mínimo cómodo (36 px) y muy por debajo del táctil
                # (44 px). Son los que llevan a resolver cada pendiente.
                '[class*="st-key-resind_"] button{min-height:38px !important;'
                'padding:4px 8px !important;}',
                '.st-key-cpxresumen [data-testid="stVerticalBlock"]{gap:.3rem !important;}']
        for _slug, _i, _l, _urgb, _cnt, *_r in inds:
            # ⚠️ v326: el estado EN REPOSO (contador a 0) usaba #9aa7b8 sobre
            # #f4f6f9 = **2.26:1**, la mitad del mínimo WCAG. Y es el estado que
            # más se ve. Esta app se abre en obra, con sol: ahí no se leía.
            from core import theme as _T
            _bg, _fg = (("#fdecec", "#c0392b") if _urgb else ("#fff4e0", "#8a5600")) \
                       if _cnt else ("#f4f6f9", _T.GRIS_SUAVE)
            _css.append(f".st-key-resind_{_slug} button{{background:{_bg}!important;"
                        f"color:{_fg}!important;border-color:{_bg}!important;}}")
        _css.append("</style>")
        st.markdown("".join(_css), unsafe_allow_html=True)

        # v303: la pista ("toca un indicador…") era un `st.caption` que costaba una
        # línea fija. Pasa al `help` de CADA botón, donde además dice a dónde lleva.
        # ⚠️ No se puede colgar del expander: `st.expander` NO acepta `help` (firma
        # comprobada en vivo: label, expanded, *, key, icon, width, on_change…).
        # v305: DOS filas (5+4) en vez de tres de tres. El alto del botón ya está en su
        # suelo (35 px; menos es ilegible), así que lo único que queda por recortar es el
        # número de FILAS. ⚠️ Medido en el navegador: con 5 columnas el botón tiene 185 px
        # incluso con la ventana en 1150 y no se parte ninguna etiqueta; con los 9 en UNA
        # fila hacen falta ≥1180 px de contenido y por debajo se parten cuatro (y la fila
        # crece a 52, perdiendo lo ganado). Se sacrifica el agrupamiento implícito de v196
        # (Proyectos / Equipo / Obra-$ eran las 3 filas), pero el ORDEN no cambia y no
        # había ningún rótulo que lo hiciera visible.
        # `st.columns(5)` en las DOS filas a propósito: el `zip` deja la 5ª celda vacía en
        # la segunda, y así los 9 botones miden igual (con `columns(4)` saldrían más anchos).
        for _fila in (inds[:5], inds[5:]):
            for _col, (slug, icon, lbl, _urgb, cnt, _sec, _sub, _secn, _fn) in \
                    zip(st.columns(5), _fila):
                if _col.button(f"{icon} {lbl} · {cnt}", key=f"resind_{slug}",
                               width="stretch",
                               help=f"See the detail and go to {_secn} and sort it out"):
                    _cur = st.session_state.get("_res_sel")
                    st.session_state["_res_sel"] = None if _cur == slug else slug
                    st.rerun()

        sel = st.session_state.get("_res_sel")
        it = next((x for x in inds if x[0] == sel), None) if sel else None
        if it:
            slug, icon, lbl, _urgb, cnt, sec, sub, secn, fn = it
            st.markdown(f"**{icon} {lbl} — {cnt}**")
            if cnt:
                st.caption(fn())
                if st.button(f"→ {t('Go to')} {secn}", key=f"go_{slug}", type="primary"):
                    _ir_a(sec, sub)
            else:
                st.caption(t("Nothing pending here. :green[:material/check_circle:]"))

        # 4) lectura del asistente (IA) — su propio desplegable, bajo demanda
        with st.expander(t(":material/forum: The assistant's read (AI)")):
            key = f"_brief_{grupo}"
            if key in st.session_state:
                st.markdown(st.session_state[key])
                b1, b2 = st.columns(2)
                if b1.button(t(":material/refresh: Refresh"), key=f"brief_ref_{grupo}"):
                    st.session_state.pop(key, None)
                    st.rerun()
                if b2.button(t(":material/send: Send it to me"), key=f"brief_send_{grupo}"):
                    from core import notify
                    _u = st.session_state.get("auth", {}).get("usuario", "")
                    _txt = st.session_state.get(key, "")
                    try:
                        rr = notify.notify_user(_u, f"🔔 Today's summary — {grupo}",
                                                [l for l in str(_txt).split("\n") if l.strip()])
                        if rr.get("email") or rr.get("telegram"):
                            st.success(t(":material/send: Summary sent."))
                        else:
                            st.warning(t("Your user has no email/Telegram configured."))
                    except Exception as e:
                        st.error(f"It could not be sent: {e}")
            else:
                st.caption(t("The assistant writes the company's status in a few sentences, with a recommendation."))
                if st.button(t("✨ Generate the read"), key=f"brief_gen_{grupo}"):
                    with st.spinner(t("Preparing…")):
                        from core import chat_agent
                        st.session_state[key] = chat_agent.admin_briefing(grupo)
                    st.rerun()


# Documentos: tipos y permisos por rol
# ⚠️ Esta lista es SOLO para el desplegable de subida manual.
# NO se usa para filtrar lo que se ve: el admin ve TODOS los tipos.
# Hasta v134 la vista filtraba por aqui, asi que los documentos generados por
# la app con un tipo ausente de la lista desaparecian EN SILENCIO: los
# Pre-Start (tipo "prestart", v97) llevaban 36 versiones invisibles y los
# calculos (tipo "calculo", v129) nacieron invisibles.
# ⚠️ "plano" NO va aquí: subirlo por el uploader genérico solo lo guardaba en
# Drive sin extraer a PlanoJSON, así que las herramientas no lo veían (v156). El
# plano se carga SOLO desde 📐 Datos del plano (_cargar_plano), que sí extrae.
_DOC_SUBIR  = ["informe_cliente", "informe_admin", "matriz_survey",
               "foto", "certificado", "otro"]
_DOC_TIPOS  = _DOC_SUBIR + ["plano"]           # para VER (el plano se sigue mostrando)
# El campo consulta lo que usa en obra: incluye el Pre-Start que firma y los
# calculos (plomada, cortes) que ejecuta.
_CAMPO_VER  = {"plano", "informe_cliente", "matriz_survey", "foto",
               "prestart", "calculo"}
_CAMPO_SUBE = ["foto"]                                                # campo solo sube fotos
# Etiquetas legibles para el filtro de tipo del buscador (v165).
_TIPO_LABEL = {"plano": "Drawing", "informe_cliente": "Client report",
               "informe_admin": "Informe admin", "matriz_survey": "Matriz survey",
               "foto": "Photos", "certificado": "Certificates",
               "prestart": "Pre-Start", "calculo": "Calculations", "otro": "Others"}
_TIPO_ORDER = ["plano", "informe_cliente", "informe_admin", "matriz_survey",
               "calculo", "prestart", "foto", "certificado", "otro"]
# Reabrir un cálculo en su herramienta (v148): solo estas 4 guardan entradas.
# v299: IDs de las SUB-pestañas de 🛠 Herramientas en la shell (`home_ui._SUBSECCIONES`),
# no las etiquetas de la nav vieja — esa nav se borró.
_CALC_NAV   = {"plomada": "🔩 Plomada", "rieles": "✂️ Rieles",
               "buffers": "🛡 Buffers", "belting": "🎗 Belting"}


def _a_fecha(v):
    """Texto de la hoja -> date, o None. Acepta lo que haya guardado de antes.

    ⚠️ Hasta v149 estas fechas eran `text_input` LIBRE y `project_schedule` hacia
    `.split("-")` con un `except` que caia a **hoy sin avisar**: escribir
    "16/07/2026" desplazaba el cronograma entero al dia 0 y falseaba curva S,
    retraso, proyeccion y radar del admin, en silencio.
    """
    from datetime import datetime as _dt
    s = str(v or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return _dt.strptime(s[:10], fmt).date()
        except Exception:
            pass
    return None


def _iso(d) -> str:
    """date -> 'YYYY-MM-DD' (el unico formato que `project_schedule` sabe leer)."""
    try:
        return d.isoformat()
    except Exception:
        return ""


def _fecha_corta(v) -> str:
    """'2026-07-16 07:44:29' -> '16/07 07:44'. Devuelve '' si no se puede."""
    s = str(v or "").strip()
    if len(s) >= 16 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}/{s[5:7]} {s[11:16]}"
    return s[:16]


def _cargar_plano(pid: str):
    """Sube el PDF del plano Y extrae sus datos a PlanoJSON (v156).

    ⚠️ El bug: subir el plano por el uploader genérico de 📎 Documentos solo lo
    guardaba en Drive; NO extraía a PlanoJSON, que es lo ÚNICO que leen las
    herramientas. Así que el plano quedaba invisible para ellas. Aquí se hace lo
    mismo que al crear el proyecto: subir + extraer + guardar.
    """
    with st.expander(t(":material/upload: Upload / update the project drawing")):
        st.caption(t("Upload the PDF and its data is extracted so the tools can use it without asking for the drawing again. It takes about 1 min."))
        _pdf = st.file_uploader(t("Drawing PDF"), type=["pdf"], key=f"planoup_{pid}")
        _idk = f"planoup_id_{pid}"
        if _pdf is not None and st.session_state.get(_idk) != f"{_pdf.name}:{_pdf.size}":
            _barra = st.progress(0.0, text=t("Reading the drawing…"))
            try:
                res = plan_data.extraer_todo(
                    _pdf, progreso=lambda fr, txt: _barra.progress(
                        min(1.0, fr), text=f"Reading the drawing… {txt}"))
                # 1) Datos → PlanoJSON (lo que leen las herramientas)
                plan_data.guardar(pid, res)
                # 2) El PDF a Drive + registro como documento (best-effort)
                try:
                    if drive_store.is_configured():
                        _fid = drive_store.upload(pid, _pdf.name, _pdf.getvalue(),
                                                  "application/pdf")
                        P.add_document(pid, _pdf.name, "plano", _fid,
                                       st.session_state.get("auth", {}).get("usuario", ""))
                except Exception as e:
                    # Los DATOS del plano (PlanoJSON) ya se guardaron arriba, que es
                    # lo que leen las herramientas; archivar el PDF es accesorio y no
                    # debe tumbar la carga. Pero mudo no: el usuario subió un PDF y
                    # luego no lo encuentra en 📎 Archivos sin saber por qué.
                    logger.warning("projects_ui: el PDF del plano no se archivó: %s", e)
                    st.info(t(":material/info: The drawing data was saved, but **the PDF could not be filed** in Drive."))
                _barra.empty()
                st.session_state[_idk] = f"{_pdf.name}:{_pdf.size}"   # guarda v112
                flash.exito(t(":material/check_circle: Drawing uploaded — it feeds your 5 technical tools."))
                st.rerun()
            except Exception as e:
                _barra.empty()
                st.error(f"The drawing could not be read: {e}")


def _plano_herramientas_html(datos) -> str:
    """Tabla: qué le da el plano a CADA una de las 5 herramientas técnicas (v175).

    El plano alimenta las cinco por igual; se muestran juntas para que no parezca
    que solo cuentan los 17 parámetros del survey.
    """
    filas = []
    for h in plan_data.por_herramienta(datos):
        chips = []
        for label, val in h["items"]:
            if val not in (None, ""):
                chips.append(
                    '<span style="display:inline-block;background:#e8f5e9;color:#1b5e20;'
                    'border-radius:6px;padding:2px 8px;margin:2px 3px;font-size:12px;">'
                    f'{label}: <b>{val}</b></span>')
            else:
                chips.append(
                    '<span style="display:inline-block;background:#fdecea;color:#b71c1c;'
                    'border-radius:6px;padding:2px 8px;margin:2px 3px;font-size:12px;">'
                    f'{label}: {_MI('warning','#e0a021')} {t("missing")}</span>')
        filas.append(
            '<tr><td style="padding:6px 10px;white-space:nowrap;font-weight:600;'
            'vertical-align:top;border-bottom:1px solid #eef1f5;">'
            f'{h["tool"]}</td><td style="padding:5px 6px;border-bottom:1px solid #eef1f5;">'
            f'{"".join(chips)}</td></tr>')
    return ('<table style="border-collapse:collapse;width:100%;margin:4px 0 8px;">'
            + "".join(filas) + "</table>")


def _plano_section(pid: str, prj: dict):
    """Qué se leyó del plano de este proyecto (columna PlanoJSON, v137) + cargarlo.

    ⚠️ El dato existía desde v137 y solo se poblaba **al crear el proyecto**. Un
    proyecto creado sin plano no tenía forma de recibirlo (subirlo en Documentos
    NO extraía), así que las herramientas no lo veían nunca. Ahora se carga aquí.
    """
    datos = plan_data.del_proyecto(pid)
    st.markdown(t("**:material/description: Drawing data**"))
    if not datos:
        st.caption(t("This project has no saved drawing data, so the tools will ask whoever uses them for the PDF. Upload it here once and they will stop asking."))
        _cargar_plano(pid)
        return

    st.caption(t("A single drawing feeds **your 5 technical tools** — all of them equally:"))
    st.markdown(_plano_herramientas_html(datos), unsafe_allow_html=True)
    if not (datos.get("faltan") or []):
        st.caption(t(":material/check_circle: The drawing gave everything the tools need."))

    par = datos.get("params") or {}
    if par:
        with st.expander(f"See the {len(par)} drawing parameters"):
            st.dataframe(pd.DataFrame([{"Parameter": k, "Valor": v}
                                       for k, v in sorted(par.items())]),
                         hide_index=True, width="stretch", column_config=tabla.cfg())
    _cargar_plano(pid)


def _galeria_fotos(fotos, pid, por_pagina=6):
    """Miniaturas de las fotos de obra.

    El campo **solo puede subir fotos**: son la unica ventana del admin a la obra
    y hasta ahora salian como una fila de texto (`📷 foto.jpg · foto`).
    Paginada a proposito: cada miniatura es una descarga de Drive, asi que
    mostrarlas todas de golpe es justo el problema que evita el resto de la
    seccion (ver `_archivos_section`).
    """
    kver = f"_fotos_n_{pid}"
    n_ver = int(st.session_state.get(kver, por_pagina))
    st.markdown(f"**:material/photo_camera: Site photos** — {len(fotos)}")
    visibles = fotos[:n_ver]
    for fila in range(0, len(visibles), 3):
        cols = st.columns(3)
        for c, d in zip(cols, visibles[fila:fila + 3]):
            did = str(d.get("DriveID", ""))
            with c:
                _b = None
                try:
                    _b = drive_store.download(did)     # cacheado 5 min
                    st.image(_b, width="stretch")
                except Exception:
                    st.caption(t(":material/broken_image: not available"))
                pie = str(d.get("Nombre", ""))
                st.caption(f"{pie[:26]}\n\n{_fecha_corta(d.get('Fecha'))}"
                           + (f" · {d.get('SubidoPor')}" if d.get("SubidoPor") else ""))
                # Reutiliza los bytes ya bajados para la miniatura: descarga directa
                # de la foto sin una segunda llamada a Drive.
                if _b is not None:
                    st.download_button(":material/download:", data=_b, file_name=pie or f"{did}.jpg",
                                       key=f"fdl_{pid}_{did}", width="stretch")
    if len(fotos) > n_ver:
        if st.button(f"See {min(por_pagina, len(fotos) - n_ver)} more "
                     f"({len(fotos) - n_ver} left)", key=f"masfotos_{pid}"):
            st.session_state[kver] = n_ver + por_pagina
            st.rerun()


def _archivos_section(pid: str):
    """:material/attach_file: Archivos: UNA lista buscable de todo lo del proyecto (v165).

    Antes eran DOS sub-secciones (Documentos y Cálculos) con tres selectores
    distintos y listas planas: con muchos archivos, encontrar uno era el problema.
    Ahora hay una sola lista con búsqueda por nombre, filtro por tipo (con
    contadores) y orden, que reduce a la vez la tabla, la galería y el descargador.

    `list_documents` ya es la UNIÓN de todo (informes, matriz, fotos, pre-starts y
    los PDF de cálculos, que `toolruns.registrar` archiva como documento tipo
    "calculo" con el MISMO DriveID que su fila). Se casa cada cálculo con su
    toolrun por DriveID para ofrecer «reabrir en la herramienta» sin duplicarlo.
    """
    from collections import Counter
    st.markdown(t("**:material/folder: Files**"))
    if not drive_store.is_configured():
        st.caption(t(":material/lock: Drive storage is not configured (the `[gdrive]` secrets are missing)."))
        return
    a = st.session_state.get("auth", {})
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    es_campo     = rol == "campo"
    # Admin/propietario: ver_tipos = None -> SIN filtro (un tipo nuevo generado por
    # la app no vuelve a desaparecer de la vista, v134). El campo ve lo suyo.
    ver_tipos    = _CAMPO_VER if es_campo else None
    sube_tipos   = _CAMPO_SUBE if es_campo else _DOC_SUBIR
    puede_borrar = rol in ("administrador", "propietario")

    # ── Unir documentos + cálculos reabribles sin PDF (casados por DriveID) ──
    docs = [d for d in P.list_documents(pid)
            if ver_tipos is None or str(d.get("Tipo", "")) in ver_tipos]
    runs = toolruns.list_for(pid) if toolruns.is_configured() else []
    runs_by_drive = {str(r.get("DriveID", "")).strip(): r
                     for r in runs if str(r.get("DriveID", "")).strip()}
    entries, casados = [], set()
    for d in docs:
        tipo = str(d.get("Tipo", ""))
        did  = str(d.get("DriveID", "")).strip()
        run  = runs_by_drive.get(did) if tipo == "calculo" else None
        if run:
            casados.add(did)
        entries.append({
            "tipo": tipo, "label": _TIPO_LABEL.get(tipo, tipo or "otro"),
            "nombre": str(d.get("Nombre", "")), "fecha": str(d.get("Fecha", "")),
            "por": str(d.get("SubidoPor", "")), "did": did,
            "resumen": str(run.get("Resumen", "")) if run else "",
            "doc": d, "run": run})
    # Cálculos con entradas guardadas pero SIN PDF archivado (Drive estaba caído):
    # no son un "archivo" descargable, pero sí se pueden reabrir. No se pierden.
    if ver_tipos is None or "calculo" in ver_tipos:
        for r in runs:
            did = str(r.get("DriveID", "")).strip()
            if did and did in casados:
                continue
            if not toolruns.entradas_de(r):
                continue
            h = str(r.get("Herramienta", ""))
            entries.append({
                "tipo": "calculo", "label": _TIPO_LABEL["calculo"],
                "nombre": (f"{toolruns.HERRAMIENTAS.get(h, '')} "
                           f"{str(r.get('Resumen', ''))[:40]}").strip(),
                "fecha": str(r.get("Fecha", "")), "por": str(r.get("Usuario", "")),
                "did": did, "resumen": str(r.get("Resumen", "")),
                "doc": None, "run": r})

    if not entries:
        st.caption(t("No files yet."))
        _subir_documento(pid, es_campo, sube_tipos, usuario)
        return

    # ── Barra para acotar: buscar + tipo (con contadores) + orden ──
    cuenta = Counter(e["tipo"] for e in entries)
    tipos = ["Todos"] + [t for t in _TIPO_ORDER if t in cuenta] \
            + [t for t in cuenta if t not in _TIPO_ORDER]

    def _tlabel(_tp):
        return (f"{t('All')} ({len(entries)})" if _tp == "Todos"
                else f"{_TIPO_LABEL.get(_tp, _tp)} ({cuenta[_tp]})")

    # ⚠️ El VALOR de cada opción se queda en español porque se compara abajo
    # (`orden == "Más reciente"`). Traducir la opción y no la comparación deja la
    # rama MUERTA sin dar ningún error — el fallo real de v442. Se traduce el
    # display con `format_func`, que es lo único que se ve.
    _ORD = {"Más reciente": "Newest", "Más antiguo": "Oldest",
            "Name A–Z": "Name A–Z", "Tipo": "Type"}

    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    q = c1.text_input(t(":material/search: Search"), key=f"arch_q_{pid}",
                      placeholder=t("name, type…")).strip().lower()
    tsel = c2.selectbox(t("Type"), tipos, format_func=_tlabel, key=f"arch_t_{pid}")
    orden = c3.selectbox(t("Order"), list(_ORD), format_func=lambda o: t(_ORD[o]),
                         key=f"arch_o_{pid}")

    vis = entries
    if tsel != "Todos":
        vis = [e for e in vis if e["tipo"] == tsel]
    if q:
        vis = [e for e in vis
               if q in f"{e['nombre']} {e['label']} {e['resumen']} {e['por']}".lower()]
    if orden == "Más reciente":
        vis = sorted(vis, key=lambda e: e["fecha"], reverse=True)
    elif orden == "Más antiguo":
        vis = sorted(vis, key=lambda e: e["fecha"])
    elif orden == "Name A–Z":
        vis = sorted(vis, key=lambda e: e["nombre"].lower())
    else:
        vis = sorted(vis, key=lambda e: (e["label"], e["fecha"]))

    if len(vis) != len(entries):
        st.caption(f"Showing **{len(vis)}** of {len(entries)} files.")

    # ── Galería de fotos (solo las que pasan el filtro; sigue siendo lazy) ──
    fotos = [e["doc"] for e in vis if e["tipo"] == "foto"]
    if fotos:
        _galeria_fotos(fotos, pid)
        st.markdown("")

    # ── Tabla del resto: CLICABLE — tocar una fila muestra su descarga ──
    # La descarga sigue siendo lazy: `st.download_button(data=…)` evalúa `data` al
    # renderizar, así que un botón por fila bajaría TODO Drive en cada pasada (el
    # problema de v147). Con selección de fila, solo se descarga la elegida.
    resto = [e for e in vis if e["tipo"] != "foto"]
    if resto:
        _ev = st.dataframe(pd.DataFrame([{
            "Archivo": e["nombre"], "Tipo": e["label"],
            "Uploaded by": e["por"], "Fecha": _fecha_corta(e["fecha"]),
        } for e in resto]), hide_index=True, width="stretch",
            on_select="rerun", selection_mode="single-row", key=f"arch_tbl_{pid}", column_config=tabla.cfg())
        st.caption(t(":material/touch_app: Tap a row to download or reopen that file."))
        try:
            _rows = list(_ev.selection.rows)
        except Exception:
            _rows = []
        # Clamp: si cambiaste el filtro con una fila elegida, el índice podría
        # apuntar fuera de la lista actual — no abrir un archivo equivocado.
        if _rows and _rows[0] < len(resto):
            _acciones_archivo(pid, resto[_rows[0]], puede_borrar)

    if not vis:
        st.info(t("No file matches the filter."))

    _subir_documento(pid, es_campo, sube_tipos, usuario)


def _acciones_archivo(pid, e, puede_borrar):
    """Descargar / reabrir / borrar el archivo elegido. Solo aquí se descarga."""
    did = e["did"]
    run = e.get("run")
    h = str((run or {}).get("Herramienta", ""))
    reabrible = bool(run) and h in _CALC_NAV and bool(toolruns.entradas_de(run))
    es_doc = e.get("doc") is not None

    if did:
        try:
            st.download_button(":material/download: Descargar " + (e["nombre"] or "archivo"),
                               data=drive_store.download(did),
                               file_name=e["nombre"] or f"{did}.pdf",
                               key=f"arch_dl_{pid}_{did}", width="stretch")
        except Exception as ex:
            st.error(f"It could not be downloaded: {ex}")
    if reabrible:
        if st.button(t(":material/replay: Reopen in the tool"), key=f"arch_reab_{pid}",
                     width="stretch"):
            if tool_save_ui.pedir_reapertura(run, h, _CALC_NAV[h]):
                st.rerun()
            else:
                st.warning(t("This calculation did not save its inputs (it predates v148)."))
    if puede_borrar and es_doc:
        if st.button(t(":material/delete: Delete"), key=f"arch_del_{pid}_{did or e['nombre']}",
                     width="stretch"):
            if did:
                drive_store.delete(did)
            P.delete_document_record(pid, did)
            st.rerun()
    if not did and not reabrible:
        st.caption(t("This calculation has no filed PDF and no inputs to reopen."))


def _subir_documento(pid, es_campo, sube_tipos, usuario):
    """Subir un documento (el campo solo puede subir fotos)."""
    with st.expander(t("Upload document"), icon=":material/upload_file:"):
        if es_campo:
            st.caption(t("As a field user you can only upload **photos**."))
        up   = st.file_uploader(t("File"), key=f"updoc_{pid}")
        tipo = st.selectbox(t("Type"), sube_tipos, key=f"uptipo_{pid}")
        if st.button(t("Upload"), key=f"upbtn_{pid}"):
            if up is None:
                st.error(t("Choose a file first."))
            else:
                try:
                    fid = drive_store.upload(pid, up.name, up.getvalue(),
                                             up.type or "application/octet-stream")
                    P.add_document(pid, up.name, tipo, fid, usuario)
                    flash.exito(t("Document uploaded."))
                    st.rerun()
                except Exception as ex:
                    st.error(f"It could not be uploaded: {ex}")


def _nuevo_proyecto_form(grupo: str, key: str = "nuevo"):
    """Crear un proyecto desde cero, sin pasar por el Survey (v135).

    Antes el proyecto SOLO nacía del survey ("Guardar como proyecto"), así que
    no se podía dar de alta una obra hasta tener el survey hecho. Ahora el
    proyecto es la entidad principal y el survey una herramienta que lo
    alimenta, igual que Plomadas o los cortes.

    El cronograma se genera de las actividades estándar a partir del NS, que es
    lo único que necesita `build_schedule` — no hace falta el survey.
    """
    import datetime as _dt
    from core.schedule import build_schedule

    with st.expander(t("New project"), icon=":material/add_circle:"):
        campos = []
        try:
            campos = [u["Usuario"] for u in auth.list_users(grupo)
                      if str(u.get("Rol", "")) == "campo"]
        except Exception:
            pass

        # ── Plano del elevador (fuera del form, para poder prellenar) ──
        # De aqui salen NS y los parametros que usan las 5 herramientas. Se lee
        # UNA vez: despues nadie vuelve a subir el PDF (antes se subia en cada
        # herramienta y cada una lo reparseaba, 30-70 s por vez).
        st.markdown(t("**:material/description: Lift drawing** — optional, but recommended"))
        st.caption(t("The drawing is read once and its data stays with the project: the field team will no longer have to upload the PDF in any tool."))
        _pdf = st.file_uploader(t("Drawing PDF"), type=["pdf"], key=f"np_pdf_{key}")
        _kd = f"np_plano_{key}"
        if _pdf is not None and st.session_state.get(f"{_kd}_id") != f"{_pdf.name}:{_pdf.size}":
            _barra = st.progress(0.0, text=t("Reading the drawing…"))
            def _prog(fr, txt):
                _barra.progress(min(1.0, fr), text=f"Reading the drawing… {txt}")
            try:
                st.session_state[_kd] = plan_data.extraer_todo(_pdf, progreso=_prog)
                st.session_state[f"{_kd}_bytes"] = _pdf.getvalue()
            except Exception as e:
                st.session_state[_kd] = None
                st.error(f"The drawing could not be read: {e}")
            # v272: prellenar NS desde el plano AQUÍ (session_state), no con `value=` en el
            # form. El widget NS ya se instanció antes de subir el plano y Streamlit ignora
            # `value=` si la key ya existe → el prellenado no tomaba (NS se quedaba en 2).
            _pl = st.session_state.get(_kd) or {}
            try:
                st.session_state[f"np_ns_{key}"] = max(2, min(50, int(float(_pl.get("ns") or 2))))
            except Exception:
                pass
            _mdl = str(_pl.get("modelo") or "").strip()   # v273: PRODUCT LINE del plano
            if _mdl:
                st.session_state[f"np_mod_{key}"] = _mdl
            # Guarda de identidad: sin esto se reextraería en CADA rerun (v112)
            st.session_state[f"{_kd}_id"] = f"{_pdf.name}:{_pdf.size}"
            _barra.empty()
            st.rerun()

        _plano = st.session_state.get(_kd)
        if _plano:
            st.success(t(":material/check_circle: Drawing read — it feeds your **5 technical tools**:"))
            st.markdown(_plano_herramientas_html(_plano), unsafe_allow_html=True)

        asg = st.multiselect(t(":material/engineering: Field users assigned"), campos,
                             key=f"np_asg_{key}")
        _certs = st.multiselect(t(":material/badge: Certificates the project requires"), credentials.CATALOGO,
                                key=f"np_certs_{key}",
                                help=t("When staff are assigned, anyone who does not meet them is flagged."))
        if asg:
            _avisar_asignados(asg, grupo, certs_req=_certs)

        # ── Ubicación en el mapa (fuera del form: el mapa necesita reruns) — v194 ──
        # v210: inline (sin expander propio) — este bloque ya vive dentro del expander
        # "➕ Nuevo proyecto", y Streamlit no permite expanders anidados.
        from core import location_ui
        st.markdown(t("**:material/map: Location on the map** — optional, drops the project pin"))
        _nplat, _nplng = location_ui.location_picker(f"nploc_{key}")

        # ── Cliente: elegir uno existente o escribir uno nuevo (fuera del form) ──
        from core import clientes as _C
        _cli_fichas = _C.list_clientes(grupo)
        _cli_names = [str(c.get("Nombre", "")) for c in _cli_fichas]
        _CLI_OTRO = t("➕ Other (type a new one)")
        _cli_sel = st.selectbox(t(":material/contacts: Client"),
                                ["— no client —"] + _cli_names + [_CLI_OTRO],
                                key=f"np_clisel_{key}",
                                help=t("Choose a client from Contacts or type a new one."))
        _cli_new = ""
        if _cli_sel == _CLI_OTRO:
            _cli_new = st.text_input(t("New client's name"), key=f"np_clinew_{key}")

        # ── Tipo de proyecto (v306) ──────────────────────────────
        # ⚠️ FUERA del `st.form` a propósito: dentro, los widgets no escriben hasta el
        # submit, así que el formulario no podría reaccionar al tipo — y aquí TIENE que
        # hacerlo, porque solo la instalación pide NS y calcula la fecha de fin sola.
        # (Misma razón por la que v127 sacó del form el selector de campo y v189 el tipo
        # de credencial.)
        _tipo = st.selectbox(t(":material/category: Project type"), P.TIPOS,
                             key=f"np_tipo_{key}",
                             help=t("Only «Installation» generates the standard job schedule (11 activities that scale with NS)."))
        _es_inst = (_tipo == P.TIPO_INSTALACION)

        # NS lo controla session_state (prellenado del plano arriba); la Ubicación se toma de
        # la dirección que buscaste en el mapa → ya no se pide dos veces (v272).
        st.session_state.setdefault(f"np_ns_{key}", 2)
        _ubi_auto = (st.session_state.get(f"nploc_{key}_addr")
                     or st.session_state.get(f"nploc_{key}_q") or "").strip()
        if _ubi_auto:
            st.caption(f":material/place: Location that will be saved: **{_ubi_auto}**")

        with st.form(f"np_form_{key}"):
            nom = st.text_input(t("Project name *"), key=f"np_nom_{key}")
            c1, c2 = st.columns(2)
            ing = c1.text_input(t("Engineer in charge"), key=f"np_ing_{key}")
            f_ini = c1.date_input(t("Start date"), value=clock.today(),
                                  key=f"np_ini_{key}")
            f_fin_manual = None
            if _es_inst:
                ns = c2.number_input(t("Number of stops (NS) *"), min_value=2, max_value=50,
                                     step=1, key=f"np_ns_{key}",
                                     help=(t("Read from the drawing.") if (_plano or {}).get("ns")
                                           else t("It sets how long the activities take.")))
                # La fecha de FIN no se teclea: sale del NS + las actividades estándar de
                # instalación (`build_schedule`), cuyas duraciones escalan con el NS. Preview:
                try:
                    _sch_prev = build_schedule(int(ns), f_ini, {})
                    c1.caption(":material/event_available: Estimated finish: "
                               f"**{_sch_prev['fecha_fin'].strftime('%d/%m/%Y')}** "
                               f"({_sch_prev['total_dias']} days) — from the NS and the standard activities.")
                except Exception:
                    pass
            else:
                # v306: un delivery/ripout no tiene paradas ni el plan de 11 actividades,
                # así que la fecha de fin SÍ se teclea (para instalación sigue saliendo sola).
                ns = 2                      # mínimo válido; no se usa para nada aquí
                f_fin_manual = c2.date_input(t("Estimated finish date"), value=clock.today(),
                                             key=f"np_fin_{key}",
                                             help=t("This project type has no standard schedule, so you set the date yourself."))
            pres = c2.number_input(t(":material/payments: Budget (0 = no budget)"), min_value=0.0,
                                   step=100.0, key=f"np_pres_{key}")
            mod = st.text_input(t("Lift model"), key=f"np_mod_{key}",
                                placeholder=t("optional"),
                                help=t("Prefilled from the drawing (PRODUCT LINE), if it was read. Editable."))
            instr = st.text_area(t(":material/push_pin: Specific instructions"), key=f"np_ins_{key}",
                                 placeholder=t("Specific instructions for the team…"))
            inds = st.text_area(t(":material/description: Inductions (one link per line)"), key=f"np_ind_{key}",
                                placeholder="https://...",
                                help=t("They are sent by Telegram/email to those assigned."))
            enviar = st.form_submit_button(t(":material/add_circle: Create project"),
                                           width="stretch")

        if enviar:
            if not nom.strip():
                st.error(t("The project name is required."))
                return
            # Ubicación = la dirección que se buscó en el mapa (ya no hay campo aparte).
            ubi = (st.session_state.get(f"nploc_{key}_addr")
                   or st.session_state.get(f"nploc_{key}_q") or "").strip()
            # Incluye archivados: crear un homonimo de uno archivado tambien confunde.
            # v422: y las internas — llamar a una obra igual que el almacén confunde igual.
            dups = [f"{p.get('ID')} · {p.get('Nombre')}"
                    for p in P.list_projects(grupo, incluir_archivados=True,
                                             incluir_internos=True)
                    if " ".join(str(p.get("Nombre") or "").lower().split())
                    == " ".join(nom.lower().split())]
            if dups and not st.session_state.get(f"np_dup_{key}"):
                st.warning(":material/warning: A project with that name already exists: "
                           + ", ".join(dups)
                           + ". If it is a different lift, tick the box and create it again.")
                st.checkbox(t("Create even though the name is repeated"), key=f"np_dup_{key}")
                return

            # Cliente elegido/escrito → texto + ClienteID (v255)
            if _cli_sel in _cli_names:
                cli = _cli_sel
                _cli_id = next((str(c.get("ID", "")) for c in _cli_fichas
                                if str(c.get("Nombre", "")) == _cli_sel), "")
            elif _cli_sel == _CLI_OTRO:
                cli, _cli_id = _cli_new.strip(), ""
            else:
                cli, _cli_id = "", ""

            # v306: el cronograma DEPENDE del tipo. Antes se generaba el plan de
            # instalación siempre, así que un delivery nacía con 11 actividades falsas —
            # y ese plan alimenta avance, curva S, SPI y el indicador «En retraso».
            if _es_inst:
                sched = build_schedule(int(ns), f_ini, {})
                _fin = (sched["fecha_fin"].strftime("%Y-%m-%d")
                        if sched.get("fecha_fin") else "")
                _acts = sched.get("activities", [])
            else:
                _fin = f_fin_manual.strftime("%Y-%m-%d") if f_fin_manual else ""
                # ⚠️ UNA actividad genérica, no CERO: el avance del proyecto es
                # Σ(peso·avance)/Σpeso sobre sus actividades, así que sin ninguna el
                # proyecto se quedaría clavado en 0% para siempre y el campo no tendría
                # dónde reportar. Con una sola, avanza 0→100 sin fingir un plan de obra.
                _dias = max(1, ((f_fin_manual - f_ini).days + 1) if f_fin_manual else 1)
                _acts = [{"nombre": "Ejecución", "duracion": _dias, "peso": 1}]
            ok, res = P.create_project(
                grupo=grupo, nombre=nom.strip(), cliente=cli, cliente_id=_cli_id, ubicacion=ubi,
                modelo=mod, ns=int(ns), ingeniero=ing, campo_asignados=asg, tipo=_tipo,
                fecha_inicio=f_ini.strftime("%Y-%m-%d"),
                fecha_fin_est=_fin,
                activities=_acts,
                creado_por=st.session_state.get("auth", {}).get("usuario", ""),
                instrucciones=instr, induccion_links=inds, presupuesto=pres,
                lat=("" if _nplat is None else _nplat),
                lng=("" if _nplng is None else _nplng),
                certs_req=";".join(_certs))
            if not ok:
                st.error(f"It could not be created: {res}")
                return

            # Datos del plano + PDF, para que ninguna herramienta vuelva a pedirlo
            if _plano:
                try:
                    plan_data.guardar(res, _plano)
                except Exception as e:
                    st.warning(f"The project was created, but the drawing data was "
                               f"not saved: {e}")
                _pb = st.session_state.get(f"{_kd}_bytes")
                if _pb and drive_store.is_configured() and drive_store.is_available():
                    try:
                        fid = drive_store.upload(res, "plano.pdf", _pb, "application/pdf")
                        P.add_document(res, "plano.pdf", "plano", fid,
                                       st.session_state.get("auth", {}).get("usuario", ""))
                    except Exception:
                        st.caption(t(":material/attach_file: The drawing could not be filed in Drive."))
                for _k in (_kd, f"{_kd}_bytes", f"{_kd}_id"):
                    st.session_state.pop(_k, None)

            st.success(f":material/check_circle: Project **{res}** created with "
                       f"{len(sched.get('activities', []))} activities"
                       + (" and the drawing data loaded." if _plano else ".")
                       + " The survey and the other tools can now feed it.")
            if asg:
                _notificar_asignados(asg, {
                    "Nombre": nom.strip(), "Cliente": cli, "Ubicacion": ubi,
                    "FechaInicio": f_ini.strftime("%Y-%m-%d"),
                    "FechaFinEst": (sched["fecha_fin"].strftime("%Y-%m-%d")
                                    if sched.get("fecha_fin") else ""),
                    "InduccionLinks": inds})
                # v219: auto-poblar el planificador con el proyecto entre sus fechas.
                _autoagenda(grupo, res, asg, [], f_ini,
                            sched.get("fecha_fin") if sched.get("fecha_fin") else None)


def _autoagenda(grupo, pid, nuevos, quitados, fecha_ini, fecha_fin):
    """Sincroniza el planificador con la asignación del proyecto (v219): pone a los
    NUEVOS asignados en el proyecto entre sus fechas (Lun–Vie, solo celdas vacías) y
    quita del planificador a los DESASIGNADOS. Best-effort; informa el resultado."""
    from core import roster as R
    msgs = []
    try:
        if nuevos and fecha_ini and fecha_fin:
            r = R.autopoblar_proyecto(grupo, pid, nuevos, fecha_ini, fecha_fin)
            if r["llenadas"]:
                _oc = (f" · {r['ocupadas']} day(s) already taken were left alone"
                       if r["ocupadas"] else "")
                msgs.append(f":material/calendar_month: Planner: {r['llenadas']} day(s) assigned to "
                            f"{len(nuevos)} person(s) in {r['semanas']} week(s){_oc}.")
            elif r["ocupadas"]:
                msgs.append(":material/calendar_month: Planner: the days in the range were already taken; nothing was overwritten.")
        elif nuevos and not fecha_fin:
            msgs.append(":material/calendar_month: The project has no **end date**, so nothing was auto-planned. Set one in :material/edit: Details, or plan by hand in :material/calendar_month: Planning.")
    except Exception:
        pass
    try:
        if quitados:
            n = R.limpiar_proyecto(grupo, pid, quitados)
            if n:
                msgs.append(f":material/cleaning_services: Planner: {n} day(s) cleared for those unassigned.")
    except Exception:
        pass
    for m in msgs:
        st.caption(m)


def _avisar_asignados(usuarios, grupo=None, exclude_pid=None, certs_req=None,
                      fechas=None):
    """Avisos ANTES de asignar (v219): contacto, credenciales, si YA está en otro
    proyecto (y hasta cuándo), cumplimiento de los certificados que EXIGE el proyecto,
    y (v432) si esa persona tiene una AUSENCIA aprobada o pedida en esas fechas.
    Todo informativo — no bloquea (una asignación con solapes o pendientes puede ser
    deliberada). `exclude_pid` = el proyecto actual (no se cuenta a sí mismo).
    `fechas` = (inicio, fin) del proyecto: si llega, solo se avisa de las ausencias
    que CRUZAN ese rango; si no, de las que aún no han terminado."""
    sin_contacto, cred_mal = [], []
    no_cumplen, cert_pv = [], []          # feature 3: certificados requeridos

    # feature 1: otros proyectos activos donde ya está cada usuario asignado.
    otros = {}
    if grupo:
        try:
            for p in P.list_projects(grupo):
                if str(p.get("ID", "")) == str(exclude_pid or ""):
                    continue
                if str(p.get("Estado", "")) in ("Completado", "Cancelado"):
                    continue
                for u in [x.strip() for x in str(p.get("CampoAsignados", "")).split(";")
                          if x.strip()]:
                    otros.setdefault(u, []).append(p)
        except Exception:
            pass

    ocupados = []
    for u in usuarios:
        try:
            info = auth.get_user(u) or {}
            if not (str(info.get("Email", "")).strip()
                    and str(info.get("TelegramChatID", "")).strip()):
                sin_contacto.append(u)
        except Exception:
            pass
        try:
            for c in credentials.list_for(u):
                # los tipos REQUERIDOS por el proyecto los cubre el chequeo de abajo
                if certs_req and str(c.get("Tipo", "")).strip() in certs_req:
                    continue
                if credentials.status(c.get("Vencimiento")) in ("vencido", "por_vencer"):
                    cred_mal.append(f"{u} — {c.get('Tipo', 'credencial')}: "
                                    f"{credentials.status_label(c.get('Vencimiento'))}")
        except Exception:
            pass
        for p in otros.get(u, []):
            _fin = str(p.get("FechaFinEst", "")).strip()
            ocupados.append(f"**{u}** → :material/apartment: {p.get('Nombre', '')}"
                            + (f" ({t('until')} {_fin})" if _fin else ""))
        if certs_req:
            try:
                comp = credentials.compliance(u, certs_req)
                faltan = [t for t in certs_req if comp["por_tipo"].get(t) in ("falta", "vencido")]
                pv = [t for t in certs_req if comp["por_tipo"].get(t) == "por_vencer"]
                if faltan:
                    no_cumplen.append(f"**{u}**: " + ", ".join(
                        f"{t} ({'falta' if comp['por_tipo'][t] == 'falta' else 'vencido'})"
                        for t in faltan))
                if pv:
                    cert_pv.append(f"**{u}**: " + ", ".join(f"{t}" for t in pv))
            except Exception:
                pass

    # ⚠️ v432: ausencias. Se podía asignar a alguien a una obra justo en su semana de
    # vacaciones y nada lo decía — el tablero sí las respeta (auto-poblar solo llena
    # celdas VACÍAS), pero quien asigna no se enteraba hasta el lunes.
    fuera = []
    if grupo:
        try:
            from core import ausencias as _AU
            from core import clock as _clk
            from core.num import parse_date as _pd
            _ini = _pd(fechas[0]) if fechas and fechas[0] else None
            _fin = _pd(fechas[1]) if fechas and fechas[1] else None
            _hoy = _clk.today(grupo)
            for u in usuarios:
                for a in _AU.list_group(grupo, usuario=u):
                    if str(a.get("Estado", "")) not in _AU.VIGENTES:
                        continue
                    _d0, _d1 = _pd(a.get("Desde")), _pd(a.get("Hasta"))
                    if not _d0 or not _d1:
                        continue
                    if _ini and _fin:
                        if not _AU._solapan(_d0, _d1, _ini, _fin):
                            continue          # no cruza las fechas de la obra
                    elif _d1 < _hoy:
                        continue              # sin fechas de obra: solo lo que no pasó
                    _t = _AU.TIPOS.get(str(a.get("Tipo", "")), {})
                    fuera.append(f"**{u}**: {_t.get('nombre', a.get('Tipo'))} "
                                 f"from {a.get('Desde')} to {a.get('Hasta')}"
                                 + ("" if str(a.get("Estado")) == _AU.APROBADA
                                    else " (not approved yet)"))
        except Exception as e:
            logger.warning("_avisar_asignados: ausencias: %s", e)

    if fuera:
        st.warning(":material/event_busy: **They will not be available on those days:**\n\n"
                   + "\n".join(f"- {x}" for x in fuera))
    if ocupados:
        st.info(":material/push_pin: **Already assigned to another project:**\n\n"
                + "\n".join(f"- {x}" for x in ocupados))
    if no_cumplen:
        st.error(":material/cancel: **They do not meet the certificates this project requires:**\n\n"
                 + "\n".join(f"- {x}" for x in no_cumplen))
    if cert_pv:
        st.warning(":material/schedule: **Required certificates EXPIRING SOON (renew):**\n\n"
                   + "\n".join(f"- {x}" for x in cert_pv))
    if cred_mal:
        st.warning(":material/badge: **Other credentials to check before sending them to site:**\n\n"
                   + "\n".join(f"- {x}" for x in cred_mal))
    if sin_contacto:
        st.warning(":material/warning: **Without full contact details (email + Telegram):** "
                   + ", ".join(sin_contacto)
                   + ". They will not receive the assignment or the inductions.")


def _cumplimiento_equipo(pid, grupo, prj):
    """Tabla VIVA de cumplimiento de certificados del equipo asignado (v219): asignados
    × certificados requeridos, ✅/🟡/🔴/—. Solo si el proyecto define requeridos."""
    req = [x.strip() for x in str(prj.get("CertsReq", "")).split(";") if x.strip()]
    if not req:
        return
    st.markdown(t("**:material/verified_user: Team certificate compliance**"))
    asign = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
    if not asign:
        st.caption(t("No field users assigned yet."))
        return
    # ⚠️ El estado se muestra con `etiqueta()` (v442), NO con un mapa propio. El que
    # había aquí traducía «vigente»→«vigente», así que las celdas salían en español
    # mientras la leyenda de abajo —ya traducida— describía iconos que la tabla no
    # pinta: dos textos contándose cosas distintas a dos centímetros. `i18n.VALORES`
    # ya sabe que vigente/por_vencer/vencido/falta son valid/expiring/expired/missing.
    filas = []
    for u in asign:
        comp = credentials.compliance(u, req)
        fila = {"Usuario": u, "Compliant": t("Yes") if comp["cumple"] else t("No")}
        for _c in req:
            _est = comp["por_tipo"].get(_c, "falta")
            fila[_c] = "—" if _est == "falta" else _etq(_est)
        filas.append(fila)
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch", column_config=tabla.cfg())
    st.caption(t("**Compliant** = no required certificate is expired or missing. "
                 "«—» means the person does not hold that certificate."))


def _notificar_asignados(usuarios, info_prj):
    """Envía la asignación e informa SIEMPRE del resultado (no falla en silencio)."""
    if not notify.any_channel_configured():
        st.caption(t(":material/mail: No notification channels configured (Gmail / Telegram)."))
        return
    n = 0
    for u in usuarios:
        try:
            rr = notify.notify_assignment(u, info_prj)
            if rr.get("email") or rr.get("telegram"):
                n += 1
        except Exception:
            pass
    if n == len(usuarios):
        st.caption(f":material/mail: {n} field user(s) notified.")
    elif n:
        st.warning(f":material/mail: Notified {n} of {len(usuarios)}. The rest have no contact details.")
    else:
        st.warning(t(":material/warning: Nobody could be notified: check email and Telegram in :material/build: My company → Users."))


def _field_users(grupo):
    """Usuarios de campo del grupo (para asignar a un proyecto)."""
    try:
        return [u["Usuario"] for u in auth.list_users(grupo)
                if str(u.get("Rol", "")) == "campo"]
    except Exception:
        return []


# ── Panel de proyectos ───────────────────────────────────────────
def _cartera_clickeable(proys, alarmas, delays, aheads, costos,
                        pendientes=None, grupo="", puede_facturar=False):
    """Cartera de proyectos como TARJETAS con toda la info ANTES de abrir (v223, opción A
    elegida por el usuario): nombre, estado + % avance (barra real), cliente, fechas,
    % de presupuesto ejecutado, nº de usuarios asignados y alertas. Se abre con «Abrir».
    Borde izq = salud (rojo=retraso, verde=adelanto, azul=en curso). Rejilla de 2 col,
    ordenada por urgencia. El contenedor keyed permite colorear el borde (verificado)."""
    import html as _htmlmod

    def esc(s):
        return _htmlmod.escape(str(s or ""))

    def _ddmm(s):
        s = str(s or "").strip()[:10]
        if not s:
            return "—"
        from datetime import datetime as _dt
        for _f in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return _dt.strptime(s, _f).strftime("%d/%m")
            except Exception:
                pass
        return "—"

    _pill = {"En progreso": ("#e8eef6", "#1e4e79"), "Planificado": ("#f0efe8", "#5f5e5a"),
             "Completado": ("#e8f5ee", "#1e6e4e"), "En pausa": ("#faeeda", "#8a5a0b"),
             "Cancelado": ("#fbeaea", "#a12d2d"), "Archivado": ("#eceff3", "#5f5e5a")}

    from core import theme

    def _salud(pid):
        # v283: colores del sistema de diseño (rojo=retraso, verde=adelanto, azul=en curso)
        return (theme.ROJO if delays.get(pid)
                else (theme.VERDE if aheads.get(pid) else theme.AZUL))

    pendientes = pendientes or {}
    proys = sorted(proys, key=lambda p: (-delays.get(str(p.get("ID", "")), 0),
                                         -alarmas.get(str(p.get("ID", "")), 0)))

    # Borde izquierdo por salud en cada tarjeta (contenedor keyed = .st-key-cart_<i>, v223).
    _css = ["<style>"]
    for _i, p in enumerate(proys):
        _css.append(f".st-key-cart_{_i}{{border-left:4px solid "
                    f"{_salud(str(p.get('ID', '')))}!important;}}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    for _r in range(0, len(proys), 2):
        _cols = st.columns(2)
        for _j in range(2):
            _idx = _r + _j
            if _idx >= len(proys):
                break
            p = proys[_idx]
            _pid = str(p.get("ID", ""))
            _av = max(0, min(100, int(P._num(p.get("Avance")))))
            _dl, _ah, _al = delays.get(_pid, 0), aheads.get(_pid, 0), alarmas.get(_pid, 0)
            _col = _salud(_pid)
            _est = str(p.get("Estado", "") or "—")
            _pbg, _pfg = _pill.get(_est, ("#eceff3", "#5f5e5a"))
            _users = len([x for x in str(p.get("CampoAsignados", "")).split(";") if x.strip()])
            _c = costos.get(_pid) or {}
            if P._num(_c.get("presupuesto")) > 0:
                _ppto = f"{int(round(P._num(_c.get('pct'))))}% ppto" + (" " + _MI("warning", "#e0a021") if _c.get("over") else "")
            else:
                _ppto = "s/ppto"
            _chips = f"{_MI('payments')} {_ppto} · {_MI('engineering')} {_users}"
            if _dl:
                _chips += f" · {_MI('cancel','#d64541')} {_dl}d"
            elif _ah:
                _chips += f" · {_MI('check_circle','#1e9e57')} {_ah}d"
            if _al:
                _chips += f" · {_MI('notifications')} {_al}"
            # v397: dinero hecho y aún no pedido. Va en la tarjeta porque hoy hay
            # $36.552 repartidos en 9 obras y no se veía en ninguna parte hasta
            # entrar obra por obra. `pend` llega ya calculado en UN mapa (regla v142).
            _pf = pendientes.get(_pid, 0.0)
            if _pf > 0:
                _chips += (f" · <b style='color:#8a5a0b;'>{_MI('receipt', '#8a5a0b')} "
                           f"{theme.dinero(_pf, 0)}</b>")
            _html = (
                "<div style='display:flex;justify-content:space-between;align-items:center;"
                "gap:8px;margin-bottom:6px;'>"
                "<div style='display:flex;align-items:center;gap:7px;min-width:0;'>"
                f"<span style='width:9px;height:9px;border-radius:50%;background:{_col};"
                "flex:none;'></span>"
                "<span style='font-weight:700;font-size:14px;overflow:hidden;"
                f"text-overflow:ellipsis;white-space:nowrap;'>{esc(p.get('Nombre', ''))}</span></div>"
                f"<span style='background:{_pbg};color:{_pfg};font-size:11px;padding:2px 8px;"
                f"border-radius:6px;white-space:nowrap;'>{esc(_est)}</span></div>"
                "<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
                "<div style='flex:1;height:7px;background:#eef1f5;border-radius:20px;"
                "overflow:hidden;'>"
                f"<div style='height:100%;width:{_av}%;background:#2e6da4;"
                "border-radius:20px;'></div></div>"
                f"<span style='font-size:12px;font-weight:600;color:#374151;'>{_av}%</span></div>"
                # v306: ID + tipo. El ID en monoespaciada porque es un identificador que
                # se dicta y se busca, no una etiqueta; el tipo solo si está marcado.
                "<div style='font-size:11px;color:#667080;margin-bottom:4px;"
                "font-family:monospace;'>"
                f"{esc(_pid)}"
                + (f"<span style='font-family:inherit;color:#6b7280;'> · "
                   f"{esc(str(p.get('Tipo', '')).strip())}</span>"
                   if str(p.get('Tipo', '')).strip() else "")
                + "</div>"
                f"<div style='font-size:12px;color:#6b7280;margin-bottom:5px;'>{_MI('person')} "
                f"{esc(p.get('Cliente', '') or '—')} · {_MI('calendar_month')} {_ddmm(p.get('FechaInicio'))} → "
                f"{_ddmm(p.get('FechaFinEst'))}</div>"
                f"<div style='font-size:12px;color:#374151;'>{_chips}</div>")
            with _cols[_j].container(border=True, key=f"cart_{_idx}"):
                st.markdown(_html, unsafe_allow_html=True)
                # ⚠️ El botón de facturar SOLO sale si esa obra tiene algo pendiente:
                # en las demás sería un botón que lleva a una factura vacía. Y solo
                # para gestión — el campo ve la cartera pero no factura (v357).
                if _pf > 0 and puede_facturar:
                    _ba, _bf = st.columns(2)
                    if _ba.button(t("Open →"), key=f"cartbtn_{_idx}",
                                  width="stretch"):
                        st.session_state["_admin_open_proj"] = _pid
                        st.rerun()
                    if _bf.button(t(":material/receipt_long: Invoice"), key=f"cartfac_{_idx}",
                                  width="stretch", type="primary",
                                  help=f"New invoice with this job and its client already "
                                       f"chosen · outstanding {theme.dinero(_pf, 0)}"):
                        _ir_a_facturar(_pid, grupo)
                        st.rerun()
                elif st.button(t("Open →"), key=f"cartbtn_{_idx}", width="stretch"):
                    st.session_state["_admin_open_proj"] = _pid
                    st.rerun()


def _cartera_lista(proys, alarmas, delays, aheads, costos, pendientes=None,
                   grupo="", puede_facturar=False):
    """Vista LISTA de la cartera (v228): la típica tabla — proyectos por filas, datos por
    columnas. Alternativa a `_cartera_clickeable`; se elige con el toggle de vista.

    ⚠️ v402: **elegir una fila ya no abre el proyecto**. Antes lo abría al instante, y eso
    dejaba la Lista como un sitio donde solo se MIRA el dinero: se veía «Sin facturar» y no
    se podía cobrar sin salir. Ahora la fila se selecciona y aparecen debajo las dos
    acciones explícitas — «Abrir →» y «Facturar» —, que es como ya funcionan Finanzas·Gastos
    (v215) y Usuarios (v226). Decisión del usuario, sabiendo el coste: **abrir pasa de 1 clic
    a 2**, y abrir es lo más frecuente.

    ⚠️ Y NO se hizo con un enlace en la celda, que era la idea de partida. Medido en el
    bundle que distribuye Streamlit (`DataFrame.*.js`), el clic de una celda de enlace hace
    `window.open(url, "_blank", …)` + `preventDefault()`: no recarga la pestaña actual
    —bien—, pero **abre una pestaña nueva**, y una pestaña nueva es una SESIÓN nueva, así
    que sin la cookie de «mantener la sesión» (opcional y desmarcada desde v221) el usuario
    aterriza en el login. Además un `LinkColumn` **ordena por la URL, no por el importe**
    (medido: $980 · $5,200 · $27,883 · $2,960, que es el orden alfabético de los PRJ-####),
    y esta columna existe justamente para ordenar por dónde está el dinero.
    """
    pendientes = pendientes or {}
    proys = sorted(proys, key=lambda p: (-delays.get(str(p.get("ID", "")), 0),
                                         -alarmas.get(str(p.get("ID", "")), 0)))

    def _ddmm(s):
        s = str(s or "").strip()[:10]
        if not s:
            return "—"
        from datetime import datetime as _dt
        for _f in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return _dt.strptime(s, _f).strftime("%d/%m/%y")
            except Exception:
                pass
        return "—"

    _rows = []
    for p in proys:
        _pid = str(p.get("ID", ""))
        _dl, _ah, _al = delays.get(_pid, 0), aheads.get(_pid, 0), alarmas.get(_pid, 0)
        _c = costos.get(_pid) or {}
        _ppto = (f"{int(round(P._num(_c.get('pct'))))}%" + (" over" if _c.get("over") else "")
                 if P._num(_c.get("presupuesto")) > 0 else "—")
        _users = len([x for x in str(p.get("CampoAsignados", "")).split(";") if x.strip()])
        _sit = (f"{_dl} d behind" if _dl else (f"{_ah} d ahead" if _ah else "—"))
        _rows.append({
            # v306: el ID primero. Es la identidad real (el nombre puede repetirse), y
            # tenerlo en la tabla permite dictarlo, buscarlo y cruzarlo con la hoja.
            "ID": _pid,
            "Proyecto": str(p.get("Nombre", "")),
            # ⚠️ v398: junto al nombre, no al final. Medido en producción: con 13
            # columnas y la tabla a ~520 px, puesta la décima **había que hacer
            # scroll para encontrarla** — o sea que no cumplía su función, que es
            # ver el dinero pendiente de un vistazo. Existir no es servir.
            "Not invoiced": round(pendientes.get(_pid, 0.0), 2),
            # ⚠️ v408 · el ORDEN de estas claves es el de las columnas (pandas respeta
            # el orden de inserción), y aquí decide qué se ve sin desplazarse. Medido en
            # producción a 1440: la tabla ocupaba 1339 px en 1054 visibles, así que
            # `Usuarios`, `Situación` y `Alertas` —las tres señales de «esto necesita
            # atención»— quedaban al otro lado del scroll, y al ir a buscarlas se
            # perdía el `ID` por la izquierda.
            # ⚠️ NO se arregló encogiendo columnas: se probó y NO cabe. Con 12-13
            # columnas y nombres de obra reales no hay reparto de anchos que quepa sin
            # CORTAR texto — glide recorta por *clip*, SIN elipsis, así que el corte no
            # deja «…» ni se ve en el DOM: hubo que medir `measureText` del canvas
            # contra el ancho de cada columna para descubrir que se comía 60 px del
            # nombre de obra y 60 del cliente. Encoger habría cambiado un problema
            # visible (hay que desplazarse) por uno invisible (lees un nombre a medias).
            # La cura es la de v398: no achicar, PRIORIZAR lo que se ve primero.
            "Avance": max(0, min(100, int(P._num(p.get("Avance"))))),
            "Status": _sit,
            "Alerts": str(_al) if _al else "",
            "Estado": _etq(str(p.get("Estado", ""))) or "—",
            "Users": _users,
            # De aquí en adelante, contexto: se consulta, no se vigila.
            "Cliente": str(p.get("Cliente", "") or "—"),
            "Tipo": str(p.get("Tipo", "") or "—"),
            "Inicio": _ddmm(p.get("FechaInicio")),
            "Fin": _ddmm(p.get("FechaFinEst")),
            "Ppto": _ppto,
        })
    _ev = st.dataframe(
        pd.DataFrame(_rows), hide_index=True, width="stretch",
        on_select="rerun", selection_mode="single-row", key="cart_tbl",
        column_config=tabla.cfg(None, {
            "Avance": st.column_config.ProgressColumn(
                t("Progress"), min_value=0, max_value=100, format="%d%%", width=78),
            # ⚠️ v399: la coma del formato NO es cosmética. Con `"$%.0f"` esta
            # celda pintaba `$27883` mientras la tarjeta de al lado —y el pie de
            # esta misma tabla, que sale de `theme.dinero`— ponían `$27,883`: la
            # misma cifra con dos caras en la misma pantalla. Medido interceptando
            # `fillText` (el DOM no sirve: glide pinta en canvas y su nodo
            # accesible lleva el valor CRUDO, `27882.67`). Se corrigieron los 39
            # formatos de dinero de la app, no solo este.
            # ⚠️ `%d` NO se cambió por `%.0f` en ningún sitio: uno TRUNCA y el otro
            # REDONDEA (3305.76 → $3,305 vs $3,306), así que sustituirlo movería
            # cifras en pantalla sin que nadie lo pidiera.
            "Not invoiced": st.column_config.NumberColumn(
                t("Not invoiced"), format="$%,.0f", width=104,
                help=t("The job's estimated revenue minus what has already been invoiced. You invoice from the card or from the job itself.")),
            # ⚠️ v408 · `pinned` en las dos de identidad. Antes, al desplazarse para
            # llegar a `Ritmo`/`Avisos`, el `ID` se salía por la izquierda — o sea que
            # justo mientras mirabas qué obra tiene problemas dejabas de saber CUÁL es,
            # y el ID es la identidad (el nombre puede repetirse). Verificado con un
            # scroll real: tras 255 px, `ID` y `Proyecto` siguen en su sitio.
            "ID":        st.column_config.TextColumn("ID", width=76, pinned=True),
            # ⚠️ v414 · 248 → 272. Medido en producción: el nombre más largo del grupo
            # («Stockland Wetherill Park — Instalación») ocupa 224 px de los 232 útiles,
            # o sea **8 px de margen**: un nombre 2-3 caracteres más largo se cortaba.
            # Y el corte es SILENCIOSO — comprobado a propósito en una mini-app: glide
            # NO dibuja «…», recorta en seco, así que un nombre a medias parece completo.
            # A 272 el margen pasa a 32 px (~5 caracteres) y ⚠️ **no se pierde ninguna
            # columna de la vista inicial**: siguen entrando las mismas 10, solo hay 24 px
            # más de scroll hacia lo que YA estaba fuera (Inicio · Fin · Ppto).
            # ⚠️ No se sube más: a 300 se cae `Tipo` de la vista. 272 es el máximo que
            # no cuesta nada.
            # Un ancho fijo nunca puede garantizar que quepa cualquier nombre; lo que
            # cierra el caso es que al seleccionar la fila la tira de acciones muestra el
            # nombre COMPLETO (v402).
            "Proyecto":  st.column_config.TextColumn(t("Project"), width=272, pinned=True),
            # Anchos medidos contra el texto REAL más largo de cada columna (peor caso),
            # no elegidos a ojo: con estos, 0 textos cortados.
            "Status": st.column_config.TextColumn(
                t("Pace"), width=100,
                help=t("Days behind or ahead of the plan.")),
            "Alerts":   st.column_config.TextColumn(
                t("Alerts"), width=70, help=t("Open alerts on the job.")),
            "Estado":    st.column_config.TextColumn(t("Status"), width=92),
            "Users":  st.column_config.NumberColumn(
                t("Team"), width=70, help=t("Field staff assigned.")),
        }))
    _tot = sum(pendientes.get(str(p.get("ID", "")), 0.0) for p in proys)
    if _tot > 0:
        # ⚠️ `theme` se importa por función en este módulo, no arriba (v342).
        from core import theme as _Tl
        _n = sum(1 for p in proys if pendientes.get(str(p.get("ID", "")), 0.0) > 0)
        st.caption(f":material/receipt: **{_Tl.dinero(_tot, 0)}** not invoiced "
                   f"in {_n} of the jobs shown.")
    st.caption(t(":material/touch_app: Tap a row and choose what to do with it.  Budget = % of the budget used (:orange[:material/warning:] if it went over) and over = over budget."))
    try:
        _sr = list(_ev.selection.rows)
    except Exception:
        _sr = []
    if _sr and _sr[0] < len(proys):
        # ⚠️ La selección NO actúa por sí sola (v402): solo muestra las acciones. Si volviera
        # a abrir el proyecto aquí, el mismo clic tendría dos significados y el botón de
        # facturar no se llegaría a ver nunca.
        from core import theme as _Tb
        _sp = proys[_sr[0]]
        _spid = str(_sp.get("ID", ""))
        _spf = float((pendientes or {}).get(_spid, 0.0) or 0)
        _con_fac = _spf > 0 and puede_facturar
        _cs = st.columns([4.4, 1.5, 1.5]) if _con_fac else st.columns([5.9, 1.5])
        _cs[0].markdown(
            f"**{_sp.get('Nombre', '')}**  \n"
            + (f":material/receipt: {_Tb.dinero(_spf, 0)} not invoiced"
               if _spf > 0 else ":material/check: nothing left to invoice"))
        if _cs[1].button(t("Open →"), key="cartlist_open", width="stretch"):
            st.session_state["_admin_open_proj"] = _spid
            st.session_state.pop("cart_tbl", None)   # limpia la selección → no re-abre al volver
            st.rerun()
        if _con_fac and _cs[2].button(
                t(":material/receipt_long: Invoice"), key="cartlist_fac", type="primary",
                width="stretch",
                help=f"New invoice with this job and its client already chosen · "
                     f"outstanding {_Tb.dinero(_spf, 0)}"):
            _ir_a_facturar(_spid, grupo)
            st.session_state.pop("cart_tbl", None)
            st.rerun()


def _panel_proyectos(grupo: str):
    # ── Proyecto ABIERTO (de una tarjeta, de HOME "ver completo", o del crear) ──
    _pp = st.session_state.pop("_prjsel_pending", None)
    if _pp:
        st.session_state["_admin_open_proj"] = str(_pp)
    _open = st.session_state.get("_admin_open_proj")
    if _open:
        # v315: sin el `---` de debajo. El botón ya iba en su propia fila y el separador
        # metía otros ~35 px entre él y la tarjeta, en una cabecera que ya era la parte
        # más pesada de la pantalla.
        if st.button(t("← Back to the portfolio"), key="pp_back_cartera"):
            st.session_state.pop("_admin_open_proj", None)
            st.rerun()
        _detalle_proyecto(str(_open), grupo)
        return

    # ── Cartera (tarjetas clickeables → abren el detalle) ──
    _ver_arch = st.checkbox(t(":material/archive: Show archived ones too"), key="ver_arch_admin",
                            help=t("Archived ones do not appear in lists or reports; open them from here to restore them."))
    proys = P.list_projects(grupo=grupo, incluir_archivados=_ver_arch)
    if not _ver_arch:
        _n_arch = len([p for p in P.list_projects(grupo=grupo, incluir_archivados=True)
                       if str(p.get("Estado", "")) == P.ARCHIVADO])
        if _n_arch:
            st.caption(f":material/inventory_2: {_n_arch} archived project(s) hidden.")
    if not proys:
        # ⚠️ El formulario va ANTES del return: desde v135 el survey ya no crea
        # proyectos, así que si aquí se cortara no habría forma de crear el primero.
        st.info(t("No projects in this company yet. Create the first one here; after that the Survey and the other tools can feed it."))
        _nuevo_proyecto_form(grupo, key="adm")
        return

    # % de presupuesto ejecutado por proyecto — de group_expenses (1 lectura CACHEADA,
    # no N): {pid: {pct, presupuesto, over, ...}}. v223.
    costos = {}
    try:
        from core import expenses as _exp
        _ge = _exp.group_expenses(grupo)
        costos = {str(r.get("id")): r for r in (_ge.get("proyectos") or [])}
    except Exception:
        pass
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    delays = P.delays_of_group(grupo)     # {pid: días de retraso} (cacheado)
    aheads = P.aheads_of_group(grupo)     # {pid: días de adelanto} (cacheado)

    # ── Filtro rápido (v209): búsqueda + chips, en doble columna ──
    _fc1, _fc2 = st.columns([2, 3])
    _q = _fc1.text_input(t("Search"), key="cart_q", label_visibility="collapsed",
                         placeholder=t("Search project or client…"))
    _filt = _fc2.radio(t("Filter"), ["Todos", "🔴 Retraso", "🟢 Adelanto", "⏸ En pausa"],
                       format_func=lambda o: {"Todos": t("All"),
                                              "🔴 Retraso": ":red[:material/trending_down:] " + t("Behind"),
                                              "🟢 Adelanto": ":green[:material/trending_up:] " + t("Ahead"),
                                              "⏸ En pausa": ":material/pause: " + t("On hold")}.get(o, o),
                       horizontal=True, key="cart_filt", label_visibility="collapsed")
    # v306: filtro por TIPO. Solo aparece si el grupo tiene proyectos de más de un tipo
    # (o alguno sin marcar): con todo igual sería un desplegable que no filtra nada.
    _SIN_T = "— no type —"
    _tipos_pres = sorted({str(p.get("Tipo", "")).strip() or _SIN_T for p in proys})
    _tsel = "Todos"
    if len(_tipos_pres) > 1:
        _tsel = st.selectbox(t("Type"), ["Todos"] + _tipos_pres, key="cart_tipo",
                             label_visibility="collapsed")
    _ql = (_q or "").strip().lower()

    def _pasa(p):
        _pid = str(p.get("ID", ""))
        # El ID entra en la búsqueda: es la identidad del proyecto y ahora se ve, así
        # que tiene que poder buscarse por él (pegar "PRJ-0007" y que salga).
        if _ql and _ql not in (f"{p.get('Nombre', '')} {p.get('Cliente', '')} "
                               f"{_pid}").lower():
            return False
        if _tsel != "Todos" and (str(p.get("Tipo", "")).strip() or _SIN_T) != _tsel:
            return False
        if _filt == "🔴 Retraso":
            return bool(delays.get(_pid))
        if _filt == "🟢 Adelanto":
            return bool(aheads.get(_pid))
        if _filt == "⏸ En pausa":
            return str(p.get("Estado", "")) == "En pausa"
        return True
    _proys_f = [p for p in proys if _pasa(p)]

    _nr, _na = len(delays), len(aheads)
    _hc1, _hc2 = st.columns([3, 2])
    _hc1.markdown(f"**{t('Portfolio')} — {len(_proys_f)} of {len(proys)}**"
                  + (f"  ·  :red[:material/cancel:] {_nr} behind schedule" if _nr else "")
                  + (f"  ·  :green[:material/check_circle:] {_na} ahead" if _na else ""))
    # v228: toggle de vista — tarjetas (resumen visual) o lista (tabla clásica).
    _view = _hc2.radio(t("View"), ["📋 Lista", "🃏 Tarjetas"], horizontal=True,
                       format_func=lambda o: {"🃏 Tarjetas": t(":material/grid_view: Cards"),
                                              "📋 Lista": t(":material/list: List")}.get(o, o),
                       key="cart_view", label_visibility="collapsed")
    # Pendiente de facturar de TODO el grupo, en UNA pasada (v397). Medido: ~32 ms y
    # 0 llamadas nuevas a Sheets en un rerun normal — por eso puede ir en la lista
    # (regla v142: medir antes de poner un dato derivado en cada fila).
    try:
        from core import invoices as _INV
        _pend = _INV.pendiente_por_proyecto(grupo)
    except Exception:
        _pend = {}
    if not _proys_f:
        st.caption(t("No project matches the filter."))
    elif _view == "📋 Lista":
        _cartera_lista(_proys_f, alarmas, delays, aheads, costos, pendientes=_pend,
                       grupo=grupo, puede_facturar=True)
    else:
        st.caption(t("Each card shows the summary; tap «Open» to see the detail."))
        _cartera_clickeable(_proys_f, alarmas, delays, aheads, costos,
                            pendientes=_pend, grupo=grupo, puede_facturar=True)
    # `_nuevo_proyecto_form` ya se pliega solo (tiene su propio expander) → no envolver
    # otra vez, o quedan dos expanders "Nuevo proyecto" anidados (v210).
    _nuevo_proyecto_form(grupo, key="adm")


def _portfolio_html(proys, horas, alarmas, ags, delays=None, aheads=None,
                    show_group=False) -> str:
    """Lista de tarjetas de proyecto: punto de estado, nombre/cliente, ubicación,
    píldora, barra de avance, horas y badges de alarmas / retraso / adelanto.
    Retraso → borde rojo + badge ⏰ · Adelanto → borde verde + badge ⏩."""
    delays = delays or {}
    aheads = aheads or {}
    parts = []
    for p in proys:
        est = str(p.get("Estado", ""))
        bg, fg, bar = _estado_colors(est)
        av  = P._num(p.get("Avance"))
        nom = str(p.get("Nombre", "")) or "(no name)"
        pid = str(p.get("ID", ""))
        hrs = horas.get(str(p.get("ID", "")), 0.0)
        na  = alarmas.get(pid, 0)
        ag  = ags.get(str(p.get("AgrupacionID", "")), "")
        sub = f"{pid} · {str(p.get('Cliente','')) or '—'}" + (f" · {ag}" if ag else "")
        if show_group and p.get("Grupo"):
            sub = f"{_MI('business')} {p.get('Grupo')} · " + sub
        ubic = str(p.get("Ubicacion", "") or "")
        ubic_html = (f'<div style="font-size:11px;white-space:nowrap;overflow:hidden;'
                     f'text-overflow:ellipsis;">{maps.maps_link_html(ubic, ubic, color="#2e6da4")}</div>'
                     if ubic else "")
        alarm = (f'<div style="width:44px;text-align:center;flex:none;color:#c0392b;'
                 f'font-size:12px;font-weight:600;">{_MI('notifications')} {na}</div>'
                 if na else '<div style="width:44px;flex:none;"></div>')
        # Retraso (rojo) / adelanto (verde) → borde + badge de días
        d, adel = delays.get(pid), aheads.get(pid)
        card_border = "border:1px solid #e6e9ef"
        retraso_badge = ""
        if d:
            card_border = "border:1px solid #e6e9ef;border-left:4px solid #c0392b"
            retraso_badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                             f'background:#fcebeb;color:#a32d2d;white-space:nowrap;flex:none;'
                             f'font-weight:600;">{_MI('alarm')} {d:.0f} d</span>')
        elif adel:
            card_border = "border:1px solid #e6e9ef;border-left:4px solid #1e8449"
            retraso_badge = (f'<span style="font-size:12px;padding:3px 9px;border-radius:20px;'
                             f'background:#eaf3de;color:#3b6d11;white-space:nowrap;flex:none;'
                             f'font-weight:600;">{_MI('trending_up')} {adel:.0f} d</span>')
        parts.append(
            f'<div style="display:flex;align-items:center;gap:12px;padding:11px 14px;'
            f'{card_border};border-radius:10px;margin-bottom:8px;background:#fff;">'
            f'<div style="width:9px;height:9px;border-radius:50%;background:{bar};flex:none;"></div>'
            '<div style="flex:1;min-width:0;">'
            f'<div style="font-size:14px;font-weight:600;color:#1f2937;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">{nom}</div>'
            f'<div style="font-size:12px;color:#6b7280;white-space:nowrap;overflow:hidden;'
            f'text-overflow:ellipsis;">{sub}</div>'
            + ubic_html +
            '</div>'
            + retraso_badge +
            f'<span style="font-size:12px;padding:3px 10px;border-radius:20px;background:{bg};'
            f'color:{fg};white-space:nowrap;flex:none;">{_etq(est)}</span>'
            '<div style="width:118px;flex:none;">'
            '<div style="display:flex;justify-content:space-between;font-size:11px;'
            f'color:#6b7280;margin-bottom:3px;"><span>Avance</span>'
            f'<span style="color:#1f2937;font-weight:600;">{av:.0f}%</span></div>'
            '<div style="height:6px;background:#eef1f5;border-radius:20px;overflow:hidden;">'
            f'<div style="height:100%;width:{av:.0f}%;background:{bar};"></div></div>'
            '</div>'
            f'<div style="width:54px;text-align:right;flex:none;font-size:12px;color:#6b7280;">'
            f'{_MI("schedule")} {hrs:.0f}h</div>'
            + alarm +
            '</div>'
        )
    return "".join(parts)


def _induccion_section(pid, prj, grupo=None, allow_send=False):
    """Muestra instrucciones particulares + inducciones (links) del proyecto.
    Si allow_send, el admin puede (re)enviarlas por Telegram/email a los asignados."""
    instr = str(prj.get("Instrucciones", "") or "").strip()
    links = P.parse_links(prj.get("InduccionLinks", ""))
    if not instr and not links:
        return
    with st.expander(t(":material/push_pin: Project instructions and inductions"), expanded=bool(links)):
        if instr:
            st.markdown(t("**Specific instructions**"))
            st.markdown(instr)
        if links:
            st.markdown(t("**Inductions to complete**"))
            for l in links:
                st.markdown(f"- [{l}]({l})")
            if allow_send and notify.any_channel_configured():
                asignados = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
                if asignados and st.button(t(":material/send: Resend the induction to those assigned"),
                                           key=f"send_ind_{pid}"):
                    n = 0
                    for un in asignados:
                        try:
                            rr = notify.notify_induction(un, prj.get("Nombre", ""), links)
                            if rr.get("email") or rr.get("telegram"):
                                n += 1
                        except Exception:
                            pass
                    st.success(f":material/send: Sent to {n} field user(s).")


def _diagnostico(ps: dict) -> dict:
    """Traduce el cronograma a lo accionable. Todo sale de `ps`; no lee nada nuevo.

    ⚠️ "SPI 0.47" no le dice nada a nadie en obra. Lo que sí: a qué ritmo vas, a
    qué ritmo tendrías que ir, **qué actividad tocaba hoy y sigue sin arrancar**
    y cuál es el próximo hito. Eso es lo que explica el retraso; el % solo lo
    constata.
    """
    sched = ps["sched"]
    acts  = sched["activities"]
    av    = ps.get("avances") or []
    proj  = ps.get("proj") or {}
    hoy   = ps["today_day"]
    total = max(1, sched["total_dias"])
    ini   = sched["start_date"]

    ev = proj.get("ev", 0.0)

    # Ritmo: %/dia hecho vs %/dia que hace falta para llegar a la fecha
    ritmo_real = (ev / hoy) if hoy and hoy > 0 else None
    dias_rest  = total - hoy
    ritmo_nec  = ((100.0 - ev) / dias_rest) if dias_rest > 0 else None
    factor     = (ritmo_nec / ritmo_real) if (ritmo_real and ritmo_real > 0.01
                                              and ritmo_nec) else None

    tocaban, en_curso, proximo = [], [], None
    for i, a in enumerate(acts):
        pct  = float(av[i]) if i < len(av) else 0.0
        fin  = a["inicio"] + a["duracion"]
        f_i  = ini + timedelta(days=int(a["inicio"]))
        # `inicio < hoy` (estricto): el dia en que se abre la ventana aun no
        # cuenta como retraso — si no, un proyecto recien creado nace en rojo.
        if a["inicio"] < hoy <= fin and pct < 100:
            tocaban.append({"nombre": a["nombre"], "avance": pct,
                            "desde": f_i, "dur": a["duracion"]})
        if 0 < pct < 100:
            en_curso.append({"nombre": a["nombre"], "avance": pct,
                             "tarde": hoy > fin})     # arrastrada: ya paso su ventana
        if proximo is None and a["inicio"] > hoy:
            proximo = {"nombre": a["nombre"], "fecha": f_i,
                       "faltan": a["inicio"] - hoy}

    # Sin arrancar y ya tocaba: es LA causa del retraso, no un detalle
    paradas = [x for x in tocaban if x["avance"] <= 0]
    return {"ritmo_real": ritmo_real, "ritmo_nec": ritmo_nec, "factor": factor,
            "dias_rest": dias_rest, "tocaban": tocaban, "paradas": paradas,
            "en_curso": en_curso, "arrastradas": [x for x in en_curso if x["tarde"]],
            "proximo": proximo, "ev": ev, "pv": proj.get("pv", 0.0)}


def _equipo_proyecto(pid, grupo):
    """:material/engineering: Quién ha trabajado en ESTE proyecto y cuántas horas (v216). El dato ya
    estaba (labor_breakdown, usado en 💰 Costos); aquí se surfacea, sin el costo."""
    try:
        from core import expenses as E
        if not E.is_configured():
            return
        _lb = E.labor_breakdown(pid, grupo)
    except Exception:
        return
    st.markdown(t("**:material/groups: Who has worked here**"))
    if not _lb["items"]:
        st.caption(t("Nobody has clocked hours to this project yet."))
        return
    st.dataframe(pd.DataFrame([{"Persona": x["usuario"], "Horas": x["horas"]}
                               for x in _lb["items"]]),
                 hide_index=True, width="stretch", column_config=tabla.cfg())
    st.caption(f"Total: **{_lb['horas']:.1f} h**")


# ⚠️ Las CLAVES son los nombres REALES de columna (`auditoria` guarda por ellos): no se
# tocan. Lo que se traduce son los VALORES, que es lo único que se pinta.
_CAMPO_LEGIBLE = {
    "MargenPct": "Margin (%)", "Presupuesto": "Budget", "Avance": "Progress (%)",
    "Estado": "Status", "EstadoManual": "Manual status", "FechaInicio": "Start date",
    "FechaFinEst": "Estimated end date", "Cliente": "Client", "ClienteID": "Client",
    "Nombre": "Name", "CampoAsignados": "Assigned staff",
    "AgrupacionID": "Grouping", "PesoEnAgrupacion": "Weight in the grouping",
    "TarifaHora": "Hourly rate",
}


def _historial_section(pid: str):
    """Quién cambió qué y cuándo en este proyecto (v342).

    Solo aparece si hay algo anotado: un desplegable vacío en cada proyecto sería
    ruido, y los proyectos anteriores a v342 no tienen rastro.
    """
    try:
        from core import auditoria, theme        # `theme` se importa local en este módulo
        filas = auditoria.historial(entidad="proyecto", entidad_id=pid, limite=50)
    except Exception:
        return
    if not filas:
        return
    with st.expander(f":material/history: Change history ({len(filas)})"):
        st.caption(t("Changes that move money or the job's status are recorded (margin, budget, dates, progress, client, staff)."))
        for r in filas:
            _quien = str(r.get("Usuario", "") or "—")
            st.markdown(f"**{r.get('Fecha','')}** · {_quien}")
            for campo, (antes, despues) in (r.get("cambios") or {}).items():
                _lbl = _CAMPO_LEGIBLE.get(campo, campo)
                _a = str(antes or "").strip() or t("(empty)")
                _d = str(despues or "").strip() or t("(empty)")
                st.markdown(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;{_lbl}: "
                    f"<span style='color:{theme.GRIS_SUAVE}'>{_a}</span> → <b>{_d}</b>",
                    unsafe_allow_html=True)


def _estado_section(pid: str, grupo: str, prj: dict):
    """Pestaña :material/bar_chart: Estado (v211: doble columna arriba — cómo va | alarmas + equipo; el
    ritmo, el desglose y el cronograma van a ancho completo abajo)."""
    ps = P.project_schedule(pid)
    if not (ps and ps["sched"].get("activities")):
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=False)
        st.info(t("This project has no activities, so there is no schedule to follow. Add them in :material/edit: Data."))
        return

    d    = _diagnostico(ps)
    proj = ps.get("proj") or {}
    dv   = proj.get("desvio", 0.0)
    dg   = proj.get("dias_gap", 0.0)

    # ── Titular: una frase que diga como va, antes de cualquier numero ──
    # ⚠️ v311: el titular se pintaba con `**...**` DENTRO de un `<div>` y Streamlit no
    # procesa markdown dentro de HTML → en pantalla salían los asteriscos literales
    # ("Vas **54 puntos por debajo** del plan"). Se emite `<b>` con el color del estado.
    # ⚠️ v452: la frase va ENTERA como clave de traduccion (con `{n}` de marcador), no
    # partida en `t("You are") + ... + t("plan")`: el orden de palabras cambia entre
    # idiomas y tres claves sueltas no se pueden recomponer en otro idioma.
    if dv <= -1:
        _tit_html, _col = (t("You are <b>{n} points behind</b> plan").replace("{n}", f"{abs(dv):.0f}"), "#c0392b")
    elif dv >= 1:
        _tit_html, _col = (t("You are <b>{n} points ahead of</b> plan").replace("{n}", f"{dv:.0f}"), "#1e8449")
    else:
        _tit_html, _col = ("You are <b>on plan</b>", "#2e6da4")
    # ⚠️ proj["today_day"] viene CLAMPADO al total: en un proyecto pasado de fecha
    # diria "día 29 de 29" llevando 40. El real es ps["today_day"].
    _hoy_real = ps["today_day"]
    _tot      = proj.get("total", 0)
    _dia_txt  = (f"day {_hoy_real} of {_tot}" if _hoy_real <= _tot
                 else f"day {_hoy_real} — {_hoy_real - _tot} more than the {_tot} planned")

    # ── KPIs (tarjetas, no st.metric planos) ──
    _fin = (proj["fecha_proj"].strftime("%d/%m/%Y")
            if proj.get("fecha_proj") else "—")
    _pd  = proj.get("proj_dias")
    _cf  = "#c0392b" if (_pd is not None and _pd > 0.5) else (
           "#1e8449" if (_pd is not None and _pd < -0.5) else None)
    _est = ("On time" if abs(dg) < 0.5
            else f"{abs(dg):.0f} d {"behind" if dg > 0 else "ahead"}")
    # v212: "Avance real" ya está en la cabecera del detalle (métrica + barra) → no
    # repetirlo aquí. "Debería ir" y "Desvío" se leen contra ese avance de la cabecera.
    tarj = [_kpi_card(t("Should be at"), f"{d['pv']:.0f}%"),
            _kpi_card(t("Variance"), f"{dv:+.0f}%", _col),
            _kpi_card(t("Situation"), _est, "#c0392b" if dg > 0.5 else None),
            _kpi_card(t("Projected finish"), _fin, _cf)]

    # ── v311: titular + KPIs a ANCHO COMPLETO ────────────────────
    # Antes iban en la columna izquierda de un [3,2] cuya derecha llevaba 6 alarmas
    # y una tabla: el bloque corto quedaba enfrente del largo y la izquierda se veía
    # vacía ~800 px. Ahora lo corto va arriba a lo ancho y abajo se enfrentan dos
    # bloques LARGOS (actividades | alarmas), que es lo que equilibra la pantalla.
    # ⚠️ El titular va en `st.markdown` SIN html: iba dentro de un `<div>` y ahí el
    # markdown NO se procesa, así que los `**` salían literales en pantalla.
    st.markdown(f"<span style='font-size:16px'>{_tit_html}</span>"
                f"<span style='color:#6b7280;font-size:14px'> · {_dia_txt}</span>",
                unsafe_allow_html=True)
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 10px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ── El ritmo: mas accionable que el SPI (banner, ancho completo) ──
    # ⚠️ v324: la guarda pedía `ritmo_nec is not None`, pero `ritmo_nec` vale None
    # EXACTAMENTE cuando `dias_rest <= 0` → el `if dias_rest <= 0` de dentro no
    # podía cumplirse nunca y su aviso era CÓDIGO MUERTO: un proyecto pasado de
    # fecha se quedaba sin banner de ritmo, en silencio. Ahora ese caso se atiende
    # ANTES de exigir `ritmo_nec`, y a partir de ahí sí está garantizado.
    if d["ritmo_real"] is not None:
        if d["dias_rest"] <= 0 or d["ritmo_nec"] is None:
            st.warning(f":material/schedule: The planned finish date has already passed and there is "
                       f"**{100 - d['ev']:.0f}%** still to complete.")
        elif d["ritmo_real"] <= 0.01:
            # ⚠️ v324: sin este caso, un proyecto SIN AVANCE caía en el `else` y
            # recibía el mensaje MÁS TRANQUILO de los tres ("justo el ritmo que
            # hace falta"). Pasaba porque `factor` se deja en None para no dividir
            # por cero, y `factor and …` es falsy → se saltaban las dos ramas de
            # aviso. El proyecto que peor va era el que menos alarma daba.
            st.error(f":material/schedule: **No progress yet**: you need "
                     f"**{d['ritmo_nec']:.1f} %/day** over the {d['dias_rest']:.0f} days "
                     f"left to make the date.")
        elif d["factor"] and d["factor"] > 1.15:
            st.error(f":material/schedule: You are running at **{d['ritmo_real']:.1f} %/day** and you need "
                     f"**{d['ritmo_nec']:.1f} %/day** to make the date: "
                     f"you have to **speed up ×{d['factor']:.1f}** over the "
                     f"{d['dias_rest']:.0f} days left.")
        elif d["factor"] and d["factor"] < 0.85:
            st.success(f":material/schedule: You are running at **{d['ritmo_real']:.1f} %/day** and at "
                       f"**{d['ritmo_nec']:.1f} %/day** you make it: there is room.")
        else:
            st.info(f":material/schedule: You are running at **{d['ritmo_real']:.1f} %/day**, exactly the "
                    f"rate needed ({d['ritmo_nec']:.1f} %/day).")

    # El diagnostico: el equipo sigue en trabajo viejo y lo de hoy no arranca
    if d["paradas"] and d["arrastradas"]:
        st.warning(":material/stethoscope: The crew is still finishing **"
                   + ", ".join(x["nombre"] for x in d["arrastradas"][:3])
                   + "**, so **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3])
                   + "** has not started yet. That is where the delay is.")
    elif d["paradas"]:
        st.warning(":material/stethoscope: Not started and already due: **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3]) + "**.")

    # ── Dos bloques LARGOS enfrentados: actividades | alarmas y equipo ──
    _izq, _der = st.columns([3, 2], gap="large")
    with _izq:
        # v311: «Tocaba hoy» y «En curso ahora» eran dos columnas, una con UNA línea
        # y otra con diez → media pantalla vacía. Se fusionan en UNA lista con el
        # estado de cada actividad, que además es como se lee el Gantt de al lado.
        st.markdown(t("**:material/checklist: Activities**"))
        _vistas = set()
        for x in d["paradas"]:
            _vistas.add(x["nombre"])
            st.markdown(f":red[:material/cancel:] **{x['nombre']}** — not started, "
                        f"it was due on {x['desde'].strftime('%d/%m')} ({x['dur']:.0f} d)")
        for x in d["tocaban"]:
            if x["nombre"] in _vistas or x["avance"] <= 0:
                continue
            _vistas.add(x["nombre"])
            st.markdown(f":green[:material/check_circle:] {x['nombre']} — "
                        f"{x['avance']:.0f}% · due today")
        for x in d["en_curso"]:
            if x["nombre"] in _vistas:
                continue
            st.markdown((":orange[:material/hourglass_top:] " if x["tarde"]
                         else ":blue[:material/play_arrow:] ")
                        + f"{x['nombre']} — {x['avance']:.0f}%"
                        + (t(" _(carried over)_") if x["tarde"] else ""))
        if not _vistas and not d["en_curso"]:
            st.caption(t("No open or overdue activity."))
        if d["proximo"]:
            st.caption(f":material/flag: Next milestone: **{d['proximo']['nombre']}** starts on "
                       f"{d['proximo']['fecha'].strftime('%d/%m/%Y')} "
                       f"(in {d['proximo']['faltan']:.0f} days).")
    with _der:
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=False)
        st.markdown("")
        _equipo_proyecto(pid, grupo)

    # ── Cumplimiento de certificados del equipo (si el proyecto exige alguno) ──
    _cumplimiento_equipo(pid, grupo, prj)

    # ── La grafica, a ANCHO COMPLETO y con lienzo ancho ──
    st.markdown(t("**:material/calendar_month: Schedule and progress**"))
    n = len(ps["sched"]["activities"])
    _VW = 1280          # el ancho del contenido; el SVG escala a 100% hasta ahí
    components.html(
        '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
        + schedule_svg(ps["sched"], real_curve=ps["real"], today_day=ps["today_day"],
                       avances=ps.get("avances"), proj=proj,
                       titulo=prj.get("Nombre", ""), vw=_VW,
                       animar=True)      # v336: pantalla sí, PDF no
        + '</body></html>',
        # ⚠️ el alto sale de la MISMA formula que el SVG (antes era `300 + n*21`,
        # 18 px de menos, y el pie del grafico se recortaba).
        height=schedule_svg_alto(n), scrolling=False,
    )
    st.caption(t("The **coloured band** between the two curves is the gap against the plan (red if you are behind, green if ahead). ● red = the activity should already have started."))


def _detalle_proyecto(pid: str, grupo: str = None):
    prj = P.get_project(pid)
    if not prj:
        st.error(t("Project not found."))
        return
    # ⚠️ v351 — EL CASO PEOR del aislamiento. La línea de abajo ADOPTA el grupo del
    # proyecto, así que sin esta comprobación un administrador abría el detalle
    # completo de otra empresa —costos, horas, personal y archivos— solo cambiando
    # `?p=` en la URL (los deep-links se cablearon en v337).
    if not tenant.exigir(prj, "This project"):
        st.session_state.pop("_admin_open_proj", None)
        return
    # El grupo se toma del propio proyecto (así el propietario puede abrir cualquiera)
    grupo = str(prj.get("Grupo", "")) or (grupo or "")

    # ⚠️ v379: el PROPIETARIO entra aquí en datos de OTRO libro (v359). Su sesión no
    # tiene grupo, así que sin declarar el ámbito todo lo de abajo —costos, horas,
    # alarmas, actividades, archivos— se leería del MAESTRO y saldría vacío.
    # Se re-entra una sola vez bajo el ámbito en vez de envolver 300 líneas en un
    # `with`: reindentar un bloque así es justo lo que rompió v120 y v148. La propia
    # condición corta la recursión (en la re-entrada el grupo activo ya es este).
    if grupo and tenant.es_propietario() and tenant.grupo_activo() != grupo:
        with tenant.como_grupo(grupo):
            return _detalle_proyecto(pid, grupo)

    avance = P._num(prj.get("Avance"))
    est    = str(prj.get("Estado", ""))
    _bg, _fg, _bar = _estado_colors(est)
    _cli  = str(prj.get("Cliente", "")) or "—"
    _ubic = (" · " + maps.maps_link_html(prj.get("Ubicacion"))) if prj.get("Ubicacion") else ""
    # v306: el ID a la vista. Es LA identidad del proyecto (el nombre puede repetirse),
    # así que se muestra siempre y en monoespaciada, para poder dictarlo o buscarlo.
    _tp = str(prj.get("Tipo", "")).strip()
    # v315: TODO en la tarjeta. Antes debajo iban dos `st.metric` de ~660 px para dos
    # números y una barra de progreso a ancho completo que repetía el mismo %: ~130 px
    # de cabecera para lo que cabe en una línea. La derecha de la tarjeta estaba vacía.
    _horas = P.project_hours(prj.get("Nombre"), grupo, pid=pid)
    _av = max(0, min(100, int(round(avance))))
    st.markdown(
        f'<div style="border:1px solid #e6e9ef;border-left:4px solid {_bar};border-radius:10px;'
        'padding:12px 16px;margin-bottom:10px;background:#fff;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;'
        'flex-wrap:wrap;">'
        f'<div style="font-size:18px;font-weight:800;color:#1f2937;">{prj.get("Nombre","")}'
        f'<span style="font-family:monospace;font-size:12px;color:#667080;font-weight:500;'
        f'margin-left:8px;">{pid}</span></div>'
        f'<span style="font-size:12px;padding:3px 11px;border-radius:20px;background:{_bg};'
        f'color:{_fg};white-space:nowrap;">{_etq(est)}</span></div>'
        f'<div style="font-size:12px;color:#6b7280;margin-top:3px;">'
        + (f'{_tp} · ' if _tp else '')
        + f'{_cli}{_ubic}</div>'
        # barra + las dos cifras en la MISMA línea: la barra ya dice el %, así que el
        # número va a su lado en vez de en una tarjeta propia.
        '<div style="display:flex;align-items:center;gap:12px;margin-top:11px;">'
        '<div style="flex:1;height:8px;background:#eef1f5;border-radius:20px;overflow:hidden;">'
        f'<div style="height:100%;width:{_av}%;background:{_bar};border-radius:20px;"></div></div>'
        f'<span style="font-size:13px;color:#374151;white-space:nowrap;">'
        f'<b>{_av}%</b> ' + t('progress') + '</span>'
        f'<span style="font-size:13px;color:#6b7280;white-space:nowrap;">'
        f'<b style="color:#374151">{_horas:.1f} h</b> {t("worked")}</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # ── Facturar, EN LA CABECERA (v397) ──────────────────────────────────────
    # El atajo existe desde v357 pero vivía al final de 💰 Costos, por debajo de la
    # tabla de mano de obra: 3 clics desde la cartera y solo visible en una de las
    # cuatro sub-pestañas. Aquí se ve siempre, y solo cuando hay algo que pedir.
    # ⚠️ `_detalle_proyecto(pid, grupo)` NO recibe `can_delete` (lo resuelve cada
    # sección por su cuenta) y este módulo importa `theme` DENTRO de cada función,
    # no a nivel de módulo: escribir `can_delete` y `theme.` aquí sin más eran dos
    # NameError seguros — el fallo de ámbito de v342.
    from core import theme as _Tc
    _rol_ok = str((st.session_state.get("auth") or {}).get("rol", "")).lower() in (
        "administrador", "propietario")
    if _rol_ok:                         # solo gestión: el campo no factura
        try:
            from core import invoices as _INV
            _pend_cab = _INV.pendiente_de_facturar(pid, grupo, prj)
        except Exception:
            _pend_cab = 0.0
        if _pend_cab > 0:
            _fc1, _fc2 = st.columns([3, 1])
            _fc1.markdown(f":material/receipt: Not invoiced: **{_Tc.dinero(_pend_cab, 0)}**")
            if _fc2.button(t(":material/receipt_long: Invoice"), key=f"faccab_{pid}",
                           width="stretch", type="primary",
                           help=t("New invoice with this job and its client already chosen.")):
                _ir_a_facturar(pid, grupo)
                st.rerun()

    # ── Sub-navegacion: 11 secciones en un scroll unico era el mismo
    # problema que tenia el Survey antes de v114. Radio, NO st.tabs (v56).
    # v234: format_func muestra iconos Material; las OPCIONES siguen siendo el ID (con
    # emoji) → el match de abajo y cualquier deep-link no cambian.
    _sec = st.radio(t("Project section"),
                    ["📊 Estado", "✏️ Datos", "💰 Costos", "📎 Archivos"],
                    format_func=lambda o: {"📊 Estado": t(":material/insights: Status"),
                                           "✏️ Datos": t(":material/edit: Data"),
                                           "💰 Costos": t(":material/payments: Costs"),
                                           "📎 Archivos": t(":material/folder: Files")}.get(o, o),
                    # v316: key `cpxseg_*` → el SEGMENTADO del kit (v292): sin bolitas,
                    # con marco y el elegido resaltado. Es la pieza para "una de N", que
                    # es lo que son estas 4 secciones. ⚠️ NO se usa la fila de botones del
                    # Panel: aquella es un acordeón de herramientas OPCIONALES (se pueden
                    # cerrar todas); aquí siempre hay una sección abierta. Medido: la fila
                    # de botones sale a 1120 px estirados y necesita CSS propio para el
                    # activo; el segmentado ocupa 412 y ya lo hace.
                    horizontal=True, key="cpxseg_prj_sec",
                    label_visibility="collapsed")
    # v316: sin el `---` de debajo. El segmentado ya lleva marco propio, así que el
    # separador era una raya más en la cabecera que justo acabamos de adelgazar.

    if _sec == "📊 Estado":
        # ── Alarmas / avisos del proyecto ──
        _estado_section(pid, grupo, prj)

    elif _sec == "✏️ Datos":
        # ── Instrucciones e inducciones ──
        _induccion_section(pid, prj, grupo, allow_send=True)


        # ── Asignar campo: FUERA del form ──
        # Dentro de un `st.form` los widgets no escriben en session_state hasta
        # el submit, asi que un aviso "en vivo" ahi dentro es imposible. Es el
        # mismo motivo por el que v127 lo saco del form en el Survey; aqui se
        # habia quedado dentro, y asignar gente a un proyecto EXISTENTE es la
        # accion del dia a dia.
        _campos_disp = _field_users(grupo)
        _actuales = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";")
                     if x.strip()]
        _opts = sorted(set(_campos_disp) | set(_actuales))
        asignados = st.multiselect(t(":material/engineering: Field users assigned"), _opts,
                                   default=_actuales, key=f"asig_{pid}")
        _ecerts = st.multiselect(
            t(":material/badge: Certificates the project requires"), credentials.CATALOGO,
            default=[x.strip() for x in str(prj.get("CertsReq", "")).split(";") if x.strip()],
            key=f"certs_{pid}",
            help=t("When staff are assigned, anyone who does not meet them is flagged."))
        # feature 1 (ya en otro proyecto) + feature 3 (cumplimiento vs certs requeridos)
        # + v432: las ausencias que cruzan las fechas DE ESTA obra (aquí sí se saben;
        # en el alta nueva las fechas viven dentro del form y aún no están escritas,
        # así que allí se avisa de las ausencias que todavía no han terminado).
        _avisar_asignados(asignados, grupo, exclude_pid=pid, certs_req=_ecerts,
                          fechas=(prj.get("FechaInicio"), prj.get("FechaFinEst")))

        # ── Ubicación en el mapa (fuera del form: el mapa necesita reruns) — v193 ──
        from core import location_ui
        # ⚠️ v419: el caso inverso — dirección escrita pero SIN pin. Esa obra no sale en
        # el mapa de Home ni en la Ruta del día, y hasta ahora no lo decía nadie: había
        # que abrir el proyecto y darse cuenta. Se avisa, pero NO se geocodifica sola
        # (decisión del usuario): un pin inventado que nadie ha mirado puede mandar a
        # alguien al sitio equivocado, y esto es una app de obra.
        _sin_pin = (str(prj.get("Ubicacion", "") or "").strip()
                    and location_ui.to_float(prj.get("Lat")) is None)
        if _sin_pin:
            st.warning(":material/wrong_location: **This job is not on the map.** It has an "
                       f"address (*{prj.get('Ubicacion')}*) but no point, so it does not "
                       "appear on the Home map or in the Day route. Open it below and "
                       "press **Search** to place it.")
        with st.expander(t("Location on the map (project pin)"), icon=":material/map:",
                         expanded=not location_ui.to_float(prj.get("Lat"))):
            _plat, _plng = location_ui.location_picker(
                f"edloc_{pid}",
                lat=location_ui.to_float(prj.get("Lat")),
                lng=location_ui.to_float(prj.get("Lng")),
                direccion=str(prj.get("Ubicacion", "")))

        # ── Cliente: elegir existente o escribir uno nuevo (fuera del form) — v256 ──
        from core import clientes as _C
        _cli_fichas = _C.list_clientes(grupo)
        _cli_names = [str(c.get("Nombre", "")) for c in _cli_fichas]
        _CLI_NONE, _CLI_OTRO = "— no client —", t("➕ Other (type a new one)")
        _opts_cli = [_CLI_NONE] + _cli_names + [_CLI_OTRO]
        _cur_cid = str(prj.get("ClienteID", "")).strip()
        _cur_txt = str(prj.get("Cliente", "")).strip()
        _cur_name = ""
        if _cur_cid:
            _cur_name = next((str(c.get("Nombre", "")) for c in _cli_fichas
                              if str(c.get("ID", "")) == _cur_cid), "")
        if not _cur_name and _cur_txt:
            _cur_name = next((n for n in _cli_names if _C._norm(n) == _C._norm(_cur_txt)), "")
        _cidx = (_opts_cli.index(_cur_name) if _cur_name
                 else (_opts_cli.index(_CLI_OTRO) if _cur_txt else 0))
        _ecli_sel = st.selectbox(t(":material/contacts: Client"), _opts_cli, index=_cidx,
                                 key=f"ed_clisel_{pid}",
                                 help=t("Choose a client from Contacts or type a new one."))
        _ecli_new = ""
        if _ecli_sel == _CLI_OTRO:
            _ecli_new = st.text_input(t("New client's name"),
                                      value=(_cur_txt if not _cur_name else ""),
                                      key=f"ed_clinew_{pid}")

        # ── Editar datos ──
        with st.form(f"edit_{pid}"):
            st.markdown(t("**Project data**"))
            nombre   = st.text_input(t("Name"), value=prj.get("Nombre", ""))
            e1, e2 = st.columns(2)
            # v306: tipo editable. `_SIN_TIPO` primero para los proyectos anteriores a
            # v306, que lo tienen vacío: se ven como "sin tipo" hasta que se marquen, en
            # vez de fingir que todos eran instalaciones.
            _TIPO_VACIO = "— no type —"
            _tp_cur = str(prj.get("Tipo", "")).strip()
            _tp_opts = ([_TIPO_VACIO] + P.TIPOS) if _tp_cur not in P.TIPOS else list(P.TIPOS)
            tipo = e1.selectbox(t("Project type"), _tp_opts,
                                index=_tp_opts.index(_tp_cur) if _tp_cur in _tp_opts else 0,
                                help=t("Only «Installation» uses the standard job schedule."))
            # ⚠️ v419: la ubicación sale del MAPA, no de un campo suelto. v272 ya lo hizo
            # al CREAR («ya no se pide dos veces») y la edición se quedó con el
            # `text_input` desconectado del pin: por eso un proyecto podía tener pin sin
            # dirección —y entonces Home, Ruta del día, Pre-Start y los avisos, que leen
            # el TEXTO, lo mostraban como si no estuviera ubicado— o dirección sin pin.
            # Dos entradas para un dato es la fuente del problema, no su síntoma.
            # ⚠️ Solo se pisa el texto si el pin se ha TOCADO en esta pantalla
            # (`_addr`/`_q` del picker). Si no, se conserva el que hay: reescribir en
            # frío cambiaría direcciones puestas a mano («Gagiope», «259 Cleveland
            # Redfern») por la versión del geocoder sin que nadie lo pidiera — es la
            # lección de v360.
            # ⚠️ Solo `_addr` —la dirección CONFIRMADA por el geocoder—, nunca `_q`. `_q`
            # es la caja de búsqueda: si alguien teclea media dirección y no pulsa
            # Buscar, se guardaría ese texto a medias como ubicación del proyecto. (Al
            # CREAR sí se usa `_q` de respaldo porque allí no hay valor previo que
            # conservar; aquí sí lo hay.)
            ubic = str(prj.get("Ubicacion", "") or "")
            _ubi_mapa = str(st.session_state.get(f"edloc_{pid}_addr") or "").strip()
            if _ubi_mapa:
                ubic = _ubi_mapa
            e2.text_input(t("Location"), value=ubic, disabled=True,
                          help=t("It comes from the map pin (above). Move it or search the address to change it."))
            modelo   = e2.text_input(t("Model"), value=prj.get("Modelo", ""))
            ing      = e1.text_input(t("Engineer"), value=prj.get("Ingeniero", ""))
            # Calendario, no texto libre: ver `_a_fecha`. El valor se guarda
            # siempre en ISO, que es lo unico que `project_schedule` sabe leer.
            f_ini    = e2.date_input(t("Start date"), value=_a_fecha(prj.get("FechaInicio")),
                                     format="YYYY-MM-DD")
            f_fin    = e1.date_input(t("Estimated finish date"), value=_a_fecha(prj.get("FechaFinEst")),
                                     format="YYYY-MM-DD")
            instr    = st.text_area(t(":material/push_pin: Specific instructions"), value=prj.get("Instrucciones", ""))
            ind      = st.text_area(t(":material/description: Inductions (one link per line)"),
                                    value=prj.get("InduccionLinks", ""),
                                    help=t("They are sent by Telegram/email when a field user is assigned."))

            actuales = _actuales

            ags = P.list_groupings(grupo=grupo)
            ag_opts = ["(none)"] + [f"{a['ID']} · {a['Nombre']}" for a in ags]
            ag_cur  = str(prj.get("AgrupacionID", ""))
            ag_idx  = next((i for i, a in enumerate(ags) if a["ID"] == ag_cur), None)
            ag_sel  = st.selectbox(t("Group of lifts"), ag_opts,
                                   index=(ag_idx + 1) if ag_idx is not None else 0)
            # Peso por defecto 1: si queda en 0 el avance de la agrupación da 0
            # aunque los elevadores estén al 100% (Σpeso·avance / Σpeso).
            peso    = st.number_input(t("Weight in the group"), min_value=0.0, step=0.5,
                                      value=P._num(prj.get("PesoEnAgrupacion")) or 1.0,
                                      help=t("How much this lift weighs in its group's consolidated progress."))
            est_man = st.selectbox(t("Manual status (override)"), P.ESTADOS_MANUAL,
                                   format_func=_etq,
                                   index=P.ESTADOS_MANUAL.index(str(prj.get("EstadoManual", "")))
                                   if str(prj.get("EstadoManual", "")) in P.ESTADOS_MANUAL else 0)
            presup  = st.number_input(t(":material/payments: Project budget (0 = no budget)"),
                                      min_value=0.0, step=100.0, value=P._num(prj.get("Presupuesto")))
            _defm = auth.group_margin_default(grupo)
            _m0 = (P._num(prj.get("MargenMO")) if str(prj.get("MargenMO", "")).strip() != ""
                   else float(_defm))
            margen  = st.number_input(
                t(":material/trending_up: Margin on labour (%) — what you charge the client"),
                min_value=0.0, max_value=500.0, step=1.0, value=_m0,
                help=f"Labour sell price = cost × (1+margin). Company default: {_defm:.0f}% "
                     f"(the owner sets it in Companies).")

            if st.form_submit_button(t(":material/save: Save changes"), width="stretch"):
                # Validar sin `st.stop()`: pararia el render de TODO lo que va
                # debajo (actividades, archivar...) y la pagina quedaria a medias.
                _err = ""
                if not str(nombre).strip():
                    _err = "The project name cannot be left empty."
                elif f_ini and f_fin and f_fin < f_ini:
                    _err = "The end date cannot be earlier than the start date."
                f_ini, f_fin = _iso(f_ini), _iso(f_fin)
                if _err:
                    st.error(_err)
                else:
                    ag_id = "" if ag_sel == "(none)" else ag_sel.split(" · ")[0]
                    # Cliente elegido/escrito → texto + ClienteID (v256)
                    if _ecli_sel in _cli_names:
                        cliente = _ecli_sel
                        _ecli_id = next((str(c.get("ID", "")) for c in _cli_fichas
                                         if str(c.get("Nombre", "")) == _ecli_sel), "")
                    elif _ecli_sel == _CLI_OTRO:
                        cliente, _ecli_id = _ecli_new.strip(), ""
                    else:
                        cliente, _ecli_id = "", ""
                    P.update_project(pid, {   # todo en UNA escritura (batch) → sin rate limit
                        "Nombre": nombre, "Cliente": cliente, "ClienteID": _ecli_id,
                        "Tipo": ("" if tipo == _TIPO_VACIO else tipo),
                        "Ubicacion": ubic, "Modelo": modelo,
                        "Ingeniero": ing, "FechaInicio": f_ini, "FechaFinEst": f_fin,
                        "CampoAsignados": ";".join(asignados),
                        "AgrupacionID": ag_id, "PesoEnAgrupacion": peso,
                        # ⚠️ v422: el tipo que se está GUARDANDO, no el que tenía. Si en
                        # esta misma edición pasa a ser una localización interna, su
                        # estado tiene que salir «Abierta» en la misma escritura — con
                        # el tipo viejo quedaría «Planificado al 0%» para siempre.
                        "EstadoManual": est_man,
                        "Estado": P.derive_estado(avance, est_man,
                                                  "" if tipo == _TIPO_VACIO else tipo),
                        "Instrucciones": instr, "InduccionLinks": ind, "Presupuesto": presup,
                        "MargenMO": margen,
                        "Lat": "" if _plat is None else _plat,
                        "Lng": "" if _plng is None else _plng,
                        "CertsReq": ";".join(_ecerts),
                    })
                    # Notificar a los usuarios de campo recién asignados
                    nuevos = [x for x in asignados if x not in actuales]
                    _sent = 0
                    if nuevos:
                        _info = {"Nombre": nombre, "Cliente": cliente, "Ubicacion": ubic,
                                 "FechaInicio": f_ini, "FechaFinEst": f_fin, "InduccionLinks": ind}
                        for un in nuevos:
                            try:
                                rr = notify.notify_assignment(un, _info)
                                if rr.get("email") or rr.get("telegram"):
                                    _sent += 1
                            except Exception:
                                pass
                    # Si cambiaron las inducciones, reenviarlas a los ya asignados
                    if str(ind).strip() != str(prj.get("InduccionLinks", "")).strip():
                        _links = P.parse_links(ind)
                        if _links:
                            for un in [x for x in asignados if x not in nuevos]:
                                try:
                                    notify.notify_induction(un, nombre, _links)
                                except Exception:
                                    pass

                    # Aviso de cambio al campo ya asignado (los nuevos ya recibieron la asignación)
                    try:
                        alerts.notify_change(pid, grupo, "The project details were updated.",
                                             st.session_state.get("auth", {}).get("usuario", ""),
                                             [x for x in asignados if x not in nuevos], nombre)
                    except Exception:
                        pass
                    # v219: sincronizar el planificador — poner a los nuevos en el
                    # proyecto entre sus fechas y quitar del roster a los desasignados.
                    _quitados = [x for x in actuales if x not in asignados]
                    _autoagenda(grupo, pid, nuevos, _quitados, f_ini, f_fin)
                    st.toast(t("Changes saved.") + (f"  :material/send: {_sent} {t('notified')}." if _sent else ""))
                    st.rerun()

        # helper: avisar al campo asignado de un cambio del admin
        _asig_now = [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]
        def _aviso_cambio(txt):
            try:
                alerts.notify_change(pid, grupo, txt,
                                     st.session_state.get("auth", {}).get("usuario", ""),
                                     _asig_now, prj.get("Nombre", ""))
            except Exception:
                pass

        # ── Actividades: tabla EDITABLE (nombre/días/peso/orden); avance = campo ──
        st.markdown(t("**Schedule activities** — editable table · progress is set by the field team"))
        acts = P.list_activities(pid)
        if acts:
            _adf = pd.DataFrame([{
                "Orden": int(P._num(a.get("Orden"))),
                "Actividad": a.get("Nombre"),
                "Días": int(P._num(a.get("DuracionDias")) or 1),
                "Peso": P._num(a.get("Peso")),
                "Avance %": P._num(a.get("Avance")),
            } for a in acts])
            _edited = st.data_editor(
                _adf, width="stretch", hide_index=True, num_rows="fixed",
                key=f"acted_{pid}", disabled=["Avance %"],
                column_config=tabla.cfg(None, {
                    "Orden": st.column_config.NumberColumn(t("Order"), min_value=1, step=1,
                                                           help=t("Change the number to reorder")),
                    "Días":  st.column_config.NumberColumn(t("Days"), min_value=1, step=1),
                    "Peso":  st.column_config.NumberColumn(t("Weight"), min_value=0.0, step=1.0,
                                                           help=t("Relative weight (the % is worked out proportionally)")),
                }))
            st.caption(t("Edit name, days, weight and order; the progress % is read-only (the field team updates it)."))
            if st.button(t(":material/save: Save activity table"), key=f"savetbl_{pid}"):
                edits = []
                for i, a in enumerate(acts):
                    r = _edited.iloc[i]
                    edits.append({"orden0": a.get("Orden"),
                                  "Nombre": str(r["Actividad"]).strip(),
                                  "DuracionDias": int(r["Días"]),
                                  "Peso": float(r["Peso"]),
                                  "Orden": int(r["Orden"])})
                ok, msg = P.save_activities(pid, edits)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    _aviso_cambio("The schedule's activity table was updated.")
                    st.rerun()
        else:
            st.caption(t("No activities recorded."))

        with st.expander(t("Add / delete activity (the % is recalculated automatically)"),
                         icon=":material/playlist_add:"):
            with st.form(f"addact_{pid}", clear_on_submit=True):
                st.markdown(t("**:material/add: Add activity**"))
                an = st.text_input(t("Name"))
                ac1, ac2 = st.columns(2)
                ad = ac1.number_input(t("Duration (days)"), min_value=1, value=2, step=1)
                ap = ac2.number_input(t("Weight (relative to the others)"), min_value=0.0, value=10.0, step=1.0)
                if st.form_submit_button(t("Add")):
                    if not an.strip():
                        st.error(t("The name is required."))
                    else:
                        ok, msg = P.add_activity(pid, an.strip(), ad, ap)
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            _aviso_cambio(f"Activity added: {an.strip()}.")
                            st.rerun()
            if acts:
                st.markdown(t("**:material/delete: Delete activity**"))
                _dmap = {f"{int(P._num(a.get('Orden')))} · {a.get('Nombre')}": a.get("Orden")
                         for a in acts}
                _orden = ui.elegir(t("Activity to delete"), _dmap, key=f"delact_{pid}",
                                   vacio=t("— none —"))
                if _orden is not None:
                    _ok_del = ui.confirmar_borrado(f"delactok_{pid}",
                                                   t("I confirm I want to delete this activity"))
                    if st.button(t("Delete"), key=f"delactb_{pid}", disabled=not _ok_del):
                        ok, msg = P.delete_activity(pid, _orden)
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            _aviso_cambio("An activity was removed from the schedule.")
                            st.rerun()
        # ── Rastro de cambios (v342) ──
        _historial_section(pid)

        # ── Archivar / eliminar ──
        _archivado = str(prj.get("Estado", "")) == P.ARCHIVADO
        if _archivado:
            st.info(t(":material/inventory_2: This project is **archived**: it does not appear in lists or reports, but nothing has been lost."))
            if st.button(t(":material/recycling: Restore project"), key=f"unarch_{pid}",
                         width="stretch"):
                ok, msg = P.set_archivado(pid, False)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        else:
            with st.expander(t(":material/inventory_2: Archive project")):
                st.caption(t("It disappears from lists and reports, but is kept in full and can be restored whenever you want. This is what is recommended when a job closes."))
                if st.button(t(":material/inventory_2: Archive"), key=f"arch_{pid}", width="stretch"):
                    ok, msg = P.set_archivado(pid, True)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

        # Borrado de verdad: SOLO propietario. `delete_project` quita el proyecto
        # y sus actividades, pero deja huerfanos documentos (con sus archivos en
        # Drive), gastos, calculos, pre-starts, alarmas y fichajes — por eso se
        # enseña el inventario antes y se exige teclear el nombre.
        if st.session_state.get("auth", {}).get("rol") == "propietario":
            with st.expander(t(":material/delete_forever: Delete permanently (irreversible)")):
                _aso = P.datos_asociados(pid)
                _hay = {k: v for k, v in _aso.items() if v}
                st.warning(t("The project and its activities will be deleted. **This cannot be undone.** Almost always what you want is to archive it."))
                if _hay:
                    st.markdown("It will be left with no project: "
                                + " · ".join(f"**{v}** {k.lower()}"
                                             for k, v in _hay.items()))
                    st.caption(t("Those rows and their files in Drive are NOT deleted: they end up pointing at a project that no longer exists."))
                _tecleado = st.text_input(
                    f"Type «{prj.get('Nombre','')}» to confirm", key=f"delnom_{pid}")
                if st.button(t("Delete permanently"), key=f"del_{pid}",
                             width="stretch",
                             disabled=(_tecleado.strip() != str(prj.get("Nombre", "")).strip())):
                    ok, msg = P.delete_project(pid)
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    elif _sec == "💰 Costos":
        # ── Gastos / compras ──
        render_expenses(pid, grupo, can_delete=True, key_prefix="adm")

    elif _sec == "📎 Archivos":
        _plano_section(pid, prj)
        st.markdown("---")

        # ── Reconstruir el survey guardado ──
        with st.expander(t(":material/sync: Rebuild the project in the Survey (regenerate reports)")):
            st.caption(t("Loads the saved parameters and matrix into the :material/architecture: Survey tab. Then press **Calculate** there to regenerate diagrams and reports."))
            if st.button(t(":material/sync: Load this project into the Survey"), key=f"rebuild_{pid}"):
                full = P.get_project_full(pid)
                params, matriz = full.get("params") or {}, full.get("matriz") or []
                if not params:
                    st.error(t("This project has no saved parameters."))
                else:
                    for k, v in params.items():
                        try:
                            st.session_state[f"inp_{k}"] = float(v)
                        except Exception:
                            pass
                    if params.get("NS"):
                        try:
                            st.session_state["ns"] = int(float(params["NS"]))
                        except Exception:
                            pass
                    if matriz:
                        try:
                            st.session_state["survey_df"] = pd.DataFrame(matriz)
                        except Exception:
                            pass
                    st.session_state["proyecto"]  = str(prj.get("Nombre", ""))
                    st.session_state["ingeniero"] = str(prj.get("Ingeniero", ""))
                    st.session_state["_rebuilt_from"] = str(prj.get("Nombre", ""))
                    st.success(t(":material/check_circle: Loaded. Go to **:material/architecture: Survey** and press **Calculate** to regenerate everything."))
        # ── Archivos del proyecto (buscable) ──
        _archivos_section(pid)


# ── Panel de agrupaciones ────────────────────────────────────────
def _dashboard_agrupacion(ag, grupo):
    """Vista consolidada de una agrupación (un edificio con varios elevadores).

    ⚠️ El avance consolidado (promedio ponderado) NO responde la pregunta que
    importa: el edificio se entrega cuando termina **el último** elevador, no el
    promedio. De ahí la fecha de entrega del conjunto y el elevador crítico.
    """
    from core import expenses as E
    aid = ag["ID"]
    proys = P.list_projects(grupo=grupo, agrupacion_id=aid, incluir_archivados=True)
    if not proys:
        st.info(t("This group has no lifts yet. Add them below."))
        return

    pr      = P.grouping_progress(aid)
    delays  = P.delays_of_group(grupo)
    aheads  = P.aheads_of_group(grupo)
    horas   = P.project_hours_bulk(grupo)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    proj    = P.grouping_projection(aid, grupo)

    tot_h    = sum(horas.get(str(p.get("ID", "")), 0.0) for p in proys)
    costos   = [E.project_cost(p.get("ID"), grupo) for p in proys] if E.is_configured() else []
    tot_c    = sum(c["total"] for c in costos)
    tot_pres = sum(c["presupuesto"] for c in costos)
    n_alarm  = sum(alarmas.get(str(p.get("ID", "")), 0) for p in proys)
    n_retras = sum(1 for p in proys if str(p.get("ID", "")) in delays)

    # ── Tarjetas KPI (mismo lenguaje que la cartera de proyectos) ──
    _fecha = (proj["fecha"].strftime("%d/%m/%Y") if proj.get("fecha") else "—")
    _col_f = "#c0392b" if n_retras else "#1e8449"
    tarjetas = [
        _kpi_card(t("Consolidated progress"), f"{pr['avance']:.0f}%"),
        _kpi_card(t("Lifts"), pr["n_proyectos"]),
        _kpi_card(t("Delivery of the whole group"), _fecha, _col_f),
        _kpi_card(t("Behind schedule"), n_retras, "#c0392b" if n_retras else None),
        _kpi_card(t("Alerts"), n_alarm, "#c0392b" if n_alarm else None),
        _kpi_card(t("Hours"), f"{tot_h:.0f}"),
        _kpi_card(t("Total cost"), f"${tot_c:,.0f}"),
    ]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
                + "".join(tarjetas) + "</div>", unsafe_allow_html=True)
    st.progress(min(1.0, pr["avance"] / 100.0))

    # ── Quién manda la fecha de entrega ──
    if proj.get("critico"):
        _d = delays.get(proj["critico_id"])
        st.markdown(
            f":material/event: **Delivery is set by «{proj['critico']}»** — expected "
            f"**{_fecha}**" + (f", with **{_d:.0f} days behind**." if _d else
                               ", on time.")
            + "  That is where reinforcing pays off most.")
    if proj.get("sin_datos"):
        st.caption("No schedule to project from: " + ", ".join(proj["sin_datos"]))

    if tot_pres > 0:
        _p = round(100 * tot_c / tot_pres)
        (st.error if tot_c > tot_pres else st.caption)(
            f"Grouping budget ${tot_pres:,.0f} · {_p}% used"
            + (" :red[:material/block:] OVER BUDGET" if tot_c > tot_pres else ""))

    # ── Curva S CONSOLIDADA (plan vs real de todo el conjunto) ──
    try:
        cur = P.grouping_curve(aid, grupo)
    except Exception:
        cur = {}
    if cur and cur.get("fechas"):
        st.markdown(t("**:material/trending_up: Progress of the whole group — plan vs actual**"))
        _df = pd.DataFrame({t("Planned"): cur["plan"], t("Actual"): cur["real"]},
                           index=pd.to_datetime(cur["fechas"]))
        st.line_chart(_df, height=240)
        st.caption(t("Weighted by each lift's weight. The actual curve stops at TODAY."))

    # ── Comparativa entre elevadores ──
    # En un edificio son unidades casi gemelas, así que la desviación respecto
    # al promedio delata al que se sale de lo normal.
    st.markdown(t("**:material/analytics: Comparison between lifts**"))
    _hs = [horas.get(str(p.get("ID", "")), 0.0) for p in proys]
    _cs = [c.get("total", 0) for c in costos] if costos else [0] * len(proys)
    _hm = (sum(_hs) / len(_hs)) if _hs else 0
    _cm = (sum(_cs) / len(_cs)) if _cs else 0

    def _dev(v, med):
        if med <= 0:
            return ""
        d = round(100 * (v - med) / med)
        return f"{d:+d}%" if abs(d) >= 15 else "≈"

    rows = []
    for i, p in enumerate(proys):
        pid = str(p.get("ID", ""))
        _na = alarmas.get(pid, 0)
        _pf = next((x["fecha"] for x in proj.get("detalle", []) if x["id"] == pid), None)
        rows.append({
            "Elevador": p.get("Nombre"), "Estado": _etq(str(p.get("Estado", ""))),
            "Avance %": P._num(p.get("Avance")),
            "Peso": P._num(p.get("PesoEnAgrupacion")),
            "Entrega prev.": _pf.strftime("%d/%m") if _pf else "—",
            "Status": (f"{delays[pid]:.0f} d behind" if pid in delays
                     else (f"{aheads[pid]:.0f} d ahead" if pid in aheads else "on time")),
            "Horas": _hs[i], "vs media h": _dev(_hs[i], _hm),
            "Costo": _cs[i], "vs media $": _dev(_cs[i], _cm),
            "Alerts": _na or "",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config=tabla.cfg())
    st.caption(t("«vs avg» compares each lift with the group average; it is only flagged if it differs by 15% or more."))

    _out = [r["Elevador"] for r in rows if r["vs media h"].startswith("+")]
    if _out:
        st.info(t(":material/warning: They use noticeably more hours than their twins:") + " **"
                + ", ".join(_out) + "**. " + t("Worth looking into why."))

    st.bar_chart(pd.DataFrame({t("Progress %"): [r["Avance %"] for r in rows]},
                              index=[r["Elevador"] for r in rows]))


def _miembros_editor(ags_proys, todos, key, pesos_actuales=None):
    """Tabla para elegir QUÉ proyectos componen una agrupación y con qué peso.

    Devuelve {pid: peso} de los marcados. Peso por defecto **1** (todos cuentan
    igual): antes había que ponerlo a mano en cada proyecto y, si quedaba en 0,
    el avance de la agrupación daba 0 aunque los elevadores fueran al 100%.
    """
    pesos_actuales = pesos_actuales or {}
    filas = []
    for p in todos:
        pid = str(p.get("ID", ""))
        otra = str(p.get("AgrupacionID", ""))
        filas.append({
            "In the grouping": pid in pesos_actuales,
            "Proyecto": f"{p.get('Nombre')} ({pid})",
            "Peso": float(pesos_actuales.get(pid, 1.0)),
            "Avance %": P._num(p.get("Avance")),
            "Already in another": (ags_proys.get(otra, "") if otra and otra not in
                           (None, "") and pid not in pesos_actuales else ""),
        })
    if not filas:
        st.caption(t("There are no projects in this company yet."))
        return {}
    ed = st.data_editor(
        pd.DataFrame(filas), hide_index=True, width="stretch",
        num_rows="fixed", key=key,
        disabled=["Proyecto", "Avance %", "Already in another"],
        column_config=tabla.cfg(None, {
            "In the grouping": st.column_config.CheckboxColumn(width="small"),
            "Peso": st.column_config.NumberColumn(
                min_value=0.0, step=0.5,
                help=t("How much this lift weighs in the consolidated progress.")),
            "Already in another": st.column_config.TextColumn(
                t(":material/warning: Already in another"), help=t("Ticking it here MOVES it to this group.")),
        }))
    out = {}
    for _, r in ed.iterrows():
        if bool(r["In the grouping"]):
            pid = str(r["Proyecto"]).rsplit("(", 1)[-1].rstrip(")")
            out[pid] = float(r["Peso"] or 1.0)
    return out


def _cartera_agrupaciones(ags, grupo):
    """Agrupaciones como botones CLICKEABLES (v214): tocar abre su tablero. Fondo =
    avance consolidado; borde = salud (entrega del elevador más lento). Ordenadas por
    urgencia. Mismo lenguaje que la cartera de proyectos."""
    # ⚠️ CON archivados: el avance consolidado (`grouping_progress`) los cuenta,
    # así que el nº de elevadores, la fecha de entrega y las alarmas de la tarjeta
    # tienen que salir del MISMO conjunto o la tarjeta se contradice a sí misma.
    proys_all = P.list_projects(grupo=grupo, incluir_archivados=True)
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    try:
        proyecc = P.projections_by_group(grupo)
    except Exception:
        proyecc = {}
    rows = []
    for a in ags:
        aid = str(a.get("ID", ""))
        miemb = [p for p in proys_all if str(p.get("AgrupacionID", "")) == aid]
        av = P.grouping_progress(aid)["avance"]
        fecha, gap = None, 0.0
        for p in miemb:
            _d = proyecc.get(str(p.get("ID", "")))
            if _d and _d.get("fecha") and (fecha is None or _d["fecha"] > fecha):
                fecha, gap = _d["fecha"], _d.get("gap") or 0.0
        n_al = sum(alarmas.get(str(p.get("ID", "")), 0) for p in miemb)
        rows.append({"a": a, "aid": aid, "n": len(miemb), "av": av,
                     "gap": gap, "n_al": n_al, "fecha": fecha})
    rows.sort(key=lambda r: -r["gap"])

    _css = ["<style>"]
    for _i, r in enumerate(rows):
        _av = max(0, min(100, int(r["av"])))
        _col = "#c0392b" if r["gap"] > 0.5 else ("#1e8449" if r["gap"] < -0.5 else "#2e6da4")
        _tint = "#fdecec" if r["gap"] > 0.5 else ("#e8f5ee" if r["gap"] < -0.5 else "#e8eef6")
        _css.append(
            f".st-key-agrc_{_i} button{{background:linear-gradient(to right,"
            f"{_tint} {_av}%,#f4f6f9 {_av}%)!important;border-left:5px solid {_col}!important;"
            "justify-content:flex-start!important;padding-left:12px!important;}"
            f".st-key-agrc_{_i} button>div{{justify-content:flex-start!important;width:100%!important;}}"
            f".st-key-agrc_{_i} button p{{text-align:left!important;width:100%!important;}}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)

    for _r0 in range(0, len(rows), 2):
        _cols = st.columns(2)
        for _j in range(2):
            _idx = _r0 + _j
            if _idx >= len(rows):
                break
            r = rows[_idx]
            _av = max(0, min(100, int(r["av"])))
            _extra = ""
            if r["gap"] > 0.5:
                _extra += f" · :material/alarm: {r['gap']:.0f}d"
            elif r["gap"] < -0.5:
                _extra += f" · :material/trending_up: {abs(r['gap']):.0f}d"
            if r["n_al"]:
                _extra += f" · :material/notifications: {r['n_al']}"
            if r["fecha"]:
                _extra += f" · :material/event: {r['fecha'].strftime('%d/%m')}"
            _lbl = f"**:material/account_tree: {r['a'].get('Nombre', '')}** · {r['n']} elev · {_av}%{_extra}"
            if _cols[_j].button(_lbl, key=f"agrc_{_idx}", width="stretch"):
                st.session_state["_admin_open_agr"] = r["aid"]
                st.rerun()


def _panel_agrupaciones(grupo: str):
    ags = P.list_groupings(grupo=grupo)
    todos = P.list_projects(grupo=grupo)
    nom_ags = {a["ID"]: a["Nombre"] for a in ags}

    # ── Agrupación ABIERTA (de una tarjeta) → tablero + gestión, sin anidar ──
    _open = st.session_state.get("_admin_open_agr")
    if _open:
        _ag = next((a for a in ags if str(a.get("ID", "")) == str(_open)), None)
        if st.button(t("← Back to the groups"), key="agr_back"):
            st.session_state.pop("_admin_open_agr", None)
            st.rerun()
        if not _ag:
            st.warning(t("Group not found."))
            st.session_state.pop("_admin_open_agr", None)
            return
        _dashboard_agrupacion(_ag, grupo)      # sin expanders internos → seguro
        st.markdown("---")
        with st.expander(t(":material/build: Projects in this group")):
            st.caption(t("Tick the lifts that belong to it. Unticking one **ungroups** it, it is not deleted."))
            _act = {str(p.get("ID")): P._num(p.get("PesoEnAgrupacion")) or 1.0
                    for p in P.list_projects(grupo=grupo, agrupacion_id=_ag["ID"], incluir_archivados=True)}
            # ⚠️ Un miembro ARCHIVADO no está en `todos` (la lista oculta archivados
            # desde v149), así que no tendría casilla y `set_grouping_members` lo
            # leería como una BAJA → se desagruparía solo al guardar. Se añade a la
            # lista para que siga marcable.
            _falta = [p for p in P.list_projects(grupo=grupo, incluir_archivados=True)
                      if str(p.get("ID")) in _act
                      and str(p.get("ID")) not in {str(q.get("ID")) for q in todos}]
            _sel = _miembros_editor(nom_ags, todos + _falta, f"agmem_{_ag['ID']}", _act)
            if len(_sel) > 12:
                st.warning(f"{len(_sel)} projects: each change is a write "
                           "to the sheet; it may take a few seconds.")
            if st.button(t(":material/save: Save the group's projects"),
                         key=f"agmemsave_{_ag['ID']}", width="stretch"):
                with st.spinner(t("Saving…")):
                    ok, msg = P.set_grouping_members(_ag["ID"], _sel, grupo)
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.rerun()
        with st.expander(t(":material/delete: Delete group")):
            st.caption(t("The projects are not deleted; they are only ungrouped."))
            _ok_del = ui.confirmar_borrado("del_agr_ok", t("I confirm I want to delete this group"))
            if st.button(t("Delete group"), disabled=not _ok_del, key="del_agr_btn"):
                ok, msg = P.delete_grouping(_ag["ID"])
                (flash.exito if ok else st.error)(msg)
                if ok:
                    st.session_state.pop("_admin_open_agr", None)
                    st.rerun()
        return

    # ── Lista de agrupaciones CLICKEABLES ──
    if ags:
        st.markdown(f"**Groups of lifts — {len(ags)}**")
        st.caption(t("Tap a group to open its dashboard."))
        _cartera_agrupaciones(ags, grupo)
    else:
        st.info(t("No groups yet. Create one below and choose which lifts belong to it."))

    # ── Crear: la agrupación se arma CON sus proyectos (v141), plegada ──
    with st.expander(t("New group of lifts"), icon=":material/create_new_folder:"):
        st.caption(t("Projects are created first; here you choose which ones belong."))
        nom = st.text_input(t("Group name"), key="nueva_agr_nom")
        des = st.text_input(t("Description (optional)"), key="nueva_agr_des")
        _nuevos = _miembros_editor(nom_ags, todos, "agmem_nueva")
        if st.button(t("Create group"), key="nueva_agr_btn", width="stretch"):
            if not nom.strip():
                st.error(t("The name is required."))
            else:
                ok, res = P.create_grouping(grupo, nom.strip(), des.strip())
                if not ok:
                    st.error(res)
                else:
                    _n = 0
                    if _nuevos:
                        with st.spinner("Assigning projects..."):
                            ok2, msg2 = P.set_grouping_members(res, _nuevos, grupo)
                        _n = len(_nuevos)
                        if not ok2:
                            st.warning(f"Group created, but: {msg2}")
                    flash.exito(f"{t('Grouping created')} ({res})"
                               + (f" with {_n} lift(s)." if _n else
                                  ". Add lifts to it from its panel."))
                    st.rerun()


# ── Panel del PROPIETARIO: todos los proyectos (todos los grupos) ──
def render_owner_projects():
    st.markdown(t("### :material/folder: All projects"))
    if not P.is_configured():
        st.warning(t("Project management needs Google Sheets configured."))
        return
    _ver_arch = st.checkbox(t(":material/archive: Show archived ones too"), key="ver_arch_owner")
    proys = P.list_projects(incluir_archivados=_ver_arch)   # todos los grupos
    _grupos = []
    try:
        _grupos = [g["Grupo"] for g in auth.list_groups(only_active=True)]
    except Exception:
        pass
    if _grupos:
        _g = st.selectbox(t("Company for the new project"), _grupos, key="own_np_grupo")
        _nuevo_proyecto_form(_g, key="own")
    if not proys:
        if not _grupos:
            st.info(t("No companies yet. Create one in **:material/business: Companies** so projects can be recorded."))
        return
    ags = {a["ID"]: a["Nombre"] for a in P.list_groupings()}
    alarmas = alerts.open_counts_all() if alerts.is_configured() else {}
    delays = _delays(proys)
    aheads = _aheads(proys)
    rows = []
    for p in proys:
        est = str(p.get("Estado", ""))
        pid = str(p.get("ID", ""))
        _na = alarmas.get(pid, 0)
        _d  = delays.get(pid)
        _ad = aheads.get(pid)
        ubic = str(p.get("Ubicacion", "") or "")
        rows.append({
            "ID":        p.get("ID"),
            "Grupo":     p.get("Grupo"),
            "Proyecto":  p.get("Nombre"),
            "Alerts":     f"{_na}" if _na else "",
            "Cliente":   p.get("Cliente"),
            "Location": ubic,
            "Mapa":        maps.maps_url(ubic),
            "Estado":    _etq(est),
            "Behind": f"{_d:.0f} d" if _d else "",
            "Ahead": f"{_ad:.0f} d" if _ad else "",
            "Avance %":  P._num(p.get("Avance")),
            "Horas":     P.project_hours(p.get("Nombre"), p.get("Grupo"),
                                        pid=str(p.get("ID", ""))),
            "Grouping": ags.get(str(p.get("AgrupacionID", "")), ""),
        })
    # Cartera de tarjetas (mismo look del admin) + tabla detallada abajo
    _hb = {}
    for p in proys:
        _hb[str(p.get("ID", ""))] = P.project_hours(p.get("Nombre"), p.get("Grupo"),
                                                    pid=str(p.get("ID", "")))
    st.markdown(f"**{t('Portfolio')} — {len(proys)} project(s)**"
                + (f"  ·  :red[:material/cancel:] {len(delays)} behind schedule" if delays else "")
                + (f"  ·  :green[:material/check_circle:] {len(aheads)} ahead" if aheads else ""))
    st.markdown(_portfolio_html(proys, _hb, alarmas, ags, delays, aheads, show_group=True),
                unsafe_allow_html=True)

    with st.expander(t(":material/assignment: See detailed table")):
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True,
                     column_config=tabla.cfg(None, {"Mapa": st.column_config.LinkColumn(t("Map"), display_text="Abrir")}))

    st.markdown(t("#### :material/search: Open project"))
    idmap = {f"{p.get('Grupo')} · {p.get('ID')} · {p.get('Nombre')}": p.get("ID") for p in proys}
    _opts = [_VACIO] + list(idmap.keys())
    sel = st.selectbox(t("Project"), _opts, key="ownerproj_sel")
    if sel and sel != _VACIO:
        _detalle_proyecto(idmap[sel])


# ── Pestaña del usuario de CAMPO: mis proyectos ──────────────────
def _field_activities(pid):
    """Tabla editable del avance del campo (v162): una tabla, un guardado.

    Antes eran N expandibles con un guardado cada uno (hasta 5 update_cell por
    actividad). Ahora `save_field_progress` escribe solo lo que cambio en 1 batch,
    y las fechas reales se registran solas (no se teclean).
    """
    st.markdown(t("#### Activities — update your progress"))
    acts = P.list_activities(pid)
    if not acts:
        st.caption(t("This project has no activities recorded."))
        return
    _df = pd.DataFrame([{
        "N": int(P._num(a.get("Orden"))),
        "Actividad": a.get("Nombre"),
        "Avance %": int(P._num(a.get("Avance"))),
        "Inicio real": str(a.get("FechaInicioReal", "")) or "—",
        "Fin real": str(a.get("FechaFinReal", "")) or "—",
        "Nota": str(a.get("Nota", "")),
    } for a in acts])
    _ed = st.data_editor(
        _df, hide_index=True, width="stretch", num_rows="fixed",
        key=f"fldacts_{pid}",
        disabled=["N", "Actividad", "Inicio real", "Fin real"],
        column_config=tabla.cfg(None, {
            "Avance %": st.column_config.NumberColumn(min_value=0, max_value=100, step=5,
                                                      help=t("Your progress on this activity")),
            "Nota": st.column_config.TextColumn(help=t("Optional")),
        }))
    st.caption(t("The dates record themselves: **start** when it goes above 0, **end** when it reaches 100."))
    if st.button(t(":material/save: Save progress"), key=f"fldsave_{pid}", width="stretch"):
        cambios, _vacias = [], []
        for i, a in enumerate(acts):
            r = _ed.iloc[i]
            _av, _nt = r["Avance %"], r["Nota"]
            # ⚠️ Una celda BORRADA vuelve como NaN: `int(NaN)` reventaba el guardado
            #    ENTERO (se perdía toda la edición, no solo esa fila) y `str(NaN)`
            #    guardaba el texto "nan" como nota del campo.
            if pd.isna(_av):
                _vacias.append(str(a.get("Nombre", "")))
                continue                    # vaciar no es poner 0: se deja como estaba
            nav = int(P._num(_av))
            nnota = "" if pd.isna(_nt) else str(_nt)
            if nav != int(P._num(a.get("Avance"))) or nnota != str(a.get("Nota", "")):
                cambios.append({"orden": a.get("Orden"), "avance": nav, "nota": nnota})
        _msg_vac = ("You left the progress blank on: **" + "**, **".join(_vacias)
                    + "**. Those are left as they were — type a number (0-100) if you meant to change them.") if _vacias else ""
        if not cambios:
            # Sin rerun: se pinta aquí mismo (encolarlo lo dejaría de fantasma)
            if _msg_vac:
                st.warning(_msg_vac)
            else:
                st.info(t("You did not change any progress."))
        else:
            # ⚠️ El rerun de abajo descarta los deltas de esta pasada (v365), así
            #    que este aviso tiene que ir por la cola para llegar a la pantalla.
            if _msg_vac:
                flash.aviso(_msg_vac)
            ok, msg = P.save_field_progress(pid, cambios)
            (flash.exito if ok else st.error)(msg)
            if ok:
                st.rerun()


def render_field_projects(usuario: str, grupo: str):
    st.markdown(t("### :material/assignment: My projects"))
    if not P.is_configured():
        st.warning(t("Project management needs Google Sheets configured."))
        return

    # ── Planificación de la semana (el campo ve toda la cuadrilla) ──
    try:
        from core import roster, roster_ui
        if roster.is_configured():
            _aa = roster.asignaciones_dia(grupo, usuario)   # v274/v277: varias, con franja
            if _aa:
                _parts = []
                for a in _aa:
                    if not a.get("etiqueta"):
                        continue
                    _fl = roster.franja_label(a.get("ini", ""), a.get("fin", ""))
                    _parts.append(a["etiqueta"] + (f" {_fl}" if _fl else ""))
                _ets = " · ".join(_parts)
                _nt = next((a["nota"] for a in _aa if str(a.get("nota", "")).strip()), "")
                _n = f" · {_nt}" if _nt else ""
                _est = all(a.get("es_estado") for a in _aa)
                (st.info if _est else st.success)(
                    f"{t(':material/calendar_month: **Today:**')} {_ets}{_n}")
            with st.expander(t(":material/calendar_month: See the week's plan (the whole crew)")):
                roster_ui.render_board_readonly(grupo, resaltar_usuario=usuario)
    except Exception:
        pass

    # ── Mi ruta del día (v270): mis obras en el mapa, ordenadas para ir a terreno ──
    with st.expander(t(":material/route: My route (my sites on the map)")):
        try:
            from core import route_ui
            route_ui.render_mi_ruta(usuario, grupo)
        except Exception:
            st.caption(t("The route could not be loaded right now."))

    # v423: **con las internas**. Quien trabaja en la oficina o el almacén tiene su sitio
    # asignado ahí (v422) y necesita lo mismo que en una obra: ver sus avisos, cargar
    # recibos y llegar a los archivos. Lo que NO tiene sentido para ella —la tabla de
    # avance— se le quita abajo, en vez de dejarla fuera de la vista entera.
    proys = P.list_projects_for_field(usuario, grupo=grupo, incluir_internos=True)
    if not proys:
        st.info(t("You have no projects assigned yet. The administrator assigns you to a project."))
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')}) — {p.get('Estado')}": p.get("ID")
             for p in proys}
    # Si el usuario tiene fichaje abierto, se abre ESE proyecto: es donde está
    # trabajando ahora (mismo criterio que usan las herramientas desde v137).
    _opts = [_VACIO] + list(idmap.keys())
    if "fieldproj_sel" not in st.session_state:
        _fich = ""
        try:
            _au = st.session_state.get("auth", {}) or {}
            _ses = timeclock.open_sessions(_au.get("nombre", ""), grupo, usuario)
            _fich = str((_ses.get(timeclock.TIPO_PROYECTO)
                         or _ses.get(timeclock.TIPO_GENERAL)
                         or {}).get("proyecto", "")).strip()
        except Exception:
            pass
        if _fich:
            _m = next((k for k in idmap if k.startswith(_fich + " (")), None)
            if _m:
                st.session_state["fieldproj_sel"] = _m
    sel = st.selectbox(t("Assigned project"), _opts, key="fieldproj_sel")
    if not sel or sel == _VACIO:
        st.caption(t("Choose the project you are working on. If you clock in at :material/schedule: Time clock, it opens on its own."))
        return
    pid = idmap[sel]
    prj = P.get_project(pid)
    if not prj:
        st.error(t("Project not found."))
        return

    # ── Cabecera: tarjetas KPI (mismo lenguaje que el resto) ──
    avance = P._num(prj.get("Avance"))
    est    = str(prj.get("Estado", ""))
    _ub = str(prj.get("Ubicacion", "") or "")
    # v423: una localización interna no tiene avance ni cliente — enseñar «0%» y «—»
    # no informa de nada; en su sitio va lo que sí la identifica.
    if P.es_interno(prj):
        tarj = [_kpi_card(t("Status"), _etq(est)),
                _kpi_card(t("Type"), _etq(str(prj.get("Tipo", ""))) or t("Internal")),
                _kpi_card(t("Person in charge"), prj.get("Ingeniero") or "—")]
    else:
        tarj = [_kpi_card(t("Status"), est),
                _kpi_card(t("Project progress"), f"{avance:.0f}%"),
                _kpi_card(t("Client"), prj.get("Cliente") or "—")]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    if not P.es_interno(prj):
        st.progress(min(1.0, avance / 100.0))
    if _ub:
        st.caption(":material/place: " + maps.maps_link_md(_ub, _ub))

    # ── Sub-navegación (radio, NO st.tabs — regla v56; como el detalle del admin) ──
    # ⚠️ v423: una localización interna NO tiene actividades, así que «Avance» sería una
    # tabla vacía y un 0% permanente. Se le quita esa pestaña y se queda con lo que sí
    # usa quien trabaja en la oficina o el almacén: avisos, recibos y archivos.
    _opts = ["🏗 Avance", "🚨 Avisos", "💰 Recibos", "📎 Archivos"]
    if P.es_interno(prj):
        _opts = _opts[1:]
    _sec = st.radio(t("Section"), _opts,
                    format_func=lambda o: {"🏗 Avance": t(":material/trending_up: Progress"),
                                           "🚨 Avisos": t(":material/report: Alerts"),
                                           "💰 Recibos": t(":material/receipt: Receipts"),
                                           "📎 Archivos": t(":material/folder: Files")}.get(o, o),
                    # v316: mismo segmentado que el detalle del admin. El campo ve la
                    # misma pieza que el admin: la coherencia entre pantallas es lo que
                    # hace que parezca un producto y no cuatro cosas pegadas.
                    horizontal=True, key="cpxseg_fld_sec", label_visibility="collapsed")
    if _sec == "🏗 Avance":
        _induccion_section(pid, prj, grupo, allow_send=False)
        _field_activities(pid)
    elif _sec == "🚨 Avisos":
        _alerts_section(pid, grupo, prj.get("Nombre", ""), allow_report=True)
    elif _sec == "💰 Recibos":
        render_expenses(pid, grupo, can_delete=False, key_prefix="fld")
    else:   # :material/attach_file: Archivos
        _archivos_section(pid)


# ── Gastos / compras por proyecto (admin, campo) ──
def _barras_html(pares, total, color=None) -> str:
    """Barras horizontales ordenadas: etiqueta · barra · valor · %.

    Para desgloses cortos (categorias de gasto, personas). Un `st.bar_chart` aqui
    obliga a leer un eje para nada; la barra con su numero al lado se lee sola.
    v283: los colores salen del SISTEMA DE DISEÑO (`core/theme.py`), no hardcodeados.
    """
    from core import theme
    if not pares or total <= 0:
        return ""
    color = color or theme.AZUL
    out = []
    for et, val in pares:
        pct = 100.0 * float(val) / total
        out.append(
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">'
            f'<div style="width:118px;flex:none;font-size:12px;color:{theme.TXT};'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{et}</div>'
            f'<div style="flex:1;height:9px;background:{theme.PISTA};border-radius:20px;'
            'overflow:hidden;">'
            f'<div style="height:9px;width:{max(1.5, pct):.1f}%;background:{color};'
            f'border-radius:20px;"></div></div>'
            f'<div style="width:96px;flex:none;text-align:right;font-size:12px;'
            f'color:{theme.TXT};font-weight:600;">${float(val):,.0f}</div>'
            f'<div style="width:42px;flex:none;text-align:right;font-size:11px;'
            f'color:{theme.GRIS_SUAVE};">{pct:.0f}%</div></div>')
    return "".join(out)


def _torta_html(pares, total) -> str:
    """Diagrama de torta (pie) con CSS `conic-gradient` + leyenda (color · rubro · $ · %).
    Sin dependencias de charting (nada de plotly/matplotlib): mismo enfoque HTML que
    `_barras_html`, se renderiza en `st.markdown`. Para el gasto por rubro del grupo
    (mano de obra + cada categoría de compra). v224."""
    from core import theme
    pares = [(k, float(v)) for k, v in pares if v and float(v) > 0]
    if not pares or total <= 0:
        return ""
    _pal = theme.PALETA          # v283: paleta única del sistema de diseño
    _stops, _leg, _acc = [], [], 0.0
    for _i, (et, val) in enumerate(pares):
        _pct = 100.0 * val / total
        _col = _pal[_i % len(_pal)]
        _stops.append(f"{_col} {_acc:.2f}% {_acc + _pct:.2f}%")
        _acc += _pct
        _leg.append(
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
            f'<span style="width:12px;height:12px;border-radius:3px;background:{_col};'
            'flex:none;"></span>'
            f'<span style="flex:1;font-size:12px;color:{theme.TXT};overflow:hidden;'
            f'text-overflow:ellipsis;white-space:nowrap;">{et}</span>'
            f'<span style="font-size:12px;font-weight:600;color:{theme.TXT};">${val:,.0f}</span>'
            f'<span style="width:40px;flex:none;text-align:right;font-size:11px;'
            f'color:{theme.GRIS_SUAVE};">{_pct:.0f}%</span></div>')
    _grad = "conic-gradient(" + ", ".join(_stops) + ")"
    # v225: centrado — se agrupan torta + leyenda y la leyenda se ACOTA (antes flex:1
    # la estiraba a todo el ancho y el monto/% se iban al borde → "todo separado").
    return (
        '<div style="display:flex;align-items:center;justify-content:center;gap:32px;'
        'flex-wrap:wrap;margin-top:4px;">'
        f'<div style="width:150px;height:150px;border-radius:50%;background:{_grad};'
        'flex:none;"></div>'
        f'<div style="width:300px;max-width:100%;">{"".join(_leg)}</div></div>')


_ORD_ICONO = {"pendiente": ":material/schedule:", "recibida": ":material/check_circle:",
              "cancelada": ":material/cancel:"}


def _ordenes_section(pid, grupo, editable=True, key_prefix="ord"):
    """Órdenes de compra del proyecto (v343): lo pedido y aún no recibido.

    Al recibir una orden se crea su recibo en `Gastos`, así que el costo real sigue
    saliendo de una sola fuente (regla v310) y esta lista solo contiene lo pendiente.
    """
    from core import clock, theme
    from core import expenses as E
    from core import orders as O
    from core.num import num as _n
    if not O.is_configured():
        return
    try:
        ords = O.list_for(pid)
    except Exception:
        return
    _pend = [o for o in ords if str(o.get("Estado", "")) == O.PENDIENTE]
    _tit = f"Purchase orders ({len(_pend)} pending)"

    with st.expander(f":material/shopping_cart: {_tit}", expanded=False):
        st.caption(t("What has already been ordered from the supplier and has not arrived yet. When it is marked **received** it is charged to the project cost on its own."))

        if ords:
            _hoy = clock.today(grupo)
            for o in ords:
                _est = str(o.get("Estado", ""))
                _oid = str(o.get("ID", ""))
                _fesp = O._parse_date(o.get("FechaEsperada"))
                _tarde = bool(_est == O.PENDIENTE and _fesp and _fesp < _hoy)
                _lin = (f"{_ORD_ICONO.get(_est,'')} **{o.get('Proveedor','')}** · "
                        f"{theme.dinero(_n(o.get('Valor')))} · "
                        f"{o.get('Descripcion','') or '—'}")
                if _fesp:
                    _lin += f" · llega {_fesp.strftime('%d/%m')}"
                if _tarde:
                    _lin += f"  :red[**{(_hoy - _fesp).days} d late**]"
                st.markdown(_lin)
                st.caption(f"{_oid} · {_etq(_est)} · ordered {o.get('Fecha','')}")

                if _est == O.RECIBIDA and not str(o.get("GastoID", "")).strip():
                    # ⚠️ Se marcó recibida pero su gasto no llegó a escribirse: ese
                    # costo NO está contado en ningún sitio hasta completarlo.
                    st.warning(t(":material/warning: This order is received but **its cost was not recorded**, so it is not being counted."))
                    if editable and st.button(t("Record the cost now"),
                                              key=f"{key_prefix}_ordfix_{_oid}"):
                        ok, msg = O.completar_gasto(
                            _oid, st.session_state.get("auth", {}).get("usuario", ""))
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()

                if editable and _est == O.PENDIENTE:
                    _a, _b, _c2 = st.columns([2, 1, 1])
                    _real = _a.number_input(
                        t("Value received"), min_value=0.0, step=10.0,
                        value=float(_n(o.get("Valor"))), key=f"{key_prefix}_ordv_{_oid}",
                        help=t("If it arrived at a different amount, correct it here before receiving."))
                    if _b.button(t("Receive"), key=f"{key_prefix}_ordr_{_oid}",
                                 width="stretch"):
                        ok, msg = O.marcar_recibida(
                            _oid, _real, st.session_state.get("auth", {}).get("usuario", ""))
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()
                    if _c2.button(t("Cancel"), key=f"{key_prefix}_ordc_{_oid}",
                                  width="stretch"):
                        ok, msg = O.cancelar(_oid)
                        (flash.exito if ok else st.error)(msg)
                        if ok:
                            st.rerun()
                st.markdown("---")
        else:
            st.caption(t("No orders recorded on this project yet."))

        if editable:
            with st.form(f"{key_prefix}_ordnew_{pid}"):
                st.markdown(t("**New order**"))
                _c1, _c2 = st.columns(2)
                _prov = _c1.text_input(t("Supplier"))
                _val  = _c2.number_input(t("Value"), min_value=0.0, step=10.0)
                _c3, _c4 = st.columns(2)
                _desc = _c3.text_input(t("Description"), placeholder=t("e.g. T75-3/B rails ×12"))
                _cat  = _c4.selectbox(t("Category"), E.CATEGORIAS)
                _fe   = st.date_input(t("Expected delivery date"), value=None,
                                      help=t("Optional. Without it the order is never flagged as late — you cannot say it is late if nobody said when it was due."))
                if st.form_submit_button(t(":material/add_circle: Record order"),
                                         width="stretch"):
                    ok, msg = O.crear(
                        pid, grupo, _prov, _val, descripcion=_desc, categoria=_cat,
                        fecha_esperada=_fe.strftime("%Y-%m-%d") if _fe else "",
                        creado_por=st.session_state.get("auth", {}).get("usuario", ""))
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()


def _ganancia_section(pid, grupo):
    """Ganancia por trabajador y hora en ESTA obra (v360).

    La ganancia dejó de ser un % del proyecto: es un importe por rubro, y el trabajador
    es un rubro. Aquí se pone cuánto quieres ganar por cada hora de cada persona; el
    precio/hora al cliente y el % salen solos.
    """
    from core import expenses as E
    from core import finance as F
    from core import theme as _T
    try:
        rev = F.project_revenue(pid, grupo)
        lb = E.labor_breakdown(pid, grupo)
    except Exception:
        return
    _gh    = P.ganancia_hora(pid)
    _fija  = P.ganancia_fija(pid)
    _items = lb.get("items") or []
    _modelo = str(rev.get("modelo", ""))
    # ⚠️ Hasta v373 aquí se volvía si nadie había fichado — y esa es JUSTO la obra que
    #    necesita la ganancia fija: un delivery no tiene horas, así que la pantalla
    #    donde ponerla no se dibujaba nunca y no había forma de darle valor.
    _a_costo = P._num(rev.get("ganancia")) <= 0

    with st.expander(t(":material/savings: How much you make on this job"),
                     expanded=bool(rev.get("sin_ganancia")) or _a_costo):
        if _modelo == "cotizado":
            st.success(":material/check_circle: This job's revenue is the **agreed price** on quote " + f"**{rev.get('cotizacion','')}**. "
                       "The " + f"{rev['margen_pct']:g}%" + " follows from that price.")
            if P._num(rev.get("fija_ignorada")) > 0:
                st.warning(":material/info: This job has a fixed profit of "
                           + _T.dinero(rev["fija_ignorada"]) + " that is **not used**: the price the client signed wins. Set it to 0 to remove the noise.")
        elif _modelo.startswith("margen"):
            st.info(":material/info: This job's labour still uses the **old model**: a " + f"**{rev['margen_pct']:g}%** on top of it. As soon as you "
                    "set what you want to earn per hour here, it moves to the new model "
                    "(an amount per line) and the % works itself out.")
        else:
            st.success(":material/check_circle: This job already uses the per-line model. The " + f"{rev['margen_pct']:g}%" + " margin follows from it; it is not something you typed.")
        if rev.get("sin_ganancia"):
            st.warning(":material/person_alert: With no profit set, their work would be invoiced **at cost**: **" + ", ".join(rev["sin_ganancia"])
                       + "**.")

        # ⚠️ El editor solo si hay gente: con la lista vacía, `disabled=[...]` y
        #    `column_config` apuntarían a columnas que no existen.
        if not _items:
            st.caption(t("Nobody has clocked hours on this job yet, so there is no hourly profit to set. If its value is not in the time (a delivery, a supply job), use the **fixed profit** below."))
        else:
            _editor_ganancia_hora(pid, _items, _gh, _T)
        _ganancia_fija_ui(pid, rev, _fija, _T, _modelo)


def _editor_ganancia_hora(pid, _items, _gh, _T):
    """La tabla persona × ganancia/h (v360). Extraída de `_ganancia_section` en v373
    para poder no dibujarla cuando la obra no tiene horas fichadas."""
    _ed = st.data_editor(
            pd.DataFrame([{
                "Persona": x.get("usuario", ""),
                "Horas": round(P._num(x.get("horas")), 2),
                "Costo/h": round(P._num(x.get("tarifa")), 2),
                "Ganancia/h": round(P._num(_gh.get(str(x.get("usuario", "")), 0)), 2),
                "Precio/h": round(P._num(x.get("tarifa"))
                                  + P._num(_gh.get(str(x.get("usuario", "")), 0)), 2),
                "Ganas": round(P._num(x.get("horas"))
                               * P._num(_gh.get(str(x.get("usuario", "")), 0)), 2),
            } for x in _items]),
            hide_index=True, width="stretch", key=f"gh_ed_{pid}",
            # ⚠️ Solo se teclea la GANANCIA. Precio/h y «Ganas» son consecuencia y van
            # bloqueados, igual que en la cotización (v355).
            disabled=["Persona", "Horas", "Costo/h", "Precio/h", "Ganas"],
            column_config=tabla.cfg(None, {
                "Costo/h": st.column_config.NumberColumn(t("Cost/h"), format="$%,.2f",
                                                         help=t("Their rate. What it costs you.")),
                "Ganancia/h": st.column_config.NumberColumn(
                    t("Profit/h"), format="$%,.2f", min_value=0.0,
                    help=t("What you want to make on each of their hours on this job.")),
                "Precio/h": st.column_config.NumberColumn(t("Price/h"), format="$%,.2f",
                                                          help=t("Cost + profit. What the client is charged.")),
                "Ganas": st.column_config.NumberColumn(t("You make"), format="$%,.2f",
                                                       help=t("Hours × profit/h."))}))

    _nuevo = {str(_ed.iloc[i]["Persona"]): P._num(_ed.iloc[i]["Ganancia/h"])
              for i in range(len(_ed)) if P._num(_ed.iloc[i]["Ganancia/h"]) > 0}
    _tot = sum(P._num(_ed.iloc[i]["Horas"]) * P._num(_ed.iloc[i]["Ganancia/h"])
               for i in range(len(_ed)))
    st.caption("With these values you would make **" + _T.dinero(_tot)
               + "** on the labour clocked so far. Materials are invoiced at cost (decision from v360).")
    _c1, _c2 = st.columns([2, 1])
    if _c1.button(t(":material/save: Save profits"), key=f"gh_save_{pid}",
                  type="primary", width="stretch"):
        ok, msg = P.set_ganancia_hora(pid, _nuevo)
        (flash.exito if ok else st.error)(msg)
        if ok:
            st.rerun()
    # ⚠️ La vuelta atrás: si migraste una obra por error, se puede deshacer (v346).
    if _gh and _c2.button(t(":material/undo: Back to the %"), key=f"gh_undo_{pid}",
                          width="stretch",
                          help=t("Removes the hourly profits and goes back to the margin %.")):
        ok, msg = P.set_ganancia_hora(pid, {})
        (flash.exito if ok else st.error)(msg)
        if ok:
            st.rerun()


def _ganancia_fija_ui(pid, rev, _fija, _T, _modelo):
    """Ganancia FIJA de la obra, en dinero (v373).

    Cubre el hueco que v370 dejó abierto: una obra creada A MANO cuyo valor no está
    en las horas (un delivery, un suministro) valía exactamente lo que costó, porque
    el margen solo se aplica a la mano de obra y los materiales van a costo. Medido:
    «Bespoke — Delivery Chullora» estimado en $380 habiendo facturado $5.200.
    """
    st.markdown("---")
    st.markdown(t("**Fixed profit for the job**"))
    st.caption(t("What this job is worth in itself, **on top of** what you make on the hours. For deliveries, supply or any work whose value is not in the time. Leave it at 0 if it does not apply."))
    _c1, _c2 = st.columns([2, 1])
    _nf = _c1.number_input(t("Fixed profit ($)"), min_value=0.0, step=100.0,
                           value=float(_fija), key=f"gf_{pid}",
                           help=t("It is added to the job's estimated revenue. A job that came from an accepted quote does NOT use it: there the price the client signed wins."))
    _costo = P._num(rev.get("costo"))
    if _modelo == "cotizado":
        _c1.caption(t(":orange[This job has an agreed price, so this amount is not used.]"))
    else:
        # Lo que pasaría a valer la obra con este número, para no teclear a ciegas.
        # Se parte del ingreso SIN la fija actual, así el cálculo no la cuenta dos veces.
        _ing = round(P._num(rev.get("ingreso")) - P._num(rev.get("ganancia_fija")) + _nf, 2)
        _c1.caption("With this amount, the job's estimated revenue would be **"
                    + _T.dinero(_ing) + "** on a cost of " + _T.dinero(_costo) + ".")
    if _c2.button(t(":material/save: Save fixed profit"), key=f"gf_save_{pid}",
                  width="stretch"):
        ok, msg = P.set_ganancia_fija(pid, _nf)
        (flash.exito if ok else st.error)(msg)
        if ok:
            st.rerun()


def _ir_a_facturar(pid, grupo):
    """Abre el alta de factura con este cliente y este proyecto ya elegidos (v357).

    ⚠️ UNA sola definición: la usan el botón de la ficha y el de la tarjeta de la
    cartera (v397). Duplicar esta preparación es cómo divergen dos caminos que
    deberían hacer lo mismo (v323); y aquí lo que se duplicaría es justo la parte
    delicada — la resolución del cliente.
    """
    prj = P.get_project(pid) or {}
    st.session_state["_fac_nueva"] = True
    # ⚠️ El selectbox de cliente se indexa por NOMBRE, y `Proyectos.Cliente` es TEXTO
    # LIBRE: en producción hay obras con «vd» y «ci», que no son fichas de cliente.
    # Preseleccionar un valor que no está entre las opciones **revienta el widget**.
    # Se resuelve por ClienteID (la relación de verdad, v306) y solo se preselecciona
    # si el nombre existe de veras entre las opciones.
    try:
        from core import clientes as _C
        _fichas = _C.list_clientes(grupo)
    except Exception:
        _fichas = []
    _nombres = {str(f.get("Nombre", "")) for f in _fichas}
    _porid = next((str(f.get("Nombre", "")) for f in _fichas
                   if str(f.get("ID", "")) == str(prj.get("ClienteID", ""))), "")
    _cli = _porid or str(prj.get("Cliente", "") or "")
    if _cli in _nombres:
        st.session_state["fac_cli"] = _cli
    else:
        st.session_state["_fac_aviso_cli"] = str(prj.get("Cliente", "") or "—")
    st.session_state["_fac_prj_pending"] = str(pid)
    st.session_state["_admin_nav_pending"] = ("finanzas", "🧾 Facturas")


def _facturar_atajo(pid, grupo, prj_nombre=""):
    """Facturar la obra desde la propia obra (v357).

    Reutiliza el alta de `invoices_ui` (no se duplica el creador de facturas) y le pasa
    el ID del proyecto; la etiqueta la resuelve allí. Muestra lo pendiente para que se
    sepa de antemano si hay algo que facturar.
    """
    try:
        from core import invoices as I
        from core import theme as _T
        pend = I.pendiente_de_facturar(pid, grupo)
        facturado = I.facturado_por_proyecto(grupo).get(str(pid), 0.0)
    except Exception:
        return
    if pend <= 0 and facturado <= 0:
        return                          # nada que facturar y nada facturado: no estorbar
    _c1, _c2 = st.columns([3, 2])
    with _c1:
        if pend > 0:
            st.markdown(":material/receipt: **Left to invoice: "
                        + _T.dinero(pend, 0) + "**")
            st.caption(t("The project's estimated revenue minus what has already been invoiced."))
        else:
            st.markdown(t(":material/check_circle: **Everything invoiced**") + " ("
                        + _T.dinero(facturado, 0) + ")")
    with _c2:
        if st.button(t(":material/receipt_long: Invoice this job"), key="fac_atajo_" + str(pid),
                     width="stretch", type="primary" if pend > 0 else "secondary",
                     help=t("Opens the new invoice with this client and this project already chosen.")):
            _ir_a_facturar(pid, grupo)
            st.rerun()


def render_expenses(pid, grupo, can_delete=False, key_prefix="ex"):
    """Costos del proyecto (v144).

    ⚠️ Antes respondia solo "cuanto llevas gastado". La pregunta accionable es
    **cuanto vas a gastar**: la barra de presupuesto se ponia roja al pasarse,
    o sea cuando ya no se puede hacer nada. Ahora la proyeccion al terminar va
    arriba del todo.
    """
    from core import expenses as E
    if not E.is_configured():
        return

    cp    = E.cost_projection(pid, grupo)      # incluye todo lo de project_cost
    lb    = E.labor_breakdown(pid, grupo)
    gastos = E.project_expenses(pid)
    pres  = cp["presupuesto"]
    proy  = cp["proyectado"]

    # ⚠️ v429: una LOCALIZACIÓN interna no termina, no lleva presupuesto (decisión del
    # usuario en v423) y su costo no se compara con nada. Las tres piezas que siguen
    # están escritas para una OBRA:
    #   · «Costará al terminar» proyecta con `total × 100 / avance`, y aquí no hay
    #     avance → salía «—» fijo;
    #   · «Presupuesto» salía «—» fijo, porque su ficha ni siquiera lo ofrece;
    #   · y el titular decía «no tiene presupuesto asignado… se define en Datos»,
    #     que es **falso**: en la ficha de una localización ese campo NO existe, así
    #     que mandaba a buscar algo que no está.
    # Quitar solo la primera dejaría las otras dos diciendo lo mismo a medias — el
    # desajuste de media-unificación de v419.
    _loc = P.es_interno(P.get_project(pid) or {})

    # ── Titular: una frase antes de cualquier numero ──
    # ⚠️ v349: los importes van por `theme.dinero` (formatea Y escapa el `$`). Con dos
    # `$` sueltos en la misma cadena, Streamlit la renderiza como LaTeX (regla v309).
    from core import theme as _T
    if _loc:
        _t = ("**Overhead** spend: it is not charged to any job and not invoiced to a client."
              if cp["total"] > 0 else
              "No spend has been recorded at this location yet.")
        _c, _fn = "#6b7280", st.info
    elif proy and pres > 0 and proy > pres * 1.02:
        _t = (f"At this rate the project will cost **{_T.dinero(proy, 0)}**, "
              f"**{_T.dinero(proy - pres, 0)} over** budget")
        _c, _fn = "#c0392b", st.error
    elif proy and pres > 0:
        _t = (f"At this rate the project will cost **{_T.dinero(proy, 0)}**, within "
              f"the budget of {_T.dinero(pres, 0)}")
        _c, _fn = "#1e8449", st.success
    elif cp["total"] > 0 and pres <= 0:
        _t = ("This project **has no budget set**, so there is nothing to compare the spend against. Set it in :material/edit: Details.")
        _c, _fn = "#6b7280", st.info
    else:
        _t, _c, _fn = ("No costs have been recorded on this project yet.",
                       "#6b7280", st.info)

    # ── Tarjetas KPI ──
    tarj = [_kpi_card(t("Total cost"), f"${cp['total']:,.0f}"),
            _kpi_card(t("Purchases"), f"${cp['compras']:,.0f}"),
            _kpi_card(t("Labour"), f"${cp['mano_obra']:,.0f}")]
    if not _loc:                       # v429: ninguna de las dos aplica a una localización
        tarj += [_kpi_card(t("Budget"), f"${pres:,.0f}" if pres > 0 else "—"),
                 _kpi_card(t("Cost at completion"), f"${proy:,.0f}" if proy else "—", _c)]
    # v343: lo COMPROMETIDO solo se enseña si hay algo pedido — una tarjeta en $0
    # en todos los proyectos sería ruido.
    if cp.get("comprometido"):
        from core import theme as _th
        tarj.insert(3, _kpi_card(t("Committed"), f"${cp['comprometido']:,.0f}",
                                 _th.AMBAR, pie="ordered, not received yet"))
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    _fn(_t)

    if pres > 0:
        st.progress(min(1.0, (cp["pct"] or 0) / 100.0))
        # ⚠️ v349: DOS `$` en la misma cadena = LaTeX (regla de v309). Se veía en
        # producción como «Llevas **0** de 10,000»: los `$` desaparecían y los `**`
        # salían literales. `theme.dinero` formatea Y escapa.
        from core import theme as _T
        _l = (f"You have spent **{_T.dinero(cp['total'], 0)}** of {_T.dinero(pres, 0)}"
              f" · **{cp['pct']}% used**")
        if cp["avance"] > 0:
            _l += f" with **{cp['avance']:.0f}% progress**"
            if cp["por_punto"]:
                _l += f" ({_T.dinero(cp['por_punto'], 0)} per point)"
        st.caption(_l + ("  :red[:material/block:] OVER BUDGET" if cp["over"] else ""))
        # ⚠️ v343: el caso que nadie veía — todavía dentro de presupuesto, pero con
        # lo ya PEDIDO se pasa seguro. Antes esto solo se sabía al llegar la factura.
        if cp.get("over_comp"):
            st.warning(
                ":material/shopping_cart: You are within budget, but with the "
                f"**{_T.dinero(cp['comprometido'], 0)} already ordered** the project reaches "
                f"**{_T.dinero(cp['total_comp'], 0)}**, "
                f"**{_T.dinero(cp['total_comp'] - pres, 0)} over** the "
                f"{_T.dinero(pres, 0)} budgeted.")

    # ── Cuánto ganas con cada persona (v360) ─────────────────────
    if can_delete:
        _ganancia_section(pid, grupo)

    # ── Facturar esta obra (atajo, v357) ─────────────────────────
    if can_delete:                      # solo gestión: el campo no factura
        _facturar_atajo(pid, grupo, prj_nombre=str(P.get_project(pid).get("Nombre", "")))

    # ── Órdenes de compra: el dinero comprometido (v343) ──
    _ordenes_section(pid, grupo, editable=can_delete, key_prefix=key_prefix)

    # ── Reparto del costo | Compras por categoría (doble columna, v213) ──
    _rep = cp["total"] > 0
    _cat = gastos.get("por_categoria") or {}

    def _blq_reparto():
        st.markdown(t("**Cost split**"))
        st.markdown(_barras_html([(t("Labour"), cp["mano_obra"]),
                                  (t("Purchases"), cp["compras"])], cp["total"]),
                    unsafe_allow_html=True)

    def _blq_categorias():
        st.markdown(t("**Purchases by category**"))
        st.markdown(_barras_html(sorted(_cat.items(), key=lambda x: -x[1]),
                                 gastos["total"], "#BA7517"), unsafe_allow_html=True)

    if _rep and _cat:
        _bc1, _bc2 = st.columns(2, gap="large")
        with _bc1:
            _blq_reparto()
        with _bc2:
            _blq_categorias()
    elif _rep:
        _blq_reparto()
    elif _cat:
        _blq_categorias()

    # ── Mano de obra por persona: labor_cost solo daba el total ──
    if lb["items"]:
        st.markdown(t("**Labour by person**"))
        st.dataframe(pd.DataFrame([{
            "Usuario": x["usuario"], "Horas": x["horas"],
            "Rate/h": x["tarifa"], "Costo": x["costo"],
        } for x in lb["items"]]), hide_index=True, width="stretch", column_config=tabla.cfg())
        if lb["sin_tarifa"]:
            st.warning(":material/warning: With no hourly rate, their hours add **$0** to the cost: **"
                       + ", ".join(lb["sin_tarifa"]) + "**. It is set in :material/build: Users.")
        if lb.get("de_baja"):          # v325: cuenta eliminada ≠ tarifa sin poner
            st.info(":material/person_off: **" + ", ".join(lb["de_baja"]) + "**: hours from someone **no longer on the books**, so they add $0 and there is nowhere to set a rate.")

    # ── Curva de gasto acumulado ──
    _curva = E.spend_curve(pid, grupo)
    _svg   = E.spend_svg(_curva, proy, str(P.get_project(pid).get("Nombre", ""))) if _curva else ""
    if _svg:
        components.html(
            '<!DOCTYPE html><html><body style="margin:0;background:transparent">'
            + _svg + '</body></html>', height=320, scrolling=False)
        st.caption(t("Cumulative cost day by day. The dashed grey line is the budget; the coloured one is where you end up at the current rate."))
    elif _curva:
        st.caption(t("More than one movement is needed to draw the spend curve."))

    # ── Cargar recibo ──
    with st.expander(t("Upload receipt"), icon=":material/receipt:"):
        with st.form(f"{key_prefix}_add_{pid}", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cat = c1.selectbox(t("Category"), E.CATEGORIAS, key=f"{key_prefix}_cat")
            val = c2.number_input(t("Total value of the receipt"), min_value=0.0, step=1.0,
                                  key=f"{key_prefix}_val")
            prov = c1.text_input(t("Supplier"), key=f"{key_prefix}_prov")
            desc = c2.text_input(t("Description"), key=f"{key_prefix}_desc")
            f = st.file_uploader(t("Photo / PDF of the receipt"), type=["pdf", "png", "jpg", "jpeg"],
                                 key=f"{key_prefix}_file")
            if st.form_submit_button(t("Save receipt")):
                if val <= 0:
                    st.error(t("Enter the value of the receipt."))
                else:
                    did, fn = "", ""
                    if f is not None:
                        fn = f.name
                        did = E.upload_receipt(pid, f.name, f.getvalue(),
                                               f.type or "application/octet-stream")
                    ok, msg = E.add(pid, grupo, val, cat, prov, desc, did, fn,
                                    st.session_state.get("auth", {}).get("usuario", ""))
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    items = gastos["items"]
    if items:
        # v213: recibos ACTIVOS — tocar uno muestra su foto inline (antes: tabla
        # redundante + botones de solo-descarga).
        with st.expander(f":material/receipt_long: Receipts ({len(items)})"):
            st.caption(t("Tap a receipt to see the photo."))
            for r in items:
                _rid = str(r.get("ID", ""))
                _did = str(r.get("DriveID", "")).strip()
                _lbl = f":material/receipt_long: {r.get('Fecha')} · {r.get('Categoria')} · ${E._num(r.get('Valor')):,.0f}"
                _ex = " · ".join(x for x in [str(r.get('Proveedor') or ''),
                                             str(r.get('Descripcion') or '')] if x)
                if _ex:
                    _lbl += f" · {_ex}"
                cc = st.columns([6, 1])
                if _did:
                    if cc[0].button(_lbl, key=f"{key_prefix}_open_{_rid}",
                                    width="stretch"):
                        _cur = st.session_state.get(f"{key_prefix}_rcb")
                        st.session_state[f"{key_prefix}_rcb"] = None if _cur == _rid else _rid
                        st.rerun()
                else:
                    cc[0].caption(_lbl + " · no file")
                if can_delete and cc[1].button(":material/delete:", key=f"{key_prefix}_del_{_rid}"):
                    ok, msg = E.delete(r.get("ID"))
                    (flash.exito if ok else st.error)(msg)
                    if ok:
                        st.session_state.pop(f"{key_prefix}_rcb", None)
                        st.rerun()

            # ── Recibo abierto: foto inline (imagen) o descarga (PDF) ──
            _sel = st.session_state.get(f"{key_prefix}_rcb")
            _ro = next((x for x in items if str(x.get("ID")) == str(_sel)), None) if _sel else None
            if _ro and str(_ro.get("DriveID", "")).strip():
                _arch = str(_ro.get("Archivo", "recibo"))
                try:
                    from core import drive_store
                    _data = drive_store.download(str(_ro.get("DriveID", "")).strip())
                    if _arch.lower().endswith((".png", ".jpg", ".jpeg")):
                        st.image(_data, caption=_arch, width="stretch")
                    else:
                        st.info(f":material/description: {_arch} — it is a PDF; download it to view it.")
                    st.download_button(t(":material/download: Download receipt"), data=_data, file_name=_arch,
                                       key=f"{key_prefix}_dlrcb_{_sel}")
                except Exception:
                    st.caption(t("The receipt file could not be loaded."))


# ── Reporte del ADMIN: gastos de todos los proyectos del grupo ──
def render_pnl(grupo: str):
    """Resumen financiero del grupo: torre de control, no una lista de cifras (v317).

    Toma las dos mecanicas que ya funcionan en la app: la **rejilla fija de indicadores
    clickeables** del «Resumen del dia» de HOME (v196/v199) y la **fila de herramientas
    que se abren debajo** del Panel de planificacion (v287). Todo sale de lectores
    cacheados -> 0 lecturas nuevas de Sheets.
    """
    from core import finance as F
    from core import theme as T
    st.caption(t("What was actually invoiced minus the costs (payroll + purchases) = profit. «Profitability» is the estimate from the margin; this is what actually happened."))

    # ── Periodo ──────────────────────────────────────────────────
    _hoy = clock.today(grupo)
    # ⚠️ Los valores se comparan justo debajo → se traduce el display, no la opción.
    _PER = {"Este mes": "This month", "Trimestre": "Quarter",
            "Este año": "This year", "Todo": "All"}
    _per = st.radio(t("Period"), list(_PER), format_func=lambda o: t(_PER[o]),
                    horizontal=True, key="cpxseg_pnl_per", label_visibility="collapsed")
    if _per == "Este mes":
        _desde, _hasta = _hoy.replace(day=1), _hoy
    elif _per == "Trimestre":
        _desde = _hoy.replace(day=1, month=((_hoy.month - 1) // 3) * 3 + 1)
        _hasta = _hoy
    elif _per == "Este año":
        _desde, _hasta = _hoy.replace(day=1, month=1), _hoy
    else:
        _desde = _hasta = None

    d = F.pnl(grupo, _desde, _hasta)
    if d["facturado"] == 0 and d["costo_total"] == 0:
        st.info(t(":material/info: There are no invoices or costs (payroll/purchases) in this period.")
                if _desde else
                t(":material/info: No invoices or costs (payroll/purchases) have been recorded yet."))
        return
    if _desde:
        st.caption(f":material/date_range: {_desde.strftime('%d/%m/%Y')} → "
                   f"{_hasta.strftime('%d/%m/%Y')}")

    # ── Las 3 cifras, con linea de contexto (como los KPI de HOME, v303) ──
    _nfac = len(d.get("por_cliente") or [])
    _mrg = (100 * d["ganancia"] / d["facturado"]) if d["facturado"] > 0 else None
    # v341: la comparación con el periodo ANTERIOR. Cuesta 0 llamadas nuevas — `pnl`
    # lee de los mismos lectores cacheados, así que el periodo previo es solo volver
    # a filtrar en memoria. ⚠️ En «Todo» no hay anterior: `var` sale vacío y las
    # tarjetas caen a su pie de siempre.
    try:
        _cmp = F.pnl_comparado(grupo, _desde, _hasta)
        _v = _cmp.get("var") or {}
    except Exception:
        _cmp, _v = {}, {}
    # ⚠️ En un COSTO, subir es peor: se invierte el sentido de `mejor`.
    _vc = dict(_v.get("costo_total") or {})
    if _vc:
        _vc["mejor"] = not _vc.get("mejor")
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin:2px 0 6px">'
                + _kpi_card(t("Income (invoiced)"), T.dinero(d["facturado"], 0),
                            var=_v.get("facturado"))
                + _kpi_card(t("Costs (what you pay)"), T.dinero(d["costo_total"], 0),
                            var=_vc or None)
                + _kpi_card(t("Profit"), T.dinero(d["ganancia"], 0),
                            T.VERDE if d["ganancia"] >= 0 else T.ROJO,
                            var=_v.get("ganancia"))
                + "</div>", unsafe_allow_html=True)
    _pie = (f"{_nfac} client(s) invoiced  ·  costs = payroll + purchases"
            + (f"  ·  {t('margin')} {_mrg:.0f}%" if _mrg is not None else ""))
    if _cmp.get("rango_previo"):
        _d0, _h0 = _cmp["rango_previo"]
        _pie += (f"  ·  compared with {_d0.strftime('%d/%m')}–{_h0.strftime('%d/%m')}")
    st.caption(_pie)

    # ── Rejilla FIJA de pendientes, clickeables (patron del Resumen del dia) ──
    # ⚠️ Estructura fija (v196): siempre los mismos 8 y en el mismo orden, con su 0
    # incluido. Que aparezcan y desaparezcan segun el dia es lo que hacia ilegible
    # el resumen antes de v196.
    _cc = {}
    try:
        _cc = F.conciliacion_mo(grupo, _desde, _hasta) or {}
    except Exception:
        pass
    try:
        _sf = F.sin_facturar(grupo)
    except Exception:
        _sf = []
    try:
        _sinmar = [r["nombre"] for r in F.group_profitability(grupo)["rows"]
                   if P._num(r.get("margen")) <= 0]
    except Exception:
        _sinmar = []
    try:
        from core import expenses as _E
        _over = [r["nombre"] for r in _E.over_budget(grupo)]
    except Exception:
        _over = []

    # slug, icono, etiqueta, valor, urgente, hay_algo, seccion, sub, detalle()
    _IND = [
        ("venc", ":material/warning:", t("Overdue"), T.dinero(d["vencido"], 0), True,
         d["vencido"] > 0, "finanzas", "🧾 Facturas",
         lambda: f"{T.dinero(d['vencido'])} in invoices past their due date."),
        ("cobrar", ":material/receipt:", "To collect", T.dinero(d["por_cobrar"], 0), False,
         d["por_cobrar"] > 0, "finanzas", "🧾 Facturas",
         lambda: f"{T.dinero(d['por_cobrar'])} invoiced and not yet collected."),
        ("sinfac", ":material/request_quote:", "Not invoiced",
         T.dinero(sum(v for _n, v in _sf), 0), True, bool(_sf), "finanzas", "🧾 Facturas",
         lambda: " · ".join(f"{n}: {T.dinero(v, 0)}" for n, v in _sf[:8])
                 or "Everything worked has been invoiced."),
        ("pagar", ":material/payments:", "To pay", T.dinero(d["por_pagar"], 0), False,
         d["por_pagar"] > 0, "finanzas", "👥 Nóminas",
         lambda: f"{T.dinero(d['por_pagar'])} in payslips issued and not marked paid."),
        ("sinnom", ":material/schedule:", "Hours with no payslip",
         T.dinero(_cc.get("cobrado_no_pagado", 0), 0), True,
         _cc.get("cobrado_no_pagado", 0) >= 1, "finanzas", "👥 Nóminas",
         lambda: "Hours charged to a job with NO workday open: they are billed to the client but do not enter any payslip, so they inflate the margin."),
        # ⚠️ v325: el indicador cuenta SOLO a quien se le puede poner tarifa. Quien
        # ya no está dado de alta no es un pendiente accionable —no hay fila donde
        # ponerla— y sumarlo aquí mandaba a Usuarios a no hacer nada; se menciona
        # en el detalle, que es donde informa sin fingir que hay una tarea.
        ("sintar", ":material/person_off:", "No rate",
         f"{len(_cc.get('sin_tarifa') or [])} pers.", False,
         bool(_cc.get("sin_tarifa")), "planificacion", "👷 Usuarios",
         lambda: "Their work counts as $0: " + ", ".join(_cc.get("sin_tarifa") or [])
                 + (("  ·  Plus, with hours but NO account any more (no rate can be set for them): " + ", ".join(_cc.get("de_baja") or []))
                    if _cc.get("de_baja") else "")),
        ("sinmar", ":material/percent:", "No margin", f"{len(_sinmar)} jobs", False,
         bool(_sinmar), "finanzas", "📈 Rentabilidad",
         lambda: "Invoiced at cost (estimated profit $0): " + ", ".join(_sinmar[:8])),
        ("over", ":material/trending_down:", "Sobre ppto.", f"{len(_over)}", True,
         bool(_over), "finanzas", "💰 Gastos",
         lambda: ", ".join(_over[:8]) or "No job is over budget."),
    ]
    st.markdown(t("**:material/notifications: Pending**"))
    _css = ["<style>"]
    for _s, _i, _l, _v, _u, _hay, _sec, _sub, _fn in _IND:
        # ⚠️ v326: mismo caso que en el resumen del día — el reposo era 2.26:1.
        _bg, _fg = (("#fdecec", "#c0392b") if _u else ("#fff4e0", "#8a5600")) \
                   if _hay else ("#f4f6f9", T.GRIS_SUAVE)
        # ⚠️ v326: el `min-height:0` anulaba la altura mínima del kit y dejaba
        # estos botones en 32 px. Son los que llevan a resolver cada pendiente.
        _css.append(f".st-key-pnlind_{_s} button{{background:{_bg}!important;"
                    f"color:{_fg}!important;border-color:{_bg}!important;"
                    "min-height:38px!important;padding:4px 8px!important;}")
    _css.append("</style>")
    st.markdown("".join(_css), unsafe_allow_html=True)
    # 2 filas de 4 (v305: 3 filas era mas alto y una sola no cabe sin partir etiquetas)
    for _fila in (_IND[:4], _IND[4:]):
        for _col, _x in zip(st.columns(4), _fila):
            if _col.button(f"{_x[1]} {_x[2]} · {_x[3]}", key=f"pnlind_{_x[0]}",
                           width="stretch",
                           help=t("See the detail and go and sort it out")):
                _cur0 = st.session_state.get("_pnl_ind")
                st.session_state["_pnl_ind"] = None if _cur0 == _x[0] else _x[0]
                st.rerun()
    _sel = st.session_state.get("_pnl_ind")
    _it = next((x for x in _IND if x[0] == _sel), None) if _sel else None
    if _it:
        st.markdown(f"**{_it[1]} {_it[2]} — {_it[3]}**")
        st.caption(_it[8]())
        if st.button(f"→ Ir a {_it[7].split(chr(32), 1)[-1]}", key=f"pnlgo_{_it[0]}",
                     type="primary"):
            _ir_a(_it[6], _it[7])

    # ── Herramientas, se abren debajo (patron del Panel) ──────────
    # La composicion del costo entra aqui como una mas (el usuario la probo fija y
    # prefirio tenerla bajo demanda): asi la pantalla arranca en la rejilla y cada
    # grafico se pide cuando se quiere mirar.
    _TOOLS = [("conc", t(":material/compare_arrows: Reconciliation")),
              ("cli", ":material/groups: By client"),
              ("comp", t(":material/pie_chart: Breakdown")),
              ("prj", ":material/apartment: By project")]
    _tc = st.columns(len(_TOOLS))
    _cur = st.session_state.get("_pnl_tool", "")
    for _i2, (_k, _lbl) in enumerate(_TOOLS):
        if _tc[_i2].button(_lbl, key=f"pnltool_{_k}", width="stretch"):
            st.session_state["_pnl_tool"] = "" if _cur == _k else _k
            st.rerun()
    if _cur:
        with st.container(border=True):
            if _cur == "conc":
                _pnl_conciliacion(_cc, T, periodo_completo=(_desde is None))
            elif _cur == "cli":
                st.markdown(t("**Invoiced by client**"))
                if d.get("por_cliente"):
                    st.markdown(_barras_html(d["por_cliente"], d["facturado"] or 1, T.AZUL),
                                unsafe_allow_html=True)
                else:
                    st.caption(t("No invoices in this period."))
            elif _cur == "comp":
                _comp = [(x, y) for x, y in (("Payroll", d["costo_nomina"]),
                                             (t("Purchases / materials"), d["compras"]))
                         if y > 0]
                if len(_comp) > 1:
                    st.markdown(t("**Cost breakdown**"))
                    st.markdown(_torta_html(_comp, d["costo_total"]), unsafe_allow_html=True)
                elif _comp:
                    st.caption(f"All the cost in the period is **{_comp[0][0]}** "
                               f"({T.dinero(_comp[0][1], 0)}): there is nothing to split.")
                else:
                    st.caption(t("No costs in this period."))
            else:
                _pnl_por_proyecto(grupo, T)


def _pnl_conciliacion(cc: dict, T, periodo_completo: bool = True):
    """El puente entre lo que se CARGA a las obras y lo que se PAGA (v313).

    ⚠️ `periodo_completo` (v324) es lo que decide si el residuo es una ALARMA o
    ruido esperable: los dos lados de la cadena se filtran por fechas DISTINTAS
    —las horas por el día trabajado, las nóminas por su `PeriodoHasta` (decisión
    de v309: el costo se devenga en el periodo que cierra)—, así que en una
    ventana corta la cadena NO puede cerrar. Con «Este mes» por defecto, eso
    sacaba un «$1,262.80 sin explicar» que no era ninguna descuadre.
    """
    if not cc:
        st.caption(t("The reconciliation could not be worked out."))
        return
    # ⚠️ v324: el signo va en la ETIQUETA (− / + / =), como en cualquier estado de
    # cuenta; el importe va en magnitud. Antes la fila restada llevaba el signo en
    # los dos sitios y se leía «− horas cobradas … $-358.80», que parece un error.
    _fil = [("Charged to jobs (hours booked × rate)", cc["cargado"], ""),
            ("− hours billed that you did NOT pay (charged with no workday)",
             cc["cobrado_no_pagado"], "#c0392b"),
            ("+ hours paid that you did NOT charge (travel, waiting)",
             cc["pagado_no_cargado"], "#c77700")]
    # ⚠️ v425: DESGLOSE de la fila de arriba, no un sumando nuevo — lo interno ya está
    # dentro de «pagadas y no cargadas», y añadirlo como fila propia descuadraría la
    # cadena. Va pegado a lo que desglosa y solo si hay algo: hasta ahora ese renglón
    # era un residuo anónimo donde cabía igual un traslado que una jornada de almacén.
    if cc.get("interno", 0.0) > 0:
        _fil.append(("· of which, overhead work (office, store)",
                     cc["interno"], "sub"))
    _fil += [("= base pay you should be paying", cc["base_teorica"], "bold"),
             ("Base pay actually entered in payslips", cc["base_nomina"], "")]
    # ⚠️ v430: este SÍ es un sumando (a diferencia del desglose de arriba). Vacaciones
    # y bajas pagadas no son horas fichadas, así que no están en la base ni pueden
    # estarlo —la base es lo que se contrasta contra la jornada—, pero salen de caja.
    if cc.get("ausencias", 0.0) > 0:
        _fil.append(("+ paid absences (holiday, sick leave)",
                     cc["ausencias"], "#c77700"))
    _fil += [("+ statutory contributions (super)", cc["aportes"], "#c77700"),
             ("= real cost of labour", cc["costo_real"], "bold")]
    _h = ['<table style="width:100%;border-collapse:collapse;font-size:13px">']
    for _lb, _v, _st in _fil:
        _b = "font-weight:700;border-top:1px solid #e6e9ef;" if _st == "bold" else ""
        # el desglose va sangrado y en gris, para que no se lea como un sumando
        if _st == "sub":
            _b = "padding-left:18px;color:#5b6472;font-size:12px;"
        _c = f"color:{_st};" if _st.startswith("#") else ""
        _h.append(f'<tr><td style="padding:4px 0;{_b}">{T._esc(_lb)}</td>'
                  f'<td style="padding:4px 0;text-align:right;{_b}{_c}">'
                  f'{T._esc(T.dinero(_v))}</td></tr>')
    _h.append("</table>")
    st.markdown("".join(_h), unsafe_allow_html=True)
    if abs(cc["sin_explicar"]) >= 1:
        if periodo_completo:
            st.warning(f":material/warning: **{T.dinero(abs(cc['sin_explicar']))} unexplained** "
                       "between what you should be paying and what is in the payslips: work "
                       "not yet paid, or payslips edited by hand.")
        else:
            st.info(f":material/info: With a narrow period the chain **cannot balance by "
                    f"construction**: hours count by the day worked and payslips by the "
                    f"period they close, so they fall in different months. "
                    f"The {T.dinero(abs(cc['sin_explicar']))} of difference is not a "
                    f"discrepancy — to reconcile properly, look at the **All** period.")
    st.caption(t("Your margin has to cover the statutory contributions and the hours you pay for without being able to charge them to any job."))


def _pnl_por_proyecto(grupo: str, T):
    """Cada obra: facturado vs lo que costo.

    ⚠️ ACUMULADO, ignora el selector de periodo — es justo lo que un P&L por mes
    natural no puede responder: la factura y sus costos caen en meses distintos.
    """
    from core import finance as F
    try:
        rows = F.resultado_por_proyecto(grupo)
    except Exception as e:
        st.caption(f"It could not be worked out: {e}")
        return
    if not rows:
        st.caption(t("No job has any invoicing or cost yet."))
        return
    st.caption(t(":material/info: **From start to finish of each job**, with no period filter: it is what a monthly summary cannot tell you, because the invoice and its costs fall in different months."))
    st.dataframe(pd.DataFrame([{
        "Proyecto": r["nombre"],
        "Facturado": r["facturado"],
        "Labour": r["mo"],
        "Purchases": r["compras"],
        "Resultado": r["resultado"],
        "Margen %": r["margen"],
    } for r in rows]), hide_index=True, width="stretch",
        column_config=tabla.cfg(None, {
            "Facturado":    st.column_config.NumberColumn(format="$%,.0f"),
            "Labour": st.column_config.NumberColumn(format="$%,.0f"),
            "Purchases":      st.column_config.NumberColumn(format="$%,.0f"),
            "Resultado":    st.column_config.NumberColumn(format="$%,.0f"),
            "Margen %":     st.column_config.NumberColumn(format="%.1f%%"),
        }))
    _t = sum(r["resultado"] for r in rows)
    st.markdown(f"Cumulative result across jobs: **{T.dinero(_t, 0)}**")
    st.caption(t("Cost = what is CHARGED to the job (hours charged × rate + purchases). Statutory contributions and unallocated hours do not belong to any one job: the margin covers them (see Reconciliation)."))


def render_group_profitability(grupo: str):
    """Rentabilidad del grupo: lo estimado CONTRA lo realmente facturado (v321).

    ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · Rentabilidad».
    """
    from core import finance as F
    from core import invoices as INV
    from core import theme as T
    st.caption(t("What each job cost (hours charged × rate + materials) against what you would charge (labour × (1 + margin) + materials). The margins are edited right here, and you can see how much of that estimate is already invoiced."))
    data = F.group_profitability(grupo)
    if not data["rows"]:
        st.info(t(":material/info: No projects with recorded cost yet (hours or purchases)."))
        return

    # Lo REALMENTE facturado por obra (1 lectura cacheada). «Por facturar» se calcula
    # como `ingreso estimado − facturado`, que es EXACTAMENTE lo que hace
    # `invoices.pendiente_de_facturar` (misma fórmula de ingreso) sin llamarla N veces.
    try:
        _fac = INV.facturado_por_proyecto(grupo)
    except Exception:
        _fac = {}
    rows = []
    for r in data["rows"]:
        f = P._num(_fac.get(str(r["id"]), 0))
        rows.append({**r, "facturado": round(f, 2),
                     "por_facturar": round(max(0.0, r["ingreso"] - f), 2)})

    _tot = data["totales"]
    _t_fac = round(sum(r["facturado"] for r in rows), 2)
    _t_pdt = round(sum(r["por_facturar"] for r in rows), 2)

    # ⚠️ v313: con margen 0% el "ingreso estimado" es IGUAL al costo, así que la
    # ganancia estimada sale 0 y la pantalla parecía rota. No lo está: es que no hay
    # margen puesto. v321: además se pueden poner AQUÍ, sin salir de la pantalla.
    _m0 = [r["nombre"] for r in rows if P._num(r.get("margen")) <= 0]
    if _m0:
        st.warning(f":material/percent: **{len(_m0)} job(s) at 0% margin**, so their "
                   "estimated revenue is exactly their cost and the profit comes out at $0: "
                   + ", ".join(_m0[:6]) + ("…" if len(_m0) > 6 else "")
                   + ". Edit them in the table below.")

    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin:2px 0 6px">'
                + _kpi_card(t("Cost charged"), T.dinero(_tot["costo"], 0))
                + _kpi_card(t("Estimated revenue"), T.dinero(_tot["ingreso"], 0))
                + _kpi_card(t("Estimated profit"), T.dinero(_tot["ganancia"], 0),
                            T.VERDE if _tot["ganancia"] > 0 else None)
                + _kpi_card(t("Already invoiced"), T.dinero(_t_fac, 0))
                + _kpi_card(t("To invoice"), T.dinero(_t_pdt, 0),
                            T.AMBAR if _t_pdt > 0 else None)
                + "</div>", unsafe_allow_html=True)
    st.caption(t("«Cost charged» = hours charged × rate + materials; it does NOT include statutory contributions or unallocated hours — the margin covers those (Summary → Reconciliation)."))

    # ── Tabla con el MARGEN EDITABLE ─────────────────────────────
    # El aviso de arriba decía "ve a Datos del proyecto" estando ya en la lista de
    # márgenes: se editan aquí (principio de elementos activos, v199).
    _con = [r for r in rows if r["costo"] > 0 or r["facturado"] > 0]
    _sin = [r for r in rows if not (r["costo"] > 0 or r["facturado"] > 0)]
    _orden = sorted(_con, key=lambda x: -x["ganancia"])
    _df = pd.DataFrame([{
        "Proyecto":         r["nombre"],
        "Costo":            round(r["costo"], 0),
        "Margen %":         float(round(r["margen"], 1)),
        "Ingreso estimado": round(r["ingreso"], 0),
        "Ganancia":         round(r["ganancia"], 0),
        "Facturado":        round(r["facturado"], 0),
        "To invoice":     round(r["por_facturar"], 0),
    } for r in _orden])
    _ed = st.data_editor(
        _df, width="stretch", hide_index=True, key="rent_ed",
        disabled=["Proyecto", "Costo", "Ingreso estimado", "Ganancia",
                  "Facturado", "To invoice"],
        column_config=tabla.cfg(None, {
            "Costo":            st.column_config.NumberColumn(format="$%,d"),
            "Margen %":         st.column_config.NumberColumn(
                                    t("Margin %"), format="%.1f%%", min_value=0.0,
                                    max_value=500.0, step=1.0,
                                    help=t("Editable: change it and press Save.")),
            "Ingreso estimado": st.column_config.NumberColumn(format="$%,d"),
            "Ganancia":         st.column_config.NumberColumn(format="$%,d"),
            "Facturado":        st.column_config.NumberColumn(format="$%,d"),
            "To invoice":     st.column_config.NumberColumn(format="$%,d"),
        }))
    # Solo lo que CAMBIO de verdad (comparando contra el valor original de cada fila)
    _cambios = {}
    for _i, r in enumerate(_orden):
        try:
            _nuevo = float(_ed.iloc[_i]["Margen %"])
        except Exception:
            continue
        if abs(_nuevo - float(r["margen"])) > 0.001:
            _cambios[r["id"]] = _nuevo
    if _cambios:
        st.info(f":material/edit: {len(_cambios)} margin(s) to save.")
        # ⚠️ Es UNA escritura por proyecto cambiado. Con 6 obras da igual; si algún día
        # son 60 y se cambian todas de golpe, hay que agrupar (patrón del 429 de v80).
        if st.button(t(":material/save: Save margins"), type="primary", key="rent_save"):
            _ok = 0
            for _pid, _m in _cambios.items():
                try:
                    P.update_project(_pid, {"MargenMO": str(_m)})
                    _ok += 1
                except Exception as e:
                    st.error(f"{_pid}: {e}")
            flash.exito(f":material/check_circle: {_ok} margin(s) saved.")
            st.session_state.pop("rent_ed", None)
            st.rerun()

    if _sin:
        with st.expander(f":material/visibility_off: {len(_sin)} job(s) with no movement "
                         "(no cost and no invoicing)"):
            st.caption(", ".join(r["nombre"] for r in _sin)
                       + ". They add nothing to profitability yet; their margin is edited on the project.")


def _partir_gasto(ge: dict) -> dict:
    """Separa el gasto del grupo en OBRA y ESTRUCTURA (v425).

    ⚠️ `group_expenses` incluye las localizaciones internas desde v422, y con razón:
    su gasto es costo REAL del grupo, y excluirlo repetiría el fallo de v310 con los
    archivados (KPI a $0 mientras la torta mostraba $1.500). Pero el KPI de esa
    pantalla se llama **«Costo cargado a obras»**, así que meterle la oficina lo haría
    MENTIR — el mismo problema que v422 resolvió en las horas. Se parten las dos
    cifras: la de obra conserva su significado y la de estructura se nombra.

    ⚠️ Las compras HUÉRFANAS (sin proyecto, o de uno borrado) se quedan del lado de
    obra: no se sabe de quién son, y moverlas a estructura sería afirmar algo que
    nadie sabe. Por eso `compras_obra` se calcula RESTANDO las internas al total del
    grupo, en vez de sumando las de obra — así se conserva la invariante de v310
    (`compras_grupo == Σ compras por proyecto + huérfanas`) y ninguna compra se pierde.

    Invariante que el guardián comprueba: `total_obra + total_int` es exactamente el
    costo del grupo de antes de v425, así que sin localizaciones NADA se mueve.

    Es una función APARTE, y no aritmética suelta dentro de la vista, para que el
    guardián pueda ejercitar la de verdad en vez de reproducirla (el error de v412).
    """
    filas = ge.get("proyectos") or []
    internas = [f for f in filas if f.get("interno")]
    obras = [f for f in filas if not f.get("interno")]
    mo_int = round(sum(f.get("mano_obra", 0) for f in internas), 2)
    cmp_int = round(sum(f.get("compras", 0) for f in internas), 2)
    mo_obra = round(sum(f.get("mano_obra", 0) for f in obras), 2)
    cmp_grupo = ge.get("compras_grupo", sum(f.get("compras", 0) for f in filas))
    cmp_obra = round(cmp_grupo - cmp_int, 2)
    return {
        "obras": obras, "internas": internas,
        "mo_obra": mo_obra, "compras_obra": cmp_obra,
        "total_obra": round(mo_obra + cmp_obra, 2),
        "mo_int": mo_int, "compras_int": cmp_int,
        "total_int": round(mo_int + cmp_int, 2),
        "huerfanos": ge.get("huerfanos", {"n": 0, "total": 0.0}),
    }


def render_group_expenses(grupo: str):
    from core import expenses as E
    from core import theme as T          # v309: `T.dinero` escapa el `$` (LaTeX)
    # ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · X» encima.
    # Era el 5º título duplicado de la app (v212, v291, v314, v319 y este barrido).
    if not E.is_configured():
        st.warning(t("Costs need Google Sheets configured."))
        return
    ge = E.group_expenses(grupo)
    filas = ge["proyectos"]
    if not filas:
        st.info(t("There are no projects in this company."))
        return

    # ⚠️ v310: UNA sola definición de gasto del grupo. `filas` ya incluye los
    # proyectos archivados, y `compras_grupo` son TODAS las compras del grupo
    # (incluidas las huérfanas), así que el KPI y la torta por fin dicen lo mismo.
    _p = _partir_gasto(ge)
    _int_filas, filas = _p["internas"], _p["obras"]
    _mo_int, _cmp_int, tot_int = _p["mo_int"], _p["compras_int"], _p["total_int"]
    _mo, tot = _p["mo_obra"], _p["total_obra"]
    _huer = _p["huerfanos"]
    tot_pres = sum(f["presupuesto"] for f in filas)
    tot_proj = sum((f["proyectado"] or f["total"]) for f in filas)
    con_pres = [f for f in filas if f["presupuesto"] > 0]
    sin_pres = [f for f in filas if f["presupuesto"] <= 0]
    n_over   = sum(1 for f in filas if f["over"])
    n_over_p = sum(1 for f in filas if f["over_proj"] and not f["over"])
    pct_grupo = round(100 * tot / tot_pres) if tot_pres > 0 else None

    # ── KPIs del grupo ──
    tarj = [_kpi_card(t("Cost charged to jobs"), T.dinero(tot, 0)),
            _kpi_card(t("Budget"), T.dinero(tot_pres, 0) if tot_pres else "—"),
            _kpi_card(t("% used"), f"{pct_grupo}%" if pct_grupo is not None else "—",
                      "#c0392b" if (pct_grupo or 0) > 100 else None),
            _kpi_card(t("Projected at completion"), T.dinero(tot_proj, 0),
                      "#c0392b" if (tot_pres and tot_proj > tot_pres) else None),
            _kpi_card(t("Over budget"), n_over, "#c0392b" if n_over else None)]
    # v343: lo COMPROMETIDO (pedido y sin recibir) solo si hay algo pedido.
    _comp_tot = round(sum(f.get("comprometido", 0.0) for f in filas), 2)
    if _comp_tot:
        tarj.insert(1, _kpi_card(t("Committed"), T.dinero(_comp_tot, 0), T.AMBAR,
                                 pie="ordered, not received yet"))
    # v425: la estructura, con su nombre. Solo si existe: sin localizaciones la
    # pantalla queda EXACTAMENTE como estaba.
    if tot_int > 0:
        tarj.append(_kpi_card(t("Overhead spend"), T.dinero(tot_int, 0),
                              pie="office and store"))
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)
    if tot_int > 0:
        st.caption(f":material/business: **{T.dinero(tot_int, 0)}** of overhead "
                   f"({T.dinero(_mo_int, 0)} of labour + {T.dinero(_cmp_int, 0)} "
                   "of purchases) across "
                   f"{len(_int_filas)} location(s). **It is not charged to any job "
                   "and does not count towards % used**, but it is a company cost and "
                   "does count in the P&L.")

    # Dinero registrado que no cuelga de ningún proyecto: se DICE, no se descarta.
    if _huer["n"]:
        st.warning(f":material/help: **{T.dinero(_huer['total'], 0)} across {_huer['n']} purchase(s) "
                   "with no project** (or from a deleted project). They count towards the company "
                   "cost, but not towards any job budget — assign them from the receipt.")
    if n_over:
        st.error(f":material/block: **{n_over} project(s) already over budget:** "
                 + ", ".join(f["nombre"] for f in filas if f["over"]))
    if n_over_p:
        st.warning(f":material/warning: **{n_over_p} more will go over at the current rate** (still within budget today): "
                   + ", ".join(f["nombre"] for f in filas if f["over_proj"] and not f["over"]))
    # ⚠️ v343: dentro de presupuesto HOY, pero con lo ya pedido se pasa seguro. Antes
    # esto solo se sabía cuando llegaba la factura, o sea cuando ya no se podía hacer nada.
    _oc = [f["nombre"] for f in filas if f.get("over_comp")]
    if _oc:
        st.warning(f":material/shopping_cart: **{len(_oc)} will go over with the material "
                   "already ordered** (not received yet): " + ", ".join(_oc))
    # Órdenes que debían haber llegado: obra parada esperando material.
    try:
        from core import orders as _O
        _atr = _O.atrasadas(grupo)
    except Exception:
        _atr = []
    if _atr:
        st.warning(":material/local_shipping: **" + str(len(_atr)) + " purchase order(s) that did not arrive on the promised date:** "
                   + " · ".join(f"{o.get('Proveedor','')} ({o['dias']} d)" for o in _atr[:6]))

    # ── Gasto por rubro (mano de obra + cada categoría de compra) ─────────
    # ⚠️ v310: se quitó el bloque de barras «Compras por categoría». Mostraba
    # EXACTAMENTE los mismos números que la torta (mismas categorías, mismos $ y
    # mismos %): dos gráficos para el mismo dato. La torta se queda porque es la
    # que el usuario pidió (v224) y además incluye la mano de obra.
    # ⚠️ v425: la torta es el gasto de TODO el grupo, y `por_categoria` incluye las
    # compras de estructura. Si la mano de obra fuera solo la de obra, la torta
    # mezclaría dos ámbitos y dejaría de cuadrar con nada — el fallo de v310 en versión
    # nueva. Se parte la mano de obra en dos rubros y la torta sigue sumando el grupo
    # entero. Sin localizaciones, `_mo_int` es 0 y el rubro ni aparece: idéntico a antes.
    _catg = ge["por_categoria"]
    _rubros = [("Labour" + (" (jobs)" if _mo_int > 0 else ""), _mo)]
    if _mo_int > 0:
        _rubros.append(("Labour (overhead)", _mo_int))
    _rubros += sorted(_catg.items(), key=lambda x: -x[1])
    _rubros = [(k, v) for k, v in _rubros if v and v > 0]
    if _rubros:
        st.markdown(t("**Spend by category**"))
        st.markdown(_torta_html(_rubros, sum(v for _, v in _rubros)),
                    unsafe_allow_html=True)
        if tot_int > 0:
            st.caption(t("Overhead included: this chart is the **company's** spend, not only what is charged to jobs."))


    # ── Proyectos CON presupuesto (tabla CLICKEABLE → abre el proyecto, v215) ──
    if con_pres:
        st.markdown(t("**Projects with a budget**"))
        _gev = st.dataframe(pd.DataFrame([{
            "Proyecto": f["nombre"], "Costo": f["total"],
            # v343: la columna solo aparece si el grupo tiene algo pedido
            **({"Comprometido": f.get("comprometido", 0.0)} if _comp_tot else {}),
            "Presupuesto": f["presupuesto"],
            "% used": f["pct"], "Avance %": f["avance"],
            "Forecast": f["proyectado"] if f["proyectado"] is not None else "—",
            "": ("sobre" if f["over"] else
                 ("pedido" if f.get("over_comp") else
                  ("riesgo" if f["over_proj"] else "ok"))),
        } for f in con_pres]), hide_index=True, width="stretch",
            on_select="rerun", selection_mode="single-row", key="ge_tbl", column_config=tabla.cfg())
        st.caption(t(":material/touch_app: Tap a row and «Open» to go to that project. **Projected** = cost at completion at the current rate. over = already over · ordered = will go over with the material already on order · at risk = will go over at the current rate · ok = within budget."))
        try:
            _grows = list(_gev.selection.rows)
        except Exception:
            _grows = []
        if _grows and _grows[0] < len(con_pres):
            _gf = con_pres[_grows[0]]
            if st.button(f"→ Open {_gf['nombre']}", key="ge_open", type="primary"):
                st.session_state["_prjsel_pending"] = str(_gf.get("id", ""))
                _ir_a("proyectos", "📊 Proyectos")

    # ── Proyectos SIN presupuesto: solo costo, y aviso ──
    if sin_pres:
        st.markdown(t("**Projects with no budget set**"))
        st.dataframe(pd.DataFrame([{
            "Proyecto": f["nombre"], "Purchases": f["compras"],
            "Labour": f["mano_obra"], "Total cost": f["total"],
        } for f in sin_pres]), hide_index=True, width="stretch", column_config=tabla.cfg())
        st.caption(f"{len(sin_pres)} project(s) with no budget: there is nothing to compare "
                   "their spend against. It is set in the project detail → :material/edit: Data.")

    # (Compras por categoría se muestra arriba, en doble columna con el reparto — v215.)

    # ── Export para contabilidad ──
    _csv = pd.DataFrame([{
        "Proyecto": f["nombre"], "Purchases": f["compras"], "Labour": f["mano_obra"],
        "Total cost": f["total"], "Presupuesto": f["presupuesto"],
        "% used": f["pct"], "Avance %": f["avance"], "Proyeccion": f["proyectado"],
    } for f in filas])
    st.download_button(t(":material/download: Export CSV (accounting)"),
                       data=_csv.to_csv(index=False).encode("utf-8"),
                       file_name=f"gastos_{grupo}.csv", mime="text/csv", key="ge_csv")


# ── Reporte del ADMIN: horas de TODOS los usuarios del grupo ──
def render_group_hours(grupo: str):
    from core import timeclock
    # ⚠️ import LOCAL, como el resto del módulo (patrón v342). Se me olvidó por SEGUNDA
    # vez en esta tanda —la primera fue en `render_localizaciones`— y lo cazó el
    # guardián de v322, no yo: aquí `theme` no está a nivel de módulo, así que usarlo
    # sin importar es un NameError que solo aparece al abrir la pantalla.
    from core import theme
    # ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta «Finanzas · X» encima.
    # Era el 5º título duplicado de la app (v212, v291, v314, v319 y este barrido).
    if not timeclock.is_configured():
        st.warning(t("The time clock needs Google Sheets configured."))
        return

    # ⚠️ `per` se compara abajo y además indexa `{"Semana": 7, …}` → la opción no se
    # toca; se traduce el display.
    _PERH = {"Hoy": "Today", "Semana": "Week", "Mes": "Month", "Todo": "All"}
    per = st.radio(t("Period"), list(_PERH), format_func=lambda o: t(_PERH[o]),
                   horizontal=True, key="gh_per", label_visibility="collapsed")
    now = clock.now()
    if per == "Hoy":
        days = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 86400.0
    else:
        days = {"Semana": 7, "Mes": 30, "Todo": None}[per]

    data = timeclock.group_hours(grupo, days=days)
    if not data:
        st.info(t("No time entries in the period."))
        return

    # ⚠️ Dos logins distintos pueden compartir Nombre (hay dos `lksdfkldsf` y dos
    # `fijiofgjei`): sin el login se vuelven indistinguibles. Se añade SOLO a los que
    # colisionan. Se define AQUÍ arriba porque lo usan el aviso y la tabla.
    from collections import Counter as _Counter
    _nombres = _Counter((d.get("nombre") or d["usuario"]) for d in data)

    def _etiqueta(d):
        nom = d.get("nombre") or d["usuario"]
        return f"{nom} ({d['usuario']})" if _nombres[nom] > 1 else nom

    # ── Totales del grupo (KPIs) ──
    tot_jorn = sum(d["general"] for d in data)
    tot_proy = sum(d["proyecto"] for d in data)
    tot_sina = sum(d["sin_asignar"] for d in data)
    tot_cost = sum(d["costo"] for d in data)
    # v425: el trabajo en oficina/almacén, que hasta ahora era un residuo anónimo
    # dentro de «sin asignar». Se paga y no se le carga a ningún cliente.
    tot_intn = sum(d.get("interno", 0.0) for d in data)
    tot_cint = sum(d.get("costo_interno", 0.0) for d in data)
    activos  = sum(1 for d in data if d["general"] or d["proyecto"] or d.get("interno"))
    pct_sina = (100 * tot_sina / tot_jorn) if tot_jorn > 0 else 0
    _dudoso  = [d for d in data if d["sin_asignar_indet"]]

    # ⚠️ v320: «Costo M.O.» pasa a llamarse por lo que ES. Tras v313 la app distingue
    # lo que PAGAS (jornada × tarifa + aportes de ley) de lo que CARGAS a las obras
    # (horas imputadas × tarifa). Esta cifra es la SEGUNDA, y llamarla "costo" a secas
    # la hacía indistinguible del «Costos» del P&L, que es otro número.
    tarj = [_kpi_card(t("People"), activos),
            _kpi_card(t("Workday"), f"{tot_jorn:.1f} h"),
            _kpi_card(t("On projects"), f"{tot_proy:.1f} h")]
    # v425: la tarjeta de estructura solo aparece si hay algo que contar. Sin
    # localizaciones sería un 0 permanente ocupando sitio, y la pantalla queda
    # EXACTAMENTE como estaba.
    if tot_intn > 0:
        tarj.append(_kpi_card(t("On overhead"), f"{tot_intn:.1f} h",
                              pie=t("office, warehouse")))
    tarj += [_kpi_card(t("Unallocated"), "—" if _dudoso else f"{tot_sina:.1f} h",
                       "#c0392b" if (_dudoso or pct_sina > 25) else None),
             _kpi_card(t("Labour charged to jobs"), f"${tot_cost:,.0f}",
                       pie=(f"+ {theme.dinero(tot_cint, 0)} interna"
                            if tot_cint > 0 else None))]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:6px">'
                + "".join(tarj) + "</div>", unsafe_allow_html=True)

    # ⚠️ «En proyectos» puede salir MAYOR que «Jornada»: alguien fichó a una obra sin
    # abrir jornada (comportamiento anterior a v150). Eso hace que el total de «sin
    # asignar» NO sea fiable —la app ya lo marcaba con «—» por persona, pero el KPI del
    # grupo seguía dando una cifra y un % como si nada— y además es el mismo hueco que
    # el resumen financiero llama «horas sin nómina»: se cobran y no se pagan.
    if _dudoso:
        _n = ", ".join(_etiqueta(d) for d in _dudoso)
        st.error(f":material/error: **{tot_proy - tot_jorn:+.1f} h**: some people charged "
                 f"MORE hours to jobs than their workday ({_n}). They clocked in without "
                 "opening their workday, so those hours **are charged to the client and appear "
                 "in no payslip**. That is why «unallocated» shows «—»: it cannot be worked out.")
    elif tot_jorn > 0:
        # v425: con estructura, «sin asignar» ya no la incluye — así que el % dice de
        # verdad lo que no se sabe, y lo que sí se sabe se nombra aparte.
        _extra = (f" Another **{100 * tot_intn / tot_jorn:.0f}%** was **overhead** work "
                  f"(office/store): it is paid and not charged to "
                  "any job." if tot_intn > 0 else "")
        st.caption(f"**{pct_sina:.0f}%** of the company workday was travel and waiting "
                   f"(unallocated).{_extra} Labour charged = hours charged × each "
                   "person rate; it does not include statutory contributions (see Summary → "
                   "Reconciliation).")

    # ── Tabla por persona (con costo; sin el Login técnico) ──
    # (`_etiqueta` y `_nombres` se definen arriba: los usa también el aviso)

    filas = []
    for d in data:
        _sa = ("—" if d["sin_asignar_indet"] else f"{d['sin_asignar']:.2f}")
        _f = {
            "Usuario": _etiqueta(d),
            "Shift (h)": d["general"],
            "On jobs (h)": d["proyecto"],
        }
        # v425: la columna solo existe si el grupo tiene estructura. Añadir una de
        # ceros a todo el mundo es ruido, y la tabla ya tiene 6 columnas.
        if tot_intn > 0:
            _f["On overhead (h)"] = d.get("interno", 0.0)
        _f.update({
            "Unassigned (h)": _sa,
            "Rate/h": d["tarifa"] or "—",
            "Labour cost": d["costo"] or 0,
        })
        filas.append(_f)
    # v215: tabla CLICKEABLE → abre la ficha de la persona (Planificación · Usuarios).
    _hev = st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True,
                        on_select="rerun", selection_mode="single-row", key="gh_tbl", column_config=tabla.cfg())
    st.caption(t(":material/touch_app: Tap a person and «Open record» to manage them."))
    try:
        _hrows = list(_hev.selection.rows)
    except Exception:
        _hrows = []
    if _hrows and _hrows[0] < len(data):
        _hd = data[_hrows[0]]
        _hn = _hd.get("nombre") or _hd["usuario"]
        if st.button(f"→ Open record for {_hn}", key="gh_open", type="primary"):
            st.session_state["gp_fichasel"] = f"{_hn} ({_hd['usuario']})"
            _ir_a("planificacion", "👷 Usuarios")

    if _dudoso:
        st.caption(t("«—» under *unallocated*: that person charged more hours to projects than their workday, so the figure is not reliable (they clocked in to the project without opening their workday). Fixed from v150 onwards; earlier history stays as it is."))
    # ⚠️ v325: dos causas MUY distintas daban el mismo aviso. «Falta ponerle la
    # tarifa» se arregla en Usuarios; «esta persona ya no está dada de alta» NO —
    # no hay fila donde ponerla, así que mandar ahí era mandar a un callejón.
    _sin_tar = [_etiqueta(d) for d in data
                if d["proyecto"] > 0 and not d["tarifa"] and d.get("existe", True)]
    _baja = [_etiqueta(d) for d in data
             if d["proyecto"] > 0 and not d["tarifa"] and not d.get("existe", True)]
    if _sin_tar:
        st.warning(":material/warning: With no **hourly rate**, their cost comes out at $0: **"
                   + ", ".join(_sin_tar) + "**. It is set in :material/build: Users.")
    if _baja:
        st.info(":material/person_off: **" + ", ".join(_baja) + "**: hours from someone **no longer on the books** (account deleted). Their hours still count, but **there is nowhere to set a rate**, so they add $0. To cost them you would have to recreate that account.")

    # ── Reparto por proyecto (a qué elevador va el tiempo del grupo) ──
    por_proy = {}
    for d in data:
        for nom, h in d["por_proyecto"].items():
            por_proy[nom] = por_proy.get(nom, 0.0) + h
    # ⚠️ Fuera los proyectos con 0.0 h: salían con la barra vacía y solo hacían ruido
    # (un fichaje de segundos redondea a 0.0). Se filtra por el valor REDONDEADO, que
    # es el que se muestra: si en pantalla pone «0.0 h», la fila no aporta nada.
    por_proy = {n: h for n, h in por_proy.items() if round(h, 1) > 0}
    if por_proy:
        st.markdown(t("**Company hours by project**"))
        _tot = sum(por_proy.values()) or 1
        for nom, h in sorted(por_proy.items(), key=lambda x: -x[1]):
            st.markdown(
                '<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                f'<div style="width:190px;flex:none;font-size:13px;color:#374151;'
                f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{nom}</div>'
                '<div style="flex:1;height:9px;background:#eef1f5;border-radius:20px;">'
                f'<div style="height:9px;width:{100*h/_tot:.0f}%;background:#2e6da4;'
                'border-radius:20px;"></div></div>'
                f'<div style="width:64px;flex:none;text-align:right;font-size:13px;'
                f'font-weight:600;color:#1f2937;">{h:.1f} h</div></div>',
                unsafe_allow_html=True)

    # ── Horas por PERSONA y PROYECTO (v216) ──────────────────────────────────
    # Responde "¿cuántas horas gastó cada usuario en cada proyecto?". El dato ya
    # lo trae group_hours en por_proyecto; aquí se muestra como matriz.
    _proys = sorted({p for d in data for p in d["por_proyecto"]})
    if _proys:
        st.divider()
        st.markdown(t("**:material/search: Hours by person and project**"))
        _mat = []
        for d in data:
            _pp = d["por_proyecto"]
            if not _pp:
                continue
            _fila = {"Persona": _etiqueta(d)}
            for _p in _proys:
                _h = _pp.get(_p, 0.0)
                _fila[_p] = round(_h, 2) if _h else ""
            _mat.append(_fila)
        if _mat:
            st.dataframe(pd.DataFrame(_mat), width="stretch", hide_index=True, column_config=tabla.cfg())
            st.caption(t("Each cell: hours that person charged to that project in the period. The columns are the projects."))


# ─────────────────────────────────────────────────────────────────────────────
# LOCALIZACIONES INTERNAS (v423) — oficina, almacén, taller
#
# Sección PROPIA, no un filtro dentro de la cartera (decisión del usuario): así la
# cartera de obras queda limpia y ninguna vista futura tiene que acordarse de
# excluirlas. El cerrojo de datos es de v422 (`list_projects(incluir_internos=False)`);
# esto es su cara visible — sin ella, una localización se podría crear y NO habría
# forma de verla, que es media aplicación de la regla v340.
#
# ⚠️ Lo que esta pantalla NO tiene, y es deliberado: cronograma, curva S, avance,
# SPI, presupuesto, margen, cliente y facturación. Una localización no se le entrega
# a nadie ni se le cobra a nadie; ponerle esas piezas sería volver a meterla en el
# mundo de la obra por la puerta de atrás.
# ─────────────────────────────────────────────────────────────────────────────

def _loc_datos(grupo):
    """Lo que necesita la lista, en una pasada (todo de cachés ya calientes)."""
    from core import expenses as E          # ⚠️ import LOCAL: así lo hace este módulo
    locs = P.list_locations(grupo, incluir_cerradas=True)
    horas, costos, alarmas = {}, {}, {}
    try:
        horas = P.project_hours_bulk(grupo)          # v422: ya incluye las internas
    except Exception:
        pass
    try:
        costos = {str(f["id"]): f for f in E.group_expenses(grupo)["proyectos"]
                  if f.get("interno")}
    except Exception:
        pass
    try:
        if alerts.is_configured():
            alarmas = alerts.open_counts_all()
    except Exception:
        pass
    return locs, horas, costos, alarmas


def _loc_personas(prj) -> list:
    return [x.strip() for x in str(prj.get("CampoAsignados", "")).split(";") if x.strip()]


def _cartera_localizaciones(locs, grupo, horas, costos, alarmas):
    """Tarjeta-botón por localización (patrón v223): toda la info ANTES de abrir."""
    from core import theme
    if not locs:
        st.info(t(":material/info: No locations yet. Create the office or the store below so the team can clock in, do their pre-start and charge costs to it."))
        return
    # Abiertas primero, y dentro de cada grupo por gasto (donde más se va el dinero).
    _ord = sorted(locs, key=lambda p: (str(p.get("Estado")) != P.INTERNO_ABIERTA,
                                       -float((costos.get(str(p.get("ID")), {}) or {})
                                              .get("total", 0) or 0)))
    for _i in range(0, len(_ord), 2):
        _cols = st.columns(2, gap="medium")
        for _j, p in enumerate(_ord[_i:_i + 2]):
            pid = str(p.get("ID", ""))
            _c = costos.get(pid, {}) or {}
            _h = float(horas.get(pid, 0.0) or 0.0)
            _al = int(alarmas.get(pid, 0) or 0)
            _cerrada = str(p.get("Estado")) != P.INTERNO_ABIERTA
            _tipo = str(p.get("Tipo", "")) or "Interno"
            _ico = P.TIPO_ICONO.get(_tipo, ":material/business:")
            with _cols[_j].container(border=True, key=f"loccard_{pid}"):
                st.markdown(f"**{_ico} {p.get('Nombre') or "(no name)"}**")
                _pie = [f"`{pid}`", _tipo]
                if _cerrada:
                    _pie.append(t(":material/lock: closed"))
                st.caption(" · ".join(_pie))
                m1, m2, m3 = st.columns(3)
                m1.markdown(f"**{_h:,.0f} h**  \n<small>worked</small>",
                            unsafe_allow_html=True)
                m2.markdown(f"**{theme.dinero(_c.get('total', 0), 0)}**  \n"
                            "<small>spent</small>", unsafe_allow_html=True)
                m3.markdown(f"**{len(_loc_personas(p))}**  \n<small>assigned</small>",
                            unsafe_allow_html=True)
                if str(p.get("Ubicacion", "")).strip():
                    st.caption(f":material/place: {p.get('Ubicacion')}")
                if _al:
                    st.markdown(f":red[:material/notifications_active: {_al} open alert(s)]")
                if st.button(t("Open →"), key=f"locopen_{pid}", width="stretch"):
                    st.session_state["_loc_open"] = pid
                    st.rerun()


def _nueva_localizacion_form(grupo: str):
    """Alta de una localización interna.

    ⚠️ Pide MUCHO menos que una obra, y eso es el punto: sin NS, sin fechas, sin
    presupuesto, sin cliente y sin margen. `create_project` con `activities=None` la
    deja sin cronograma, y `derive_estado` la marca «Abierta» por su tipo (v422).
    """
    with st.expander(t("New location"), icon=":material/add_circle:"):
        campos = []
        try:
            campos = [u["Usuario"] for u in auth.list_users(grupo)
                      if str(u.get("Rol", "")) == "campo"]
        except Exception:
            pass

        # ⚠️ FUERA del form (el mapa necesita reruns) e INLINE, sin expander propio:
        # esto ya vive dentro de un expander y Streamlit no permite anidarlos (v210).
        from core import location_ui
        st.markdown(t("**:material/map: Where it is** — optional, drops the pin"))
        _lat, _lng = location_ui.location_picker("nlocloc")
        _ubi = (st.session_state.get("nlocloc_addr")
                or st.session_state.get("nlocloc_q") or "").strip()
        if _ubi:
            st.caption(f":material/place: It will be saved as: **{_ubi}**")

        # Los asignados aquí son el «perfil de oficina» (v422): quien esté asignado de
        # forma permanente puede ficharla siempre. Fuera del form para poder avisar en
        # vivo de credenciales y contacto (misma razón que v127).
        asg = st.multiselect(t(":material/engineering: Who normally works here"),
                             campos, key="nloc_asg",
                             help=t("Being assigned here is what gives permanent access to clock in. Anyone coming for a single day is assigned from Planning, without touching this list."))
        if asg:
            _avisar_asignados(asg, grupo)

        with st.form("nloc_form"):
            nom = st.text_input(t("Name *"), key="nloc_nom",
                                placeholder=t("Sydney office, Chullora store…"))
            c1, c2 = st.columns(2)
            tipo = c1.selectbox(t("Type *"), P.TIPOS_INTERNOS, key="nloc_tipo")
            resp = c2.text_input(t("Person in charge"), key="nloc_resp", placeholder=t("optional"))
            instr = st.text_area(t(":material/push_pin: Instructions / notes"), key="nloc_ins",
                                 placeholder=t("Hours, access, site rules…"))
            _guardar = st.form_submit_button(t(":material/save: Create location"),
                                             type="primary", width="stretch")
        if _guardar:
            if not nom.strip():
                st.error(t("The name is required."))
                return
            _ok, _res = P.create_project(
                grupo, nom.strip(), ubicacion=_ubi, ingeniero=resp.strip(),
                campo_asignados=asg, instrucciones=instr, tipo=tipo,
                lat="" if _lat is None else _lat,
                lng="" if _lng is None else _lng,
                creado_por=st.session_state.get("auth", {}).get("usuario", ""))
            if not _ok:
                st.error(f"It could not be created: {_res}")
                return
            if asg:
                _notificar_asignados(asg, {"ID": _res, "Nombre": nom.strip(),
                                           "Ubicacion": _ubi, "Grupo": grupo})
            for k in ("nloc_nom", "nloc_resp", "nloc_ins", "nloc_asg"):
                st.session_state.pop(k, None)
            flash.exito(f"Location created: {_res} · {nom.strip()}")
            st.session_state["_loc_open"] = _res
            st.rerun()


def _loc_equipo(pid, grupo):
    """Quién trabaja aquí y cuánto tiempo — el «seguimiento» que se pidió."""
    from core import expenses as E, theme
    st.markdown(t("#### :material/engineering: Who has worked here"))
    try:
        filas = E.labor_breakdown(pid, grupo) if E.is_configured() else {}
    except Exception as e:
        st.caption(f"The hours could not be read: {e}")
        return
    # ⚠️ La clave es `items` (no `personas`) y cada fila trae `usuario`, no el nombre:
    # comprobado ejecutándolo, no leyendo el nombre que parecía lógico (regla v135).
    _p = (filas or {}).get("items") or []
    if not _p:
        st.caption(t("Nobody has clocked in here yet."))
        return
    # El login se traduce a nombre con la regla de siempre: se desempata SOLO si el
    # nombre se repite (v319/v413), para que dos homónimos no salgan idénticos justo
    # en la tabla que dice quién trabajó aquí.
    try:
        _et = auth.etiqueta_usuarios(auth.list_users(grupo) or [])
    except Exception:
        _et = {}
    _df = pd.DataFrame([{"Persona": _et.get(str(r.get("usuario")), str(r.get("usuario"))),
                         "Horas": round(float(r.get("horas", 0)), 2),
                         "Rate/h": float(r.get("tarifa", 0)),
                         "Costo": float(r.get("costo", 0))} for r in _p])
    st.dataframe(_df, width="stretch", hide_index=True,
                 column_config=tabla.cfg(None, {"Horas": st.column_config.NumberColumn(format="%.2f"),
                                "Rate/h": st.column_config.NumberColumn(format="$%,.2f"),
                                "Costo": st.column_config.NumberColumn(format="$%,.2f")}))
    st.caption(f"**{float(filas.get('horas', 0)):,.1f} h** · "
               f"{theme.dinero(filas.get('total', 0))} — ⚠️ this is "
               "**overhead**: it is not charged to any job and not invoiced to anyone.")
    if filas.get("sin_tarifa"):
        st.warning(":material/warning: With no hourly rate, their work here counts as $0: " + ", ".join(filas["sin_tarifa"]))


def _loc_prestarts(pid):
    """Historial de pre-starts de la localización (un almacén también tiene riesgos)."""
    st.markdown(t("#### :material/health_and_safety: Pre-Start"))
    from core import prestart
    try:
        # ⚠️ `list_prestarts(pid)` — un solo argumento. `list_for` no existe.
        regs = prestart.list_prestarts(pid) if prestart.is_configured() else []
    except Exception as e:
        st.caption(f"The history could not be read: {e}")
        return
    if not regs:
        st.caption(t("No pre-starts recorded at this location. They are done from the Pre-Start section, choosing this location."))
        return
    for r in regs[:10]:
        d = prestart.leer(r)
        # ⚠️ `near_miss` es un BOOL, no la cadena "YES": compararlo con "YES" daba
        # SIEMPRE False y habría pintado en verde un pre-start con incidente — en la
        # única pantalla donde ese semáforo sirve para algo.
        _mal = bool(d.get("near_miss")) or int(d.get("n_no", 0) or 0) > 0
        _pie = [str(d.get("facilitador", "")) or "—",
                f"{len(d.get('asistentes', []))} asistente(s)"]
        if int(d.get("n_no", 0) or 0):
            _pie.append(f":red[{d['n_no']} control(s) answered NO]")
        if d.get("near_miss"):
            _pie.append(":red[near miss]")
        st.markdown(f"{'🔴' if _mal else '🟢'} **{d.get('fecha', '')}** "
                    f"{d.get('hora', '')} · " + " · ".join(_pie))
    if len(regs) > 10:
        st.caption(f"… and {len(regs) - 10} more.")


def _detalle_localizacion(pid: str, grupo: str):
    prj = P.get_project(pid)
    if not prj:
        st.warning(t("The location was not found."))
        st.session_state.pop("_loc_open", None)
        return
    # ⚠️ Cerrojo de aislamiento (v351): esta vista trae el objeto por ID GLOBAL, igual
    # que el detalle de proyecto, factura, nómina y activo. Sin esto, editar la URL
    # abriría la oficina de otra empresa cliente.
    if not tenant.exigir(prj, t("This location")):
        return
    if not P.es_interno(prj):
        st.warning(t("That ID is not an internal location."))
        st.session_state.pop("_loc_open", None)
        return

    if st.button(t(":material/arrow_back: Back to locations"), key="loc_back"):
        st.session_state.pop("_loc_open", None)
        st.rerun()

    _tipo = str(prj.get("Tipo", "")) or "Interno"
    _cerrada = str(prj.get("Estado")) != P.INTERNO_ABIERTA
    with st.container(border=True):
        st.markdown(f"### {P.TIPO_ICONO.get(_tipo, ':material/business:')} "
                    f"{prj.get('Nombre') or "(no name)"}")
        _c = [f"`{pid}`", _etq(_tipo),
              (t(":material/lock: closed") if _cerrada
               else t(":material/check_circle: open"))]
        if str(prj.get("Ingeniero", "")).strip():
            _c.append(f"resp. {prj.get('Ingeniero')}")
        st.caption(" · ".join(_c))
        if str(prj.get("Ubicacion", "")).strip():
            st.markdown(maps.maps_link_md(prj.get("Ubicacion")))
    if str(prj.get("Instrucciones", "")).strip():
        st.info(prj.get("Instrucciones"))

    _sec = st.segmented_control(
        t("Section"), ["👥 Equipo", "💰 Gastos", "🦺 Pre-Start", "📎 Archivos", "✏️ Datos"],
        format_func=lambda o: {"👥 Equipo": t(":material/groups: Team"),
                               "💰 Gastos": t(":material/payments: Expenses"),
                               "🦺 Pre-Start": t(":material/health_and_safety: Pre-Start"),
                               "📎 Archivos": t(":material/folder: Files"),
                               "✏️ Datos": t(":material/edit: Data")}.get(o, o),
        default="👥 Equipo", key="cpxseg_loc_sec", label_visibility="collapsed")
    _sec = _sec or "👥 Equipo"

    if _sec == "👥 Equipo":
        a, b = st.columns([3, 2])
        with a:
            _loc_equipo(pid, grupo)
        with b:
            st.markdown(t("#### :material/badge: Permanently assigned"))
            _ppl = _loc_personas(prj)
            if _ppl:
                for u in _ppl:
                    st.markdown(f"· {u}")
                st.caption(t("They can always clock in here. For a single day, assign it from Planning."))
            else:
                st.caption(t("Nobody permanently assigned. Only those who have it set for today in Planning will be able to clock in."))
            _alerts_section(pid, grupo, project_name=prj.get("Nombre"))
    elif _sec == "💰 Gastos":
        render_expenses(pid, grupo, can_delete=True, key_prefix="loc")
    elif _sec == "🦺 Pre-Start":
        _loc_prestarts(pid)
    elif _sec == "📎 Archivos":
        _archivos_section(pid)
    else:
        _editar_localizacion(pid, grupo, prj)


def _editar_localizacion(pid, grupo, prj):
    campos = []
    try:
        campos = [u["Usuario"] for u in auth.list_users(grupo)
                  if str(u.get("Rol", "")) == "campo"]
    except Exception:
        pass
    _actuales = _loc_personas(prj)
    # Fuera del form: para avisar en vivo de contacto/credenciales al asignar (v149).
    _asg = st.multiselect(t(":material/engineering: Who normally works here"),
                          sorted(set(campos) | set(_actuales)), default=_actuales,
                          key=f"eloc_asg_{pid}")
    _nuevos = [u for u in _asg if u not in _actuales]
    if _nuevos:
        _avisar_asignados(_nuevos, grupo, exclude_pid=pid)

    with st.form(f"eloc_form_{pid}"):
        nom = st.text_input(t("Name *"), value=str(prj.get("Nombre", "")),
                            key=f"eloc_nom_{pid}")
        c1, c2 = st.columns(2)
        _tp = str(prj.get("Tipo", "")) or P.TIPOS_INTERNOS[0]
        # ⚠️ La pertenencia se pregunta con `es_interno`, la definición ÚNICA, no
        # comparando contra la lista aquí — el guardián de v422 lo exige, y con razón:
        # así solo hay un sitio donde cambiar qué cuenta como interno.
        tipo = c1.selectbox(t("Type *"), P.TIPOS_INTERNOS,
                            index=P.TIPOS_INTERNOS.index(_tp) if P.es_interno(_tp) else 0,
                            key=f"eloc_tipo_{pid}")
        resp = c2.text_input(t("Person in charge"), value=str(prj.get("Ingeniero", "")),
                             key=f"eloc_resp_{pid}")
        # ⚠️ «Cerrada» es el estado propio de una localización (v422): no tiene avance,
        # así que «En pausa»/«Completado» no significan nada aquí.
        _est_act = str(prj.get("EstadoManual", "")) or ""
        _opts = ["", P.INTERNO_CERRADA, P.ARCHIVADO]
        est = st.selectbox(t("Status"), _opts,
                           index=_opts.index(_est_act) if _est_act in _opts else 0,
                           format_func=lambda v: {"": t("Open"),
                                                  P.INTERNO_CERRADA: t("Closed"),
                                                  P.ARCHIVADO: t("Archived")}.get(v, v),
                           key=f"eloc_est_{pid}",
                           help=t("Closed = no longer used, but its history is kept. Archived = it also disappears from the list."))
        instr = st.text_area(t(":material/push_pin: Instructions / notes"),
                             value=str(prj.get("Instrucciones", "")),
                             key=f"eloc_ins_{pid}")
        _guardar = st.form_submit_button(t(":material/save: Save"), type="primary",
                                         width="stretch")
    if _guardar:
        if not nom.strip():
            st.error(t("The name is required."))
            return
        _ok, _msg = P.update_project(pid, {
            "Nombre": nom.strip(), "Tipo": tipo,
            "Ingeniero": resp.strip(), "Instrucciones": instr,
            "CampoAsignados": ";".join(_asg),
            "EstadoManual": est,
            "Estado": P.derive_estado(0, est, tipo),
        })
        if not _ok:
            st.error(_msg)
            return
        if _nuevos:
            _notificar_asignados(_nuevos, {"ID": pid, "Nombre": nom.strip(),
                                           "Ubicacion": prj.get("Ubicacion", ""),
                                           "Grupo": grupo})
        flash.exito(t("Location updated."))
        st.rerun()


def render_localizaciones(grupo: str):
    """🏢 Localizaciones internas: oficina, almacén, taller.

    ⚠️ SIN título propio: `home_ui._sub_header` ya pinta «Proyectos · Localizaciones».
    Repetirlo ha pasado cuatro veces (v212, v291, v314, v319).
    """
    _abierta = st.session_state.get("_loc_open")
    if _abierta:
        _detalle_localizacion(str(_abierta), grupo)
        return

    from core import theme
    locs, horas, costos, alarmas = _loc_datos(grupo)
    _abiertas = [p for p in locs if str(p.get("Estado")) == P.INTERNO_ABIERTA]
    _h = sum(float(horas.get(str(p.get("ID")), 0) or 0) for p in locs)
    _g = sum(float((costos.get(str(p.get("ID")), {}) or {}).get("total", 0) or 0)
             for p in locs)
    _n = len({u for p in locs for u in _loc_personas(p)})

    # ⚠️ `_kpi_card` DEVUELVE el HTML, no lo pinta. Mi primera versión hacía
    # `with k[0]: _kpi_card(...)` dentro de columnas y las cuatro tarjetas salían
    # INVISIBLES — código válido que no lanza, así que ningún guardián lo vio: lo cazó
    # mirar la pantalla en producción (como el `:material/` literal de v375). El patrón
    # correcto es el del resto del repo: construir la lista y pintarla de una vez.
    _tarj = [
        _kpi_card(t("Locations"), str(len(_abiertas)),
                  pie=f"of {len(locs)}" if len(locs) != len(_abiertas) else t("open")),
        _kpi_card(t("Hours worked"), f"{_h:,.0f}", pie="not charged to any job"),
        _kpi_card(t("Overhead spend"), theme.dinero(_g, 0), pie=t("never invoiced")),
        _kpi_card(t("People"), str(_n), pie="assigned on a regular basis"),
    ]
    st.markdown('<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px">'
                + "".join(_tarj) + "</div>", unsafe_allow_html=True)

    st.caption(t("Offices, stores and workshops: this is where people clock in, do the pre-start and charge admin costs. **They have no schedule and no progress, and their cost is never charged to a job or invoiced to a client.**"))
    _cartera_localizaciones(locs, grupo, horas, costos, alarmas)
    _nueva_localizacion_form(grupo)
