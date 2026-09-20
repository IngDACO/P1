# ── Costos: sin las piezas de OBRA ──────────────────────────────────────────
# ⚠️ v429: una localización no termina, no lleva presupuesto (v423) y su costo no se
# compara con nada. «Costará al terminar» salía «—» fijo, «Presupuesto» también, y el
# titular decía «no tiene presupuesto asignado… se define en Datos» — donde ese campo
# NO existe para una localización, o sea que mandaba a buscar algo que no está.
print("")
print("== la pantalla de Costos no habla de lo que no aplica ==")
_re = fn(PU, "render_expenses")
_esint_re = [n for n in ast.walk(_re) if isinstance(n, ast.Call)
             and getattr(n.func, "attr", "") == "es_interno"]
chk("`render_expenses` distingue las internas", len(_esint_re) >= 1)


def _bajo_if_interno(f, marca):
    """¿`marca` aparece dentro de un `if` que consulta si es interna (o su else)?"""
    for n in ast.walk(f):
        if not isinstance(n, ast.If):
            continue
        _t = ast.dump(n.test)
        if "_loc" not in _t and "es_interno" not in _t:
            continue
        for rama in (n.body, n.orelse):
            for s_ in rama:
                for c in ast.walk(s_):
                    if (isinstance(c, ast.Constant) and isinstance(c.value, str)
                            and marca in c.value):
                        return True
    return False


chk("«Costará al terminar» cuelga de si es interna",
    _bajo_if_interno(_re, "Costará al terminar"))
chk("«Presupuesto» también", _bajo_if_interno(_re, "Presupuesto"))
chk("y el titular tiene su propia rama para estructura",
    _bajo_if_interno(_re, "estructura"))

