"""
Tablero semanal de asignación de cuadrilla — UI del admin (v159).

Sección 📅 Planificación en 🛠 Mi grupo: la rejilla persona×día coloreada (como
el board del usuario), edición de la semana persona a persona, "copiar la semana
anterior" y el catálogo de trabajos.
"""
from datetime import timedelta, time as _time

import streamlit as st

from core import flash

from core import roster as R
from core import auth
from core import projects as P
from core import clock


def _to_time(hhmm, default="07:00") -> _time:
    """'HH:MM' → datetime.time (para st.time_input); cae al default si viene vacío/inválido."""
    for cand in (hhmm, default):
        try:
            hh, mm = str(cand).split(":")
            return _time(int(hh), int(mm))
        except Exception:
            continue
    return _time(7, 0)


def _staff(grupo):
    """Personal de campo del grupo que va al tablero."""
    try:
        return [u for u in auth.list_users(grupo=grupo)
                if str(u.get("Rol", "")).lower() == "campo"]
    except Exception:
        return []


def _texto_sobre(hex_color) -> str:
    """Negro o blanco según la luminancia del fondo, para que el texto se lea."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#1f2937" if lum > 0.6 else "#ffffff"
    except Exception:
        return "#1f2937"


def _semana_activa() -> "date":
    """Lunes de la semana que se está viendo (en session_state)."""
    k = "ros_lunes"
    if k not in st.session_state:
        st.session_state[k] = R.lunes_de().isoformat()
    from datetime import date as _d
    y, m, dd = str(st.session_state[k]).split("-")
    return _d(int(y), int(m), int(dd))


def _cobertura_hoy(lunes, staff, datos):
    """Cobertura del día en vista (hoy si cae en la semana, si no el lunes): en obra /
    sin asignar (con nombres) / OFF-Leave — para ver los huecos de un vistazo (v217)."""
    off = (clock.today() - lunes).days
    d = R.DIAS[off] if 0 <= off <= 4 else R.DIAS[0]
    fecha = R.fecha_de_dia(lunes, d)
    en_obra, estado, sin = 0, 0, []
    for u in staff:
        asigs = R.celda_asigs(datos, u["Usuario"], d)     # v274: varias por día
        if any(a not in R.ESTADOS for a in asigs):
            en_obra += 1
        elif asigs:                                       # solo estados (OFF/Leave/…)
            estado += 1
        else:
            sin.append(u.get("Nombre") or u["Usuario"])
    partes = [f":green[:material/check_circle:] **{en_obra}** en obra"]
    if sin:
        _n = ", ".join(sin[:4]) + ("…" if len(sin) > 4 else "")
        partes.append(f":orange[:material/warning:] **{len(sin)}** sin asignar ({_esc(_n)})")
    else:
        partes.append(":green[:material/check_circle:] nadie sin asignar")
    if estado:
        partes.append(f":gray[:material/crop_square:] **{estado}** OFF/Leave")
    st.markdown(f"**{R.DIAS_LABEL[d]} {fecha.strftime('%d/%m')}** · " + " · ".join(partes))


def _min(hhmm):
    try:
        hh, mm = str(hhmm).split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return None


def _solapa(i1, f1, i2, f2) -> bool:
    """¿Se solapan dos franjas? Una franja vacía (día completo) ocupa todo → siempre choca."""
    a1, a2, b1, b2 = _min(i1), _min(f1), _min(i2), _min(f2)
    if None in (a1, a2, b1, b2):
        return True
    return a1 < b2 and b1 < a2


_EJE_MIN = 240   # 4 h: por debajo, un día de una hora daría un eje sin contexto


def _clase_franja(it) -> str:
    """`hora` (franja utilizable) · `dia` (ini/fin vacíos = día completo, v277) ·
    `rara` (trae hora pero no forma un intervalo positivo: fin ≤ inicio, o falta uno).
    ⚠️ Las `rara` NO se descartan en silencio — se listan y se dicen: una franja mal
    tecleada dibujada como bloque saldría con ancho 0 o negativo y no se vería."""
    a, b = _min(it.get("ini")), _min(it.get("fin"))
    if a is None and b is None:
        return "dia"
    return "hora" if (a is not None and b is not None and b > a) else "rara"


def _carriles(items):
    """Reparte las franjas en carriles paralelos: dos que se solapan NUNCA comparten
    carril, así el choque se VE en vez de quedar un bloque tapando al otro (que es
    justo lo que la celda del tablero esconde tras el «+N» de v295)."""
    carriles = []
    for it in sorted(items, key=lambda x: (_min(x["ini"]), _min(x["fin"]))):
        for c in carriles:
            if not any(_solapa(it["ini"], it["fin"], o["ini"], o["fin"]) for o in c):
                c.append(it)
                break
        else:
            carriles.append([it])
    return carriles


def _hm(m) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def _vista_dia(grupo, lunes, usuario, nom, dia, datos, tidx):
    """El día de UNA persona, desglosado y a escala, a ancho completo (v387).

    La celda del tablero solo cabe «primero +N» (v295), así que un día con varias
    obras esconde precisamente lo que hay que decidir: a qué hora va cada una y si
    se pisan. Aquí se ve el día entero.

    ⚠️ El EJE HORARIO solo se dibuja para las asignaciones que TRAEN hora. Medido
    sobre los datos reales antes de diseñarlo: 32 de 35 asignaciones no la tienen
    (el roster nació sin franja; `ini`/`fin` vacíos significan «día completo»,
    v277). Colocarlas en un eje sería inventarse una precisión que el dato no
    tiene, y dejaría un gráfico casi vacío con pinta de roto → van como banda
    aparte, declaradas como lo que son.
    """
    f = R.fecha_de_dia(lunes, dia)
    items = R.celda_items(datos, usuario, dia)
    nota = R.celda(datos, usuario, dia).get("nota", "")
    con_hora = [it for it in items if _clase_franja(it) == "hora"]

    with st.container(border=True):
        c1, c2 = st.columns([4, 2])
        c1.markdown(f"<div style='font-size:18px;font-weight:600'>{_esc(nom)} · "
                    f"{R.DIAS_LABEL[dia]} {f.strftime('%d/%m')}</div>",
                    unsafe_allow_html=True)
        _tot = sum(_min(it["fin"]) - _min(it["ini"]) for it in con_hora)
        _res = f"{len(items)} asignación" + ("es" if len(items) != 1 else "")
        if _tot:
            _res += f" · {_tot / 60:.1f} h con horario"
        c2.markdown(f"<div style='font-size:13px;color:#5b6472;text-align:right;"
                    f"padding-top:8px'>{_res}</div>", unsafe_allow_html=True)

        if not items:
            st.info("Este día está sin asignar.")
        # ── El aviso que la celda no puede dar: dos obras en la misma franja ──
        _pares = [(a, b) for i, a in enumerate(con_hora) for b in con_hora[i + 1:]
                  if _solapa(a["ini"], a["fin"], b["ini"], b["fin"])]
        if _pares:
            _txt = " · ".join(f"{R.etiqueta_de(a['asig'], tidx)} ↔ "
                              f"{R.etiqueta_de(b['asig'], tidx)}" for a, b in _pares)
            st.warning(f":material/warning: **Se pisan en la misma franja:** {_txt}. "
                       f"O es un día partido que falta detallar, o alguien está "
                       f"contado dos veces a la misma hora.")

        # ── Línea de tiempo (solo lo que tiene horario) ──
        if con_hora:
            lo = max(0, (min(_min(it["ini"]) for it in con_hora) // 60 - 1) * 60)
            hi = min(1440, (-(-max(_min(it["fin"]) for it in con_hora) // 60) + 1) * 60)
            if hi - lo < _EJE_MIN:
                # ⚠️ Ampliar por ARRIBA no basta: `hi` está topado en las 24:00, así
                # que un turno que acaba cerca de medianoche se quedaba con un eje
                # más corto que el mínimo. Si no cabe hacia arriba, se baja `lo`.
                hi = min(1440, lo + _EJE_MIN)
                lo = max(0, hi - _EJE_MIN)
            span = hi - lo
            filas = []
            for c in _carriles(con_hora):
                bl = []
                for it in c:
                    a, b = _min(it["ini"]), _min(it["fin"])
                    bg = R.color_de(it["asig"], tidx)
                    bl.append(
                        f'<div style="position:absolute;left:{(a - lo) / span * 100:.2f}%;'
                        f'width:{(b - a) / span * 100:.2f}%;top:0;bottom:0;background:{bg};'
                        f'color:{_texto_sobre(bg)};border-left:3px solid rgba(0,0,0,.28);'
                        f'border-radius:0 5px 5px 0;display:flex;align-items:center;'
                        f'padding:0 8px;font-size:12px;font-weight:600;overflow:hidden;'
                        f'white-space:nowrap;text-overflow:ellipsis">'
                        f'{_esc(R.etiqueta_de(it["asig"], tidx))} · '
                        f'{_esc(it["ini"])}–{_esc(it["fin"])}</div>')
                filas.append('<div style="position:relative;height:28px;background:#f1f5f9;'
                             'border-radius:6px;margin-bottom:5px">' + "".join(bl) + "</div>")
            paso = 60 if span <= 480 else 120
            marcas, m = [], lo
            while m <= hi:
                # ⚠️ Los ticks de los extremos NO se centran: con translateX(-50%) la
                # mitad del primero se sale del contenedor y se recorta.
                _tr = ("none" if m == lo else
                       "translateX(-100%)" if m + paso > hi else "translateX(-50%)")
                marcas.append(f'<span style="position:absolute;'
                              f'left:{(m - lo) / span * 100:.2f}%;transform:{_tr}">'
                              f'{_hm(m)}</span>')
                m += paso
            st.markdown("".join(filas) +
                        '<div style="position:relative;height:18px;font-size:11px;'
                        'color:#8a929e">' + "".join(marcas) + "</div>",
                        unsafe_allow_html=True)

        # ── Detalle por asignación (activo: cada obra se abre desde aquí) ──
        _ETQ = {"dia": "todo el día", "rara": "franja incompleta"}
        for i, it in enumerate(items):
            k = _clase_franja(it)
            cl = st.columns([4, 2, 1, 2])
            bg = R.color_de(it["asig"], tidx)
            cl[0].markdown(
                f"<div style='padding-top:6px'><span style='display:inline-block;"
                f"width:11px;height:11px;border-radius:3px;background:{bg};"
                f"margin-right:8px'></span><span style='font-size:14px'>"
                f"{_esc(R.etiqueta_de(it['asig'], tidx))}</span></div>",
                unsafe_allow_html=True)
            _fr = (f"{it['ini']}–{it['fin']}" if k == "hora"
                   else _ETQ[k] + (f" ({it['ini'] or '—'}→{it['fin'] or '—'})"
                                   if k == "rara" else ""))
            cl[1].markdown(f"<div style='font-size:13px;color:#5b6472;padding-top:7px'>"
                           f"{_esc(_fr)}</div>", unsafe_allow_html=True)
            _du = (f"{(_min(it['fin']) - _min(it['ini'])) / 60:.1f} h"
                   if k == "hora" else "—")
            cl[2].markdown(f"<div style='font-size:13px;color:#5b6472;padding-top:7px'>"
                           f"{_du}</div>", unsafe_allow_html=True)
            _pv = R.proyecto_de(it["asig"], tidx)
            if _pv and cl[3].button(f"→ {R.etiqueta_de(it['asig'], tidx)}",
                                    key=f"vdop_{lunes:%Y%m%d}_{usuario}_{dia}_{i}",
                                    use_container_width=True):
                st.session_state["_prjsel_pending"] = _pv
                st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                st.rerun()

        if nota:
            st.caption(f":material/sticky_note_2: {nota}")
        if st.button(":material/close: Cerrar", key=f"vdcl_{lunes:%Y%m%d}"):
            st.session_state.pop("_dia_abierto", None)
            st.rerun()


def _asignar_al_dia(grupo, lunes, usuario, sem_persona, dia, pid, ini, fin):
    """Añade el proyecto (con franja) al día de la persona SIN pisar sus otras asignaciones;
    guarda la semana completa (1 escritura)."""
    sem = dict(sem_persona or {})
    cur = R._norm_cell(sem.get(dia, {}))
    if str(pid) not in [it["asig"] for it in cur["items"]]:
        cur["items"].append({"asig": str(pid), "ini": ini, "fin": fin})
    sem[dia] = {"items": [{"a": it["asig"], "i": it["ini"], "f": it["fin"]} for it in cur["items"]],
                "nota": cur["nota"]}
    return R.guardar_persona(grupo, lunes, usuario, sem)


def _asignacion_inteligente(grupo, lunes, staff, tidx):
    """Sugiere a quién asignar a un proyecto en un día/franja = libre esa franja + cumple los
    certificados que exige + sin choque de turno (v279). Asigna a los elegidos con un clic."""
    from core import credentials
    with st.container():   # v287: el título lo da el botón de la fila de herramientas
        try:
            proys = [p for p in P.list_projects(grupo)
                     if str(p.get("Estado", "")) not in ("Completado", "Cancelado", "Archivado")]
        except Exception:
            proys = []
        if not proys:
            st.caption("No hay proyectos activos para asignar.")
            return
        # ⚠️ v306: la clave es el **ID**, no el nombre. Con `{Nombre: ID}` dos proyectos
        # homónimos colapsaban y uno quedaba IMPOSIBLE de elegir aquí, en silencio (el
        # mismo fallo de v147/v150, que se arregló en el fichaje y no aquí). El nombre
        # es solo la etiqueta que se muestra, y lleva el ID detrás para desempatar.
        _opts = [str(p.get("ID")) for p in proys]
        _lbl = {str(p.get("ID")): f"{p.get('Nombre') or '(sin nombre)'} ({p.get('ID')})"
                for p in proys}
        _psel = st.selectbox("Proyecto", ["—"] + _opts, key="ai_prj",
                             format_func=lambda i: "— elige el proyecto —" if i == "—"
                             else _lbl.get(i, i))
        if _psel == "—":
            return
        pid = _psel
        prj = P.get_project(pid)
        certs = [c.strip() for c in str((prj or {}).get("CertsReq", "")).split(";") if c.strip()]

        cda, cdb = st.columns([2, 3])
        _dsel = cda.selectbox("Día", R.DIAS, key="ai_dia",
                              format_func=lambda d: f"{R.DIAS_LABEL[d]} "
                              f"{R.fecha_de_dia(lunes, d).strftime('%d/%m')}")
        c1, c2 = cdb.columns(2)
        _ti = c1.time_input("Inicio", value=_to_time(R.TURNO_DEFAULT[0]), key="ai_ini", step=900)
        _tf = c2.time_input("Fin", value=_to_time(R.TURNO_DEFAULT[1]), key="ai_fin", step=900)
        ini, fin = _ti.strftime("%H:%M"), _tf.strftime("%H:%M")
        if certs:
            st.caption(":material/badge: Exige: " + " · ".join(certs))

        datos = R.get_semana(grupo, lunes)
        libres, ocupados = [], []
        for u in staff:
            usr = u["Usuario"]
            nom = u.get("Nombre") or usr
            items = R.celda_items(datos, usr, _dsel)
            choca = any(_solapa(ini, fin, it["ini"], it["fin"]) for it in items)
            comp = credentials.compliance(usr, certs) if certs else {"cumple": True, "por_tipo": {}}
            todo_vigente = all(e == "vigente" for e in comp["por_tipo"].values())
            estado = "🟢" if (comp["cumple"] and todo_vigente) else ("🟡" if comp["cumple"] else "🔴")
            (ocupados if choca else libres).append(
                {"usr": usr, "nom": nom, "cumple": comp["cumple"], "estado": estado})
        libres.sort(key=lambda f: (0 if f["cumple"] else 1, f["nom"]))

        if not libres:
            st.warning(f":material/warning: Nadie libre el {R.DIAS_LABEL[_dsel]} en {ini}–{fin}.")
        else:
            _opts = {f"{f['estado']} {f['nom']}" + ("" if f["cumple"] else " — no cumple"): f["usr"]
                     for f in libres}
            _pick = st.multiselect("Sugeridos (libres) — elige a quién asignar:",
                                   list(_opts), key="ai_pick")
            if st.button(f":material/check: Asignar {len(_pick)} a «{_psel}»", key="ai_go",
                         type="primary", use_container_width=True, disabled=not _pick):
                _n = 0
                for _lbl in _pick:
                    _u = _opts[_lbl]
                    ok, _ = _asignar_al_dia(grupo, lunes, _u, datos.get(_u, {}), _dsel, pid, ini, fin)
                    if ok:
                        try:
                            P.add_field_user(pid, _u)
                        except Exception:
                            pass
                        _n += 1
                flash.exito(f"Asignados {_n} a «{_psel}» el {R.DIAS_LABEL[_dsel]} {ini}–{fin}.")
                st.rerun()
        if ocupados:
            st.caption(":material/block: Ocupados esa franja: "
                       + _esc(", ".join(f["nom"] for f in ocupados)))


def _radar_scan(grupo, lunes, staff, tidx):
    """Escanea la semana vista y devuelve (choques, sin_cumplir, marcas).

    `marcas` = {(usuario, dia): {"choque", "cert"}} → para que el TABLERO pinte
    DÓNDE está el problema (v292). Antes la KPI decía "Choques de turno: 1" en rojo
    y el tablero no señalaba la celda: había que abrir el Radar para enterarse.
    El dato ya se calculaba aquí y se tiraba.

    ⚠️ El valor es un CONJUNTO, no una etiqueta (v294). En v292 el choque "ganaba"
    al cert en la misma celda y eso ESCONDÍA un problema. Ahora la celda lleva los
    dos anillos y no se pierde nada. (El contador del Radar sigue sin coincidir con
    el nº de anillos, y es correcto: un cert vencido en un proyecto asignado dos
    días es 1 problema y 2 celdas. Son unidades distintas, no una incoherencia.)

    Reusado por el radar, por los KPIs y por el tablero (un solo escaneo, v280/v282).
    """
    from core import credentials
    datos = R.get_semana(grupo, lunes)
    choques, sin_cumplir, _seen = [], [], set()
    marcas, _comp = {}, {}          # _comp: cachea compliance por (usuario, proyecto)
    for u in staff:
        usr = u["Usuario"]
        nom = u.get("Nombre") or usr
        for d in R.DIAS:
            items = R.celda_items(datos, usr, d)
            ov = False
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    if _solapa(items[i]["ini"], items[i]["fin"], items[j]["ini"], items[j]["fin"]):
                        ov = True
                        break
                if ov:
                    break
            if ov:
                marcas.setdefault((usr, d), set()).add("choque")
                _lbls = " y ".join(R.etiqueta_de(it["asig"], tidx) for it in items)
                choques.append(f"{nom} · {R.DIAS_LABEL[d]} "
                               f"{R.fecha_de_dia(lunes, d).strftime('%d/%m')}: {_lbls} se solapan")
            for it in items:
                if it["asig"] in R.ESTADOS:
                    continue
                pid = R.proyecto_de(it["asig"], tidx)
                if not pid:
                    continue
                _k = (usr, pid)
                if _k not in _comp:              # una sola consulta por persona×proyecto
                    prj = P.get_project(pid)
                    certs = [c.strip() for c in str((prj or {}).get("CertsReq", "")).split(";")
                             if c.strip()]
                    _comp[_k] = credentials.compliance(usr, certs) if certs else None
                comp = _comp[_k]
                if comp is None or comp["cumple"]:
                    continue
                # ⚠️ La marca va SIEMPRE, aunque el aviso ya se haya listado: `_seen`
                # evita repetir la MISMA línea en el radar, pero cada día afectado
                # tiene su propia celda que señalar.
                marcas.setdefault((usr, d), set()).add("cert")
                if _k in _seen:
                    continue
                _seen.add(_k)
                faltan = [t for t, e in comp["por_tipo"].items() if e in ("vencido", "falta")]
                sin_cumplir.append(f"{nom} → {R.etiqueta_de(it['asig'], tidx)}: "
                                   + ", ".join(faltan))
    return choques, sin_cumplir, marcas


def _radar_personal(grupo, lunes, staff, tidx, scan=None):
    """Radar de personal: choques de turno + certificados que bloquean (v280).
    v287: se abre desde la fila de herramientas del Panel (ya no es un expander)."""
    # ⚠️ `_radar_scan` devuelve 3 elementos desde v292 (el 3º son las marcas del
    # tablero). Se indexa en vez de desempaquetar para no romper al añadir más.
    _sc = scan if scan is not None else _radar_scan(grupo, lunes, staff, tidx)
    choques, sin_cumplir = _sc[0], _sc[1]
    n = len(choques) + len(sin_cumplir)
    with st.container():   # v287: vive en la fila de herramientas del Panel
        if not n:
            st.success("Sin choques de turno ni certificados que bloqueen esta semana.")
            return
        if choques:
            st.markdown("**:orange[:material/warning:] Choques de turno:**")
            for c in choques:
                st.markdown(f"- {_esc(c)}")
        if sin_cumplir:
            st.markdown("**:red[:material/block:] Certificados que bloquean:**")
            for c in sin_cumplir:
                st.markdown(f"- {_esc(c)}")


def _ficha_rapida(grupo, usuario):
    """Tarjeta compacta de una persona (al clic en su nombre, v282): contacto, asignación
    de hoy (con franja), certificados y un botón a su ficha 360° completa."""
    from core import credentials
    u = auth.get_user(usuario) or {}
    nom = u.get("Nombre") or usuario
    with st.container(border=True):
        cA, cB = st.columns([5, 1])
        cA.markdown(f"**{_esc(nom)}**"
                    + (f" · {_esc(u.get('Rol', ''))}" if u.get("Rol") else ""))
        if cB.button("✕", key="fp_close"):
            st.session_state.pop("_panel_ficha", None)
            st.rerun()
        _cont = []
        if str(u.get("Email", "")).strip():
            _cont.append(f":material/mail: {_esc(u.get('Email'))}")
        if str(u.get("TelegramChatID", "")).strip():
            _cont.append(":material/send: Telegram")
        st.caption(" · ".join(_cont) if _cont else ":material/warning: Sin contacto registrado")

        aa = R.asignaciones_dia(grupo, usuario)
        if aa:
            _h = " · ".join(
                a["etiqueta"] + (f" {R.franja_label(a['ini'], a['fin'])}"
                                 if R.franja_label(a["ini"], a["fin"]) else "")
                for a in aa if a.get("etiqueta"))
            st.markdown(f":material/today: **Hoy:** {_esc(_h)}")
        else:
            st.caption(":material/today: Hoy: sin asignación")

        try:
            creds = credentials.list_for(usuario)
            _ic = {"vigente": "🟢", "por_vencer": "🟡", "vencido": "🔴"}
            bits = [f"{_ic.get(credentials.status(c.get('Vencimiento')) or 'vigente', '🟢')} "
                    f"{c.get('Tipo')}" for c in creds]
            st.caption(":material/badge: " + (" · ".join(bits) if bits else "Sin certificados"))
        except Exception:
            pass

        if st.button("→ Ver ficha completa", key="fp_full", use_container_width=True):
            st.session_state["gp_fichasel"] = f"{nom} ({usuario})"
            st.session_state["_admin_nav_pending"] = ("planificacion", "👷 Usuarios")
            st.rerun()


def _panel_kpis(grupo, lunes, staff, datos, choques, sin_cumplir):
    """Fila de KPIs del Panel, con el kit de diseño COPEX (v282/v283)."""
    from core import timeclock
    from core import theme
    ab = timeclock.open_now(grupo) if timeclock.is_configured() else []
    fich = len({(s["usuario"] or s["nombre"]) for s in ab})
    en_prj = len({(s["usuario"] or s["nombre"]) for s in ab
                  if s["tipo"] == timeclock.TIPO_PROYECTO})
    off = (clock.today() - lunes).days
    d = R.DIAS[off] if 0 <= off <= 4 else None
    libres = ([u for u in staff if not R.celda_items(datos, u["Usuario"], d)]
              if d else [])
    theme.kpi_row([
        ("Fichados ahora", fich, f"{en_prj} en un proyecto", theme.VERDE if fich else theme.GRIS_TXT),
        ("Libres hoy", (len(libres) if d else "—"),
         (", ".join((u.get("Nombre") or u["Usuario"]) for u in libres[:2]) +
          ("…" if len(libres) > 2 else "")) if libres else ("sin huecos" if d else "fin de semana"),
         theme.AZUL),
        ("Choques de turno", len(choques), "franjas que se solapan",
         theme.ROJO if choques else theme.GRIS_TXT),
        ("Certs que bloquean", len(sin_cumplir), "asignado sin cumplir",
         theme.AMBAR if sin_cumplir else theme.GRIS_TXT),
    ])


def render_planificacion(grupo):
    # ⚠️ SIN cabecera propia: `home_ui._sub_header` ya pinta "## Planificación · Panel"
    # justo encima. Un "#### Panel de personal" aquí repetía el título en la misma
    # pantalla (mismo caso que el % de avance duplicado de v212).
    if not R.is_configured():
        st.warning("La planificación necesita Google Sheets configurado.")
        return

    staff = _staff(grupo)
    if not staff:
        st.info("Aún no tienes personal de campo. Créalo en :material/build: Usuarios de campo.")
        return

    lunes = _semana_activa()
    tidx  = R.trabajos_idx(grupo)
    datos = R.get_semana(grupo, lunes)

    # ── KPIs + estado en vivo (un solo escaneo del radar, reusado en los KPIs) ──
    _scan = _radar_scan(grupo, lunes, staff, tidx)
    _panel_kpis(grupo, lunes, staff, datos, _scan[0], _scan[1])

    # ── Ficha rápida (aparece al tocar un nombre en el tablero) ──
    if st.session_state.get("_panel_ficha"):
        _ficha_rapida(grupo, st.session_state["_panel_ficha"])

    # ── BARRA: semana + vista + copiar, en UNA fila (v291) ──────────────────
    # Antes eran CUATRO bandas apiladas entre los KPIs y el tablero (nav de semana,
    # cobertura, toggle de vista y un caption). Era lo que quedaba del efecto "lista"
    # después de v287: el tablero —a lo que se viene— arrancaba media pantalla abajo.
    # El caption pasó a `help` del toggle: útil el primer día, ruido a partir del segundo.
    # El radio va DENTRO de una columna = 1 solo nivel (no son columnas anidadas).
    b1, b2, b3, b4, b5 = st.columns([1, 3, 1, 4, 3])
    if b1.button("◀", key="ros_prev", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes - timedelta(days=7)).isoformat()
        st.rerun()
    b2.markdown(f"<div style='text-align:center;font-weight:700;font-size:16px;"
                f"padding-top:6px'>{R.rango_label(lunes)}</div>", unsafe_allow_html=True)
    if b3.button("▶", key="ros_next", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes + timedelta(days=7)).isoformat()
        st.rerun()
    _vista = b4.radio(
        "vista", ["📋 Tablero", "👀 Disponibilidad"], horizontal=True,
        key="cpxseg_vista", label_visibility="collapsed",   # cpxseg_ = segmentado del kit
        help="En el tablero: toca una **celda** para asignar o editar (con su franja "
             "horaria); toca un **nombre** para abrir su ficha rápida.",
        format_func=lambda o: {
            "📋 Tablero": ":material/calendar_view_week: Tablero",
            "👀 Disponibilidad": ":material/event_available: Disponibilidad"}.get(o, o))
    if b5.button(":material/assignment: Copiar semana anterior", key="ros_copy",
                 use_container_width=True):
        ok, msg = R.copiar_semana(grupo, lunes - timedelta(days=7), lunes)
        (flash.exito if ok else st.warning)(msg)
        if ok:
            st.rerun()

    # ── Cobertura del día (esto es DATO, no chrome: se queda) ──
    _cobertura_hoy(lunes, staff, datos)

    if _vista == "👀 Disponibilidad":
        _dd = st.selectbox("¿Quién está libre el…?", R.DIAS, key="panel_libredia",
                           format_func=lambda d: f"{R.DIAS_LABEL[d]} "
                           f"{R.fecha_de_dia(lunes, d).strftime('%d/%m')}")
        _libres = [(u.get("Nombre") or u["Usuario"]) for u in staff
                   if not R.celda_items(datos, u["Usuario"], _dd)]
        if _libres:
            st.success(f":material/person_check: **{len(_libres)}** libres el "
                       f"{R.DIAS_LABEL[_dd]}: " + _esc(", ".join(_libres)))
        else:
            st.warning(f":material/warning: Nadie libre el {R.DIAS_LABEL[_dd]}.")
        st.caption("Verde = libre · gris = ocupado (con su franja horaria).")
        st.markdown(_disponibilidad_html(staff, lunes, datos, tidx), unsafe_allow_html=True)
    else:
        _tablero_editable(grupo, lunes, staff, datos, tidx, marcas=_scan[2])
        # ── El día abierto desde una celda (v387), a ancho completo bajo el tablero ──
        # ⚠️ Se guarda la SEMANA junto a la persona y el día: al navegar de semana,
        # el mismo (usuario, día) sería otra fecha con otros datos — se cierra sola
        # en vez de enseñar el día equivocado. Igual si esa persona ya no está.
        _da = st.session_state.get("_dia_abierto") or {}
        _u = next((x for x in staff if x["Usuario"] == _da.get("u")), None)
        if _u and _da.get("wk") == lunes.isoformat() and _da.get("d") in R.DIAS:
            _vista_dia(grupo, lunes, _u["Usuario"], _u.get("Nombre") or _u["Usuario"],
                       _da["d"], datos, tidx)
        elif _da:
            st.session_state.pop("_dia_abierto", None)

    # ── HERRAMIENTAS: una fila, un panel (v287) ─────────────────────────────
    # Antes eran 5 bloques APILADOS (asignación, radar, en vivo, plan-vs-real, catálogo)
    # y el Panel se leía como una lista. Ahora es una fila de accesos y solo se abre
    # el elegido — la pantalla queda: KPIs → vista → tablero → una herramienta.
    _n_rad = len(_scan[0]) + len(_scan[1])
    # v293: «En vivo» y «Plan vs real» eran la misma pregunta a distinta resolución
    # de tiempo → una sola herramienta «Cumplimiento» (lo vivo va en cada fila).
    _TOOLS = [("asignar", ":material/bolt: Asignar"),
              ("radar", ":material/radar: Radar" + (f" ({_n_rad})" if _n_rad else "")),
              ("cumpl", ":material/fact_check: Cumplimiento"),
              ("cat", ":material/palette: Trabajos")]
    st.markdown("")
    _tc = st.columns(len(_TOOLS))
    _cur = st.session_state.get("_panel_tool", "")
    for _i, (_k, _lbl) in enumerate(_TOOLS):
        if _tc[_i].button(_lbl, key=f"ptool_{_k}", use_container_width=True):
            st.session_state["_panel_tool"] = "" if _cur == _k else _k
            st.rerun()
    if _cur:
        with st.container(border=True):
            if _cur == "asignar":
                _asignacion_inteligente(grupo, lunes, staff, tidx)
            elif _cur == "radar":
                _radar_personal(grupo, lunes, staff, tidx, scan=_scan)
            elif _cur == "cumpl":
                _cumplimiento(grupo, lunes, staff, tidx)
            else:
                _catalogo(grupo)


def _cumplimiento(grupo, lunes, staff, tidx):
    """Plan vs real + estado EN VIVO en UNA sola vista (v293).

    Antes eran dos herramientas que respondían la MISMA pregunta —¿se está
    cumpliendo lo planificado?— a distinta resolución de tiempo: «En vivo»
    (¿quién trabaja ahora mismo?) y «Plan vs real» (¿se cumplió el día?). El
    solape era grande: «En vivo» ya calculaba «asignados hoy y sin fichar», que
    es una de las ramas de «Plan vs real», y repetía la métrica «Fichados ahora»
    que YA es la primera tarjeta KPI del Panel.

    Lo vivo NO es un bloque aparte: es una columna más de cada fila cuando el día
    elegido es HOY. Así una sola línea dice plan + real + cuánto lleva fichado,
    en vez de obligar a mirar en dos sitios para saber lo mismo de una persona.

    ⚠️ `proyectos_por_usuario_dia` DESCARTA los fichajes sin proyecto, así que de
    ahí no se puede deducir «está en jornada pero no ha imputado obra» — que era
    la única señal que vivía SOLO en «En vivo» y se habría perdido en la fusión.
    Para HOY se rescata con `open_now` (sesiones abiertas). Para días PASADOS no
    se puede distinguir: ahí «sin fichar» puede ser «fichó sin imputar», y el
    texto NO afirma lo contrario.
    """
    from core import timeclock
    with st.container():   # v287: vive en la fila de herramientas del Panel
        if not timeclock.is_configured():
            st.caption("Necesita el fichaje configurado.")
            return
        # Día a comparar: hoy si cae en la semana vista, si no el lunes.
        hoy = clock.today()
        _idx_def = (hoy - lunes).days if 0 <= (hoy - lunes).days <= 4 else 0
        _dsel = st.radio("Día", R.DIAS, index=_idx_def, horizontal=True,
                         format_func=lambda d: f"{R.DIAS_LABEL[d]} "
                         f"{R.fecha_de_dia(lunes, d).strftime('%d/%m')}",
                         key="cpxseg_cumpl_dia", label_visibility="collapsed")
        fecha = R.fecha_de_dia(lunes, _dsel)
        es_hoy = (fecha == hoy)
        datos = R.get_semana(grupo, lunes)
        real  = timeclock.proyectos_por_usuario_dia(grupo, fecha)

        # ── Capa EN VIVO (solo si el día elegido es HOY: ayer no hay nadie fichado) ──
        vivo = {}
        if es_hoy:
            for s in timeclock.open_now(grupo):
                _k = s["usuario"] or s["nombre"]
                _v = vivo.setdefault(_k, {"prj": None, "gen": None})
                _v["prj" if s["tipo"] == timeclock.TIPO_PROYECTO else "gen"] = s

        def _hm(seg):
            h, m = seg // 3600, (seg % 3600) // 60
            return f"{h}h{m:02d}" if h else f"{m}min"

        def _ahora(usr):
            """Sufijo en vivo: cuánto lleva fichado. '' si no está fichado o no es hoy."""
            _v = vivo.get(usr)
            if not _v:
                return ""
            _s = _v["prj"] or _v["gen"]
            return f" · :green[en curso {_hm(_s['segundos'])}]"

        if es_hoy:
            _n_prj = sum(1 for v in vivo.values() if v["prj"])
            if vivo:
                st.markdown(f":green[:material/sensors:] **{len(vivo)}** fichados ahora "
                            f"· {_n_prj} en un proyecto")
            else:
                st.caption(":material/sensors: Nadie fichado en este momento.")

        n_ok = n_desvio = n_sin = 0
        filas = []
        for u in staff:
            usr = u["Usuario"]
            nom = u.get("Nombre") or usr
            plan_asigs = R.celda_asigs(datos, usr, _dsel)          # v274: varias por día
            plan_pids = {R.proyecto_de(a, tidx) for a in plan_asigs if R.proyecto_de(a, tidx)}
            plan_lbl = ", ".join(R.etiqueta_de(a, tidx) for a in plan_asigs
                                 if R.proyecto_de(a, tidx)) or "—"
            solo_estados = bool(plan_asigs) and all(a in R.ESTADOS for a in plan_asigs)
            trabajos_sin_prj = [a for a in plan_asigs
                                if a not in R.ESTADOS and not R.proyecto_de(a, tidx)]
            reales = real.get(usr, [])
            real_pids = {e["pid"] for e in reales if e["pid"]}
            real_txt = ", ".join(e["nombre"] for e in reales) or "—"

            _v = vivo.get(usr)
            _solo_jornada = bool(_v and _v["gen"] and not _v["prj"])   # fichado sin imputar

            if plan_pids:
                falta = plan_pids - real_pids
                extra = real_pids - plan_pids
                if not real_pids:
                    n_sin += 1
                    if _solo_jornada:
                        # ⚠️ La señal que solo existía en «En vivo»: está trabajando,
                        # pero sus horas no van a ninguna obra. Es el olvido típico.
                        filas.append((":orange[:material/timer:]", nom,
                                      f"asignado a {plan_lbl} · fichado en jornada pero "
                                      f"SIN imputar obra{_ahora(usr)}"))
                    else:
                        filas.append((":orange[:material/warning:]", nom,
                                      f"asignado a {plan_lbl} · sin fichar aún"))
                elif not falta:
                    n_ok += 1
                    _ex = f" (+ también {real_txt})" if extra else ""
                    filas.append((":green[:material/check_circle:]", nom,
                                  f"{plan_lbl} — fichó donde tocaba{_ex}{_ahora(usr)}"))
                elif plan_pids & real_pids:
                    n_desvio += 1
                    filas.append((":orange[:material/warning:]", nom,
                                  f"asignado a {plan_lbl} · fichó en {real_txt} "
                                  f"(faltan algunas){_ahora(usr)}"))
                else:
                    n_desvio += 1
                    filas.append((":red[:material/cancel:]", nom,
                                  f"asignado a {plan_lbl} · fichó en {real_txt}{_ahora(usr)}"))
            elif solo_estados:
                if reales or _solo_jornada:
                    _est = ", ".join(R.etiqueta_de(a, tidx) for a in plan_asigs)
                    _d = real_txt if reales else "jornada (sin obra)"
                    filas.append((":blue[:material/info:]", nom,
                                  f"marcado {_est} pero fichó en {_d}{_ahora(usr)}"))
                # OFF/Leave sin fichar: correcto, no se lista
            elif trabajos_sin_prj:                          # trabajo(s) sin enlace a PRJ
                _tr = ", ".join(R.etiqueta_de(a, tidx) for a in trabajos_sin_prj)
                filas.append(("—", nom, f"{_tr} (sin proyecto que comparar)"
                              + (f" · fichó en {real_txt}" if reales else "")
                              + _ahora(usr)))
            elif reales:                                    # sin plan pero fichó
                filas.append((":material/help:", nom,
                              f"sin asignación · fichó en {real_txt}{_ahora(usr)}"))
            elif _solo_jornada:                             # sin plan y sin imputar
                filas.append((":orange[:material/timer:]", nom,
                              f"sin asignación · fichado en jornada, sin imputar obra"
                              f"{_ahora(usr)}"))

        st.markdown(f":green[:material/check_circle:] {n_ok} donde tocaba  ·  :red[:material/cancel:] {n_desvio} en otro sitio  ·  "
                    f":orange[:material/warning:] {n_sin} sin fichar")
        if not filas:
            st.caption("Nada que comparar este día (sin asignaciones a proyecto ni fichajes).")
        for ic, nom, txt in filas:
            st.markdown(f"{ic}  **{_esc(nom)}** — {_esc(txt)}")


def render_board_readonly(grupo, resaltar_usuario=""):
    """Tablero de la semana en SOLO LECTURA (para el campo: ve toda la cuadrilla).

    Decisión del usuario: el campo ve el board completo para saber con quién va a
    cada obra. Resalta su propia fila.
    """
    if not R.is_configured():
        return
    staff = _staff(grupo)
    if not staff:
        return
    lunes = _semana_activa()
    tidx  = R.trabajos_idx(grupo)
    datos = R.get_semana(grupo, lunes)

    c1, c2, c3 = st.columns([1, 3, 1])
    if c1.button("◀", key="rosf_prev", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes - timedelta(days=7)).isoformat()
        st.rerun()
    c2.markdown(f"<div style='text-align:center;font-weight:700;padding-top:6px'>"
                f"{R.rango_label(lunes)}</div>", unsafe_allow_html=True)
    if c3.button("▶", key="rosf_next", use_container_width=True):
        st.session_state["ros_lunes"] = (lunes + timedelta(days=7)).isoformat()
        st.rerun()
    st.markdown(_grid_html(staff, lunes, datos, tidx, resaltar_usuario),
                unsafe_allow_html=True)


def _guardar_celda(grupo, lunes, usuario, datos, dias_destino, items, nota):
    """Escribe la MISMA asignación en UNO O VARIOS días de la semana (v301).

    `dias_destino` = lista de claves de `R.DIAS`. Antes era `dia` + un booleano
    `toda_semana`: o un día o los cinco, sin término medio — así que planificar a
    alguien tres días obligaba a abrir tres celdas. Ahora se eligen los días que sean.

    `items` = [{'asig','ini','fin'}] (varias asignaciones por día, cada una con su
    franja, v277). Se escribe la semana COMPLETA en 1 sola llamada, así que N días
    cuestan lo mismo que uno. `guardar_persona` omite las vacías → items vacío +
    nota vacía = limpiar esos días.
    """
    sem = dict(datos.get(usuario, {}) or {})
    cell = {"items": [{"a": it["asig"], "i": it.get("ini", ""), "f": it.get("fin", "")}
                      for it in (items or []) if it.get("asig")],
            "nota": nota}
    for d in (dias_destino or []):
        sem[d] = dict(cell)
    return R.guardar_persona(grupo, lunes, usuario, sem)


def _cumplimiento_celda(usuario, pid):
    """Dentro del popover: avisa si el usuario cumple los certificados que EXIGE el
    proyecto (CertsReq). Reusa `credentials.compliance` (v219). Silencioso si el
    proyecto no exige certificados."""
    try:
        prj = P.get_project(pid)
        certs = [c.strip() for c in str((prj or {}).get("CertsReq", "")).split(";")
                 if c.strip()]
        if not certs:
            return
        from core import credentials
        comp = credentials.compliance(usuario, certs)
        _ic = {"vigente": "🟢", "por_vencer": "🟡", "vencido": "🔴", "falta": "⚪"}
        bits = " · ".join(f"{_ic.get(e, '⚪')} {t}" for t, e in comp["por_tipo"].items())
        if comp["cumple"]:
            st.success(f"Cumple los certificados del proyecto: {bits}")
        else:
            st.warning(f":material/warning: No cumple todos los certificados: {bits}")
    except Exception:
        pass


def _tablero_editable(grupo, lunes, staff, datos, tidx, marcas=None):
    """Board del admin EDITABLE EN SITIO (v217): cada celda es un `st.popover`
    coloreado con el color de su trabajo (clase `st-key-<key>` sobre el trigger —
    verificado en vivo antes de construir). Al tocar la celda se edita AHÍ MISMO
    (asignación + nota, con «aplicar a toda la semana») y, si el trabajo enlaza a un
    proyecto, se salta a su detalle — sin salir del tablero ni un formulario aparte.
    Una celda vacía (＋) también asigna en sitio. Reemplaza el editor por-persona de
    abajo (v159). El board del campo sigue siendo el HTML de `_grid_html`.
    """
    dias = R.DIAS
    _wk = lunes.strftime("%Y%m%d")   # las keys llevan la SEMANA: al navegar semanas, una
                                     # celda no hereda la selección de otra (evita pisar datos).
    op = _opciones(grupo, tidx)
    op_real = [(e, v) for e, v in op if v != ""]        # sin el neutro (para el multiselect)
    etq = [e for e, _ in op_real]
    val_by_etq = {e: v for e, v in op_real}
    etq_by_val = {v: e for e, v in op_real}

    # 0) DENSIDAD del tablero (v287): el board se veía aireado porque cada celda es un
    # botón/popover con el padding por defecto de Streamlit. Se compacta el trigger para
    # que la rejilla se lea como una tabla (como el diseño), sin perder la edición en sitio.
    st.markdown("""
