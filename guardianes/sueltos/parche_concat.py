"""Cierra la bolsa de CONCATENACIONES: 30 trozos de frase que nunca pasaban por t().

⚠️ El arreglo NO es envolver cada trozo: un trozo no es una frase y el orden de las
palabras cambia entre idiomas. Cada frase pasa a ser UNA clave con marcadores
(`{x}`) y los valores calculados se inyectan con `.replace()` — el mismo patrón que
el titular de v452.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

R = {}

# ---------------------------------------------------------------- auth_ui
R["auth_ui.py"] = [
    ('''                st.warning(":material/warning: With clients in separate books, the **owner's consolidated summaries** still only count the ones in the master book. Left out of the consolidation: **"
                           + ", ".join(_fuera) + "**. Each client does see all of their own data.")''',
     '''                st.warning(t(":material/warning: With clients in separate books, the **owner's "
                             "consolidated summaries** still only count the ones in the master book. "
                             "Left out of the consolidation: **{x}**. Each client does see all of "
                             "their own data.").replace("{x}", ", ".join(_fuera)))'''),

    ('''        st.warning(
            ":material/notifications_off: **This company's alerts do not reach "
            f"{len(_sc)}** of their recipients: "
            + ", ".join(f"**{x['usuario']}** ({_etq(str(x['rol']))})" for x in _sc)
            + ". With no email and no Telegram, the alert stays inside the app. Fix it by adding an email on their profile.")''',
     '''        st.warning(
            t(":material/notifications_off: **This company's alerts do not reach {n}** of their "
              "recipients: {x}. With no email and no Telegram, the alert stays inside the app. "
              "Fix it by adding an email on their profile.")
            .replace("{n}", str(len(_sc)))
            .replace("{x}", ", ".join(f"**{x['usuario']}** ({_etq(str(x['rol']))})" for x in _sc)))'''),
]

# ---------------------------------------------------------------- payroll_ui
R["payroll_ui.py"] = [
    ('''            flash.error(":material/event_repeat: **Nothing was generated** because the chosen period overlaps payslips already issued — the same hours would be paid twice:\\n\\n" + _líneas +
                        "\\n\\nAdjust the dates so they do not overlap, or void those payslips in the list below and generate again.")''',
     '''            flash.error(t(":material/event_repeat: **Nothing was generated** because the chosen "
                          "period overlaps payslips already issued — the same hours would be paid "
                          "twice:")
                        + "\\n\\n" + _líneas + "\\n\\n"
                        + t("Adjust the dates so they do not overlap, or void those payslips in "
                            "the list below and generate again."))'''),
]

# ---------------------------------------------------------------- plan_ui
R["plan_ui.py"] = [
    ('''            st.caption(f":orange[:material/warning:] The drawing did not give: {', '.join(datos['faltan'][:8])}"
                       + ("…" if len(datos["faltan"]) > 8 else "")
                       + " — enter them by hand.")''',
     '''            st.caption(t(":orange[:material/warning:] The drawing did not give: {x} — enter "
                         "them by hand.")
                       .replace("{x}", ", ".join(datos["faltan"][:8])
                                + ("…" if len(datos["faltan"]) > 8 else "")))'''),
]

# ---------------------------------------------------------------- survey_ui
R["survey_ui.py"] = [
    ('''                    st.info("There are no projects yet. Create one in "
                            + ("**👑 Administration → :material/folder: Projects**" if _ROL == "propietario"
                               else "**:material/build: My company → :material/bar_chart: Projects → :material/add: New project**")
                            + " and come back here to attach this survey to it.")''',
     '''                    st.info(t("There are no projects yet. Create one in {x} and come back here "
                              "to attach this survey to it.")
                            .replace("{x}", t("**👑 Administration → :material/folder: Projects**")
                                     if _ROL == "propietario" else
                                     t("**:material/build: My company → :material/bar_chart: "
                                       "Projects → :material/add: New project**")))'''),
]

# ---------------------------------------------------------------- quotes_ui
R["quotes_ui.py"] = [
    ('''        st.warning(":material/schedule: **" + str(len(_venc)) + " expired quote(s)** with no answer: " + " · ".join(
                       f"{c.get('ClienteNombre','')} ({T.dinero(c.get('Total'), 0)})"
                       for c in _venc[:5])
                   + ". Issue a new version if it still stands.")''',
     '''        st.warning(t(":material/schedule: **{n} expired quote(s)** with no answer: {x}. "
                     "Issue a new version if it still stands.")
                   .replace("{n}", str(len(_venc)))
                   .replace("{x}", " · ".join(
                       f"{c.get('ClienteNombre','')} ({T.dinero(c.get('Total'), 0)})"
                       for c in _venc[:5])))'''),

    ('''            st.warning(":material/sync_problem: **The catalogue changed** since you built this quote: " + _txt + ". The quote's prices do NOT change on their own.")''',
     '''            st.warning(t(":material/sync_problem: **The catalogue changed** since you built "
                         "this quote: {x}. The quote's prices do NOT change on their own.")
                       .replace("{x}", _txt))'''),

    ('''        st.info(":material/savings: Project budget: **"
                + T.dinero(_tot["costo"], 0) + "** — that is your quoted **cost**, not the price to the client (" + T.dinero(_tot["subtotal"], 0) + "). That way the over-budget alert fires when you are eating into the margin, not when you are already losing money.")''',
     '''        st.info(t(":material/savings: Project budget: **{a}** — that is your quoted **cost**, "
                  "not the price to the client ({b}). That way the over-budget alert fires when "
                  "you are eating into the margin, not when you are already losing money.")
                .replace("{a}", T.dinero(_tot["costo"], 0))
                .replace("{b}", T.dinero(_tot["subtotal"], 0)))'''),

    ('''        st.caption("Linked to project " + str(c.get("ProyectoID")) + ".")''',
     '''        st.caption(t("Linked to project {x}.").replace("{x}", str(c.get("ProyectoID"))))'''),

    ('''        st.caption(":material/trending_up: At the current rate the job will cost "
                   + T.dinero(comp["costo_proyectado"], 0) + " against the "
                   + T.dinero(comp["costo"]["cotizado"], 0) + " " + t("quoted."))''',
     '''        st.caption(t(":material/trending_up: At the current rate the job will cost {a} "
                     "against the {b} quoted.")
                   .replace("{a}", T.dinero(comp["costo_proyectado"], 0))
                   .replace("{b}", T.dinero(comp["costo"]["cotizado"], 0)))'''),

    # ⚠️ Las DOS ramas del mismo if/elif, cada una como frase COMPLETA (v452).
    ('''        st.warning(":material/warning: " + t("You are at") + " **" + T.dinero(comp["costo"]["dif"], 0)
                   + " above** what was quoted, with the project at **"
                   + ("%.0f" % _av) + "%**. At this rate the final profit will be lower than quoted.")''',
     '''        st.warning(t(":material/warning: You are at **{m} above** what was quoted, with the "
                     "project at **{p}%**. At this rate the final profit will be lower than quoted.")
                   .replace("{m}", T.dinero(comp["costo"]["dif"], 0))
                   .replace("{p}", "%.0f" % _av))'''),

    ('''        st.success(":material/check_circle: " + t("You are at") + " **"
                   + T.dinero(abs(comp["costo"]["dif"]), 0) + " below** what was quoted, with the project at " + ("%.0f" % _av) + "%.")''',
     '''        st.success(t(":material/check_circle: You are at **{m} below** what was quoted, with "
                     "the project at **{p}%**.")
                   .replace("{m}", T.dinero(abs(comp["costo"]["dif"]), 0))
                   .replace("{p}", "%.0f" % _av))'''),
]

# ---------------------------------------------------------------- projects_ui
R["projects_ui.py"] = [
    ('''                st.warning(":material/warning: A project with that name already exists: "
                           + ", ".join(dups)
                           + ". If it is a different lift, tick the box and create it again.")''',
     '''                st.warning(t(":material/warning: A project with that name already exists: {x}. "
                             "If it is a different lift, tick the box and create it again.")
                           .replace("{x}", ", ".join(dups)))'''),

    ('''            st.success(f":material/check_circle: Project **{res}** created with "
                       f"{len(sched.get('activities', []))} activities"
                       + (" and the drawing data loaded." if _plano else ".")
                       + " The survey and the other tools can now feed it.")''',
     '''            st.success((t(":material/check_circle: Project **{p}** created with {n} activities "
                          "and the drawing data loaded.") if _plano else
                        t(":material/check_circle: Project **{p}** created with {n} activities."))
                       .replace("{p}", str(res))
                       .replace("{n}", str(len(sched.get("activities", []))))
                       + " " + t("The survey and the other tools can now feed it."))'''),

    ('''        st.warning(":material/warning: **Without full contact details (email + Telegram):** "
                   + ", ".join(sin_contacto)
                   + ". They will not receive the assignment or the inductions.")''',
     '''        st.warning(t(":material/warning: **Without full contact details (email + Telegram):** "
                     "{x}. They will not receive the assignment or the inductions.")
                   .replace("{x}", ", ".join(sin_contacto)))'''),

    ('''        st.warning(":material/stethoscope: The crew is still finishing **"
                   + ", ".join(x["nombre"] for x in d["arrastradas"][:3])
                   + "**, so **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3])
                   + "** has not started yet. That is where the delay is.")''',
     '''        st.warning(t(":material/stethoscope: The crew is still finishing **{a}**, so **{b}** "
                     "has not started yet. That is where the delay is.")
                   .replace("{a}", ", ".join(x["nombre"] for x in d["arrastradas"][:3]))
                   .replace("{b}", ", ".join(x["nombre"] for x in d["paradas"][:3])))'''),

    ('''        st.warning(":material/stethoscope: Not started and already due: **"
                   + ", ".join(x["nombre"] for x in d["paradas"][:3]) + "**.")''',
     '''        st.warning(t(":material/stethoscope: Not started and already due: **{x}**.")
                   .replace("{x}", ", ".join(x["nombre"] for x in d["paradas"][:3])))'''),

    ('''        st.markdown(
            f":material/event: **Delivery is set by «{proj['critico']}»** — expected "
            f"**{_fecha}**" + (f", with **{_d:.0f} days behind**." if _d else
                               ", on time.")
            + "  That is where reinforcing pays off most.")''',
     '''        st.markdown(
            (t(":material/event: **Delivery is set by «{c}»** — expected **{f}**, with "
               "**{d} days behind**.") .replace("{d}", f"{_d:.0f}") if _d else
             t(":material/event: **Delivery is set by «{c}»** — expected **{f}**, on time."))
            .replace("{c}", str(proj["critico"])).replace("{f}", str(_fecha))
            + "  " + t("That is where reinforcing pays off most."))'''),

    ('''        st.info(t(":material/warning: They use noticeably more hours than their twins:") + " **"
                + ", ".join(_out) + "**. " + t("Worth looking into why."))''',
     '''        st.info(t(":material/warning: They use noticeably more hours than their twins: **{x}**. "
                  "Worth looking into why.").replace("{x}", ", ".join(_out)))'''),

    ('''            st.success(":material/check_circle: This job's revenue is the **agreed price** on quote " + f"**{rev.get('cotizacion','')}**. "
                       "The " + f"{rev['margen_pct']:g}%" + " follows from that price.")''',
     '''            st.success(t(":material/check_circle: This job's revenue is the **agreed price** on "
                         "quote **{q}**. The {m}% follows from that price.")
                       .replace("{q}", str(rev.get("cotizacion", "")))
                       .replace("{m}", f"{rev['margen_pct']:g}"))'''),

    ('''                st.warning(":material/info: This job has a fixed profit of "
                           + _T.dinero(rev["fija_ignorada"]) + " that is **not used**: the price the client signed wins. Set it to 0 to remove the noise.")''',
     '''                st.warning(t(":material/info: This job has a fixed profit of {x} that is **not "
                             "used**: the price the client signed wins. Set it to 0 to remove the "
                             "noise.").replace("{x}", _T.dinero(rev["fija_ignorada"])))'''),

    ('''            st.success(":material/check_circle: This job already uses the per-line model. The " + f"{rev['margen_pct']:g}%" + " margin follows from it; it is not something you typed.")''',
     '''            st.success(t(":material/check_circle: This job already uses the per-line model. The "
                         "{m}% margin follows from it; it is not something you typed.")
                       .replace("{m}", f"{rev['margen_pct']:g}"))'''),

    ('''            st.warning(":material/person_alert: With no profit set, their work would be invoiced **at cost**: **" + ", ".join(rev["sin_ganancia"])
                       + "**.")''',
     '''            st.warning(t(":material/person_alert: With no profit set, their work would be "
                         "invoiced **at cost**: **{x}**.")
                       .replace("{x}", ", ".join(rev["sin_ganancia"])))'''),

    ('''    st.caption("With these values you would make **" + _T.dinero(_tot)
               + "** on the labour clocked so far. Materials are invoiced at cost (decision from v360).")''',
     '''    st.caption(t("With these values you would make **{x}** on the labour clocked so far. "
                 "Materials are invoiced at cost (decision from v360).")
               .replace("{x}", _T.dinero(_tot)))'''),

    ('''        _c1.caption("With this amount, the job's estimated revenue would be **"
                    + _T.dinero(_ing) + "** on a cost of " + _T.dinero(_costo) + ".")''',
     '''        _c1.caption(t("With this amount, the job's estimated revenue would be **{a}** on a "
                      "cost of {b}.")
                    .replace("{a}", _T.dinero(_ing)).replace("{b}", _T.dinero(_costo)))'''),

    ('''                    cc[0].caption(_lbl + " · no file")''',
     '''                    cc[0].caption(_lbl + " · " + t("no file"))'''),

    ('''        st.warning(f":material/percent: **{len(_m0)} job(s) at 0% margin**, so their "
                   "estimated revenue is exactly their cost and the profit comes out at $0: "
                   + ", ".join(_m0[:6]) + ("…" if len(_m0) > 6 else "")
                   + ". Edit them in the table below.")''',
     '''        st.warning(t(":material/percent: **{n} job(s) at 0% margin**, so their estimated "
                     "revenue is exactly their cost and the profit comes out at $0: {x}. "
                     "Edit them in the table below.")
                   .replace("{n}", str(len(_m0)))
                   .replace("{x}", ", ".join(_m0[:6]) + ("…" if len(_m0) > 6 else "")))'''),
]

total = 0
for fn, pares in R.items():
    p = CORE / fn
    s = p.read_text(encoding="utf-8")
    for viejo, nuevo in pares:
        n = s.count(viejo)
        if n != 1:
            print(f"  ANCLA x{n} en {fn}: {viejo.strip()[:70]!r}")
            sys.exit(1)
        s = s.replace(viejo, nuevo)
    # ⚠️ No se escribe un fichero que no compile (la guarda que salvó v440).
    ast.parse(s)
    p.write_text(s, encoding="utf-8")
    total += len(pares)
    print(f"  OK  {fn}: {len(pares)} frases")

print(f"\n{total} frases reconstruidas como clave unica con marcadores")
