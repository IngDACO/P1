# -*- coding: utf-8 -*-
"""v470 · los dos textos que pasaron a mentir, y el aviso que faltaba al editar."""
import io
import os

RAIZ = r"C:\Users\diego\P1\survey_app"
hechos, fallos = [], []


def parche(rel, viejo, nuevo, etq):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    s = io.open(p, encoding="utf-8").read()
    n = s.count(viejo)
    if n != 1:
        fallos.append("%s · %s: ancla %s (%d)"
                      % (rel, etq, "ausente" if not n else "ambigua", n))
        return
    io.open(p, "w", encoding="utf-8", newline="").write(s.replace(viejo, nuevo))
    hechos.append("%s · %s" % (rel, etq))


# ── 1 · los dos `help` pasaron a ser FALSOS al añadir el tipo ────────────────
parche(
    "core/projects_ui.py",
    'help=t("Only «Installation» generates the standard job schedule (11 activities that scale with NS)."))',
    'help=t("«Installation» and «Ripout + Installation» generate the standard job '
    'schedule (activities that scale with the number of stops); the combined type adds '
    'the strip-out of the existing lift as the first activity."))',
    "help del alta")

parche(
    "core/projects_ui.py",
    'help=t("Only «Installation» uses the standard job schedule."))',
    'help=t("Changing the type here does NOT rebuild the schedule: that would wipe the '
    'progress the crew has already reported. Add or remove activities below instead."))',
    "help de la edición")

# ── 2 · el aviso que faltaba ─────────────────────────────────────────────────
# ⚠️ Va como CONDICIÓN, no como evento: si saliera solo en el instante de cambiar el
# tipo se perdería con el primer rerun (v375/v383). Y va DONDE se arregla —junto a la
# tabla de actividades, con el «Add activity» debajo— en vez de junto al selector
# (regla v395).
parche(
    "core/projects_ui.py",
    '''        with st.expander(t("Add / delete activity (the % is recalculated automatically)"),
                         icon=":material/playlist_add:"):''',
    '''        # ⚠️ v470 · Cambiar el tipo NO regenera el cronograma, y es lo correcto:
        # regenerarlo borraría el avance que el campo ya haya reportado (la razón por la
        # que `attach_survey` tampoco lo toca desde v135). Pero hasta aquí eso pasaba en
        # SILENCIO: se marcaba la obra como «Ripout + Installation» y su plan seguía sin
        # el desmontaje, sin que nada lo dijera. Se avisa por CONDICIÓN, no por evento
        # (un aviso que solo sale al cambiar el tipo se pierde en el primer rerun,
        # v375/v383), y aquí —donde está el botón que lo arregla—, no junto al selector.
        if P.con_ripout(prj.get("Type", "")) and acts:
            from core.schedule import FASE_RIPOUT as _FR
            if not any(str(a.get("Name", "")).strip() == _FR[0] for a in acts):
                st.warning(t("This job is a rip-out plus installation, but its schedule "
                             "has no strip-out activity. Changing the type does not "
                             "rebuild the schedule (that would wipe the progress already "
                             "reported), so add it below: «{act}».", act=_FR[0]))

        with st.expander(t("Add / delete activity (the % is recalculated automatically)"),
                         icon=":material/playlist_add:"):''',
    "aviso por condición")

print("APLICADO:")
for h in hechos:
    print("   ok  " + h)
if fallos:
    print("FALLOS:")
    for f in fallos:
        print("   !!  " + f)
    raise SystemExit(1)
