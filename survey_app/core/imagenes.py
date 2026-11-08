# -*- coding: utf-8 -*-
"""Las fotos que entran en la app, abiertas solo como JPEG, PNG o WEBP (v655).

Pillow reconoce un fichero por su CONTENIDO, no por la extensión: una «foto.jpg» que por dentro
es un PSD, un TIFF o un FITS pasa por ese decodificador. Los fallos conocidos de Pillow están
casi todos en formatos que la app no usa nunca, y la versión que admite Streamlit 1.64 (`<13`)
no los arregla todos. Así que Pillow, en esta app, solo abre lo que la app acepta:

- `limitar_pillow()` quita del registro de Pillow todos los demás formatos para ABRIR (guardar
  sigue igual). Lo llama `app.py` al arrancar, antes de pintar nada, y vale para todo lo que use
  Pillow por dentro: `st.image`, reportlab, las miniaturas.
- `abrir(datos)` = `Image.open` con esos formatos, para los sitios que abren una foto subida.

Las 750 fotos de la Biblioteca son `.jpg` (medido el 08/11/2026). MPO es el JPEG de varias
imágenes que guardan algunos móviles: se queda.

Módulo HOJA: solo Pillow.
"""
import io

FORMATOS = ("JPEG", "PNG", "WEBP", "MPO")


def limitar_pillow() -> None:
    """Deja en Pillow solo los decodificadores de `FORMATOS` (repetirlo no hace nada)."""
    from PIL import Image
    Image.init()                      # carga todos los plugins una vez (después, `init` no hace nada)
    for k in list(Image.OPEN):
        if k not in FORMATOS:
            Image.OPEN.pop(k, None)
    # `Image.open` recorre `ID` y busca cada uno en `OPEN`: los dos, iguales
    Image.ID[:] = [k for k in Image.ID if k in FORMATOS]


def abrir(datos):
    """`Image.open` de una foto subida (bytes o fichero), solo en los formatos permitidos."""
    from PIL import Image
    limitar_pillow()
    fuente = io.BytesIO(datos) if isinstance(datos, (bytes, bytearray)) else datos
    # ⚠️ Solo los que Pillow tiene REGISTRADOS para abrir: «MPO» no lo está (lo abre el de JPEG,
    # que lo reconoce dentro), y pedirlo en `formats=` daba KeyError (lo destapó verif_v655).
    return Image.open(fuente, formats=[f for f in FORMATOS if f in Image.OPEN])
