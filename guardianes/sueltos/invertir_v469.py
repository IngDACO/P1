# -*- coding: utf-8 -*-
"""Invierte los guardianes que afirmaban «el DATO sigue en español», caducados por
v469 (regla v385: se actualiza la afirmación con la razón escrita, no se relaja).

⚠️ Se escribe a fichero y no por heredoc: los escapes (`\\n`, `\\b`) y los backticks
se rompen ahí, y ya ha mordido cinco veces (trampa nº26)."""
import io
import os

D = os.environ["SCRW"]

RZ = ("# ⚠️ CADUCADO EN v469, INVERTIDO — no relajado (regla v385). Hasta v468 esto\n"
      "# exigia que el valor siguiera en ESPANOL, porque es el dato de la hoja y\n"
      "# traducirlo deja de casar en silencio. v469 lo migra A PROPOSITO, asi que la\n"
      "# afirmacion cambia de objeto pero NO de principio.\n")

P = []

# ── v445 · la constante SUELTA del fichaje.
# ⚠️ Este es el chequeo que habria cazado el fallo real de v469.
P.append((D + "/verif_v445.py",
          'chk("timeclock: las constantes de tipo no se tradujeron",\n'
          "    'TIPO_GENERAL  = \"general\"' in TC and 'TIPO_PROYECTO = \"proyecto\"' in TC)",
          RZ + '''# ⚠️ Y AQUI ESTA EL CHEQUEO QUE FALTABA. v469 migro `TIPO_PROYECTO` a "project" y
# dejo `("Sheet1", "Type")` FUERA de la lista blanca de `valores.COLUMNAS`, asi que las
# ~500 filas del historico seguian diciendo `proyecto`, se leian sin canonizar y
# `_tipo_of(r) == TIPO_PROYECTO` era FALSO para todas: ni una hora imputada a una obra
# contaba como tal — nomina, costo de obra, conciliacion y reparto por proyecto, todo a
# cero, en lo que mas se usa de la app. Y no daba ningun error. El barrido que lo busco
# tampoco lo vio, porque solo miraba constantes que son LISTA y estas son sueltas.
# Se comprueba EJECUTANDO la funcion real sobre una fila vieja y una nueva.
from core import timeclock as _TCM, valores as _VAL             # noqa: E402
chk("timeclock: el tipo que se GUARDA es el canonico",
    _TCM.TIPO_PROYECTO == "project" and _TCM.TIPO_GENERAL == "general",
    "%r / %r" % (_TCM.TIPO_PROYECTO, _TCM.TIPO_GENERAL))
chk("...y `Sheet1.Type` esta en la lista blanca (si no, el historico no casa)",
    ("Sheet1", "Type") in _VAL.COLUMNAS)
_casos = {"proyecto": True, "project": True, "": True, "general": False}
_mal = [v for v, esp in _casos.items()
        if (_TCM._tipo_of(_VAL.canonizar([{"Type": v}], "Sheet1")[0])
            == _TCM.TIPO_PROYECTO) != esp]
chk("...y una fila SIN migrar sigue contando como segmento de proyecto",
    not _mal, "fallan: %s" % _mal)'''))

# ── v447 · categorias de gasto
P.append((D + "/verif_v447.py",
          'chk("expenses: las CATEGORÍAS de gasto siguen en español (se guardan)",\n'
          "    '\"Materiales\"' in _ex)",
          RZ + '''from core import expenses as _EXP, valores as _VAL2            # noqa: E402
chk("expenses: las CATEGORIAS que se guardan son las canonicas",
    "Materials" in _EXP.CATEGORIAS and "Fuel" in _EXP.CATEGORIAS, str(_EXP.CATEGORIAS))
chk("...y una fila SIN migrar sigue casando (canon la traduce al leer)",
    _VAL2.canon("Materiales") == "Materials"
    and _VAL2.canonizar([{"Category": "Combustible"}], "Expenses")[0]["Category"] == "Fuel")'''))

# ── v449 · estados del proyecto
P.append((D + "/verif_v449.py",
          'chk("los ESTADOS siguen en español en `projects` (son el dato de la hoja)",\n'
          '    "En pausa" in P.ESTADOS_MANUAL and P.derive_estado(50, "", "") == "En progreso")\n'
          'chk("...y el mapa de i18n los traduce solo al MOSTRARLOS",\n'
          '    i18n.etiqueta("En progreso") == "In progress")',
          RZ + '''from core import valores as _VAL3                              # noqa: E402
chk("el ESTADO que se guarda es el canonico",
    "On hold" in P.ESTADOS_MANUAL and P.derive_estado(50, "", "") == "In progress",
    "%s - %s" % (P.ESTADOS_MANUAL, P.derive_estado(50, "", "")))
chk("...y una fila SIN migrar sigue casando",
    _VAL3.canon("En progreso") == "In progress" and _VAL3.canon("En pausa") == "On hold")
chk("...y `etiqueta()` no muta un estado que ya es canonico",
    all(i18n.etiqueta(e) == e for e in P.ESTADOS_MANUAL if e))'''))

