"""GUARDIÁN v365 — un mensaje seguido de `st.rerun()` NO se ve.

`st.rerun()` descarta los deltas del run en curso, así que cualquier
`st.success/warning/error/info/toast` emitido justo antes **nunca llega a la pantalla**.
v222 ya lo documentó para `components.html`; aquí resulta que llevaba versiones pasando
con los mensajes de generar nóminas: ni «N creadas», ni el aviso de v346 sobre la gente
sin tarifa (que es LA razón de ser de esa versión), ni el bloqueo de solape de v364.

Barre el repo por AST: dentro de un mismo bloque, ¿hay una llamada a un mensaje ANTES de
un `st.rerun()`, sin nada que lo salve?

⚠️ `st.toast` es la excepción: sobrevive al rerun (es una notificación flotante del
navegador, no un delta del árbol). Y un mensaje seguido de `return` está bien.
"""
import ast
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = pathlib.Path(r"C:\Users\diego\P1\survey_app")

MENSAJES = {"success", "warning", "error", "info"}     # toast NO: sobrevive al rerun
hallazgos = []


def _attrs_st(nodo):
    """Todos los `st.<attr>` que actúan de CALLABLE en esta expresión.

    ⚠️ v366: la primera versión solo miraba `st.success(...)` como atributo directo, y
    por eso NO vio el idioma que usa este repo:
        (st.success if ok else st.error)(msg)
    …donde el llamable es un `IfExp`. El fichaje entero se escapó del barrido por eso.
    Es la lección de v349: un guardián acota el fallo a la forma en que lo viste.
    """
    if isinstance(nodo, ast.Attribute) and getattr(nodo.value, "id", "") == "st":
        return [nodo.attr]
    if isinstance(nodo, ast.IfExp):
        return _attrs_st(nodo.body) + _attrs_st(nodo.orelse)
    return []


def es_llamada(nodo, attrs):
    """¿El statement llama a alguno de esos `st.<attr>`? Devuelve el primero que casa."""
    if not isinstance(nodo, ast.Expr) or not isinstance(nodo.value, ast.Call):
        return None
    for a in _attrs_st(nodo.value.func):
        if a in attrs:
            return a
    return None


_WIDGETS = {"button", "form_submit_button", "checkbox", "toggle", "download_button"}


def _test_es_widget(test):
    """¿La condición del `if` es un WIDGET? Entonces el mensaje de arriba es un ESTADO
    que se pinta en cada pasada, no una confirmación que muera en el rerun."""
    for n in (ast.walk(test) if test is not None else []):
        if isinstance(n, ast.Call):
            f = n.func
            # ⚠️ v489: el receptor NO tiene que ser `st`. `c1.button(...)` (el botón de una
            # columna) es igual de widget, y exigir `st` daba un FALSO POSITIVO sobre la
            # pregunta de «Disconnect Xero», que se pinta en cada pasada mientras está
            # abierta. Solo se amplía el RECEPTOR, nunca la lista de widgets: un
            # `flash.exito` o un `X.enviar` no son botones.
            if isinstance(f, ast.Attribute) and f.attr in _WIDGETS:
                return True
    return False


def _rerun_anidado(stmt):
    """Línea del `st.rerun()` que cuelga DIRECTAMENTE de este if/try/for, si lo hay."""
    if _test_es_widget(getattr(stmt, "test", None)):
        return None
    for campo in ("body", "orelse", "finalbody"):
        for s in getattr(stmt, campo, None) or []:
            if es_llamada(s, {"rerun"}):
                return s.lineno
    for h in getattr(stmt, "handlers", []) or []:
        for s in h.body:
            if es_llamada(s, {"rerun"}):
                return s.lineno
    return None


class Visitante(ast.NodeVisitor):
    def __init__(self, fichero):
        self.f = fichero

    def _revisar(self, cuerpo):
        """En un bloque de sentencias, busca mensaje … rerun sin corte."""
        pendientes = []
        for st_ in cuerpo:
            m = es_llamada(st_, MENSAJES)
            if m:
                pendientes.append((m, st_.lineno, st_))
                continue
            ln_rerun = None
            if es_llamada(st_, {"rerun"}):
                ln_rerun = st_.lineno
            else:
                # ⚠️ v366 (2ª ceguera): el rerun puede estar en un bloque ANIDADO —
                #    `(st.success if ok else st.error)(msg)` / `if ok: st.rerun()`,
                #    que es como lo escribe el fichaje. El mensaje muere igual, y
                #    justo en el caso que importa: cuando la acción SALIÓ BIEN.
                ln_rerun = _rerun_anidado(st_)
            if ln_rerun:
                _test = getattr(st_, "test", None)
                for (msg, ln, nodo) in pendientes:
                    fn = nodo.value.func
                    # ⚠️ En `(A if cond else B)(msg)` con el rerun bajo `if cond:`, SOLO
                    #    muere la rama que reruns; la otra se pinta y se queda. Marcar
                    #    las dos daba 68 falsos positivos —todos los `st.error` que SÍ
                    #    se ven— y habría empujado a convertirlos, que es justo lo que
                    #    los rompería.
                    if isinstance(fn, ast.IfExp):
                        if _test is not None and ast.dump(_test) == ast.dump(fn.test):
                            rama = fn.body      # el rerun cuelga del `if <test>` verdadero
                            if not (isinstance(rama, ast.Attribute)
                                    and getattr(rama.value, "id", "") == "st"):
                                continue        # ya está en flash → no muere
                            msg = rama.attr
                        else:
                            continue            # condiciones distintas: no se puede afirmar
                    hallazgos.append(f"{self.f}:{ln}  st.{msg}(…) → se pierde en el "
                                     f"st.rerun() de la línea {ln_rerun}")
                pendientes = []
                continue
            # ⚠️ Un `return`/`raise` corta el flujo: el mensaje SÍ se ve.
            if isinstance(st_, (ast.Return, ast.Raise)):
                pendientes = []
        self.generic_visit_cuerpo(cuerpo)

    def generic_visit_cuerpo(self, cuerpo):
        for st_ in cuerpo:
            for campo in ("body", "orelse", "finalbody"):
                sub = getattr(st_, campo, None)
                if isinstance(sub, list) and sub:
                    self._revisar(sub)
            for h in getattr(st_, "handlers", []) or []:
                self._revisar(h.body)

    def visit_FunctionDef(self, n):
        self._revisar(n.body)
        self.generic_visit(n)


for f in sorted(RAIZ.rglob("*.py")):
    if ".streamlit" in str(f):
        continue
    try:
        arbol = ast.parse(f.read_text(encoding="utf-8"))
    except SyntaxError as e:
        print(f"⚠️ {f.name} no compila: {e}")
        continue
    Visitante(f.relative_to(RAIZ).as_posix()).visit(arbol)

print(f"== mensajes que mueren en un st.rerun(): {len(hallazgos)} ==")
for h in sorted(set(hallazgos)):
    print("  ", h)

print("\n== resultado ==")
if hallazgos:
    print("   ⚠️ hay mensajes que el usuario NUNCA ve")
    sys.exit(1)
print("   ✓ ningún mensaje se pierde en un rerun")
