# -*- coding: utf-8 -*-
"""Añade a la sección de v445 el hallazgo del centinela congelado."""
import io
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = r"C:\Users\diego\P1\CLAUDE.md"

BLOQUE = """
### ⚠️ Y el hallazgo del rojo de la suite: un `t()` que se CONGELA al importar
`verif_auth_guards` se puso rojo y, al mirar el código acusado (regla v385), había
algo peor que un guardián caducado:

```python
SESION_OCUPADA = t("This account already has an active session on another device.")
```

Eso se evalúa **al IMPORTAR `auth`**, cuando todavía no hay sesión ni idioma elegido,
así que la cadena queda **congelada** en el idioma de ese instante. Y esta constante
no es un texto cualquiera: **se compara** (`auth_ui` hace `tok == auth.SESION_OCUPADA`
para decidir si ofrece el botón «cerrar la otra sesión e iniciar aquí»). El día que se
llene el diccionario español, traducir un lado y no el otro **haría desaparecer ese
botón sin dar ningún error** — que es justo el fallo silencioso que toda esta
migración intenta evitar, esta vez desde dentro del propio motor.

Arreglo: la constante vuelve a ser un **CENTINELA** (dato interno, se compara) y la
traducción se mueve a donde se PINTA (`st.error(f"…: {t(tok)}")`). Es la misma
separación etiqueta/dato del resto del módulo i18n.
⚠️ Barrido del repo: **`d()` a nivel de módulo SÍ vale** —devuelve siempre el idioma
base (v436), así que `plumb.LINE_NAMES` está bien—, y **`app.py` no cuenta**: no es un
módulo importado, es el script que Streamlit re-ejecuta entero en cada rerun, así que
ahí no se congela nada (incluirlo daba 8 falsos positivos). Con las dos exclusiones,
0 casos. Guardián permanente, validado en las dos direcciones.
"""

s = io.open(P, encoding="utf-8").read()
ancla = "### Lo que queda de F5"
assert ancla in s, "ancla NO casa"
assert "un `t()` que se CONGELA al importar" not in s, "ya estaba insertado"
s = s.replace(ancla, BLOQUE.strip() + "\n\n" + ancla, 1)
io.open(P, "w", encoding="utf-8", newline="").write(s)

for simbolo in ("SESION_OCUPADA", "auth_ui", "plumb.LINE_NAMES", "app.py"):
    assert simbolo in s, f"perdió {simbolo!r}"
print("bloque del centinela añadido a la sección de v445")
