"""
Bloque compartido "descargar + guardar en el proyecto" para las herramientas.

Las cuatro herramientas de cálculo lo usan igual, así que vive aquí en vez de
copiarse cuatro veces (y desviarse cuatro veces).

Flujo: elegir proyecto → descargar el PDF → guardarlo contra el proyecto
(`toolruns.registrar`, que escribe en la hoja Calculos y archiva en Drive).
"""
import streamlit as st

from core import projects as P
from core import toolruns


def _proyectos_de(rol, usuario, grupo):
    """Mismo criterio que el Pre-Start: cada rol ve lo suyo."""
    if rol == "propietario":
        return P.list_projects()
    if rol == "administrador":
        return P.list_projects(grupo=grupo)
    return P.list_projects_for_field(usuario, grupo=grupo)


def render_guardar(herramienta: str, titulo_pdf: str, pdf_bytes: bytes,
                   resumen: str, datos: dict, nombre_archivo: str,
                   key: str) -> None:
    """Descarga del PDF + guardado contra un proyecto.

    `herramienta` es la clave de `toolruns.HERRAMIENTAS`.
    """
    if not pdf_bytes:
        return

    st.markdown("---")
    c1, c2 = st.columns([1, 1])
    c1.download_button(f"⬇️ Descargar {titulo_pdf} (PDF)", data=pdf_bytes,
                       file_name=nombre_archivo, mime="application/pdf",
                       use_container_width=True, key=f"dl_{key}")

    if not toolruns.is_configured():
        c2.caption("🔒 Guardar en el proyecto requiere Google Sheets configurado.")
        return

    a = st.session_state.get("auth", {}) or {}
    rol, usuario = a.get("rol", ""), a.get("usuario", "")
    grupo = a.get("grupo", "")
    proys = _proyectos_de(rol, usuario, grupo)
    if not proys:
        c2.caption("No hay proyectos disponibles para asociar este cálculo.")
        return

    idmap = {f"{p.get('Nombre')} ({p.get('ID')})": p for p in proys}
    with c2:
        sel = st.selectbox("Guardar en el proyecto", list(idmap.keys()),
                           key=f"prj_{key}")
        if st.button("💾 Guardar en el proyecto", use_container_width=True,
                     key=f"save_{key}"):
            prj = idmap[sel]
            with st.spinner("Guardando..."):
                res = toolruns.registrar(
                    pid=str(prj.get("ID", "")),
                    grupo=str(prj.get("Grupo", grupo)),
                    herramienta=herramienta, resumen=resumen, datos=datos,
                    usuario=usuario, pdf=pdf_bytes, filename=nombre_archivo)
            if res.get("ok"):
                msg = f"✅ Guardado como **{res['id']}** en {prj.get('Nombre')}."
                if not res.get("drive_id"):
                    msg += " (El PDF no se archivó en Drive: revisa la conexión.)"
                st.success(msg)
            else:
                st.error(f"No se pudo guardar: {res.get('error')}")
