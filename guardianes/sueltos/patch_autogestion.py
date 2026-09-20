# -*- coding: utf-8 -*-
"""Las tres pantallas «mías» del campo, bajo un nivel de AUTOGESTIÓN (peticion del usuario).

Mis credenciales · Mis colillas · Mis ausencias pasan de tres secciones sueltas a
sub-pestañas de una sola: la nav del campo baja de **8 a 6**, que en un movil es la
diferencia entre ver el menu entero y tener que buscar.

⚠️ v154 y v430 las habian dejado SUELTAS a proposito —«enterrarla un nivel le costaria
un toque cada mañana a quien lo usa en el movil»— asi que esto lo revierte a sabiendas.
Medido en el codigo, esa razon no aplica igual a las tres: en credenciales el campo
**solo mira** (`editable=False`, las carga el admin) y en colillas mira y descarga;
la unica donde ACTUA es ausencias, y ahi la accion urgente —avisar de una baja, que
v430 registra al instante— **se compensa con un atajo desde Fichaje**, que es la
pantalla que esa persona abre esa misma mañana.

⚠️ Y el atajo no es una duplicacion accidental: es criterio del usuario —«estos avisos
en varios sitios ayudan a que no se pasen por alto»— aplicado a la accion mas urgente
que tiene el campo.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\home_ui.py"
s = io.open(P, encoding="utf-8").read()

# ── 1. las tres secciones -> una ─────────────────────────────────────────────
VIEJO1 = '''    ("credenciales", ":material/badge: My credentials"),
    ("colillas",     ":material/payments: My payslips"),
    # v430: la autogestión de ausencias. Va SUELTA, como el Pre-Start (v154): pedir
    # un día o avisar de una baja no es «un proyecto» ni «una herramienta», y
    # enterrarla un nivel le costaría un toque a quien la usa desde el móvil.
    ("ausencias",    ":material/event_busy: My absences"),
'''
NUEVO1 = '''    # v478 · Las tres pantallas «mías» bajo UN nivel (petición del usuario): la nav
    # del campo pasa de 8 a 6, que en un móvil es lo que separa ver el menú entero de
    # tener que buscarlo. ⚠️ v154/v430 las habían dejado sueltas a propósito —«costaría
    # un toque cada mañana a quien lo usa en el móvil»—, y eso sigue siendo cierto SOLO
    # para la acción urgente de ausencias (avisar de una baja), que por eso gana un
    # atajo desde Fichaje. Credenciales y colillas son consulta ocasional: ahí el toque
    # de más no le cuesta nada a nadie.
    ("autogestion",  ":material/account_circle: My things"),
'''

# ── 2. sus sub-pestañas ──────────────────────────────────────────────────────
VIEJO2 = '''_SUBSECCIONES_CAMPO = {
    "herramientas": (_SUBSECCIONES["herramientas"][0],
                     [(_i, _d) for _i, _d in _SUBSECCIONES["herramientas"][1]
                      if _i != "🦺 Pre-Start"]),
}
'''
NUEVO2 = '''_SUBSECCIONES_CAMPO = {
    "herramientas": (_SUBSECCIONES["herramientas"][0],
                     [(_i, _d) for _i, _d in _SUBSECCIONES["herramientas"][1]
                      if _i != "🦺 Pre-Start"]),
    # ⚠️ El ID conserva el emoji porque ES el identificador con el que casa el
    # despachador y al que apunta el atajo desde Fichaje (v232); el display es lo
    # único que se traduce. Ausencias va PRIMERA: es la única de las tres con una
    # acción, y las otras dos son consulta.
    "autogestion": ("campo_auto_sub", [
        ("🌴 Ausencias", ":material/event_busy: My absences"),
        ("🎫 Credenciales", ":material/badge: My credentials"),
        ("💰 Colillas", ":material/payments: My payslips")]),
}
'''

# ── 3. el despachador ────────────────────────────────────────────────────────
VIEJO3 = '''    if key in ("misproyectos", "prestart", "credenciales", "colillas", "ausencias"):
        _usr = st.session_state.get("auth", {}).get("usuario", "")
        if key == "misproyectos":
            from core.projects_ui import render_field_projects
            render_field_projects(_usr, grupo)
        elif key == "prestart":
            from core.prestart_ui import render_prestart_tab
            render_prestart_tab()
        elif key == "credenciales":
            from core.auth_ui import render_my_credentials
            render_my_credentials()
        elif key == "ausencias":
            from core import ausencias_ui
            ausencias_ui.render_mis_ausencias()
        else:
            from core.payroll_ui import render_mis_colillas
            render_mis_colillas(_usr, grupo)
        return
'''
NUEVO3 = '''    if key in ("misproyectos", "prestart", "autogestion"):
        _usr = st.session_state.get("auth", {}).get("usuario", "")
        if key == "misproyectos":
            from core.projects_ui import render_field_projects
            render_field_projects(_usr, grupo)
        elif key == "prestart":
            from core.prestart_ui import render_prestart_tab
            render_prestart_tab()
        else:
            # v478 · las tres «mías», bajo un solo nivel. ⚠️ Se compara contra el ID
            # EXACTO (con su emoji), que es lo que guarda el estado y a lo que apunta
            # el atajo de Fichaje — comparar contra el display navega a ninguna parte
            # y no da ningún error (el fallo real de v303).
            _sub = _sub_header("autogestion")
            if _sub == "🎫 Credenciales":
                from core.auth_ui import render_my_credentials
                render_my_credentials()
            elif _sub == "💰 Colillas":
                from core.payroll_ui import render_mis_colillas
                render_mis_colillas(_usr, grupo)
            else:
                from core import ausencias_ui
                ausencias_ui.render_mis_ausencias()
        return
'''

for viejo, nuevo, etq in ((VIEJO1, NUEVO1, "secciones"),
                          (VIEJO2, NUEVO2, "subsecciones"),
                          (VIEJO3, NUEVO3, "despachador")):
    if s.count(viejo) != 1:
        raise SystemExit("ancla %s: %d coincidencias" % (etq, s.count(viejo)))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/home_ui.py: autogestion con sus 3 sub-pestañas; el campo pasa de 8 a 6")
