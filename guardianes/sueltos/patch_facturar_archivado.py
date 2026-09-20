"""v358 — una obra ARCHIVADA se puede facturar.

Verificando v357 en producción: el atajo de `prueba1` ($330 pendientes) llevaba al alta
de factura y **esa obra no estaba entre las opciones de alcance**, así que la
preselección no hacía nada y el radio se quedaba en «Todo el cliente». Causa:
`list_projects(grupo)` oculta los archivados (v149) y `prueba1` está archivado.

Archivar no es no-cobrar: lo habitual es archivar al terminar y facturar después. Es la
misma familia que v310 (los costos de los archivados desaparecían del grupo) y v322 (los
ascensores archivados se caían de su agrupación).

Además mi guarda tenía un hueco: contemplaba «es de otro cliente» pero no «no está en la
lista» — y ese caso salía en SILENCIO.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

u = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\invoices_ui.py")
s = u.read_text(encoding="utf-8")

VIEJO = '''    # Proyectos del cliente (para precargar y para el desplegable de líneas)
    prjs = [p for p in P.list_projects(grupo=grupo) if C.es_del_cliente(p, cid, cnorm)]'''

NUEVO = '''    # Proyectos del cliente (para precargar y para el desplegable de líneas)
    prjs = [p for p in P.list_projects(grupo=grupo) if C.es_del_cliente(p, cid, cnorm)]
    # ⚠️ v358: `list_projects` oculta los ARCHIVADOS (v149), pero archivar no es
    # no-cobrar: lo normal es archivar al terminar y facturar después. Si el atajo desde
    # el proyecto apunta a una obra que no está en la lista, se añade — si no, el
    # formulario se abría sin esa opción y la preselección no hacía nada, en silencio.
    _peek = st.session_state.get("_fac_prj_pending")
    if _peek and str(_peek) not in {str(p.get("ID", "")) for p in prjs}:
        _extra = P.get_project(str(_peek)) or {}
        if _extra and str(_extra.get("Grupo", "")) == str(grupo):
            prjs = prjs + [_extra]'''

assert VIEJO in s, "ancla de prjs no encontrada"
s = s.replace(VIEJO, NUEVO)

# y que el caso «no se pudo resolver» deje de ser silencioso
VIEJO2 = '''    _pend_pid = st.session_state.pop("_fac_prj_pending", None)
    if _pend_pid:
        _et = _lbl.get(str(_pend_pid))
        if _et in prj_names:
            st.session_state["fac_scope"] = _et
        elif _et:
            st.info(":material/info: Ese proyecto no es de este cliente; elige el alcance a mano.")'''
NUEVO2 = '''    _pend_pid = st.session_state.pop("_fac_prj_pending", None)
    if _pend_pid:
        _et = _lbl.get(str(_pend_pid))
        if _et in prj_names:
            st.session_state["fac_scope"] = _et
        else:
            # ⚠️ Antes, si el proyecto no estaba en la lista, `_et` era None y NO se
            # decía nada: el usuario acababa en «Todo el cliente» sin saber por qué.
            st.info(":material/info: No se pudo preseleccionar ese proyecto para este "
                    "cliente (revisa a qué cliente está enlazado). Elige el alcance a mano.")'''
assert VIEJO2 in s, "ancla de la guarda no encontrada"
s = s.replace(VIEJO2, NUEVO2)
u.write_text(s, encoding="utf-8")
print("✓ invoices_ui: se puede facturar una obra archivada, y el fallo deja de ser mudo")
