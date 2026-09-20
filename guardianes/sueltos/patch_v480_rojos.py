# -*- coding: utf-8 -*-
"""Los tres rojos de la suite de v480, clasificados uno a uno (regla v385).

A) `es_del_proyecto` con nombre VACIO devolvia True para CUALQUIER jornada general
   (`"" == ""`). No es cosmetico: las tres llamadas alimentan las horas del proyecto y
   el COSTO DE MANO DE OBRA, asi que una obra con el `Name` en blanco —y el cliente
   tiene acceso a su propio libro— se comeria todas las jornadas generales como suyas.
   Salio de un rojo que parecia falsa alarma.

B) `check_ceros.py` leia `Nombre`/`Grupo`, en español: v468 renombro esas columnas, asi
   que le llegaba el nombre VACIO a `es_del_proyecto` y por eso acusaba. ⚠️ Se mantuvo
   verde 12 versiones solo porque el libro de la demo no tenia obras: en cuanto hay una
   obra y una jornada, mentia. Es la clase de guardian que grita en cuanto entra un
   cliente real.

C) `verif_v455` exigia ver >=3 modelos de ingreso distintos en cuanto hubiera UNA obra.
   Su salvaguarda solo contemplaba el libro vacio. Con una obra la variedad es
   imposible, asi que la condicion pasa a pedir datos suficientes, no simplemente datos.
"""
import ast
import io

# ── A ── el fallback nunca puede casar con un nombre vacio ───────────────────
P = "C:\\Users\\diego\\P1\\survey_app\\core\\timeclock.py"
s = io.open(P, encoding="utf-8").read()
VA = '''    rp = pid_of(r)
    if rp and pid:
        return rp == str(pid).strip()
    return (str(r.get("Project", "")).strip().casefold()
            == str(nombre or "").strip().casefold())
'''
NA = '''    rp = pid_of(r)
    if rp and pid:
        return rp == str(pid).strip()
    # ⚠️ v480: sin nombre NO hay respaldo posible. Antes `"" == ""` daba True, así que
    # un proyecto con el `Name` en blanco —o una llamada que lo lea con la clave
    # equivocada— se quedaba con TODAS las jornadas generales (las que no llevan
    # proyecto) y con sus horas. Eso entra en `project_hours` y en el costo de mano de
    # obra, o sea que era un fallo de dinero silencioso. Lo destapó un rojo de la suite
    # que parecía falsa alarma.
    _nom = str(nombre or "").strip()
    if not _nom:
        return False
    return str(r.get("Project", "")).strip().casefold() == _nom.casefold()
'''
if s.count(VA) != 1:
    raise SystemExit("A: ancla no unica (%d)" % s.count(VA))
s = s.replace(VA, NA)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("A) core/timeclock.py: sin nombre no hay respaldo (era un fallo de dinero)")

# ── B ── el diagnostico, con las claves de v468 ──────────────────────────────
P2 = "check_ceros.py"
s2 = io.open(P2, encoding="utf-8").read()
VB = '''    pid, nom = str(p.get("ID", "")), str(p.get("Nombre", ""))
    h = P.project_hours(nom, p.get("Grupo"), pid=pid)
'''
NB = '''    # ⚠️ v480: `Nombre`/`Grupo` son de ANTES de v468. Con la clave vieja llegaba el
    # nombre vacío y `es_del_proyecto` casaba con cualquier jornada general, así que
    # este chequeo acusaba a obras inocentes. Se mantuvo verde solo mientras el libro
    # de la demo estuvo sin obras.
    pid, nom = str(p.get("ID", "")), str(p.get("Name", ""))
    h = P.project_hours(nom, p.get("Group"), pid=pid)
'''
if s2.count(VB) != 1:
    raise SystemExit("B: ancla no unica (%d)" % s2.count(VB))
s2 = s2.replace(VB, NB)
ast.parse(s2)
io.open(P2, "w", encoding="utf-8", newline="").write(s2)
print("B) check_ceros.py: claves de v468")

# ── C ── variedad solo cuando hay con que ────────────────────────────────────
P3 = "verif_v455.py"
s3 = io.open(P3, encoding="utf-8").read()
VC = '''if not _mods:
    print("     (sin proyectos: no se puede comprobar la variedad de modelos)")
else:
    chk(len(_vistos) >= 3, f"\u2026y el chequeo ve variedad real, no un solo caso ({len(_vistos)})")
'''
NC = '''# \u26a0\ufe0f v480: la salvaguarda solo contemplaba el libro VACIO, y con UNA obra exigia ver
# tres modelos distintos \u2014 imposible por aritmetica, no por un fallo. Se pide que haya
# con que comprobar, no simplemente que haya algo.
if len(_mods) < 3:
    print(f"     ({len(_mods)} proyecto(s): no hay con que comprobar la variedad)")
else:
    chk(len(_vistos) >= 3, f"\u2026y el chequeo ve variedad real, no un solo caso ({len(_vistos)})")
'''
if s3.count(VC) != 1:
    raise SystemExit("C: ancla no unica (%d)" % s3.count(VC))
s3 = s3.replace(VC, NC)
ast.parse(s3)
io.open(P3, "w", encoding="utf-8", newline="").write(s3)
print("C) verif_v455.py: variedad solo con >=3 obras")
