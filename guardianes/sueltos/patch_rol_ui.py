# -*- coding: utf-8 -*-
"""«Invalid role» al crear un usuario de campo: dos literales que v469 no migro.

v469 paso los roles a ingles (`owner`/`administrator`/`field`) — la constante, el dato
de la hoja y la canonizacion al leer— y **se dejo dos literales en la interfaz**:

  · `auth_ui:1109` · el ADMIN creando un usuario de campo pasaba `"campo"` →
    `add_user` valida contra `auth.ROLES` y devolvia **«Invalid role.»**. Es el fallo
    que reporto el usuario: no se podia dar de alta a nadie de campo.
  · `auth_ui:275` · el BOOTSTRAP (crear el primer propietario con la hoja `Login`
    vacia) pasaba `"propietario"`. Latente pero PEOR: una instalacion desde cero no
    habria podido crear su primer usuario, o sea que la app no arranca.

⚠️ Barrido antes de tocar, para arreglar la CLASE y no el caso: de 101 literales
sospechosos, 93 eran claves internas de dicts (`.get("usuario")`) y otros 6 son
etiquetas internas cuyo productor y consumidor coinciden y que **no se canonizan al
leer** (comprobado contra `valores.COLUMNAS`: `Alerts.Origin` y `AssetMovements.To`
no estan en la lista blanca; `Login.Role` SI, que es lo que hace que una fila vieja se
siga leyendo bien). Los unicos rotos eran estos dos.

⚠️ Y el guardian de ramas muertas de v469 no podia verlo: barre **comparaciones**, y
esto es un **argumento**. Por eso el chequeo nuevo mira los argumentos.
"""
import ast
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\auth_ui.py"
s = io.open(P, encoding="utf-8").read()

CAMBIOS = [
    ('                    ok, msg = auth.add_user(u, p1, "propietario", nm)\n',
     '                    # ⚠️ El rol va en su forma CANONICA (v469). Con "propietario"\n'
     '                    # `add_user` devolvia «Invalid role.» y el bootstrap no podia\n'
     '                    # crear el primer usuario: la app no arrancaba desde cero.\n'
     '                    ok, msg = auth.add_user(u, p1, "owner", nm)\n'),
    ('                ok, msg = auth.add_user(u, pw, "campo", nm, grupo)\n',
     '                # ⚠️ Canonico (v469): con "campo" salia «Invalid role.» y no se\n'
     '                # podia dar de alta a NADIE de campo — el fallo que se reporto.\n'
     '                ok, msg = auth.add_user(u, pw, "field", nm, grupo)\n'),
]

for viejo, nuevo in CAMBIOS:
    if s.count(viejo) != 1:
        raise SystemExit("ancla no unica (%d): %r" % (s.count(viejo), viejo[-40:]))
    s = s.replace(viejo, nuevo)

ast.parse(s)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("core/auth_ui.py: los dos roles, en su forma canonica")
