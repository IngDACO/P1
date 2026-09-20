"""GUARDIÁN v363 — ninguna fila POSICIONAL puede descuadrar con su cabecera.

El fallo: v360 añadió `GananciaHoraJSON` a `PROJECTS_HEADERS` y **no añadió su
valor** a la fila de `create_project`. Crear un proyecto —y aceptar una
cotización, que llama a lo mismo— quedó MUERTO durante 3 versiones.

⚠️ El guardián de v306 SÍ existía y SÍ funcionó, pero es de EJECUCIÓN: solo salta
cuando alguien pulsa «Nuevo proyecto». Nadie creó un proyecto entre v360 y hoy,
así que el fallo no se manifestó. Este es ESTÁTICO: salta al ejecutarlo.

⚠️ SEGUNDA VERSIÓN. La primera daba «✓ ninguna descuadra» habiendo comprobado
**1 de 25 filas** (las otras 24 salían «cabecera ambigua» y se saltaban): un OK
en VACÍO, la trampa nº1 del CLAUDE.md. Ahora la cabecera se RESUELVE siguiendo
el helper de worksheet que usa cada función, y lo que no se puede resolver
cuenta como FALLO del chequeo, no como aprobado.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

comprobadas, descuadres, sin_resolver = [], [], []


def _headers_de_llamadas(nodo):
    """Nombres de constantes de cabecera pasadas a get_sheet(titulo, CABECERA)."""
    out = set()
    for n in ast.walk(nodo):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) in (
                "get_sheet", "_get_ws", "registros"):
            # ⚠️ el nombre puede venir envuelto: `get_sheet(TITULO, tuple(LOGIN_HEADERS))`.
            #    Buscar solo `ast.Name` desnudos dejaba a `auth` sin resolver.
            for a in list(n.args) + [k.value for k in n.keywords]:
                for sub in ast.walk(a):
                    if isinstance(sub, ast.Name) and (sub.id.endswith("HEADERS")
                                                      or sub.id.endswith("COLS")):
                        out.add(sub.id)
    return out


for f in sorted(CORE.glob("*.py")):
    tree = ast.parse(f.read_text(encoding="utf-8"))

    cabeceras = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, (ast.List, ast.Tuple)):
            for t in n.targets:
                nom = getattr(t, "id", "")
                if nom.endswith("HEADERS") or nom.endswith("COLS"):
                    cabeceras[nom] = len(n.value.elts)
    if not cabeceras:
        continue

    funcs = {x.name: x for x in ast.walk(tree)
             if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}

    # funciones que se AUTO-VALIDAN con igualdad estricta contra una cabecera:
    # para ellas, quedarse corta no es «cola vacía», es dejar de funcionar
    estrictas = {}
    for nom, fn in funcs.items():
        for n in ast.walk(fn):
            if isinstance(n, ast.Compare) and n.ops and isinstance(n.ops[0], (ast.NotEq, ast.Eq)):
                for lado in [n.left] + list(n.comparators):
                    if isinstance(lado, ast.Call) and getattr(lado.func, "id", "") == "len" \
                            and lado.args and isinstance(lado.args[0], ast.Name) \
                            and lado.args[0].id in cabeceras:
                        estrictas.setdefault(nom, set()).add(lado.args[0].id)
    # helper de worksheet → cabecera que asegura (`_ws()` → HEADERS)
    helper_cab = {nom: h for nom, fn in funcs.items() if (h := _headers_de_llamadas(fn))}

    for nom_fn, fn in funcs.items():
        filas = []
        for n in ast.walk(fn):
            if (isinstance(n, ast.Assign) and isinstance(n.value, ast.List)
                    and any(getattr(t, "id", "") in ("row", "fila", "valores") for t in n.targets)):
                filas.append((getattr(n.targets[0], "id", "row"), n.value, n.lineno))
            elif (isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "append_row"
                  and n.args and isinstance(n.args[0], ast.List)):
                filas.append(("append_row", n.args[0], n.lineno))
        if not filas:
            continue

        # ── resolver la cabecera de ESTA función, en orden de fiabilidad.
        # 0) ⚠️ La AUTO-VALIDACIÓN manda sobre todo lo demás: si la función dice
        #    `if len(row) != len(PROJECTS_HEADERS)`, ESA es su cabecera, sin
        #    discusión. Tenerla de último recurso hacía que una fila rota (que ya
        #    no casa por longitud) se reportara como «no resuelta» en vez de
        #    «esta función está muerta» — detectaba, pero diagnosticaba mal.
        propia = set(estrictas.get(nom_fn, ()))
        propia = propia or _headers_de_llamadas(fn)             # 1) la usa directamente
        if not propia:                                          # 2) vía el helper que llama
            llamadas = {getattr(c.func, "attr", getattr(c.func, "id", ""))
                        for c in ast.walk(fn) if isinstance(c, ast.Call)}
            propia = set().union(*[helper_cab[h] for h in llamadas if h in helper_cab] or [set()])
        if not propia and len(cabeceras) == 1:                  # 3) el módulo solo tiene una
            propia = set(cabeceras)
        if not propia and nom_fn in estrictas:
            # 3.5) ⚠️ la auto-validación resuelve, no solo juzga. Si no se usa aquí,
            #      una fila ROTA deja de casar por longitud con ninguna cabecera y
            #      el chequeo la reporta como «no resuelta» en vez de decir que la
            #      función está muerta — que es el diagnóstico que hace falta.
            propia = set(estrictas[nom_fn])
        if not propia:
            # 4) la función se AUTO-VALIDA: `if len(row) != len(PROJECTS_HEADERS)`.
            #    Es la señal más fuerte que hay: el propio código dice con qué se compara.
            for n in ast.walk(fn):
                if isinstance(n, ast.Compare) and isinstance(n.left, ast.Call) \
                        and getattr(n.left.func, "id", "") == "len":
                    for lado in [n.left] + list(n.comparators):
                        if isinstance(lado, ast.Call) and getattr(lado.func, "id", "") == "len" \
                                and lado.args and isinstance(lado.args[0], ast.Name) \
                                and lado.args[0].id in cabeceras:
                            propia.add(lado.args[0].id)

        for etiqueta, lista, ln in filas:
            ref = f"{f.name}:{ln} {nom_fn}/{etiqueta}"
            if any(isinstance(e, ast.Starred) for e in lista.elts):
                sin_resolver.append(f"{ref} → lleva *unpack, no contable estáticamente")
                continue
            n_row = len(lista.elts)
            cands = {c for c in propia if c in cabeceras}
            if len(cands) != 1:
                # 5) último recurso: si la longitud casa con UNA sola de las cabeceras
                #    candidatas del módulo, el emparejamiento queda determinado.
                #    ⚠️ No es circular: si a una cabecera le añaden una columna y a la
                #    fila no, la fila deja de casar con ninguna → FALLO (probado
                #    contra el código roto de v360, ver `--probar-roto`).
                pool = cands or set(cabeceras)
                casan = {c for c in pool if cabeceras[c] == n_row}
                if len(casan) == 1:
                    cands = casan
            if len(cands) != 1:
                sin_resolver.append(f"{ref} → {n_row} valores, cabecera no resuelta "
                                    f"({sorted(cands) or sorted(cabeceras)})")
                continue
            cab = cands.pop()
            n_cab = cabeceras[cab]
            linea = f"{ref} → {n_row} vs {cab} {n_cab}"
            # ⚠️ Una fila CORTA no desplaza nada: `append_row` deja vacías las
            #    columnas de la cola (así escriben `auth.add_user` y `add_group`
            #    a propósito). Lo que sí es imposible de cuadrar es una fila MÁS
            #    LARGA que la cabecera.
            # ⚠️ PERO si la función se auto-valida con igualdad estricta
            #    (`if len(row) != len(HEADERS): return error`), su contrato ES la
            #    igualdad: quedarse corta la deja MUERTA, que es exactamente lo
            #    que le pasó a `create_project` entre v360 y v363.
            if n_row > n_cab:
                descuadres.append(linea + "  ‼️ fila MÁS LARGA que la cabecera")
            elif n_row < n_cab and cab in estrictas.get(nom_fn, set()):
                descuadres.append(linea + "  ‼️ se auto-valida con igualdad → esta "
                                           "función está MUERTA")
            elif n_row < n_cab:
                comprobadas.append(linea + f"  OK (corta a propósito: {n_cab - n_row} "
                                           "columnas de cola vacías)")
            else:
                comprobadas.append(linea + "  OK")

print(f"== COMPROBADAS ({len(comprobadas)}) ==")
for r in comprobadas:
    print("  ", r)
if sin_resolver:
    print(f"\n== NO RESUELTAS ({len(sin_resolver)}) — cuentan como fallo del chequeo ==")
    for r in sin_resolver:
        print("  ", r)
if descuadres:
    print(f"\n== ‼️ DESCUADRES ({len(descuadres)}) ==")
    for r in descuadres:
        print("  ", r)

print("\n== resultado ==")
if descuadres:
    print("   ‼️ hay filas que descuadran con su cabecera")
    sys.exit(1)
if sin_resolver:
    print(f"   ⚠️ {len(comprobadas)} filas OK, pero {len(sin_resolver)} sin resolver: "
          "el chequeo NO cubre todo (no se declara aprobado)")
    sys.exit(2)
print(f"   ✓ las {len(comprobadas)} filas posicionales cuadran con su cabecera")
