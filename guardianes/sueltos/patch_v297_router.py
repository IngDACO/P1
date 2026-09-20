# -*- coding: utf-8 -*-
"""El chequeo del router: de nombres de SECCION a «cada pantalla la sirve su funcion».

⚠️ Va por fichero y con cadenas RAW: la ruta de Windows lleva `\\Users`, y en una
cadena normal `\\U` arranca un escape unicode → SyntaxError. Es la familia de la
trampa nº26 (los escapes que se rompen al pasarlos por un heredoc).
"""
import ast
import io

P = "verif_v297.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = (r'''# las 4 ramas nuevas estan en el router
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\home_ui.py").read_text(encoding="utf-8")
for k in ("misproyectos", "prestart", "credenciales", "colillas"):
    check(f"router contempla '{k}'", f'"{k}"' in src)
''')

NUEVO = (r'''# ⚠️ ACTUALIZADO en v478: `credenciales` y `colillas` ya no son claves de SECCION —
# el router llega a ellas por el ID de su sub-pestaña dentro de «autogestion». Lo que
# hay que proteger no es el nombre de la rama, sino que **cada pantalla del campo la
# siga sirviendo su funcion**. Se comprueba el ID EXACTO (con su emoji): comparar
# contra el display navega a ninguna parte y no da ningun error (el fallo de v303).
src = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\home_ui.py").read_text(encoding="utf-8")
for k in ("misproyectos", "prestart", "autogestion"):
    check(f"router contempla la seccion '{k}'", f'"{k}"' in src)
for k in ("\U0001F3AB Credenciales", "\U0001F4B0 Colillas"):
    check(f"router despacha el ID exacto '{k}'", f'"{k}"' in src)
for _fn in ("render_my_credentials", "render_mis_colillas", "render_mis_ausencias"):
    check(f"router llama a {_fn}", _fn in src)
''')

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v297.py: router por seccion + ID exacto + funcion")
