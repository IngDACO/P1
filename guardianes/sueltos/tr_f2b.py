"""F2 (2/2) — cierra los cuatro módulos de campo.

⚠️ Lo que NO se toca, y está a la vista en el mismo volcado:
  · claves de dict y de hoja: `usuario`, `Usuario`, `proyecto`, `nombre`, `fecha`,
    `Desde`, `Hasta`, `Tipo`, `Estado` — traducirlas rompe la lectura sin dar error;
  · el JavaScript del cronómetro (líneas 45-71 de timeclock_ui): es código, no texto.
Todo lo demás de esos ficheros es etiqueta y se traduce.
"""
import ast
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")

R = {
"core/timeclock_ui.py": [
    ('f"You have just clocked in to **{obra}** y hoy todavía **no hay Pre-Start** "\n'
     '                "registrado en esa obra.")',
     'f"You have just clocked in to **{obra}** and there is still "\n'
     '                "**no Pre-Start** recorded on that site today.")'),
    ('f"You have just clocked in to **{obra}**. La charla de seguridad de hoy ya está "\n'
     '                "registrada, pero **tú no constas entre quienes la firmaron**.")',
     'f"You have just clocked in to **{obra}**. Today\'s safety talk is already "\n'
     '                "recorded, but **you are not among those who signed it**.")'),
    ('st.caption("La lista de asistentes es el registro de quién recibió la charla. "\n'
     '               "Tu firma se añade a ese mismo Pre-Start, en una hoja de anexo con su hora."\n'
     '               + (f" La registró {quien}." if quien else ""))',
     'st.caption(t("The attendee list is the record of who received the talk. Your "\n'
     '                 "signature is added to that same Pre-Start, on an annex sheet with "\n'
     '                 "its time.")\n'
     '               + (f" {t(\'Recorded by\')} {quien}." if quien else ""))'),
    ('_dialogo_firmar(nombre or "esta obra"', '_dialogo_firmar(nombre or t("this site")'),
    ('_dialogo_prestart(nombre or "esta obra")', '_dialogo_prestart(nombre or t("this site"))'),
    ('_chrono_mini(gen["clock_in"], "Jornada", _AZUL', '_chrono_mini(gen["clock_in"], t("Workday"), _AZUL'),
    ('_pn = str(prj.get("proyecto") or "Proyecto")', '_pn = str(prj.get("proyecto") or t("Project"))'),
    ('_lbl = ("Cerrar la jornada" if not prj else "Cerrar jornada y proyecto")',
     '_lbl = (t("Close the workday") if not prj else t("Close workday and project"))'),
    ('":material/play_circle: Abrir jornada"', 't(":material/play_circle: Open workday")'),
    ('vacio="— elige la obra —"', 'vacio=t("— pick the site —")'),

    ('etq = ("jornada general" if tipo == timeclock.TIPO_GENERAL\n'
     '               else f"proyecto «{s[\'proyecto\'] or \'—\'}»")',
     'etq = (t("general workday") if tipo == timeclock.TIPO_GENERAL\n'
     '               else f"{t(\'project\')} «{s[\'proyecto\'] or \'—\'}»")'),
    ('lineas.append(f"- **{etq}** abierta desde **{s[\'clock_in\']}**")',
     'lineas.append(f"- **{etq}** {t(\'open since\')} **{s[\'clock_in\']}**")'),
    ('":material/warning: Tienes fichaje(s) de un día anterior **sin cerrar**:\\n"',
     't(":material/warning: You have time entries from a previous day **still open**:\\n")'),
    ('+ "\\n\\nCiérralos indicando **a qué hora terminaste de verdad** — si no, "\n'
     '                 "se contarían como trabajadas las horas de la noche.")',
     '+ t("\\n\\nClose them stating **what time you actually finished** — "\n'
     '                   "otherwise the overnight hours would count as worked."))'),
    ('+ "  ·  tus fichajes son privados.")', '+ t("  ·  your time entries are private."))'),
    ('_est = ("En un proyecto" if prj else\n'
     '            ("Jornada abierta, sin proyecto" if gen else "Sin fichar"))',
     '_est = (t("On a project") if prj else\n'
     '            (t("Workday open, no project") if gen else t("Not clocked in")))'),
    ('f"{prj[\'proyecto\'] or \'—\'} · desde las {prj[\'clock_in\'][11:16]}" if prj else\n'
     '            (f"desde las {gen[\'clock_in\'][11:16]}" if gen else\n'
     '             "abre la jornada o ficha directamente a un proyecto"))',
     'f"{prj[\'proyecto\'] or \'—\'} · {t(\'since\')} {prj[\'clock_in\'][11:16]}" if prj else\n'
     '            (f"{t(\'since\')} {gen[\'clock_in\'][11:16]}" if gen else\n'
     '             t("open the workday or clock straight in to a project")))'),
    ('tarj = [_tarjeta("Jornada de hoy", f"{hoy[\'general\']:.2f} h",\n'
     '                     "el tiempo pagado", _AZUL, bool(gen)),\n'
     '            _tarjeta("Imputado a proyectos", f"{hoy[\'proyecto\']:.2f} h",\n'
     '                     f"{len(hoy[\'por_proyecto\'])} proyecto(s)", _VERDE, bool(prj)),\n'
     '            _tarjeta("Sin asignar", f"{hoy[\'sin_asignar\']:.2f} h",\n'
     '                     "traslados, espera o proyecto sin fichar",',
     'tarj = [_tarjeta(t("Today\'s workday"), f"{hoy[\'general\']:.2f} h",\n'
     '                     t("the paid time"), _AZUL, bool(gen)),\n'
     '            _tarjeta(t("Charged to projects"), f"{hoy[\'proyecto\']:.2f} h",\n'
     '                     f"{len(hoy[\'por_proyecto\'])} {t(\'project(s)\')}", _VERDE, bool(prj)),\n'
     '            _tarjeta(t("Unassigned"), f"{hoy[\'sin_asignar\']:.2f} h",\n'
     '                     t("travel, waiting or a project not clocked in"),'),
    ('_tarjeta("Esta semana", f"{sem[\'general\']:.2f} h",\n'
     '                     f"lunes a hoy · {sem[\'dias\']} día(s)", _AZUL)]',
     '_tarjeta(t("This week"), f"{sem[\'general\']:.2f} h",\n'
     '                     f"{t(\'Monday to today\')} · {sem[\'dias\']} {t(\'day(s)\')}", _AZUL)]'),
    ('st.markdown("#### :material/schedule: Jornada")', 'st.markdown(t("#### :material/schedule: Workday"))'),
    ('st.caption(f"Desde las {gen[\'clock_in\'][11:16]}."\n'
     '                       + ("  Al cerrarla se cierra también el proyecto en curso." if prj else ""))',
     'st.caption(f"{t(\'Since\')} {gen[\'clock_in\'][11:16]}."\n'
     '                       + (t("  Closing it also closes the project in progress.") if prj else ""))'),
    ('":material/check_circle: Abrir jornada"', 't(":material/check_circle: Open workday")'),
    ('_chronometer(prj["clock_in"], "En este proyecto", _VERDE', '_chronometer(prj["clock_in"], t("On this project"), _VERDE'),
    ('vacio="— elige el proyecto —")', 'vacio=t("— pick the project —"))'),
    ('st.markdown("**Hoy has imputado**")', 'st.markdown(t("**Charged today**"))'),
    ('"": "Jornada" if f["tipo"] == timeclock.TIPO_GENERAL else "Proyecto",\n'
     '                "Proyecto": f["proyecto"] or "—",',
     '"": t("Workday") if f["tipo"] == timeclock.TIPO_GENERAL else t("Project"),\n'
     '                t("Project"): f["proyecto"] or "—",'),
],
"core/prestart_ui.py": [
    ('_VACIO = "— elige el proyecto —"', '_VACIO = "— pick the project —"'),
    ('st.caption("Añadidos: "', 'st.caption(t("Added") + ": "'),
    ('st.caption("fichó hoy aquí" if a["ficho"] else\n'
     '                       ("de la cuadrilla" if a["usuario"] else "añadido a mano"))',
     'st.caption(t("clocked in here today") if a["ficho"] else\n'
     '                       (t("from the crew") if a["usuario"] else t("added by hand")))'),
    ('st.caption(":green[✓ firmado]" if firma else ":orange[falta la firma]")',
     'st.caption(t(":green[✓ signed]") if firma else t(":orange[signature missing]"))'),
    ('f"{info.get(\'id\', \'\')} · lo registró **{info.get(\'facilitador\', \'\') or \'—\'}**"',
     'f"{info.get(\'id\', \'\')} · {t(\'recorded by\')} **{info.get(\'facilitador\', \'\') or \'—\'}**"'),
    ('+ (" · ya firmaron: " + ", ".join(info.get("asistentes", []))',
     '+ (f" · {t(\'already signed\')}: " + ", ".join(info.get("asistentes", []))'),
    ('f":material/info: Today there are **{_otras + 1} charlas** registradas en "\n'
     '                       f"esta obra. Se te ofrece la más reciente; si firmaste otra, "\n'
     '                       f"díselo a quien la registró.")',
     'f":material/info: Today there are **{_otras + 1} talks** recorded on this "\n'
     '                       f"site. The most recent one is offered; if you signed a "\n'
     '                       f"different one, tell whoever recorded it.")'),
    ('flash.exito(f"Signed. Your signature was added to the {info.get(\'id\', \'\')} "\n'
     '                                "como hoja de anexo, sin tocar el documento original.")',
     'flash.exito(f"Signed. Your signature was added to {info.get(\'id\', \'\')} "\n'
     '                                "as an annex sheet, without touching the original.")'),
    ('st.error(r.get("error") or "No se pudo firmar.")',
     'st.error(r.get("error") or t("Could not sign."))'),
    ('st.info("No hay proyectos disponibles. "\n'
     '                + ("El administrador debe asignarte a un proyecto." if rol == "campo"\n'
     '                   else "Crea un proyecto desde el Survey."))',
     'st.info(t("No projects available.") + " "\n'
     '                + (t("The administrator must assign you to a project.") if rol == "campo"\n'
     '                   else t("Create a project from the Survey.")))'),
    ('_pend.append("Near Miss/Hazard (sección 2)")', '_pend.append(t("Near Miss/Hazard (section 2)"))'),
    ('_pend.append("Al menos un asistente (sección 5)")', '_pend.append(t("At least one attendee (section 5)"))'),
    ('"Firma de: "', 't("Signature of") + ": "'),
    ('st.caption("Falta por completar: "', 'st.caption(t("Still to complete") + ": "'),
    ('st.spinner("Generando PDF y archivando...")', 'st.spinner(t("Generating the PDF and filing it…"))'),
    ('st.error(res["error"] or "No se pudo guardar el pre-start.")',
     'st.error(res["error"] or t("The pre-start could not be saved."))'),
    ('":material/warning: Checks marcados **NO** (revisar antes de trabajar): "',
     't(":material/warning: Checks answered **NO** (review before working)") + ": "'),
    ('f":material/cancel: A project alert was opened for {len(_no)} "\n'
     '                           "control(es) en NO. El administrador queda avisado.")',
     'f":material/cancel: A project alert was opened for {len(_no)} "\n'
     '                           "control(s) answered NO. The administrator has been notified.")'),
    ('_kpi("Con near miss", n_nm', '_kpi(t("With near miss"), n_nm'),
    ('_kpi("Con checks en NO", n_fail', '_kpi(t("With NO checks"), n_fail'),
    ('_kpi("Último", prev[0]["fecha"] or "—")', '_kpi(t("Latest"), prev[0]["fecha"] or "—")'),
    ('_res.append(f"{d[\'n_no\']} check(s) en NO")',
     '_res.append(f"{d[\'n_no\']} check(s) answered NO")'),
    ('(d["near_miss_desc"] or "(sin descripción)")', '(d["near_miss_desc"] or t("(no description)"))'),
    ('st.markdown("**:material/engineering: Asistentes:** "',
     'st.markdown(f"**:material/engineering: {t(\'Attendees\')}:** "'),
],
"core/ausencias_ui.py": [
    ('f"{r.get(\'Hasta\')} · {r.get(\'Dias\')} día(s) · {_chip_estado(str(r.get(\'Estado\')))}"',
     'f"{r.get(\'Hasta\')} · {r.get(\'Dias\')} {t(\'day(s)\')} · {_chip_estado(str(r.get(\'Estado\')))}"'),
    ('pie="días usados en el periodo"', 'pie=t("days used in the period")'),
    ('f":material/event_available: Tu año de vacaciones va del "',
     'f"{t(\':material/event_available: Your leave year runs from\')} "'),
    ('f"(desde que entraste, el {_per[\'ingreso\']}).")',
     'f"({t(\'since you started, on\')} {_per[\'ingreso\']}).")'),
    ('f":material/help: Contamos por año natural "',
     'f"{t(\':material/help: We are counting by calendar year\')} "'),
    ('f"(**{_per[\'desde\']}** → **{_per[\'hasta\']}**) porque no consta "\n'
     '                       "tu fecha de alta. Pídele a tu responsable que la cargue y el "\n'
     '                       "saldo pasará a contar desde tu aniversario.")',
     'f"(**{_per[\'desde\']}** → **{_per[\'hasta\']}**) because your start date "\n'
     '                       "is not on record. Ask your manager to enter it and the "\n'
     '                       "balance will count from your anniversary.")'),
    ('f"este año (usados {_s[\'usados\']:.0f} of {_s[\'asignados\']:.0f}). "\n'
     '                         "Habla con tu responsable.")',
     'f"this year (used {_s[\'usados\']:.0f} of {_s[\'asignados\']:.0f}). "\n'
     '                         "Talk to your manager.")'),
    ('f"día(s)** de {cfg[\'nombre\'].lower()} this year.")',
     'f"day(s)** of {cfg[\'nombre\'].lower()} this year.")'),
    ('":material/send: Registrar la baja"', 't(":material/send: Record the sick leave")'),
    ('f":material/block: Pides **{len(_d)} día(s)** y te quedan "',
     'f":material/block: You are asking for **{len(_d)} {t(\'day(s)\')}** and you have "'),
    ('else f"Solicitud enviada ({res}). Te avisaremos al resolverla.")',
     'else f"{t(\'Request sent\')} ({res}). {t(\'We will let you know when it is resolved.\')}")'),
    ('_pie.append(f"resuelta por {r.get(\'ResueltaPor\')}")',
     '_pie.append(f"{t(\'resolved by\')} {r.get(\'ResueltaPor\')}")'),
    ('_lines = [f"<b>{nombre}</b> ha CANCELADO su "',
     '_lines = [f"<b>{nombre}</b> has CANCELLED their "'),
    ('f"del {r.get(\'Desde\')} al {r.get(\'Hasta\')}.",',
     'f"from {r.get(\'Desde\')} to {r.get(\'Hasta\')}.",'),
    ('"Esos días vuelven a quedar libres en el planificador: si habías "\n'
     '                  "reorganizado la cuadrilla, revísalo."]',
     '"Those days are free again in the planner: if you had reorganised "\n'
     '                  "the crew, review it."]'),
    ('("Se registró automáticamente (no requiere aprobación)."',
     '("It was recorded automatically (no approval needed)."'),
    ('"Está PENDIENTE de tu aprobación → Planificación · Ausencias.")]',
     '"It is PENDING your approval → Planning · Absences.")]'),
    ('pie="esperan tu decisión"', 'pie=t("waiting for your decision")'),
    ('_kpi("Fuera hoy"', '_kpi(t("Away today")'),
    ('_kpi("Próximos 7 días"', '_kpi(t("Next 7 days")'),
    ('pie="ausencias aprobadas"', 'pie=t("approved absences")'),
    ('f"de {cfg.get(\'nombre\', \'\').lower()} este año")',
     'f"{t(\'of\')} {cfg.get(\'nombre\', \'\').lower()} {t(\'this year\')}")'),
    ('(" — **se pasaría del saldo**" if s["restantes"] < 0 else ".")',
     '(t(" — **this would go over the balance**") if s["restantes"] < 0 else ".")'),
    ('st.warning(":material/warning: Ya está asignado esos días a **"',
     'st.warning(t(":material/warning: They are already assigned on those days to") + " **"'),
    ('+ "**. Si apruebas, esos días quedan "\n'
     '                       "libres en el tablero.")',
     '+ t("**. If you approve, those days are freed on the board."))'),
    ('st.caption(":material/check: libres y con los certificados: "',
     'st.caption(t(":material/check: free and holding the certificates") + ": "'),
    ('st.caption(":material/warning: libres pero SIN los certificados "\n'
     '                                   "que exige la obra: " + ", ".join(_no))',
     'st.caption(t(":material/warning: free but WITHOUT the certificates the "\n'
     '                                     "site requires") + ": " + ", ".join(_no))'),
    ('f":material/groups: Esos días ya hay {len(_otros)} persona(s) fuera: "',
     'f":material/groups: {len(_otros)} {t(\'other person(s) are already away those days\')}: "'),
    ('(f" {_n} día(s) marcados en el planificador."',
     '(f" {_n} {t(\'day(s) marked in the planner.\')}"'),
    ('f" ⚠️ No se pudo escribir en el planificador: {_n}"))',
     'f" ⚠️ {t(\'Could not write to the planner\')}: {_n}"))'),
    ('_l = [f"Tu solicitud de <b>{cfg.get(\'nombre\')}</b> "\n'
     '              f"({r.get(\'Desde\')} → {r.get(\'Hasta\')}) ha sido <b>{_s}</b>."]',
     '_l = [f"Your request for <b>{cfg.get(\'nombre\')}</b> "\n'
     '              f"({r.get(\'Desde\')} → {r.get(\'Hasta\')}) has been <b>{_s}</b>."]'),
    ('notify.notify_user(usuario, f"Ausencia {_s}: {r.get(\'Desde\')} → {r.get(\'Hasta\')}", _l)',
     'notify.notify_user(usuario, f"Absence {_s}: {r.get(\'Desde\')} → {r.get(\'Hasta\')}", _l)'),
],
"core/route_ui.py": [
    ('":orange[:material/warning:] Sin ubicación (no entran en la ruta): "',
     't(":orange[:material/warning:] No location (they are left out of the route)") + ": "'),
    ('_DIAS_L = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]',
     '_DIAS_L = [t("Monday"), t("Tuesday"), t("Wednesday"), t("Thursday"), t("Friday"),\n'
     '               t("Saturday"), t("Sunday")]'),
    ('f"{_DIAS_L[fecha.weekday()].lower()}. La semana normal es de "\n'
     '                    "lunes a viernes; el fin de semana se añade desde el Panel.")',
     'f"{_DIAS_L[fecha.weekday()].lower()}. The normal week is Monday to "\n'
     '                    "Friday; the weekend is added from the Panel.")'),
    ('sin_prj.append(f"{nom} — (obra no encontrada)")',
     'sin_prj.append(f"{nom} — ({t(\'site not found\')})")'),
    ('_estado = "🟢 fichado aquí"', '_estado = t("🟢 clocked in here")'),
    ('_estado = "🔴 fichó en " + ", ".join(_fich_noms[:2])',
     '_estado = t("🔴 clocked in at") + " " + ", ".join(_fich_noms[:2])'),
    ('_estado = "⚠️ sin fichar"', '_estado = t("⚠️ not clocked in")'),
    ('"día completo"', 't("full day")'),
    ('"Obra": obra, "Estado": _estado,\n'
     '                            "Dirección": str(prj.get("Ubicacion", "")) or "—"})',
     't("Site"): obra, t("Status"): _estado,\n'
     '                            t("Address"): str(prj.get("Ubicacion", "")) or "—"})'),
    ('+ ("con gente hoy" if sitios else "ninguno hoy")',
     '+ (t("with people today") if sitios else t("none today"))'),
    ('f":material/wrong_location: Sin ubicación\\n\\n{len(sin_coord)}\\n\\n"',
     'f":material/wrong_location: No location\\n\\n{len(sin_coord)}\\n\\n"'),
    ('+ ("fija el pin" if sin_coord else "todas ubicadas")',
     '+ (t("set the pin") if sin_coord else t("all located"))'),
    ('"todos planificados"', 't("all planned")'),
    ('f":gray[{s[\'dir\'] or \'sin dirección\'}]  \\n"',
     'f":gray[{s[\'dir\'] or t(\'no address\')}]  \\n"'),
    ('":orange[:material/warning:] Obra sin ubicación en el mapa (no entra "\n'
     '                   "en la ruta): "',
     't(":orange[:material/warning:] Site with no map location (left out of "\n'
     '                     "the route)") + ": "'),
    ('":material/info: Asignado a un estado/otro (no es obra): "',
     't(":material/info: Assigned to a status/other (not a site)") + ": "'),
],
}

fallos = []
for rel, reps in R.items():
    s = (RAIZ / rel).read_text(encoding="utf-8")
    for o, nv in reps:
        if s.count(nv) >= 1 and s.count(o) == 0:
            continue
        if s.count(o) != 1:
            fallos.append(f"{rel} ({s.count(o)}x) {o[:75]!r}")
if fallos:
    print(f"{len(fallos)} anclas no casan:")
    for f in fallos:
        print("   ...", " | ".join(f.splitlines()))
    sys.exit(1)

for rel, reps in R.items():
    p = RAIZ / rel
    s = p.read_text(encoding="utf-8")
    n = 0
    for o, nv in reps:
        if s.count(o) == 1:
            s = s.replace(o, nv, 1)
            n += 1
    ast.parse(s)
    p.write_text(s, encoding="utf-8")
    print(f"  {rel:26} {n} reemplazos")
print("OK")
