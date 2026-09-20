# -*- coding: utf-8 -*-
"""v381 estaba anclado a `PRJ-0007`, una fila que ya no existe.

⚠️ CADUCADO, no regresion — y comprobado antes de tocar: con un proyecto que SI existe,
admin y propietario devuelven **lo mismo**; la diferencia solo aparecia con un pid
inexistente, donde `datos_asociados` no puede resolver el grupo y cae a la sesion (el
propietario, sin grupo, al maestro vacio). Es la misma caducidad que v475 arreglo en
`verif_v379` (iba fijado a «Meriton»): un ancla sobre DATOS caduca en cuanto alguien
los borra (trampa nº16), y la demo se vacio en v456.

⚠️ Y el reanclaje lo deja MAS fuerte que antes: el chequeo viejo comparaba dos numeros
de la hoja real que podian ser **los dos CERO** —comparar 0 con 0 no distingue nada,
el paso en vacio de la trampa nº1—. Ahora el caso construido tiene datos que contar y
se exige explicitamente que los haya antes de comparar.
"""
import ast
import io

P = "verif_v381.py"
s = io.open(P, encoding="utf-8").read()

VIEJO = '''como("administrator", "cliente1")
d1 = P.datos_asociados("PRJ-0007")
como("owner")
d2 = P.datos_asociados("PRJ-0007")
'''

NUEVO = '''# ⚠️ Caso CONSTRUIDO (v477): antes iba fijado a `PRJ-0007`, que dejo de existir al
# vaciarse la demo (v456) — y con un pid inexistente `datos_asociados` no puede
# resolver el grupo y cae a la sesion, asi que la diferencia que salia NO era el fallo
# de v381 sino el ancla caducada. Ademas el caso trae datos que CONTAR: comparar dos
# ceros no distingue una lectura buena de una rota.
_FILA_Z = [{"ID": "PRJ-Z1", "Group": "cliente1", "Name": "Obra Z", "Status": "En progreso"}]
_GASTOS_Z = [{"ProjectID": "PRJ-Z1"}, {"ProjectID": "PRJ-Z1"}, {"ProjectID": "OTRO"}]
_FICH_Z = [{"ProjectID": "PRJ-Z1", "Project": "Obra Z"}]
_rec_z, _fic_z = P._records, P._fichaje_records
P._records = lambda t=None: (_FILA_Z if t == P.PROJECTS_SHEET
                             else _GASTOS_Z if t == "Gastos" else [])
P._fichaje_records = lambda: _FICH_Z
try:
    como("administrator", "cliente1")
    d1 = P.datos_asociados("PRJ-Z1")
    como("owner")
    d2 = P.datos_asociados("PRJ-Z1")
finally:
    P._records, P._fichaje_records = _rec_z, _fic_z
# sin datos que contar, comparar los dos recuentos no distinguiria nada
if not any(d1.values()):
    ok = False
    print("   ‼️ el caso construido no cuenta nada: la comparacion no probaria nada")
'''

if s.count(VIEJO) != 1:
    raise SystemExit("ancla no unica: %d" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO)
ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v381.py: caso construido con datos que contar")
