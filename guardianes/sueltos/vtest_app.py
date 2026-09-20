"""¿Sirve `streamlit-drawable-canvas` para la firma manual del Pre-Start?

⚠️ El componente es de 2023 y aquí corre Streamlit 1.57. Una dependencia mal
elegida ya provocó segfaults en el Cloud (v66), así que antes de prometer nada:
que RENDERICE, que DEVUELVA los trazos, y que de ahí salga un PNG que reportlab
pueda meter en el PDF.
"""
import io

import streamlit as st

st.set_page_config(page_title="firma", layout="wide")
st.title("Prueba de firma manual")

try:
    from streamlit_drawable_canvas import st_canvas
    st.success("import OK — streamlit_drawable_canvas disponible")
except Exception as e:
    st.error(f"NO se puede importar: {type(e).__name__}: {e}")
    st.stop()

st.caption("Dibuja algo en el recuadro:")
try:
    res = st_canvas(
        stroke_width=3,
        stroke_color="#111111",
        background_color="#ffffff",
        height=140,
        width=420,
        drawing_mode="freedraw",
        key="firma_test",
    )
    st.write("**el componente renderizó sin lanzar**")
except Exception as e:
    st.error(f"REVIENTA al renderizar: {type(e).__name__}: {e}")
    st.stop()

hay = res is not None and getattr(res, "image_data", None) is not None
st.write("¿devuelve image_data?", hay)

if hay:
    import numpy as np
    arr = res.image_data
    tinta = int((arr[:, :, 3] > 0).sum())          # píxeles con alfa = trazo
    st.write(f"forma del array: {arr.shape} · píxeles con trazo: **{tinta}**")
    if tinta:
        from PIL import Image
        img = Image.fromarray(arr.astype("uint8"), mode="RGBA")
        fondo = Image.new("RGB", img.size, "white")
        fondo.paste(img, mask=img.split()[3])
        buf = io.BytesIO()
        fondo.save(buf, format="PNG")
        st.write(f"PNG generado: **{len(buf.getvalue())} bytes**")
        st.image(buf.getvalue(), caption="lo que iría al PDF", width=300)
        # y que reportlab lo acepte
        try:
            from reportlab.platypus import Image as RLImage
            buf.seek(0)
            RLImage(buf, width=120, height=40)
            st.success("reportlab acepta el PNG → se puede meter en el PDF del Pre-Start")
        except Exception as e:
            st.error(f"reportlab NO lo acepta: {type(e).__name__}: {e}")
    else:
        st.info("aún sin trazos: dibuja para completar la prueba")
