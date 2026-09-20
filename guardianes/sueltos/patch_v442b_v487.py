# -*- coding: utf-8 -*-
"""v442 reanclado, 2ª pasada: RESOLVER la variable de las opciones (leccion v471).

La 1ª pasada miraba `n.args[1]`, que ahora es el nombre `_ems`: traducir las opciones
dentro de la asignacion a `_ems` pasaba el chequeo. Se resuelve la asignacion (incluidas
las de tupla `_ems, _emi = ...`) y se recorre su VALOR.
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verif_v442.py")
s = io.open(P, encoding="utf-8").read()
VIEJO = "\n".join([
    "_ok442 = bool(_sel442) and all(",
    "    any(k.arg == 'format_func' for k in n.keywords) and len(n.args) > 1",
    "    and not any(isinstance(c, _ast442.Call)",
    "                and (getattr(c.func, 'id', None) or getattr(c.func, 'attr', '')) in _trad442",
    "                for c in _ast442.walk(n.args[1]))",
    "    for n in _sel442)",
])
NUEVO = "\n".join([
    "# ⚠️ Las opciones llegan por VARIABLE (`_ems`): mirar solo el nombre dejaba pasar una",
    "# traduccion hecha en su asignacion. Se resuelve (tambien `_ems, _emi = ...`), v471.",
    "_arb442 = _ast442.parse(_pu)",
    "",
    "",
    "def _valores442(nodo):",
    "    if not isinstance(nodo, _ast442.Name):",
    "        return [nodo]",
    "    out = [nodo]",
    "    for a in _ast442.walk(_arb442):",
    "        if isinstance(a, _ast442.Assign):",
    "            for tg in a.targets:",
    "                nombres = [tg] if isinstance(tg, _ast442.Name) else list(getattr(tg, 'elts', []))",
    "                if any(isinstance(x, _ast442.Name) and x.id == nodo.id for x in nombres):",
    "                    out.append(a.value)",
    "    return out",
    "",
    "",
    "_ok442 = bool(_sel442) and all(",
    "    any(k.arg == 'format_func' for k in n.keywords) and len(n.args) > 1",
    "    and not any(isinstance(c, _ast442.Call)",
    "                and (getattr(c.func, 'id', None) or getattr(c.func, 'attr', '')) in _trad442",
    "                for v in _valores442(n.args[1]) for c in _ast442.walk(v))",
    "    for n in _sel442)",
])
if s.count(VIEJO) != 1:
    raise SystemExit("ancla aparece %d veces" % s.count(VIEJO))
s = s.replace(VIEJO, NUEVO, 1)
compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("verif_v442: resuelve la variable de las opciones")
