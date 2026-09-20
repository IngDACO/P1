# -*- coding: utf-8 -*-
"""FASE 0.1 — la caché del lote deja de acoplar a todos los clientes.

`invalidar()` hacía `_lote.clear()` **sin argumento**, que borra la entrada de TODOS
los libros. O sea que una escritura de un cliente obligaba a releer a todos los demás:
con N clientes activos, cada guardado costaba hasta N lecturas en vez de una.

⚠️ Verificado EN VIVO antes de escribir esto (no leído en la documentación): con
Streamlit 1.57, `f.clear("LIBRO_A")` relee A y **deja B en caché**; sin argumento
relee los dos.

⚠️ El argumento es el TÍTULO de la hoja, no el sheet_id, porque las hojas GLOBALES
(Login, Groups, Rails, Manuals, Library, LibraryModels) viven en el MAESTRO y no en el
libro del grupo: resolver «el libro de la sesión» tras escribir en una de ellas
limpiaría otro libro y dejaría el valor viejo hasta 120 s — el «lo guardé y no sale»
que v339 vino a evitar.

⚠️ Y sin título se sigue tirando el lote ENTERO, que es el comportamiento de siempre y
el SEGURO: limpiar de más cuesta una lectura; limpiar el libro equivocado enseña datos
viejos. Un llamador que se olvide no rompe nada.
"""
import ast
import io
import os

RAIZ = "C:\\Users\\diego\\P1\\survey_app\\core"

# ── 1 · la función ───────────────────────────────────────────────────────────
P = os.path.join(RAIZ, "hojas.py")
s = io.open(P, encoding="utf-8").read()

VIEJO = '''def invalidar():
    try:
        _lote.clear()
    except Exception:
        pass
'''

NUEVO = '''def invalidar(titulo: str = "", grupo: str = None):
    """Tira el lote. Con `titulo`, SOLO el del libro donde vive esa hoja.

    ## Por qué recibe el título

    ⚠️ Antes hacía `_lote.clear()` sin argumento, que borra la entrada de **todos los
    libros**: una escritura de un cliente obligaba a releer a todos los demás, así que
    los inquilinos se acoplaban entre sí contra el techo de 60 lecturas/min de la
    ÚNICA cuenta de servicio.

    ⚠️ Y el argumento es el TÍTULO, no el `sheet_id`, porque las hojas GLOBALES
    (`Login`, `Groups`, `Rails`, `Manuals`, `Library`, `LibraryModels`) viven en el
    MAESTRO y no en el libro del grupo: resolver «el libro de la sesión» tras escribir
    en una de ellas limpiaría **otro** libro y dejaría el valor viejo hasta 120 s —
    el «lo guardé y no sale» que v339 vino a evitar.

    ⚠️ **Sin título se tira ENTERO**, que es el comportamiento de siempre y el seguro:
    limpiar de más cuesta una lectura; limpiar el libro equivocado enseña datos viejos.
    Un llamador que se olvide degrada al comportamiento anterior, no rompe nada.
    """
    sid = ""
    if titulo:
        try:
            sid = timeclock.sheet_id_para(titulo, grupo)
        except Exception as e:
            # No se pudo resolver el libro: se limpia TODO, que es lo conservador.
            logger.warning("hojas: no se pudo resolver el libro de %s: %s", titulo, e)
    try:
        if sid:
            _lote.clear(sid)
        else:
            _lote.clear()
    except Exception:
        # `clear(arg)` existe desde Streamlit 1.36; si algún día no estuviera, se cae
        # al borrado completo antes que dejar la caché sucia.
        try:
            _lote.clear()
        except Exception:
            pass
'''

if s.count(VIEJO) != 1:
    raise SystemExit("hojas.py: ancla no unica (%d)" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("hojas.py: invalidar(titulo) limpia SOLO el libro de esa hoja")

# ── 2 · los llamadores ───────────────────────────────────────────────────────
# El título de cada módulo, DERIVADO de lo que ese módulo lee (no escrito a ojo).
# Donde el módulo lee por variable (`title`) o por literal, se pone una hoja suya
# representativa: lo que importa es EN QUÉ LIBRO vive, y las hojas de un mismo
# módulo viven todas en el mismo.
LLAMADORES = {
    "alerts.py":       '"Alerts"',
    "auditoria.py":    "SHEET",
    "ausencias.py":    "SHEET",
    "auth.py":         '"Login"',           # GLOBAL -> maestro
    "catalogo.py":     "SHEET",
    "clientes.py":     "CLIENTES_SHEET",
    "correcciones.py": "SHEET",
    "credentials.py":  "SHEET",
    "expenses.py":     "SHEET",
    "inventory.py":    '"Assets"',
    "invoices.py":     "FACTURAS_SHEET",
    "library.py":      "SHEET",             # GLOBAL -> maestro
    "orders.py":       "SHEET",
    "payroll.py":      "NOMINAS_SHEET",
    "prestart.py":     "SHEET",
    "projects.py":     '"Projects"',
    "quotes.py":       "SHEET",
    "rails.py":        "RIELES_SHEET",      # GLOBAL -> maestro
    "roster.py":       "ROSTER_SHEET",
    "timeclock.py":    '"Sheet1"',
    "toolruns.py":     "SHEET",
}

tot = 0
for fich, arg in sorted(LLAMADORES.items()):
    ruta = os.path.join(RAIZ, fich)
    t = io.open(ruta, encoding="utf-8").read()
    n = t.count("hojas.invalidar()")
    if n == 0:
        raise SystemExit("%s: no hay ninguna llamada que cambiar" % fich)
    t = t.replace("hojas.invalidar()", "hojas.invalidar(%s)" % arg)
    ast.parse(t)
    io.open(ruta, "w", encoding="utf-8", newline="").write(t)
    tot += n
    print("   %-18s x%d -> hojas.invalidar(%s)" % (fich, n, arg))

print("total: %d llamadas" % tot)
