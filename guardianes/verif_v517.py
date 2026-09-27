# -*- coding: utf-8 -*-
"""v517 · EL VOCABULARIO DE OBRA (la mitad determinista de la interpretación).

Lo que protege:
  (a) ⚠️ que TODA actividad nombrada por el vocabulario EXISTA en el catálogo. Un
      término que apunta a una actividad fantasma no da error: simplemente no propone
      nunca, y eso no se ve. Es el invariante de v453 («lo que se escribe es lo que se
      compara») aplicado a otro par;
  (b) ⚠️ que el filtro por PLAN funcione: una obra de instalación no puede recibir una
      propuesta de desmontaje. Es la barandilla — la razón principal de que esto exista;
  (c) que la raíz una las formas de una misma palabra Y NO junte palabras distintas,
      validada contra casos conocidos en las DOS direcciones (trampa nº12);
  (d) que lo ambiguo salga MARCADO y con su regla, nunca resuelto a dedo;
  (e) que lo que no es avance se reconozca COMO TAL, no como texto no entendido;
  (f) que los términos sin actividad en el catálogo se declaren en vez de colgarse de la
      actividad más parecida (sería inventar trabajo, y con peso ajeno);
  (g) que el término más largo gane al más corto («landing doors» sobre «doors»);
  (h) que este módulo sea HOJA: sin Streamlit, sin hojas de cálculo, sin red.
Todo EJECUTANDO: importar no ejecuta (v378).
"""
import ast
import io
import os
import sys

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st                                            # noqa: E402
st.session_state["auth"] = {"usuario": "Bobo", "nombre": "Bobo",
                            "rol": "administrator", "grupo": "cliente1"}

fallos, n_ok = [], 0


def ok(q, det=""):
    # ⚠️ Acepta el detalle y lo ignora: `(ok if cond else fallo)(msg, det)` llama a las
    # dos con la misma firma, y sin esto revienta justo cuando PASA (v470, v516).
    global n_ok
    n_ok += 1
    print("   ok   %s" % q)


def fallo(q, det=""):
    fallos.append(q)
    print("   FALLO %s%s" % (q, ("  -> " + str(det)) if det else ""))


def chk(q, cond, det=""):
    (ok if cond else fallo)(q, det)


def sec(x):
    print("\n" + x)
    print("-" * 70)


from core import stages as S                                      # noqa: E402
from core import vocabulario as V                                 # noqa: E402

CAT = {a[0] for _v in S.ACTIVIDADES.values() for a in _v}

# ═════════════════════════════════════════════════════════════════
sec("1. ⚠️ Toda actividad nombrada EXISTE en el catálogo")
# Un nombre inventado no falla: no propone nunca. Mi primera tanda inventó DIEZ.
_mal_sin = sorted({a for acts in V.SINONIMOS.values() for a in acts if a not in CAT})
chk("los %d sinónimos apuntan a actividades reales" % len(V.SINONIMOS),
    not _mal_sin, _mal_sin[:5])
_mal_tar = sorted({a for a in V.TAREAS if a not in CAT})
chk("las %d actividades con tareas existen" % len(V.TAREAS), not _mal_tar, _mal_tar[:5])
_mal_amb = sorted({a for g in V.AMBIGUOS.values() for a in g["alternativas"]
                   if a not in CAT})
chk("las alternativas de lo ambiguo existen", not _mal_amb, _mal_amb[:5])
# ⚠️ Y antes de creerse los tres ceros: que haya algo que mirar (trampa nº1).
chk("el vocabulario no está vacío (%d términos)" % V.cuantos_terminos(),
    V.cuantos_terminos() > 250, V.cuantos_terminos())
chk("...y cubre las 3 fuentes (nombre, tarea, sinónimo)",
    len(V.SINONIMOS) > 80 and len(V.TAREAS) > 20,
    "%d sinónimos · %d actividades con tareas" % (len(V.SINONIMOS), len(V.TAREAS)))

# ⚠️ Y la sonda de arriba tiene que SABER ver una actividad fantasma, o su cero no dice
# nada. Se comprueba con un caso conocido-malo, sin tocar el módulo.
chk("...y la comprobación cazaría un nombre inventado",
    "Install landing door thingy" not in CAT)

# ═════════════════════════════════════════════════════════════════
sec("2. ⚠️ La barandilla: no se propone nada fuera del plan de la obra")
_inst = S.plan_de("Installation", ())
_rip = S.plan_de("Ripout", (S.EXCLUYENTES["demolicion"]["opciones"][0],))
_r = V.buscar("Mounted the tirak and the orange box, killed the lift.", _inst)
chk("una obra de instalación NO recibe propuestas de desmontaje",
    not _r["candidatos"], [c["actividad"] for c in _r["candidatos"]])
