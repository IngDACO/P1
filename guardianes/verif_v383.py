"""GUARDIÁN v383 — firma dibujada en el Pre-Start.

Se ejercita de verdad: se genera un PDF con firmas reales, se comprueba que la
imagen entra, que la firma NO llega a la hoja, y que las ramas de degradación
funcionan (sin lienzo, y con una firma corrupta — la del `except` que esconde los
NameError, como pasó en v370).
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st                                     # noqa: E402
st.session_state["auth"] = {"usuario": "jlopez", "grupo": "cliente1", "rol": "field"}

from core import prestart as PS, prestart_pdf as PP        # noqa: E402
from core import clock                                     # noqa: E402

ok = True


def png_firma(texto="firma"):
    """Un PNG con un trazo de verdad (lo que devolvería el lienzo)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (420, 90), "white")
    d = ImageDraw.Draw(img)
    d.line([(20, 60), (90, 20), (160, 70), (240, 25), (330, 60)], fill="black", width=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


BASE = {
    "grupo": "cliente1", "proyecto_id": "PRJ-0007", "proyecto_nombre": "Meriton Torre A",
    "fecha": clock.today("cliente1"), "hora": "07:30", "location": "Sydney",
    "facilitador": "Javier López", "activities_notes": "prueba",
    "s1": {k: "YES" for k, _ in PS.CHECKS_S1},
    "s3": {k: "YES" for k, _ in PS.CHECKS_S3},
    "near_miss": "NO", "near_miss_desc": "", "general_notes": "",
    "creado_por": "jlopez",
}

print("== 1. el PDF con firmas dibujadas ==")
firmas = [{"name": "Javier López", "initial": "JL", "sig": png_firma()},
          {"name": "Mei Chen", "initial": "MC", "sig": png_firma()}]
d = dict(BASE, attendees=firmas)
pdf = PP.generate_prestart_pdf(d)
print(f"   PDF generado: {len(pdf):,} bytes")
ok &= len(pdf) > 5000

# ¿la imagen ENTRÓ? Un PDF con 2 firmas pesa notablemente más que uno sin ellas.
sin = PP.generate_prestart_pdf(dict(BASE, attendees=[
    {"name": "Javier López", "initial": "JL", "sig": None},
    {"name": "Mei Chen", "initial": "MC", "sig": None}]))
print(f"   el mismo PDF SIN firmas: {len(sin):,} bytes")
_entro = len(pdf) > len(sin) + 1000
ok &= _entro
print(f"   {'✓ la firma va dentro del PDF' if _entro else '‼️ el PDF no engorda: la imagen no entró'}"
      f"  (+{len(pdf)-len(sin):,} bytes)")

print("\n== 2. ⚠️ la firma NO puede llegar a la hoja ==")
fila = PS._asistentes_para_hoja(firmas)
txt = json.dumps(fila, ensure_ascii=False)
_sin_bytes = "sig" not in txt
ok &= _sin_bytes
print(f"   {'✓' if _sin_bytes else '‼️'} el JSON de la hoja no lleva la imagen")
print(f"   {len(txt)} caracteres (una celda de Sheets admite 50.000)")
ok &= len(txt) < 2000
print(f"   contenido: {txt[:120]}")
_marca = all("firmado" in a for a in fila)
ok &= _marca
print(f"   {'✓' if _marca else '‼️'} pero SÍ queda el rastro de que firmó")
# y que serializa (con bytes dentro, json.dumps reventaría)
try:
    json.dumps(firmas)
    print("   ‼️ los bytes serializan?? revisar")
    ok = False
except TypeError:
    print("   ✓ confirmado: los bytes NO serializan → sin el filtro, submit fallaría")

print("\n== 3. degradación: sin lienzo y con firma corrupta ==")
d2 = dict(BASE, attendees=[{"name": "Sin firma", "initial": "SF", "sig": None}])
p2 = PP.generate_prestart_pdf(d2)
print(f"   sin lienzo (solo iniciales) → PDF de {len(p2):,} bytes  ✓ se genera igual")
ok &= len(p2) > 3000
# ⚠️ la rama del `except`, que es donde vivía el NameError de v370
d3 = dict(BASE, attendees=[{"name": "Corrupta", "initial": "CC", "sig": b"esto-no-es-un-png"}])
try:
    p3 = PP.generate_prestart_pdf(d3)
    print(f"   firma CORRUPTA → PDF de {len(p3):,} bytes  ✓ cae a las iniciales sin romper")
    ok &= len(p3) > 3000
except Exception as e:
    ok = False
    print(f"   ‼️ REVIENTA con una firma corrupta: {type(e).__name__}: {e}")

print("\n== 4. el detector de firma en blanco ==")
# ⚠️ Detectarla por el canal ALFA daba 58.800 «píxeles de trazo» en un lienzo VACÍO:
#    todo el mundo constaría como firmado.
import numpy as np                                          # noqa: E402
from core import prestart_ui as PU                          # noqa: E402


class _Res:
    def __init__(self, arr):
        self.image_data = arr


blanco = np.dstack([np.full((90, 420, 3), 255, dtype="uint8"),
                    np.full((90, 420), 255, dtype="uint8")])
trazo = blanco.copy()
trazo[40:46, 30:300, :3] = 0
r1, r2 = PU._firma_png(_Res(blanco)), PU._firma_png(_Res(trazo))
ok &= r1 is None and r2 is not None
print(f"   {'✓' if r1 is None else '‼️'} lienzo en blanco → None (no cuenta como firmado)")
print(f"   {'✓' if r2 else '‼️'} lienzo con trazo → PNG de {len(r2) if r2 else 0} bytes")

print("\n" + ("✅ v383 OK: la firma entra en el PDF, no llega a la hoja, degrada sin "
              "romper y un lienzo vacío no cuenta" if ok else "⚠️ REVISAR"))
sys.exit(0 if ok else 1)
