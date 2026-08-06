import streamlit as st

SECC = [("home", "🏠  Home"), ("fichaje", "⏱  Fichaje"),
        ("planificacion", "📅  Planificación"), ("proyectos", "📁  Proyectos"),
        ("finanzas", "💰  Finanzas")]
SUB = {"planificacion": ["📋 Tablero", "👷 Usuarios"],
       "proyectos": ["📊 Proyectos", "🗂 Agrupaciones"]}
cur = st.session_state.get("cur", "planificacion")
cursub = st.session_state.get("cursub", "👷 Usuarios")

with st.sidebar:
    css = ["<style>",
           '[class*="st-key-nav_"] button,[class*="st-key-navsub_"] button{'
           'border:none!important;background:transparent!important;box-shadow:none!important;'
           'justify-content:flex-start!important;padding:5px 12px!important;min-height:0!important;}',
           '[class*="st-key-nav_"] button p,[class*="st-key-navsub_"] button p{'
           'text-align:left!important;width:100%!important;}',
           '[class*="st-key-navsub_"] button{padding-left:26px!important;font-size:.85rem!important;}',
           f'.st-key-nav_{cur} button{{background:#e8eef6!important;color:#1e4e79!important;'
           'font-weight:600!important;border-radius:8px!important;}']
    if cur in SUB:
        i = SUB[cur].index(cursub) if cursub in SUB[cur] else 0
        css.append(f'.st-key-navsub_{cur}_{i} button{{background:#e8eef6!important;'
                   'color:#1e4e79!important;font-weight:600!important;border-radius:8px!important;}')
    css.append("</style>")
    st.markdown("".join(css), unsafe_allow_html=True)
    st.markdown("###### NAVEGACIÓN")
    for k, lbl in SECC:
        has = k in SUB
        mark = "  ▾" if (has and k == cur) else ("  ▸" if has else "")
        if st.button(lbl + mark, key=f"nav_{k}", use_container_width=True):
            st.session_state["cur"] = k
            st.rerun()
        if has and k == cur:
            for j, s in enumerate(SUB[k]):
                if st.button(f"› {s}", key=f"navsub_{k}_{j}", use_container_width=True):
                    st.session_state["cursub"] = s
                    st.rerun()

st.write("cur:", cur, "· sub:", cursub)
