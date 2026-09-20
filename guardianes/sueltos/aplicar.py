"""Aplica un diccionario de traducción a unos módulos, por POSICIÓN exacta.

  python aplicar.py dic_f2 core/timeclock_ui.py core/prestart_ui.py ...

⚠️ DOS trampas que costaron una tanda entera:

 1. **`col_offset` / `end_col_offset` del AST son offsets en BYTES UTF-8, no en
    caracteres.** Cortar el `str` de la línea con ellos se desplaza en cuanto la línea
    lleva un acento — se comió el paréntesis de cierre de un `st.caption(...)` y el
    fichero dejó de compilar. Se corta sobre la línea CODIFICADA y se decodifica.
 2. **Un literal puede ocupar VARIAS líneas** (concatenación implícita: `"a "\\n"b"`).
    El AST lo da como UN Constant de `lineno` a `end_lineno`, así que hay que sustituir
    el rango entero, no una línea.

Envuelve en `t(...)` (interfaz: sigue el idioma de la pantalla). Dentro de un f-string
traduce EN SITIO, sin envolver: envolverlo exigiría reestructurar la llamada.
"""
import ast
import importlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from i18n_tool import piezas                                      # noqa: E402

RAIZ = Path(r"C:\Users\diego\P1\survey_app")
TRAD = importlib.import_module(sys.argv[1]).TRAD
SECO = "--seco" in sys.argv
RELS = [a for a in sys.argv[2:] if not a.startswith("--")]

tot_ok = tot_falta = 0
faltan_todas = []
rotos = []

for rel in RELS:
    p = RAIZ / rel
    src = p.read_text(encoding="utf-8")
    lin = src.splitlines(True)
    ok, faltan = 0, []
    for pz in piezas(p):                    # ya vienen de atrás hacia delante
        eng = TRAD.get(pz["txt"])
        if eng is None:
            faltan.append(pz["txt"])
            continue
        # ⚠️ Un trozo de f-string PARTIDO entre líneas se deja A MANO, a propósito.
        # Intenté automatizarlo y hay TRES formas distintas, no dos: además del literal
        # entrecomillado y del trozo suelto, está el caso MIXTO — una cadena normal
        # concatenada con una f-string (`c1.caption("texto " f"**{x}** …")`), donde el
        # span EMPIEZA en la comilla de apertura y TERMINA dentro de la f-string, así
        # que la sustitución tendría que dejar una f-string abierta. Automatizar eso en
        # un módulo de 5.000 líneas es más riesgo que valor: se listan y se hacen con
        # ancla, que es verificable de un vistazo.
        if pz["fstr"] and pz["lin"] != pz["elin"]:
            faltan.append(pz["txt"])
            continue
        i0, i1 = pz["lin"] - 1, pz["elin"] - 1
        # ⚠️ bytes, no caracteres (ver cabecera)
        bl0, bl1 = lin[i0].encode("utf-8"), lin[i1].encode("utf-8")
        b0, b1 = bl0[:pz["col"]], bl1[pz["ecol"]:]
        crudo = (bl0[pz["col"]:] if i0 != i1 else bl0[pz["col"]:pz["ecol"]]).decode("utf-8")
        # ⚠️ NINGUNA heurística de caracteres distingue bien los tres casos:
        #   · literal entrecomillado          → `"Nombre"`            → hay que envolver
        #   · cadena NORMAL junto a una f-string → su span INCLUYE las comillas
        #   · trozo de f-string                → `'>Persona</div>`    → puede EMPEZAR
        #     por comilla siendo contenido, y `aaa ` no lleva ninguna
        # Se decide PARSEANDO el trozo exacto: si es una expresión de cadena válida, es
        # un literal; si no, es texto suelto de dentro de una f-string. Es semántico, no
        # una conjetura sobre el primer carácter (que ya falló dos veces).
        _bruto = (bl0[pz["col"]:] if i0 != i1
                  else bl0[pz["col"]:pz["ecol"]]).decode("utf-8")
        if i0 != i1:
            _bruto = _bruto + "".join(lin[i0 + 1:i1]) + \
                bl1[:pz["ecol"]].decode("utf-8")
        try:
            _nodo = ast.parse("(" + _bruto + ")", mode="eval").body
            _literal = (isinstance(_nodo, ast.JoinedStr)
                        or (isinstance(_nodo, ast.Constant)
                            and _nodo.value == pz["txt"]))
        except SyntaxError:
            _literal = False
        con_comillas = _literal
        q = '"' if '"' not in eng else "'"
        if q == "'" and "'" in eng:
            faltan.append(pz["txt"])        # comillas de los dos tipos: a mano
            continue
        # ⚠️ El valor del AST viene DECODIFICADO y el fuente lleva los ESCAPES: meter
        # un salto de línea real dentro de una f-string la deja sin cerrar. Se re-escapa
        # lo que el fuente escapa, y se doblan las llaves (dentro de una f-string un `{`
        # suelto abre una interpolación).
        def _esc(s, dentro_f):
            s = s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
            if dentro_f:
                s = s.replace("{", "{{").replace("}", "}}")
            return s
        if not con_comillas and ('"' in eng or "'" in eng):
            faltan.append(pz["txt"])        # comilla dentro de una f-string: a mano
            continue
        eng = _esc(eng, not con_comillas)
        if con_comillas:
            # literal completo: se re-emite entrecomillado. Si va suelto (no pegado a
            # una f-string) se puede envolver en t(); si está concatenado, NO — mezclar
            # una llamada con una concatenación implícita no es Python válido.
            nuevo = f"{q}{eng}{q}" if pz["fstr"] else f"t({q}{eng}{q})"
        else:
            nuevo = eng                     # texto dentro de una f-string
        lin[i0:i1 + 1] = [b0.decode("utf-8") + nuevo + b1.decode("utf-8")]
        ok += 1
    nueva = "".join(lin)
    if ok and not re.search(r"^from core\.i18n import .*\bt\b", nueva, re.M):
        m = re.search(r"^(from|import) .+$", nueva, re.M)
        assert m, rel
        nueva = nueva[:m.end()] + chr(10) + chr(10) + "from core.i18n import t" + nueva[m.end():]
    try:
        ast.parse(nueva)
    except SyntaxError as e:
        rotos.append(f"{rel}: {e}")
        ok = 0                              # no se escribe un fichero roto
    if ok and not SECO:
        p.write_text(nueva, encoding="utf-8")
    print(f"  {rel:26} {ok:4} hechas   {len(faltan):3} sin traducir"
          + ("   ⚠️ NO COMPILA — no se escribió" if rel in " ".join(rotos) else ""))
    tot_ok += ok
    tot_falta += len(faltan)
    faltan_todas += faltan

print(f"\n{tot_ok} aplicadas · {tot_falta} pendientes"
      + ("  · MODO SECO (no se escribió nada)" if SECO else ""))
for r in rotos:
    print("  ⚠️", r)
if faltan_todas:
    print("\nsin traducción (únicas):")
    for x in sorted(set(faltan_todas)):
        print(f"  {x[:110]!r}")
