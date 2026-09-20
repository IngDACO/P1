# -*- coding: utf-8 -*-
"""Los guardianes simulaban sesiones con un ROL que ya no existe (v469).

v469 migro los roles del dato a ingles (`owner`/`administrator`/`field`) y **nadie lo
llevo a los guardianes**: 43 seguian poniendo `{"rol": "administrador"}` en
`session_state["auth"]`. Medido, no supuesto: `tenant.es_propietario()` devuelve
**False** con `"propietario"`, asi que los caminos de propietario no se estaban
ejercitando — la suite salia verde bajo una sesion IMPOSIBLE.

Es la misma caducidad que v469 dejo en `verif_v374_positivo` con las columnas
(`ProyectoID`/`Fecha` en vez de `ProjectID`/`Date`): un valor migrado en el codigo y
olvidado en lo que lo comprueba.

⚠️ Se toca SOLO el valor de la clave `rol` dentro de un dict literal, localizado por
AST: la misma palabra aparece como valor de negocio legitimo en otros sitios (la
columna `Role` de una fila SIN migrar, que algun guardian comprueba a proposito).
"""
import ast
import io
import pathlib

MAPA = {"propietario": "owner", "administrador": "administrator",
        "campo": "field", "conductor": "field"}
tocados = {}

for p in sorted(pathlib.Path(".").glob("*.py")):
    if not p.name.startswith(("verif_", "check_")):
        continue
    src = p.read_text(encoding="utf-8")
    try:
        arb = ast.parse(src)
    except SyntaxError:
        continue
    # (linea, col, viejo, nuevo) de cada valor a sustituir
    puntos = []
    for n in ast.walk(arb):
        if not isinstance(n, ast.Dict):
            continue
        for k, v in zip(n.keys, n.values):
            if (isinstance(k, ast.Constant) and str(k.value).lower() == "rol"
                    and isinstance(v, ast.Constant) and v.value in MAPA):
                puntos.append((v.lineno, v.col_offset, v.value, MAPA[v.value]))
    if not puntos:
        continue
    lineas = src.split("\n")
    # de atras hacia delante, para no desplazar los offsets de la misma linea
    for ln, col, viejo, nuevo in sorted(puntos, reverse=True):
        L = lineas[ln - 1]
        # ⚠️ col_offset va en BYTES (la leccion de v468): se corta sobre los bytes
        b = L.encode("utf-8")
        trozo = b[col:].decode("utf-8", "replace")
        if not (trozo.startswith('"%s"' % viejo) or trozo.startswith("'%s'" % viejo)):
            raise SystemExit("%s:%d el literal no esta donde dice el AST: %r"
                             % (p.name, ln, trozo[:20]))
        comilla = trozo[0]
        nuevo_trozo = comilla + nuevo + comilla + trozo[len(viejo) + 2:]
        lineas[ln - 1] = b[:col].decode("utf-8", "replace") + nuevo_trozo
    nueva = "\n".join(lineas)
    ast.parse(nueva)                     # no se escribe nada que no compile
    p.write_text(nueva, encoding="utf-8", newline="")
    tocados[p.name] = len(puntos)

for f, n in tocados.items():
    print("   %-28s %d sesion(es)" % (f, n))
print("\n%d guardianes actualizados · %d sesiones" % (len(tocados), sum(tocados.values())))
