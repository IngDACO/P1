"""Prueba el guardián de v435 contra el CÓDIGO ROTO (lección v410).

⚠️ Algunas roturas se hacen en un fichero de PRUEBA dentro de core/, porque lo que se
audita es un patrón que hoy no existe en el repo (nadie usa `t()` todavía). Ese
fichero se borra siempre.
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
GUARD = Path(__file__).with_name("verif_v435.py")
SUCIO = RAIZ / "core" / "_zz_prueba_i18n.py"


def correr():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(RAIZ), capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    return r.returncode, [l.strip() for l in (r.stdout or "").splitlines() if "FALLO" in l]


# (titulo, fichero, viejo, nuevo)  ·  fichero None = crear SUCIO con ese contenido
CASOS = [
    ("un VALOR DE DATO pasa por t() (deja de encontrarse lo completado)", None,
     "from core.i18n import t\nx = t('Completado')\n"),

    ("t() recibe un f-string (nunca casará con el diccionario)", None,
     "from core.i18n import t\nn = 3\nx = t(f'Saved {n} rows')\n"),

    ("t() recibe una concatenación", None,
     "from core.i18n import t\nn = 'x'\nx = t('Saved ' + n)\n"),

    ("el idioma pasa a vivir en un GLOBAL (se le cambiaría a otra sesión)",
     "core/i18n.py",
     '        v = str(st.session_state.get(_CLAVE, "") or "")\n        return v if v in IDIOMAS else BASE',
     '        return _ACTIVO'),

    ("un diccionario roto vuelve a tumbar el render", "core/i18n.py",
     "        try:\n            texto = _dic(idi).get(texto, texto)\n        except Exception as e:\n            logger.warning(\"i18n: diccionario %s ilegible: %s\", idi, e)",
     "        texto = _dic(idi).get(texto, texto)"),

    ("`etiqueta` deja de traducir los estados", "core/i18n.py",
     "        return VALORES.get(v, v)", "        return v"),

    ("i18n deja de ser módulo HOJA (importa core → ciclos)", "core/i18n.py",
     "import streamlit as st", "import streamlit as st\nfrom core import auth"),

    ("el diccionario español deja de arrancar vacío", "core/lang_es.py",
     "TEXTOS = {}", "TEXTOS = {'x': 'y'}"),
]

print("Estado SANO:")
rc, f = correr()
if rc != 0:
    print("  !! el guardián ya falla sin romper nada:", f)
    sys.exit(1)
print("  OK   pasa\n")

malos = []
for i, (titulo, rel, *resto) in enumerate(CASOS, 1):
    orig = None
    try:
        if rel is None:
            SUCIO.write_text(resto[0], encoding="utf-8")
        else:
            p = RAIZ / rel
            orig = p.read_text(encoding="utf-8")
            if resto[0] not in orig:
                print(f"{i}. {titulo}\n     !! NO SE PUDO ROMPER (ancla ausente)")
                malos.append(titulo)
                continue
            p.write_text(orig.replace(resto[0], resto[1], 1), encoding="utf-8")
        rc, fallos = correr()
    finally:
        if rel is None:
            SUCIO.unlink(missing_ok=True)
        elif orig is not None:
            (RAIZ / rel).write_text(orig, encoding="utf-8")
    if rc == 0:
        print(f"{i}. {titulo}\n     !! NO SE CAZA — agujero en el guardián")
        malos.append(titulo)
    else:
        print(f"{i}. {titulo}\n     cazado: {fallos[0][:90] if fallos else '(sin línea)'}")

print("\nEstado restaurado:")
rc, f = correr()
print("  " + ("OK   el guardián vuelve a pasar" if rc == 0 else f"!! sigue fallando: {f}"))
print(f"  fichero de prueba borrado: {not SUCIO.exists()}")
print(f"\n{len(CASOS) - len(malos)}/{len(CASOS)} roturas cazadas"
      + ("" if not malos else f"\nSE ESCAPAN: {malos}"))
sys.exit(0 if (not malos and rc == 0 and not SUCIO.exists()) else 1)
