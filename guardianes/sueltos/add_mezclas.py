# -*- coding: utf-8 -*-
"""Añade a `verif_v463` la red de MEZCLAS (valor migrado y sin migrar conviviendo).

⚠️ La red se construye sobre `i18n.VALORES` (vocabulario COMPLETO) y NO sobre
`valores.LEGADO` (solo lo que v469 migró): mi primera versión usó LEGADO y era ciega
al caso real — el `estado_cobro` que devolvía cuatro estados en español y uno migrado.
Un cero de esa red no significaba nada, y solo lo destapó validarla contra un caso
conocido-bueno (trampa nº12). El guardián la valida él mismo antes de creerse su cero.
"""
import io
import os

D = os.environ["SCRW"]
p = D + "/verif_v463.py"
s = io.open(p, encoding="utf-8").read()

BLOQUE = '''

print("")
print("8. Ningun sitio MEZCLA un valor migrado con uno sin migrar")
# ⚠️ Es el peor caso de una migracion (v443/v450): el productor devuelve el valor
# nuevo y el consumidor indexa por el viejo, asi que la rama no casa NUNCA y no da
# ningun error. Paso de verdad en v469: `invoices.estado_cobro` devolvia `anulada`,
# `cobrada`, `vencida` y `parcial` en espanol y `pending` migrado, asi que el chip de
# factura perdia icono y color y salia el texto crudo.
#
# ⚠️ La red va sobre `i18n.VALORES` (vocabulario COMPLETO), NO sobre `valores.LEGADO`
# (solo lo que se migro): con LEGADO era CIEGA a este caso exacto, porque los cuatro
# estados espanoles no estan en el mapa de migracion. Un valor migrado FUERA de ese
# mapa es justo donde duele.
_VIEJO = set(i18n.VALORES)
_NUEVO = set(i18n.VALORES.values())
_AMBOS = _VIEJO & _NUEVO           # neutros (Delivery, Ripout...): no informan


def _mezclas():
    _out = []
    for _f in sorted(os.listdir("core")):
        if not _f.endswith(".py"):
            continue
        _a = ast.parse(io.open("core/" + _f, encoding="utf-8").read())
        for _n in ast.walk(_a):
            if isinstance(_n, ast.FunctionDef):
                _r = {_x.value.value for _x in ast.walk(_n)
                      if isinstance(_x, ast.Return)
                      and isinstance(_x.value, ast.Constant)
                      and isinstance(_x.value.value, str)}
                _v, _c = sorted((_r & _VIEJO) - _AMBOS), sorted((_r & _NUEVO) - _AMBOS)
                if _v and _c:
                    _out.append("return %s.%s: sin migrar=%s migrado=%s"
                                % (_f, _n.name, _v, _c))
            if isinstance(_n, ast.Dict):
                _k = {_x.value for _x in _n.keys
                      if isinstance(_x, ast.Constant) and isinstance(_x.value, str)}
                _v, _c = sorted((_k & _VIEJO) - _AMBOS), sorted((_k & _NUEVO) - _AMBOS)
                if _v and _c:
                    _out.append("claves %s:%d: sin migrar=%s migrado=%s"
                                % (_f, _n.lineno, _v, _c))
    return _out


# ⚠️ Validar la sonda ANTES de creerse su cero: se reintroduce la mezcla REAL de v469
# y tiene que verla. Sin este paso, un "0 mezclas" no significa nada (trampa nº12).
_pinv = "core/invoices.py"
_orig = io.open(_pinv, encoding="utf-8").read()
try:
    io.open(_pinv, "w", encoding="utf-8", newline="").write(
        _orig.replace('    return "pendiente"', '    return "pending"', 1))
    _ve = [m for m in _mezclas() if "invoices.py" in m]
finally:
    io.open(_pinv, "w", encoding="utf-8", newline="").write(_orig)
if _ve:
    ok("la sonda ve el caso conocido-bueno (%s)" % _ve[0][:60])
else:
    fallo("la sonda esta CIEGA: su cero no significaria nada")

_mz = _mezclas()
if not _mz:
    ok("0 mezclas en los %d modulos de core" % len([f for f in os.listdir("core")
                                                    if f.endswith(".py")]))
else:
    for _m in _mz:
        fallo("MEZCLA -> " + _m)
'''

ANCLA = '\nprint("")\nprint("6. El markdown de color NO se cuela en una celda de tabla")'
assert s.count(ANCLA) == 1, "ancla ausente o ambigua"

# el bloque va al final, antes del resumen; se busca el print del veredicto
# ⚠️ El bloque va ANTES del veredicto. Un bloque añadido al final queda DESPUÉS del
# `sys.exit` y no se ejecuta nunca — un chequeo en vacío escrito por descuido (v452).
VEREDICTO = '\nprint("")\nif fallos:\n'
assert s.count(VEREDICTO) == 1, "no se encuentra el veredicto del guardian"
i = s.index(VEREDICTO)
s = s[:i] + BLOQUE + s[i:]

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("bloque 8 añadido a verif_v463")