# ── v446 · derive_estado
P.append((D + "/verif_v446.py",
          'chk("projects.derive_estado sigue devolviendo el estado en ESPAÑOL",\n'
          '    P.derive_estado(50, "", "") == "En progreso"\n'
          '    and P.derive_estado(0, "", "") == "Planificado",\n'
          '    f"{P.derive_estado(50, \'\', \'\')} · {P.derive_estado(0, \'\', \'\')}")',
          RZ + '''chk("projects.derive_estado devuelve el estado CANONICO",
    P.derive_estado(50, "", "") == "In progress"
    and P.derive_estado(0, "", "") == "Planned",
    f"{P.derive_estado(50, '', '')} - {P.derive_estado(0, '', '')}")'''))

# ── v446 · cotizaciones
P.append((D + "/verif_v446.py",
          'chk("quotes: los estados siguen en español (se guardan)",\n'
          '    Q.BORRADOR == "borrador" and "aceptada" in Q.ESTADOS, str(Q.ESTADOS))',
          RZ + '''from core import valores as _VAL4                              # noqa: E402
chk("quotes: los estados que se guardan son los canonicos",
    Q.BORRADOR == "draft" and Q.ACEPTADA in Q.ESTADOS, str(Q.ESTADOS))
chk("...y una cotizacion SIN migrar sigue casando",
    _VAL4.canon("aceptada") == Q.ACEPTADA and _VAL4.canon("borrador") == Q.BORRADOR)'''))

# ── el literal suelto de `set_estado`, en los dos ficheros: pasa a la CONSTANTE, asi
#    no puede volver a quedarse atras cuando el vocabulario cambie.
for _f in ("verif_v446.py", "check_f5b_smoke.py"):
    P.append((D + "/" + _f, '"aceptada")', "Q.ACEPTADA)"))

# ── v461 · estados de las correcciones de fichaje
P.append((D + "/verif_v461.py",
          '_sin = [e for e in C.ESTADOS if e not in i18n.VALORES]\n'
          'if not _sin:\n'
          '    ok("los %d estados están en i18n.VALORES" % len(C.ESTADOS))\n'
          'else:\n'
          '    fallo("estados que saldrían en español: " + ", ".join(_sin))',
          RZ + '''# El canonico NO tiene que ser CLAVE de `VALORES`: ese mapa es ahora el legado del
# lado del display. Lo que no puede pasar es que `etiqueta()` le cambie el texto a un
# valor que YA es canonico — si lo hiciera, es que la constante sigue sin migrar.
_sin = [e for e in C.ESTADOS if i18n.etiqueta(e) != e]
if not _sin:
    ok("los %d estados son canonicos y `etiqueta()` no los muta" % len(C.ESTADOS))
else:
    fallo("estados que saldrian en espanol: " + ", ".join(_sin))'''))

P.append((D + "/verif_v461.py",
          'if i18n.etiqueta(C.REVERTIDA) == "reverted":\n'
          '    ok("revertida se muestra como «reverted»")\n'
          'else:\n'
          '    fallo("revertida no se traduce: %r" % i18n.etiqueta(C.REVERTIDA))\n'
          '# ⚠️ …y el DATO sigue en español: traducirlo dejaría de casar en silencio (v442)\n'
          'if C.REVERTIDA == "revertida" and C.APROBADA == "aprobada":\n'
          '    ok("el dato que se guarda sigue siendo el español")\n'
          'else:\n'
          '    fallo("se tradujo el DATO: las comparaciones dejarían de casar")',
          '''if C.REVERTIDA == "reverted" and C.APROBADA == "approved":
    ok("el dato que se guarda es el canonico")
else:
    fallo("la constante no es canonica: %r / %r" % (C.REVERTIDA, C.APROBADA))
# ⚠️ …y la fila SIN migrar sigue casando: es lo que permite desplegar ANTES de migrar
# la hoja. Sin esto, toda correccion del historico quedaria sin resolver.
from core import valores as _VAL5                              # noqa: E402
if (_VAL5.canon("revertida") == C.REVERTIDA
        and _VAL5.canonizar([{"Status": "aprobada"}], "TimeCorrections")[0]["Status"]
        == C.APROBADA):
    ok("una correccion SIN migrar sigue casando (canon la traduce al leer)")
else:
    fallo("la fila vieja deja de resolver")'''))

for path, viejo, nuevo in P:
    s = io.open(path, encoding="utf-8").read()
    n = s.count(viejo)
    if n != 1:
        print("  !! ancla %s en %s (%d)"
              % ("ausente" if not n else "ambigua", os.path.basename(path), n))
        continue
    io.open(path, "w", encoding="utf-8", newline="").write(s.replace(viejo, nuevo))
    print("  ok %s" % os.path.basename(path))
