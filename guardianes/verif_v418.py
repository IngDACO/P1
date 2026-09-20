"""v418: el Pre-Start deja de pedir lo que ya sabe.

Dos peticiones del usuario y una tercera pieza que las hace correctas:

  (a) el PROYECTO se preselecciona por tener FICHAJE ABIERTO, no por el rol. v170 lo
      limitó al campo dando por hecho que «admin/propietario no fichan» — falso desde
      v150, donde el fichaje pasó a ser de dos relojes para TODOS los roles;

  (b) los ASISTENTES salen de la cuadrilla (asignados + fichados hoy), en vez de
      teclearse. Un nombre mal escrito no casa con `pendiente_de_firma` y a esa persona
      se le seguiría pidiendo firmar una charla en la que ya consta;

  (c) ⚠️ y por eso se guarda el LOGIN del asistente: con la lista, dos homónimos
      («Mei Chen», v413) producen entradas IDÉNTICAS, y sin el login firmar una apagaría
      el aviso de la otra. El respaldo por nombre queda ACOTADO a los asistentes que no
      tienen login — si comparase contra todos, anularía el desempate (lo cazó la prueba,
      no la lectura del código).
"""
import ast
import io
import json
import sys
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
sys.path.insert(0, str(RAIZ))

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


def _arbol(fich):
    src = (RAIZ / "core" / fich).read_text(encoding="utf-8")
    return ast.parse(tokenize.untokenize(
        [t for t in tokenize.generate_tokens(io.StringIO(src).readline)
         if t.type != tokenize.COMMENT]))


# ── (a) La preselección no puede volver a depender del ROL ──────────────────
print("== a) el proyecto se preselecciona por FICHAJE, no por rol ==")
arb = _arbol("prestart_ui.py")
fn = next(n for n in ast.walk(arb)
          if isinstance(n, ast.FunctionDef) and n.name == "render_prestart_tab")
# el `if` que envuelve la búsqueda del fichaje no puede comparar contra "campo"
_gate = False
for n in ast.walk(fn):
    if not isinstance(n, ast.If):
        continue
    usa_open = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                   and c.func.attr == "open_sessions" for c in ast.walk(n))
    if not usa_open:
        continue
    if any(isinstance(c, ast.Constant) and c.value == "campo" for c in ast.walk(n.test)):
        _gate = True
chk("la búsqueda del fichaje NO está detrás de un `rol == 'campo'`", not _gate)
_usa = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
           and c.func.attr == "open_sessions" for c in ast.walk(fn))
chk("...y sigue consultando el fichaje abierto", _usa)

# ── (b) Los asistentes salen de una lista, y se puede añadir a mano ─────────
print("\n== b) los asistentes se ELIGEN, y cabe quien no está de alta ==")
fa = next((n for n in ast.walk(arb)
           if isinstance(n, ast.FunctionDef) and n.name == "_asistentes_con_firma"), None)
chk("existe `_asistentes_con_firma`", fa is not None)
_ms = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
          and c.func.attr == "multiselect" for c in ast.walk(fa))
chk("se eligen de un multiselect (ya no se teclean uno a uno)", _ms)
cad = "".join(n.value for n in ast.walk(fa)
              if isinstance(n, ast.Constant) and isinstance(n.value, str))
chk("...y queda la vía de nombre libre para quien no está en la lista",
    "ps_invitados" in cad or "invit" in cad)
fc = next((n for n in ast.walk(arb)
           if isinstance(n, ast.FunctionDef) and n.name == "_cuadrilla"), None)
chk("existe `_cuadrilla`", fc is not None)
_asig = any(isinstance(c, ast.Constant) and c.value == "FieldAssigned"
            for c in ast.walk(fc))
_fich = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
            and c.func.attr == "proyectos_por_usuario_dia" for c in ast.walk(fc))
chk("la lista incluye a los ASIGNADOS", _asig)
chk("...y a los que FICHARON hoy", _fich)

# ⚠️ La clave del lienzo no puede ir por POSICIÓN: al añadir o quitar a alguien,
# la firma ya dibujada pasaría a otra persona.
fk = next((n for n in ast.walk(arb)
           if isinstance(n, ast.FunctionDef) and n.name == "_clave_firma"), None)
chk("la firma se indexa por PERSONA, no por posición", fk is not None)

# ── (c) El login manda, y el respaldo por nombre está acotado ───────────────
print("\n== c) firmar uno no puede apagar el aviso del homónimo ==")
import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "x", "grupo": "g", "rol": "field"}
from core import prestart as PS, prestart_ui as PUI, clock, auth, timeclock  # noqa: E402

HOY = clock.today()


def _fila(asist):
    return {"ID": "PS-1", "ProjectID": "PRJ-1", "Date": HOY.isoformat(),
            "FacilitatedBy": "F", "Location": "", "DriveID": "", "File": "",
            "S1JSON": "{}", "S3JSON": "{}", "NearMiss": "NO",
            "Attendees": json.dumps(asist, ensure_ascii=False)}


_o = PS._records
try:
    PS._records = lambda: [_fila([{"name": "Mei Chen", "firmado": True,
                                   "usuario": "mchen2"}])]
    chk("quien firmó no vuelve a ver el aviso",
        PS.pendiente_de_firma("PRJ-1", "g", "Mei Chen", usuario="mchen2"), {})
    chk("LA OTRA homónima sigue teniendo que firmar",
        bool(PS.pendiente_de_firma("PRJ-1", "g", "Mei Chen", usuario="mchen")), True)
    # compatibilidad con lo ya registrado antes de v418
    PS._records = lambda: [_fila([{"name": "Mei Chen", "firmado": True}])]
    chk("registro ANTERIOR (sin login) sigue casando por nombre",
        PS.pendiente_de_firma("PRJ-1", "g", "Mei Chen", usuario="mchen"), {})
    chk("...y también si no se pasa usuario",
        PS.pendiente_de_firma("PRJ-1", "g", "Mei Chen"), {})
    # invitado tecleado a mano: no tiene login y debe constar por su nombre
    PS._records = lambda: [_fila([{"name": "Pepe Sub", "firmado": True}])]
    chk("un invitado a mano consta por su nombre",
        PS.pendiente_de_firma("PRJ-1", "g", "pepe  SUB", usuario="psub"), {})
finally:
    PS._records = _o

# Lo que se GUARDA es el nombre + el login, nunca la etiqueta con el login dentro.
f = PS._asistentes_para_hoja([{"name": "Mei Chen", "initial": "MC",
                               "usuario": "mchen2", "sig": b"x"}])
chk("se guarda el NOMBRE limpio", f[0]["name"], "Mei Chen")
chk("...y el login en su propio campo", f[0].get("usuario"), "mchen2")
chk("un asistente sin login no inventa uno",
    "usuario" in PS._asistentes_para_hoja([{"name": "Pepe", "sig": None}])[0], False)

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