<style>
[class*="st-key-roscel_"] button {
  padding: 4px 7px !important; min-height: 0 !important; border-radius: 7px !important;
  line-height: 1.2 !important;
}
[class*="st-key-roscel_"] button p {
  font-size:12px !important; font-weight: 600 !important;
  text-align: left !important; width: 100%; white-space: normal !important;
}
[class*="st-key-pnm_"] button {
  padding: 4px 8px !important; min-height: 0 !important;
  background: transparent !important; border: none !important;
  border-left: 3px solid #2e6da4 !important; border-radius: 0 !important;
}
[class*="st-key-pnm_"] button p {
  font-size:13px !important; font-weight: 700 !important;
  text-align: left !important; width: 100%; color: #1e4e79;
}
[class*="st-key-pnm_"] button:hover { background: #f4f7fb !important; }
</style>""", unsafe_allow_html=True)

    # 1) CSS de color por celda (color de la 1ª asignación; las vacías, tenues) +
    #    ANILLO de conflicto (v292): rojo = choque de turno, ámbar = certificado que
    #    bloquea. Va como `box-shadow` y NO como `border` a propósito: el borde ya lo
    #    usa el color del trabajo, y un box-shadow no desplaza la rejilla.
    #    ⚠️ Mecanismo medido en vivo antes de escribirlo (el anillo convive con el
    #    background del trabajo; la celda sin marca queda con `box-shadow: none`).
    from core import theme
    marcas = marcas or {}
    css = []
    for pi, u in enumerate(staff):
        for di, d in enumerate(dias):
            idx = pi * len(dias) + di
            _asigs = R.celda_asigs(datos, u["Usuario"], d)
            asig = _asigs[0] if _asigs else ""
            key = f"roscel_{_wk}_{idx}"
            # Anillos: rojo DENTRO (choque) y ámbar FUERA (cert). `box-shadow` admite
            # varias capas, así que una celda con los dos problemas los enseña LOS DOS.
            # v292 daba prioridad al rojo y eso escondía el cert (verificado en vivo).
            _m = marcas.get((u["Usuario"], d)) or set()
            _capas = []
            if "choque" in _m:
                _capas.append(f"0 0 0 2px {theme.ROJO}")
            if "cert" in _m:
                _capas.append(f"0 0 0 {'4px' if 'choque' in _m else '2px'} {theme.AMBAR}")
            _sombra = f"box-shadow:{','.join(_capas)}!important;" if _capas else ""
            if asig:
                bg = R.color_de(asig, tidx)
                css.append(f".st-key-{key} button{{background:{bg}!important;"
                           f"color:{_texto_sobre(bg)}!important;border-color:{bg}!important;"
                           f"{_sombra}}}")
            else:
                # Celda vacía: fuera el chevron del popover — con solo el ＋ se lee
                # como un hueco donde asignar, no como un desplegable.
                # ⚠️ El chevron NO es un <svg>: es un Material Symbol de FUENTE
                # (span[data-testid=stIconMaterial]). Se usa el data-testid, que es
                # contrato de Streamlit; las clases `st-emotion-cache-*` cambian de
                # versión a versión. Verificado en vivo.
                css.append(f".st-key-{key} button{{background:#f8fafc!important;"
                           f"color:#b6c0cd!important;border:1px dashed #e2e8f0!important;"
                           f"{_sombra}}}"
                           f".st-key-{key} button [data-testid='stIconMaterial']"
                           f"{{display:none!important;}}")
    if css:
        st.markdown("<style>" + "".join(css) + "</style>", unsafe_allow_html=True)
    _leyenda = [f":material/schedule: la hora solo aparece si difiere del turno "
                f"({R.TURNO_DEFAULT[0]}–{R.TURNO_DEFAULT[1]})"]
    if marcas:
        _leyenda.insert(0, ":red[:material/error:] borde rojo = choque de turno  ·  "
                           ":orange[:material/shield:] borde ámbar = certificado que "
                           "bloquea (una celda puede llevar **los dos**)")
    st.caption("  ·  ".join(_leyenda))

    # 2) Cabecera (persona + días)
    anchos = [1.4] + [1] * len(dias)
    h = st.columns(anchos)
    # Cabecera de la rejilla (v301): 13.5px + seminegrita y TODO centrado — a 12px
    # gris claro apenas se leía, y "Persona" iba alineada a la izquierda mientras los
    # días ya estaban centrados, así que la fila no cuadraba.
    _CAB = ("font-size:13px;font-weight:600;color:#5b6472;"
            "text-align:center;margin-bottom:6px")
    h[0].markdown(f"<div style='{_CAB}'>Persona</div>", unsafe_allow_html=True)
    for i, d in enumerate(dias):
        f = R.fecha_de_dia(lunes, d)
        h[i + 1].markdown(f"<div style='{_CAB}'>{R.DIAS_LABEL[d]} "
                          f"{f.strftime('%d/%m')}</div>", unsafe_allow_html=True)

    # 3) Filas: nombre + una celda-popover por día
    for pi, u in enumerate(staff):
        usuario = u["Usuario"]
        nom = u.get("Nombre") or usuario
        cols = st.columns(anchos)
        if cols[0].button(nom, key=f"pnm_{_wk}_{pi}", use_container_width=True,
                          help="Ver ficha rápida de la persona"):
            st.session_state["_panel_ficha"] = usuario
            st.rerun()
        for di, d in enumerate(dias):
            idx = pi * len(dias) + di
            col = cols[di + 1]
            items_cur = R.celda_items(datos, usuario, d)              # v277: con franja
            asigs = [it["asig"] for it in items_cur]
            fr_cur = {it["asig"]: (it["ini"], it["fin"]) for it in items_cur}
            nota = R.celda(datos, usuario, d).get("nota", "")
            # Etiqueta del trigger (v295). Antes se pegaban todas las etiquetas CON su
            # franja y la celda desbordaba a 2 líneas ilegibles:
            #     "prueba2 7:00–15:30 · prueba 3 7:00–15:30"
            # Dos arreglos:
            #  (a) la franja SOLO si difiere del turno estándar — repetir "7:00–15:30"
            #      en cada chip gastaba medio ancho diciendo «lo normal», y de paso
            #      escondía las que SÍ son excepción, que es lo único que hay que ver.
            #  (b) con 3+ trabajos no entra ni así → el primero y un contador; el
            #      resto se ve (y se edita) al abrir la celda.
            _trig = []
            for it in items_cur:
                _fl = R.franja_label(it["ini"], it["fin"])
                if (it["ini"], it["fin"]) == R.TURNO_DEFAULT:
                    _fl = ""
                _trig.append(R.etiqueta_de(it["asig"], tidx) + (f" {_fl}" if _fl else ""))
            et = f"{_trig[0]} +{len(_trig) - 1}" if len(_trig) > 2 else " · ".join(_trig)
            with col.popover(et or "＋", key=f"roscel_{_wk}_{idx}", use_container_width=True):
                f = R.fecha_de_dia(lunes, d)
                st.caption(f"**{_esc(nom)}** · {R.DIAS_LABEL[d]} {f.strftime('%d/%m')}")
                # «Ver el día» → el detalle se pinta DEBAJO del tablero, a ancho
                # completo. Aquí dentro no: el popover mide ~300 px y una línea de
                # tiempo con sus horas no se lee (se midieron las tres opciones).
                # ⚠️ El rerun cierra el popover, que es lo que se quiere: se ha ido
                # a MIRAR el día, no a editarlo.
                # Se ofrece con UNA asignación además de con varias: el motivo del
                # botón es el día doble, pero esconderlo en las celdas simples haría
                # que la función solo se descubra por accidente, y con una sola
                # también dice su horario, su duración y la nota.
                if items_cur and st.button(":material/timeline: Ver el día",
                                           key=f"pvd_{_wk}_{idx}",
                                           use_container_width=True):
                    st.session_state["_dia_abierto"] = {"u": usuario, "d": d,
                                                        "wk": lunes.isoformat()}
                    st.rerun()
                _def = [etq_by_val[a] for a in asigs if a in etq_by_val]
                _sel = st.multiselect("Asignaciones del día (puedes elegir varias)",
                                      etq, default=_def, key=f"pva_{_wk}_{idx}")
                _selvals = [val_by_etq[e] for e in _sel]
                # Por cada asignación: si es PROYECTO/TRABAJO → franja horaria (default 7:00–15:30)
                # + aviso de cumplimiento de certificados. Los estados (OFF/Leave) no llevan franja.
                _items = []
                for _v in _selvals:
                    if _v in R.ESTADOS:
                        _items.append({"asig": _v, "ini": "", "fin": ""})
                        continue
                    _pv = R.proyecto_de(_v, tidx)
                    if _pv:
                        _cumplimiento_celda(usuario, _pv)
                    _ci, _cf = fr_cur.get(_v, R.TURNO_DEFAULT)
                    _c1, _c2 = st.columns(2)
                    _ti = _c1.time_input(f"{R.etiqueta_de(_v, tidx)} · inicio",
                                         value=_to_time(_ci, R.TURNO_DEFAULT[0]),
                                         key=f"pvi_{_wk}_{idx}_{_v}", step=900)
                    _tf = _c2.time_input(f"{R.etiqueta_de(_v, tidx)} · fin",
                                         value=_to_time(_cf, R.TURNO_DEFAULT[1]),
                                         key=f"pvf_{_wk}_{idx}_{_v}", step=900)
                    _items.append({"asig": _v, "ini": _ti.strftime("%H:%M"),
                                   "fin": _tf.strftime("%H:%M")})
                _nota = st.text_input("Nota (para todo el día)", value=nota, key=f"pvn_{_wk}_{idx}",
                                      placeholder="vehículo, equipo…")
                # v301: planificar VARIOS días de una. Antes era un check "toda la
                # semana" (o uno, o los cinco), así que asignar a alguien 2-3 días
                # obligaba a abrir una celda por día. Arranca con el día tocado.
                # v302: el atajo de la semana completa VUELVE como check, no como
                # botón que rellene el selector: eso exigiría `st.rerun()` para poder
                # escribir la clave de un widget ya instanciado (regla v111) y el
                # rerun CIERRA el popover — habría que reabrirlo para guardar. El
                # check va ANTES para poder deshabilitar el selector cuando manda él.
                _all = st.checkbox("Toda la semana (Lun–Vie)", key=f"pvwa_{_wk}_{idx}")
                _dd = st.multiselect(
                    "Aplicar a estos días", R.DIAS, default=[d], key=f"pvw_{_wk}_{idx}",
                    disabled=_all,
                    format_func=lambda x: f"{R.DIAS_LABEL[x]} "
                                          f"{R.fecha_de_dia(lunes, x).strftime('%d/%m')}")
                _destino = list(R.DIAS) if _all else _dd
                if len(_destino) > 1:
                    st.caption(f":material/content_copy: Se guardará igual en "
                               f"**{len(_destino)} días**.")
                if st.button(":material/save: Guardar", key=f"pvs_{_wk}_{idx}", type="primary",
                             use_container_width=True, disabled=not _destino):
                    ok, msg = _guardar_celda(grupo, lunes, usuario, datos, _destino,
                                             _items, _nota)
                    if ok:
                        # cada PROYECTO agendado mete al usuario como asignado del proyecto
                        # → acceso desde su cuenta (no quita a nadie de otros).
                        for _it in _items:
                            _pv = R.proyecto_de(_it["asig"], tidx)
                            if _pv:
                                try:
                                    P.add_field_user(_pv, usuario)
                                except Exception:
                                    pass
                        st.rerun()
                    else:
                        st.error(msg)
                # Abrir cada proyecto elegido (un botón por proyecto).
                for _v in _selvals:
                    _pv = R.proyecto_de(_v, tidx)
                    if _pv and st.button(f"→ {R.etiqueta_de(_v, tidx)}",
                                         key=f"pvo_{_wk}_{idx}_{_v}", use_container_width=True):
                        st.session_state["_prjsel_pending"] = _pv
                        st.session_state["_admin_nav_pending"] = ("proyectos", "📊 Proyectos")
                        st.rerun()
            if nota:
                col.caption(nota)


def _grid_html(staff, lunes, datos, tidx, resaltar="") -> str:
    ths = ['<th style="text-align:left;padding:6px 8px;font-size:12px;color:#6b7280;'
           'position:sticky;left:0;background:#fff;">Persona</th>']
    for d in R.DIAS:
        f = R.fecha_de_dia(lunes, d)
        ths.append(f'<th style="padding:6px 8px;font-size:12px;color:#6b7280;'
                   f'min-width:120px;">{R.DIAS_LABEL[d]} {f.strftime("%d/%m")}</th>')
    filas = []
    for u in staff:
        usr = u["Usuario"]
        nom = u.get("Nombre") or usr
        _mio = (str(usr) == str(resaltar))
        _nbg = "#fff7e6" if _mio else "#fff"
        celdas = [f'<td style="padding:5px 8px;font-size:13px;font-weight:{"800" if _mio else "600"};'
                  f'color:#1f2937;white-space:nowrap;position:sticky;left:0;background:{_nbg};'
                  f'border-right:1px solid #eef1f5;">{"<span style=\"font-family:&#39;Material Symbols Rounded&#39;;vertical-align:-2px\">arrow_forward</span> " if _mio else ""}{_esc(nom)}</td>']
        for d in R.DIAS:
            items = R.celda_items(datos, usr, d)              # v277: con franja horaria
            nota  = R.celda(datos, usr, d).get("nota", "")
            if items:
                _chips = []
                for it in items:
                    _bg = R.color_de(it["asig"], tidx)
                    _fl = R.franja_label(it["ini"], it["fin"])
                    _fh = (f'<span style="opacity:.85;font-weight:400;"> · {_esc(_fl)}</span>'
                           if _fl else "")
                    _chips.append(
                        f'<div style="background:{_bg};color:{_texto_sobre(_bg)};'
                        f'border-radius:5px;padding:2px 5px;margin-bottom:2px;font-weight:600;">'
                        f'{_esc(R.etiqueta_de(it["asig"], tidx))}{_fh}</div>')
                cont = "".join(_chips)
                if nota:
                    cont += (f'<div style="font-size:11px;opacity:0.8;color:#4b5563;">'
                             f'{_esc(nota)}</div>')
            else:
                cont = "&nbsp;"
            celdas.append(f'<td style="padding:4px 5px;background:#fff;'
                          f'font-size:11px;line-height:1.25;vertical-align:top;">'
                          f'{cont}</td>')
        filas.append("<tr>" + "".join(celdas) + "</tr>")
    return ('<div style="overflow-x:auto;margin:10px 0;">'
            '<table style="border-collapse:separate;border-spacing:3px;width:100%;">'
            "<thead><tr>" + "".join(ths) + "</tr></thead>"
            "<tbody>" + "".join(filas) + "</tbody></table></div>")


def _opciones(grupo, tidx):
    """[(etiqueta, valor)] para el selector: neutro + PROYECTOS (directo) + trabajos
    (no-proyecto) + estados. Un proyecto ya es asignable por sí mismo (v218): no hay que
    crear un 'trabajo' que lo enlace. Los proyectos completados/cancelados no se ofrecen."""
    op = [("— sin asignar —", "")]
    try:
        for p in P.list_projects(grupo=grupo):
            if str(p.get("Estado", "")) in ("Completado", "Cancelado"):
                continue
            op.append((str(p.get("Nombre", "")), str(p.get("ID", ""))))
    except Exception:
        pass
    for r in R.list_trabajos(grupo):
        num = str(r.get("Numero", "")).strip()
        op.append((f"{num}. {r.get('Nombre','')}" if num else f"{r.get('Nombre','')}",
                   str(r.get("ID", ""))))
    for k, v in R.ESTADOS.items():
        op.append((str(v["nombre"]), k))
    return op


def _catalogo(grupo):
    with st.container():   # v287: vive en la fila de herramientas del Panel
        st.caption("Para trabajos que **no** son un proyecto: entregas, cursos, policía, "
                   "traslados… Los **proyectos se asignan directo** en el tablero (ya son un "
                   "trabajo en sí mismos), no hace falta crearlos aquí.")
        # incluir_inactivos: los desactivados SÍ se listan (para reactivarlos).
        # Los ELIMINADOS no: su fila solo existe para que el histórico del tablero
        # siga resolviendo nombre y color (v301).
        trabajos = R.list_trabajos(grupo, incluir_inactivos=True)
        _colmap = {n: h for n, h in R.PALETA}
        _colinv = {h.lower(): n for n, h in R.PALETA}      # hex → nombre, para precargar
        _edit = st.session_state.get("_trab_edit", "")
        if trabajos:
            for r in trabajos:
                tid = str(r.get("ID", ""))
                _act = str(r.get("Activo", "SI")).upper() in ("SI", "SÍ", "TRUE", "1")
                cc = st.columns([0.5, 3.6, 1.6, 1.3])
                cc[0].markdown(f"<div style='width:20px;height:20px;border-radius:5px;"
                               f"background:{r.get('Color','#2e6da4')};margin-top:4px'></div>",
                               unsafe_allow_html=True)
                _prj = str(r.get("ProyectoID", "")).strip()
                cc[1].markdown(f"**{str(r.get('Numero','')).strip()}. {r.get('Nombre','')}**"
                               + (f"  ·  :material/link: {_prj}" if _prj else "")
                               + ("" if _act else "  ·  _inactivo_"))
                if cc[2].button("Activar" if not _act else "Desactivar", key=f"trab_act_{tid}"):
                    R.set_activo_trabajo(tid, not _act)
                    st.rerun()
                if cc[3].button(":material/edit: Editar", key=f"trab_ed_{tid}"):
                    st.session_state["_trab_edit"] = "" if _edit == tid else tid
                    st.rerun()

                # Panel de edición en sitio. El BORRADO vive aquí dentro a propósito:
                # obliga a abrir la ficha antes de poder borrar (dos pasos), en vez de
                # dejar una papelera al lado de cada fila — es la lección de v139, donde
                # un clic de más borraba algo que nadie había elegido.
                if _edit == tid:
                    with st.container(border=True):
                        e1, e2, e3 = st.columns([1, 2.5, 1.5])
                        _n = e1.text_input("Número", value=str(r.get("Numero", "")),
                                           key=f"tedn_{tid}")
                        _nm = e2.text_input("Nombre", value=str(r.get("Nombre", "")),
                                            key=f"tednm_{tid}")
                        _cur = _colinv.get(str(r.get("Color", "")).lower())
                        _nombres = list(_colmap)
                        _cn = e3.selectbox("Color", _nombres, key=f"tedc_{tid}",
                                           index=_nombres.index(_cur) if _cur in _nombres else 0)
                        g1, g2 = st.columns([1, 1])
                        if g1.button(":material/save: Guardar cambios", key=f"teds_{tid}",
                                     type="primary", use_container_width=True):
                            if not _nm.strip():
                                st.error("El nombre es obligatorio.")
                            else:
                                ok, msg = R.update_trabajo(tid, {
                                    "Numero": _n.strip(), "Nombre": _nm.strip(),
                                    "Color": _colmap[_cn]})
                                (flash.exito if ok else st.error)(msg)
                                if ok:
                                    st.session_state["_trab_edit"] = ""
                                    st.rerun()
                        # v301: eliminar SIEMPRE se puede. Si tiene historia, la fila se
                        # conserva marcada (sale del catálogo y del desplegable, pero el
                        # tablero sigue resolviendo su nombre y color en las semanas ya
                        # planificadas). Se dice ANTES de pulsar, no después.
                        _usos = R.usos_de_trabajo(grupo, tid)
                        if _usos:
                            g2.caption(f":material/history: Está en **{_usos}** "
                                       f"{'día ya planificado' if _usos == 1 else 'días ya planificados'}: "
                                       f"al eliminarlo sale del catálogo, pero **el histórico se "
                                       f"conserva** tal cual.")
                        _conf = g2.checkbox("Confirmo eliminarlo", key=f"tedcf_{tid}")
                        if g2.button(":material/delete: Eliminar", key=f"tedd_{tid}",
                                     disabled=not _conf, use_container_width=True):
                            ok, msg = R.delete_trabajo(grupo, tid)
                            (flash.exito if ok else st.warning)(msg)
                            if ok:
                                st.session_state["_trab_edit"] = ""
                                st.rerun()
        else:
            st.caption("Aún no hay trabajos. Añade el primero abajo.")

        st.markdown("**:material/add: Nuevo trabajo** (no-proyecto)")
        c1, c2, c3 = st.columns([1, 2.5, 1.5])
        num = c1.text_input("Número", key="trab_num", placeholder="89")
        nom = c2.text_input("Nombre", key="trab_nom", placeholder="Entrega / Curso / Traslado…")
        colnom = c3.selectbox("Color", list(_colmap.keys()), key="trab_col")   # _colmap: arriba
        # Muestra del color con el MISMO lenguaje que la lista de arriba (cuadradito
        # de 20×20). Antes era una franja a todo el ancho que se leía como un
        # artefacto de renderizado atravesando la tarjeta, no como una muestra.
        c3.markdown(f"<div style='width:20px;height:20px;border-radius:5px;"
                    f"background:{_colmap[colnom]};border:1px solid #e3e8ef'></div>",
                    unsafe_allow_html=True)
        if st.button("Crear trabajo", key="trab_add", use_container_width=True):
            if not nom.strip():
                st.error("El nombre es obligatorio.")
            else:
                ok, res = R.add_trabajo(grupo, num, nom, _colmap[colnom], "")
                (flash.exito if ok else st.error)(
                    f"Trabajo creado ({res})." if ok else res)
                if ok:
                    st.rerun()


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _disponibilidad_html(staff, lunes, datos, tidx) -> str:
    ths = ['<th style="text-align:left;padding:6px 8px;font-size:12px;color:#6b7280;'
           'position:sticky;left:0;background:#fff;">Persona</th>']
    for d in R.DIAS:
        f = R.fecha_de_dia(lunes, d)
        ths.append(f'<th style="padding:6px 8px;font-size:12px;color:#6b7280;'
                   f'min-width:110px;">{R.DIAS_LABEL[d]} {f.strftime("%d/%m")}</th>')
    filas = []
    for u in staff:
        usr = u["Usuario"]
        nom = u.get("Nombre") or usr
        celdas = [f'<td style="padding:5px 8px;font-size:13px;font-weight:600;color:#1f2937;'
                  f'white-space:nowrap;position:sticky;left:0;background:#fff;'
                  f'border-right:1px solid #eef1f5;">{_esc(nom)}</td>']
        for d in R.DIAS:
            items = R.celda_items(datos, usr, d)
            if not items:
                cont = ('<div style="background:#EAF3DE;color:#3B6D11;border-radius:5px;'
                        'padding:3px 6px;font-weight:600;text-align:center;">libre</div>')
            else:
                _cs = []
                for it in items:
                    _fl = R.franja_label(it["ini"], it["fin"])
                    _fh = (f' <span style="opacity:.8;">· {_esc(_fl)}</span>') if _fl else ""
                    _cs.append(f'<div style="background:#F1EFE8;color:#444441;border-radius:5px;'
                               f'padding:2px 5px;margin-bottom:2px;">'
                               f'{_esc(R.etiqueta_de(it["asig"], tidx))}{_fh}</div>')
                cont = "".join(_cs)
            celdas.append(f'<td style="padding:4px 5px;background:#fff;font-size:11px;'
                          f'line-height:1.25;vertical-align:top;">{cont}</td>')
        filas.append("<tr>" + "".join(celdas) + "</tr>")
    return ('<div style="overflow-x:auto;margin:10px 0;">'
            '<table style="border-collapse:separate;border-spacing:3px;width:100%;">'
            "<thead><tr>" + "".join(ths) + "</tr></thead>"
            "<tbody>" + "".join(filas) + "</tbody></table></div>")