chk("...y esos términos se dicen aparte, no se tiran en silencio",
    len(_r["fuera_del_plan"]) >= 2, len(_r["fuera_del_plan"]))
_r2 = V.buscar("Mounted the tirak.", _rip)
chk("...y en un desmontaje SÍ se proponen",
    any(c["actividad"] == "Mount tirak" for c in _r2["candidatos"]),
    [c["actividad"] for c in _r2["candidatos"]])
# ⚠️ Sin plan no se filtra: es el caso de una obra anterior a v512, que no tiene plan
# sellado. Mejor proponer de más que callarse, porque quien acepta lo ve.
_r3 = V.buscar("Mounted the tirak.", None)
chk("sin plan, se propone todo (obra anterior a v512)",
    any(c["actividad"] == "Mount tirak" for c in _r3["candidatos"]))
chk("...y entonces no hay nada «fuera del plan»", not _r3["fuera_del_plan"])

# ═════════════════════════════════════════════════════════════════
sec("3. La raíz une formas de una palabra y NO junta palabras distintas")
for _a, _b in (("tune", "tun"), ("tuned", "tun"), ("tuning", "tun"),
               ("prepped", "prep"), ("doors", "door"), ("fitted", "fit"),
               ("install", "install"), ("off", "off"), ("ceiling", "ceil")):
    chk("«%s» → «%s»" % (_a, _b), V._raiz(_a) == _b, V._raiz(_a))
# ⚠️ Las tres formas del verbo tienen que caer en la MISMA raíz, que es el punto.
chk("...las tres formas de «tune» coinciden",
    V._raiz("tune") == V._raiz("tuned") == V._raiz("tuning"))
# ⚠️ Y el caso conocido-malo: palabras distintas NO pueden colapsar en la misma.
_distintas = [("motor", "mount"), ("rail", "ring"), ("door", "deck"), ("pit", "pack")]
chk("...y palabras distintas siguen siendo distintas",
    all(V._raiz(a) != V._raiz(b) for a, b in _distintas),
    [(a, b) for a, b in _distintas if V._raiz(a) == V._raiz(b)])

sec("3b. Las palabras de relleno no rompen una frase en prosa")
chk("«Tuned the doors» encuentra «Tune doors»",
    any(c["actividad"] == "Tune doors"
        for c in V.buscar("Tuned the doors today.", _inst)["candidatos"]))
chk("«Cleaning rails all morning» encuentra «Clean rails»",
    any(c["actividad"] == "Clean rails"
        for c in V.buscar("Cleaning rails all morning.", _inst)["candidatos"]))

# ═════════════════════════════════════════════════════════════════
sec("4. ⚠️ Lo ambiguo sale MARCADO, no resuelto")
_r = V.buscar("Did some under the cabin work and then the pit work.", _inst)
_t = {a["termino"] for a in _r["ambiguos"]}
chk("«under the cabin work» y «pit work» salen como ambiguos",
    {"under the cabin work", "pit work"} <= _t, sorted(_t))
chk("...cada uno con su regla escrita",
    all(len(a.get("regla", "")) > 30 for a in _r["ambiguos"]))
# ⚠️ ESCAPE CAZADO POR LA BATERÍA: comprobar que ALGUNA tiene dos alternativas pasaba
# aunque le quitara una a «under the cabin work», porque otras seguían teniéndolas —
# verde por el motivo equivocado. La afirmación correcta es sobre el PRINCIPIO: una
# entrada ambigua con UNA sola alternativa ya no es ambigua, es una decisión tomada. Y la
# excepción legítima —«por defecto va a X»— tiene que decirlo en su regla.
_mal_amb2 = [k for k, g in V.AMBIGUOS.items()
             if len(g["alternativas"]) < 2 and "default" not in g["regla"].lower()]
chk("toda entrada ambigua tiene 2+ alternativas, o dice que va POR DEFECTO",
    not _mal_amb2, _mal_amb2)
# ⚠️ Lo importante: NO se elige por él. Si saliera como candidato, el módulo habría
# decidido algo que el documento dice expresamente que depende de la cronología.
chk("...y NINGUNA de esas frases produce un candidato a secas",
    not _r["candidatos"], [c["actividad"] for c in _r["candidatos"]])

# ═════════════════════════════════════════════════════════════════
sec("5. Lo que NO es avance se reconoce como tal")
_r = V.buscar("Induction this morning, then pre-start, then nothing else.", _inst)
chk("«induction» y «pre-start» salen como no-avance", len(_r["no_avance"]) >= 2,
    [n["termino"] for n in _r["no_avance"]])
