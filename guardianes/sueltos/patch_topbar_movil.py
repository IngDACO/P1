# -*- coding: utf-8 -*-
"""La barra superior deja de comerse un cuarto de la pantalla en el movil.

MEDIDO en la app real, con sesion de campo y viewport de 375x812 (no leido):
la barra son CUATRO columnas —atras · buscador · version · campana— y en un movil
Streamlit **las apila**, asi que una fila de 44 px se convierte en **112 px en tres
bandas** y el titulo de la pantalla empieza en y=196: el **24% del telefono** gastado
en chrome antes de ver nada. Es la misma clase que v291 y v394 arreglaron para
escritorio, en el sitio donde mas duele.

Con la regla: barra **112 → 44 px** y el titulo de y=196 a **y=128** — 68 px, un 8% de
la pantalla, recuperados.

⚠️ Y el camino hasta aqui es la mitad del valor: el primer intento ganaba los mismos
68 px y dejaba el `←` en **26 px de ancho**, por debajo del minimo de 36 que fijo la
auditoria de v326/v327 — habria reintroducido en el movil justo lo que aquella version
arreglo. Se vio MIDIENDO los botones, no mirando la captura. El suelo de 44 px lo cierra.

⚠️ Anclado a una KEY (`.st-key-cpxtop`), no a `:first-of-type`: un selector que depende
del ORDEN del documento se rompe en silencio en cuanto otra pantalla pinta una fila
antes (v304/v332), y un CSS que no casa no da ningun error. Misma tecnica de v410.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\home_ui.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''    st.markdown("<style>header[data-testid='stHeader']{background:transparent;}"
                "div.block-container{padding-top:1rem !important;}</style>",
                unsafe_allow_html=True)
    cback, c1, cver, c2 = st.columns([1, 7, 1.4, 1])
'''

NUEVO = '''    st.markdown(
        "<style>header[data-testid='stHeader']{background:transparent;}"
        "div.block-container{padding-top:1rem !important;}"
        # ⚠️ v478 · En un MOVIL, Streamlit apila las columnas: esta barra pasaba de una
        # fila de 44 px a TRES bandas de 112, y el titulo de la pantalla empezaba en
        # y=196 — el 24% del telefono en chrome. Medido con sesion de campo a 375x812.
        # Se fuerza a UNA fila por debajo de 640 px, con suelo de 44 px por boton: sin
        # ese suelo quedaban en 26 px de ancho, bajo el minimo de 36 de v326/v327, y en
        # el movil es donde peor se pulsa.
        "@media (max-width:640px){"
        ".st-key-cpxtop [data-testid='stHorizontalBlock']{flex-wrap:nowrap !important;"
        "align-items:center !important;gap:8px !important;}"
        ".st-key-cpxtop [data-testid='stColumn']{flex:0 0 44px !important;"
        "min-width:44px !important;}"
        ".st-key-cpxtop [data-testid='stColumn']:nth-child(2){flex:1 1 auto !important;"
        "min-width:0 !important;}"
        ".st-key-cpxtop button{width:100% !important;min-width:44px !important;}"
        "}</style>", unsafe_allow_html=True)
    # ⚠️ El contenedor se usa como OBJETO (`_top.columns`), no con `with`: asi los
    # bloques de abajo no hay que reindentarlos, que es la clase de cambio que rompio
    # v120 y v148.
    _top = st.container(key="cpxtop")
    cback, c1, cver, c2 = _top.columns([1, 7, 1.4, 1])
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/home_ui.py: la barra superior cabe en UNA fila en el movil")
