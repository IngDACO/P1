"""v359 (2/2) — la pantalla para enlazar el libro + el límite dicho en voz alta.

⚠️ **El límite conocido**: las cachés de lectura de cada módulo (`_records`) están
indexadas por HOJA, no por libro. Los flujos de admin y campo van bien porque siempre
tienen un grupo en sesión y el lote (`hojas._lote`) sí está indexado por libro. Pero las
vistas CONSOLIDADAS del propietario —las que cruzan grupos— leerían solo el maestro.
Hacerlo bien es tocar el `_records` de 13 módulos, y sin un segundo libro real no se
puede verificar. Así que **se avisa** en vez de enseñar un consolidado incompleto sin
decir nada: un número que miente es peor que un número que falta.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) auth: saber qué grupos tienen libro propio ───────────────
a = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\auth.py")
s = a.read_text(encoding="utf-8")
if "def grupos_con_libro_propio" not in s:
    s += '''

def grupos_con_libro_propio() -> list:
    """Grupos que ya viven en su propio libro de Google (v359).

    Lo usan las vistas CONSOLIDADAS del propietario para avisar de que su resumen
    no los incluye todavía (ver el límite documentado en v359)."""
    return [str(g.get("Grupo", "")) for g in _group_records()
            if str(g.get("SheetID", "") or "").strip()]
'''
    a.write_text(s, encoding="utf-8")
    print("✓ auth.grupos_con_libro_propio")

# ── 2) auth_ui: enlazar el libro desde Administración → Grupos ──
u = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\auth_ui.py")
s = u.read_text(encoding="utf-8")
ANCLA = '''    # ── Zona horaria por grupo (v173) ──'''
NUEVO = '''    # ── Libro de Google propio de cada cliente (v359) ──
    # Aislamiento de datos: cada empresa puede vivir en su propio fichero, en vez de
    # compartirlo separada solo por una columna `Grupo`.
    if grupos:
        with st.expander("Libro de datos de cada cliente", icon=":material/menu_book:"):
            st.caption("Cada empresa cliente puede tener su **propio archivo de Google "
                       "Sheets**, para que sus datos no compartan fichero con los de "
                       "otra. Vacío = usa el libro maestro.")
            _gl = ui.elegir("Grupo", [g["Grupo"] for g in grupos], key="gsheet_sel",
                            vacio="— elige un grupo —")
            if _gl:
                _sid_now = auth.group_sheet_id(_gl)
                st.markdown(":material/info: Crea una hoja de cálculo en blanco, "
                            "**compártela como editor** con la cuenta de servicio de la "
                            "app, y pega aquí su enlace o su ID.")
                _nuevo = st.text_input("Enlace o ID del libro", value=_sid_now,
                                       key="gsheet_val",
                                       placeholder="https://docs.google.com/spreadsheets/d/…")
                _c1, _c2 = st.columns(2)
                if _c1.button(":material/link: Guardar enlace", key="gsheet_save",
                              use_container_width=True):
                    ok, msg = auth.set_group_sheet_id(_gl, _nuevo)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if _sid_now and _c2.button(":material/link_off: Volver al maestro",
                                           key="gsheet_del", use_container_width=True):
                    ok, msg = auth.set_group_sheet_id(_gl, "")
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
                if _sid_now:
                    st.success(":material/check_circle: **" + _gl + "** usa su propio "
                               "libro. `Login`, `Grupos` y `Rieles` siguen en el maestro: "
                               "son el registro de la app, no datos suyos.")
            # ⚠️ El límite se DICE. Un consolidado al que le faltan clientes sin avisar
            # es peor que no tenerlo (ver v359).
            _fuera = auth.grupos_con_libro_propio()
            if _fuera:
                st.warning(":material/warning: Con clientes en libros aparte, los "
                           "**resúmenes consolidados del propietario** todavía solo "
                           "cuentan los del maestro. Fuera del consolidado: **"
                           + ", ".join(_fuera) + "**. Cada cliente sí ve lo suyo completo.")

    # ── Zona horaria por grupo (v173) ──'''
if "Libro de datos de este cliente" not in s:
    assert ANCLA in s, "ancla de zona horaria no encontrada"
    s = s.replace(ANCLA, NUEVO, 1)
    u.write_text(s, encoding="utf-8")
    print("✓ auth_ui: bloque para enlazar el libro en Administración → Grupos")

# ── 3) el aviso en las vistas consolidadas del propietario ──────
d = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\admin_digest.py")
s = d.read_text(encoding="utf-8")
if "grupos_con_libro_propio" not in s:
    s = s.replace('''def owner_digest() -> list:''',
'''def grupos_fuera_del_maestro() -> list:
    """Grupos con libro propio (v359). Sus datos NO entran en este consolidado.

    ⚠️ Se expone para que la pantalla lo DIGA. Un resumen al que le faltan clientes sin
    avisar es peor que no tenerlo: el propietario tomaría decisiones sobre una foto
    incompleta creyéndola entera."""
    try:
        return auth.grupos_con_libro_propio()
    except Exception:
        return []


def owner_digest() -> list:''')
    d.write_text(s, encoding="utf-8")
    print("✓ admin_digest.grupos_fuera_del_maestro")