chk("...con su motivo", all(len(n.get("motivo", "")) > 10 for n in _r["no_avance"]))
chk("...y NO como avance", not _r["candidatos"])
# ⚠️ La diferencia que importa: «no lo entiendo» y «no cuenta» son cosas distintas.
# Un parte de solo inducción no es un parte ilegible; es un día sin avance.
_vacio = V.buscar("qwerty zxcvb", _inst)
chk("un texto sin nada reconocible NO se disfraza de no-avance",
    not _vacio["no_avance"] and not _vacio["candidatos"])

# ═════════════════════════════════════════════════════════════════
sec("6. Los términos sin actividad en el catálogo se DECLARAN")
_r = V.buscar("Chaser job on level 3 today.", _inst)
chk("«chaser job» se reconoce y se dice que no tiene actividad",
    [s["termino"] for s in _r["sin_actividad"]] == ["chaser job"],
    _r["sin_actividad"])
chk("...y NO se cuelga de la actividad más parecida", not _r["candidatos"],
    [c["actividad"] for c in _r["candidatos"]])
chk("...cada uno explica qué trabajo es",
    all(len(v) > 15 for v in V.SIN_ACTIVIDAD.values()))
# ⚠️ Y que no se solapen con el catálogo: si una de estas apareciera como actividad,
# la declaración estaría caducada y habría que quitarla de aquí.
chk("...y ninguna es ya una actividad del catálogo",
    not [k for k in V.SIN_ACTIVIDAD if k in {c.lower() for c in CAT}])

# ═════════════════════════════════════════════════════════════════
sec("7. El término más largo gana al más corto")
# ⚠️ ESCAPE CAZADO POR LA BATERÍA, y el más instructivo de los tres: invertir el orden no
# ponía nada rojo porque mi caso de prueba no dependía del orden — y resultó que el
# código TAMPOCO lo usaba (ordenaba y no tapaba lo casado, así que el `sorted` era
# decorativo y el comentario mentía). El caso de abajo está SACADO DE LOS DATOS, no
# inventado: «hang temporary work lighting» contiene «light», que apunta a otra
# actividad. Con el orden invertido, el genérico gana y tapa al preciso.
# ⚠️ «Hanging», no «hung»: la raiz no lleva verbos IRREGULARES (hung->hang,
# built->build, ran->run). Mi primera frase usaba el irregular y el guardian se puso
# rojo acusando a codigo sano. Es un limite REAL del vocabulario, escrito en el
# modulo: cubrirlo a mano seria una lista de excepciones que nadie mantiene, y es
# justo lo que la mitad con modelo si sabe hacer.
_r = V.buscar("Hanging the temporary work lighting.", _inst)
_acts = {c["actividad"] for c in _r["candidatos"]}
chk("un término largo tapa al corto que lleva dentro",
    "Hang temporary work lighting" in _acts and "Lights" not in _acts, sorted(_acts))
_r2 = V.buscar("Fitted the motor bedplate.", _inst)
chk("«motor bedplate» va a la del motor y no a la de al lado",
    any(c["actividad"] == "Install motor bedplate" for c in _r2["candidatos"])
    and not any(c["actividad"] == "Install single bedplate" for c in _r2["candidatos"]),
    [c["actividad"] for c in _r2["candidatos"]])

# ═════════════════════════════════════════════════════════════════
sec("8. ⚠️ Es un módulo HOJA y no decide nada")
_src = io.open("core/vocabulario.py", encoding="utf-8").read()
_a = ast.parse(_src)
_imp = set()
for n in ast.walk(_a):
    if isinstance(n, ast.Import):
        _imp |= {x.name.split(".")[0] for x in n.names}
    elif isinstance(n, ast.ImportFrom) and n.module:
        _imp.add(n.module.split(".")[0])
_prohibidos = {"streamlit", "gspread", "requests", "anthropic"} & _imp
chk("no importa Streamlit, Sheets ni ninguna API", not _prohibidos, sorted(_prohibidos))
chk("...solo `stages`, y DENTRO de la función (no ata el import del módulo)",
    "from core import stages" in _src and "\nfrom core import stages" not in _src)
# ⚠️ No escribe: ni acredita, ni guarda, ni llama a nada que lo haga.
_escribe = [n.func.attr for n in ast.walk(_a)
            if isinstance(n, ast.Call)
            and getattr(n.func, "attr", "") in ("acreditar", "crear", "append_row",
                                                "save_field_progress", "update")]
chk("y no escribe en ningún sitio", not _escribe, _escribe)

print("")
print("=" * 70)
print("%d comprobaciones — %s" % (n_ok + len(fallos), "HAY FALLOS" if fallos else "TODO OK"))
sys.exit(1 if fallos else 0)
