# -*- coding: utf-8 -*-
"""Prueba el guardián de v484 contra código ROTO.

⚠️ NUNCA en paralelo con la suite: modifica ficheros del árbol (los 7 rojos falsos
de v455). Y espaciado, que cada corrida lee Sheets de verdad (trampa nº19).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
GUARDIAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v484.py")

_NL = chr(10)   # ⚠️ nunca "\n" literal por heredoc (trampa nº26, siete veces ya)

ROTURAS = [
    # ── el criterio de v432 vuelve a pagar dos veces el mismo día ──
    ("ausencias.py", "el RECORTE de v432 desaparece (vuelve el doble pago)",
     "            _pag = max(0.0, HORAS_DIA - _ya)",
     "            _pag = HORAS_DIA"),

    # ── el agregado deja de delegar: segunda definición de lo que se paga ──
    ("ausencias.py", "el agregado vuelve a RECALCULAR por su cuenta",
     _NL.join(["    out = {}",
               "    for clave, e in horas_pagadas_dia(grupo, desde, hasta).items():"]),
     _NL.join(["    out = {}",
               "    for _r in _records():",
               "        pass",
               "    for clave, e in horas_pagadas_dia(grupo, desde, hasta).items():"])),

    # ⚠️ RETIRADA: «los dias se recuentan» cambiaba `dias` del agregado, y medido
    # NADIE lo lee — `payroll.generar` usa `recortados`, `nombre`, `horas` y
    # `por_tipo`, y el parte usa la vista por dia. Una rotura sobre un campo sin
    # consumidor no corresponde a ningun defecto: exigirla seria clavar un detalle
    # de implementacion, no una conducta. El oraculo lo sigue fijando, que es gratis.

    # ── los conceptos dejan de derivarse ──
    ("contable.py", "los conceptos se escriben A MANO (se pierde un tipo)",
     _NL.join(['        pag = tuple(k for k, v in _AU.TIPOS.items() if v.get("pagado"))']),
     '        pag = ("vacaciones",)'),

    ("contable.py", "los conceptos incluyen el tipo NO pagado",
     'pag = tuple(k for k, v in _AU.TIPOS.items() if v.get("pagado"))',
     'pag = tuple(_AU.TIPOS)'),

    ("contable.py", "el mapa SUSTITUYE los conceptos en vez de fusionar",
     '                cfg["conceptos"].update({kk: str(vv) for kk, vv in (v or {}).items()})',
     '                cfg["conceptos"] = {kk: str(vv) for kk, vv in (v or {}).items()}'),

    # ── la forma del CSV ──
    ("contable.py", "un dia sin horas sale como 0.00 en vez de VACIO",
     '             + [(_numero(f["horas"][d]) if d in f["horas"] else "") for d in r["dias"]]',
     '             + [_numero(f["horas"].get(d, 0)) for d in r["dias"]]'),

    ("contable.py", "se pierde el ORDEN de las columnas (= el array de la API)",
     '           + [d.strftime(_FECHA) for d in r["dias"]] + [t("Total")])',
     '           + [d.strftime(_FECHA) for d in reversed(r["dias"])] + [t("Total")])'),

    ("contable.py", "el periodo deja de topar (un ano = 365 columnas)",
     "    while d <= d1 and len(dias) < _MAX_DIAS:",
     "    while d <= d1:"),

    # ── los avisos ──
    ("contable.py", "el aviso de homonimos salta tambien con nombre UNICO",
     '        elif not pid and _cuenta_nombre.get(nombre.strip().lower(), 0) > 1:',
     '        elif not pid:'),

    ("contable.py", "deja de avisar de quien tiene horas y no esta en Login",
     '            de_baja.append(nombre)',
     '            pass'),

    # ── el identificador de nomina ──
    ("auth.py", "PayrollID se mete en MEDIO de la cabecera",
     _NL.join(['                 "StartedOn",']),
     _NL.join(['                 "PayrollID2", "StartedOn",'])),

    ("auth.py", "el setter generico deja de rechazar los campos SECRETOS",
     _NL.join(["    if campo in _CAMPOS_SECRETOS:",
               '        return False, f"{t(\'That field cannot be edited here\')}: {campo}"']),
     "    if False:" + _NL + "        pass"),

    ("auditoria.py", "PayrollID sale del rastro de cambios",
     '"HourlyRate", "Role", "Group", "Active", "StartedOn", "PayrollID",',
     '"HourlyRate", "Role", "Group", "Active", "StartedOn",'),

    # ── la pantalla ──
    ("contable_ui.py", "el parte pierde su propio periodo (usa el contable)",
     '    desde = c1.date_input(t("From"), value=hoy - _timedelta(days=13), key="cont_p_d")',
     "    desde = hoy - _timedelta(days=13)"),

    ("contable_ui.py", "render_contable deja de pintar el parte",
     _NL.join(["    T.section(t(\"Timesheet for payroll\"),",
               "              t(\"Paid hours, person by person and day by day\"))",
               "    _partes_section(grupo)"]),
     "    pass"),

    ("auth_ui.py", "el PayrollID deja de poder ponerse (campo inalcanzable)",
     'ok, msg = auth.set_login_setting(sel, "PayrollID", _pid)',
     'ok, msg = (False, "no")'),

    # ── CONTROL: un cambio inocuo que DEBE seguir pasando ──
    ("contable.py", "CONTROL: solo un comentario nuevo",
     "logger = logging.getLogger(__name__)",
     _NL.join(["logger = logging.getLogger(__name__)",
               "# comentario inocuo del control"])),
]


def corre(espera=6):
    time.sleep(espera)
    r = subprocess.run([sys.executable, GUARDIAN], cwd=RAIZ,
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode


print("verde de BASE antes de romper nada:", "OK" if corre(0) == 0 else "*** ROJO ***")
print("(si esto sale rojo, la tanda de abajo no prueba NADA — leccion v459)")
print("")

def _leer(ruta):
    with io.open(ruta, encoding="utf-8") as f:
        return f.read()


def _escribir(ruta, txt):
    # ⚠️ Con `with`: el patron `io.open(...).write(...)` deja el descriptor abierto a
    # merced del recolector, y en Windows la reapertura del MISMO fichero en el bucle
    # fallo con OSError 22 — dejando la rotura VIVA en el arbol de trabajo (el doble
    # pago de v432, suelto). Un `finally` que puede fallar no es una garantia.
    with io.open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(txt)


def _restaurar(ruta, orig, que):
    """Devuelve el fichero a su sitio y lo COMPRUEBA. Si no puede, aborta la tanda:
    seguir con codigo roto en el arbol es peor que no haber probado nada."""
    for intento in range(5):
        try:
            _escribir(ruta, orig)
            if _leer(ruta) == orig:
                return True
        except OSError as e:
            print(f"       (reintento {intento + 1} restaurando {os.path.basename(ruta)}: {e})")
        time.sleep(1.5)
    print(f"  *** NO SE PUDO RESTAURAR {ruta} tras «{que}» — se aborta la tanda")
    print(f"  *** el original esta en {_COPIA.get(ruta)}")
    return False


# ⚠️ Copia en disco ANTES de tocar nada: si el proceso muere a mitad, el original
# no se pierde con la memoria.
_COPIA = {}
for _f in {f for f, *_ in ROTURAS}:
    _r = os.path.join(RAIZ, "core", _f)
    _c = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"_orig_{_f}")
    _escribir(_c, _leer(_r))
    _COPIA[_r] = _c
print("copias de seguridad:", ", ".join(os.path.basename(v) for v in _COPIA.values()))
print("")

cazadas = escapadas = 0
for fich, que, viejo, nuevo in ROTURAS:
    ruta = os.path.join(RAIZ, "core", fich)
    orig = _leer(ruta)
    if orig.count(viejo) < 1:
        print("  ??   %-58s ANCLA NO ENCONTRADA" % que[:58])
        escapadas += 1
        continue
    cod = None
    try:
        _escribir(ruta, orig.replace(viejo, nuevo, 1))
        cod = corre()
    finally:
        if not _restaurar(ruta, orig, que):
            sys.exit(2)
    es_control = que.startswith("CONTROL")
    bien = (cod == 0) if es_control else (cod != 0)
    cazadas += 1 if bien else 0
    escapadas += 0 if bien else 1
    print("  %s %-58s (%s)" % ("ok  " if bien else "ESCAPA", que[:58],
                               "pasa" if cod == 0 else "rojo"))

print("")
print("%d correctas · %d mal" % (cazadas, escapadas))
sys.exit(0 if escapadas == 0 else 1)
