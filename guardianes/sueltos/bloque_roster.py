

# ── Enganche con el PLANIFICADOR ─────────────────────────────────
def choques(grupo, usuario, desde, hasta) -> list:
    """Obras a las que esa persona YA está asignada dentro del rango.

    ⚠️ Esto es «todo lo que implica» aprobar: si alguien pide una semana en la que ya
    tiene tres obras, aprobar sin mirar deja esas obras sin nadie **y nadie se entera**
    hasta el lunes. Se le enseña al administrador ANTES de decidir.

    Devuelve `[{fecha, dia, asig, etiqueta, proyecto_id}]`, solo lo que es TRABAJO:
    un `OFF` o un `LEAVE` que ya estuviera puesto no es un choque, es lo mismo que se
    está pidiendo.
    """
    from core import roster as R
    out = []
    dias = dias_del_rango(desde, hasta, incluir_findes=True)
    if not dias:
        return out
    # Una lectura por SEMANA, no por día (con 15 días serían 15 lecturas).
    for lunes in sorted({R.lunes_de(d) for d in dias}):
        try:
            sem = R.get_semana(grupo, lunes)
        except Exception as e:
            logger.warning("ausencias.choques: %s", e)
            continue
        celdas = (sem.get(str(usuario), {}) or {})
        tidx = None
        for d in dias:
            if R.lunes_de(d) != lunes:
                continue
            dia = R.DIAS_TODOS[d.weekday()]
            raw = R._norm_cell(celdas.get(dia, {}))
            for it in raw.get("items", []):
                asig = str(it.get("asig", "") or "")
                if not asig or asig in R.ESTADOS:      # OFF/LEAVE no es un choque
                    continue
                if tidx is None:
                    tidx = R.trabajos_idx(grupo)
                out.append({"fecha": d, "dia": dia, "asig": asig,
                            "etiqueta": R.etiqueta_de(asig, tidx),
                            "proyecto_id": R.proyecto_de(asig, tidx)})
    return out


def aplicar_al_roster(a: dict, quitar: bool = False) -> tuple:
    """Escribe (o retira) la ausencia en el planificador. Devuelve (ok, n_dias|error).

    ⚠️ **PISA lo que hubiera** en esos días, a propósito: si la ausencia está aprobada,
    esa persona no está, y dejar la obra asignada haría que el tablero, la ruta del día
    y «plan vs real» siguieran contando con ella. Lo que se pisó se le enseña antes al
    administrador (`choques`), para que decida el sustituto con la información delante
    en vez de descubrirlo el lunes.

    ⚠️ `quitar=True` NO devuelve la asignación anterior: se limpia el día. Restaurar
    una obra que quizá ya se reasignó a otra persona sería peor que dejar el hueco —
    un hueco se ve en la cobertura del día; un doble asignado, no.

    Una escritura por SEMANA (`guardar_persona` escribe la fila entera), no por día.
    """
    from core import roster as R
    tipo = str(a.get("Tipo", ""))
    cfg = TIPOS.get(tipo, {})
    estado = cfg.get("estado_roster", "OFF")
    usuario = str(a.get("Usuario", ""))
    grupo = str(a.get("Grupo", ""))
    # Se marcan TODOS los días del rango, fin de semana incluido: si la persona no
    # está, no está — y el tablero ya admite sábado y domingo desde v390.
    dias = dias_del_rango(a.get("Desde"), a.get("Hasta"), incluir_findes=True)
    if not dias:
        return False, "El rango no tiene días."
    nota = f"{cfg.get('nombre', tipo)} · {a.get('ID', '')}"
    n = 0
    for lunes in sorted({R.lunes_de(d) for d in dias}):
        try:
            sem = R.get_semana(grupo, lunes)
            celdas = dict(sem.get(usuario, {}) or {})
            for d in dias:
                if R.lunes_de(d) != lunes:
                    continue
                dia = R.DIAS_TODOS[d.weekday()]
                if quitar:
                    # solo se retira lo que puso ESTA ausencia (por su ID en la nota)
                    _c = R._norm_cell(celdas.get(dia, {}))
                    if str(a.get("ID", "")) in str(_c.get("nota", "")):
                        celdas.pop(dia, None)
                        n += 1
                else:
                    celdas[dia] = {"asig": estado, "nota": nota}
                    n += 1
            ok, msg = R.guardar_persona(grupo, lunes, usuario, celdas)
            if not ok:
                return False, msg
        except Exception as e:
            logger.warning("ausencias.aplicar_al_roster: %s", e)
            return False, str(e)
    return True, n


def sustitutos(grupo, fecha, proyecto_id=None, excluir=None) -> list:
    """Quién podría cubrir ese día: libre, sin ausencia y con los certificados.

    Reusa lo que ya sabe la app en vez de inventar un criterio nuevo: `roster` dice
    quién tiene el día ocupado y `credentials.compliance` si cumple lo que la obra
    exige (v219). Devuelve `[{usuario, nombre, cumple, faltan}]`.
    """
    from core import roster as R, auth
    fuera = {str(x.get("Usuario", "")) for x in ausentes_en(grupo, fecha)}
    try:
        gente = [u for u in auth.list_users(grupo)
                 if str(u.get("Rol", "")) == "campo"
                 and str(u.get("Activo", "SI")).upper() != "NO"]
    except Exception:
        return []
    try:
        sem = R.get_semana(grupo, R.lunes_de(fecha))
    except Exception:
        sem = {}
    dia = R.DIAS_TODOS[fecha.weekday()]
    _req = []
    if proyecto_id:
        try:
            from core import projects as P
            _p = P.get_project(proyecto_id) or {}
            _req = [x.strip() for x in str(_p.get("CertsReq", "")).split(";") if x.strip()]
        except Exception:
            _req = []
    out = []
    for u in gente:
        us = str(u.get("Usuario", ""))
        if us == str(excluir) or us in fuera:
            continue
        if R._norm_cell((sem.get(us, {}) or {}).get(dia, {})).get("items"):
            continue                                   # ese día ya tiene algo
        cumple, faltan = True, []
        if _req:
            try:
                from core import credentials as C
                _c = C.compliance(us, _req)
                cumple = bool(_c.get("cumple"))
                faltan = [t for t, e in (_c.get("por_tipo") or {}).items()
                          if e in ("falta", "vencido")]
            except Exception:
                pass
        out.append({"usuario": us, "nombre": str(u.get("Nombre") or us),
                    "cumple": cumple, "faltan": faltan})
    # los que cumplen primero: el admin ve antes a quien puede ir de verdad
    return sorted(out, key=lambda x: (not x["cumple"], x["nombre"]))
