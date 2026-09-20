# -*- coding: utf-8 -*-
"""ATENCION: `t()` a nivel de modulo, QUINTA vez (v445 auth, v446 ausencias,
v447 plan_data y toolruns, y ahora este). El dict se construye al IMPORTAR, cuando
no hay sesion, asi que la traduccion queda congelada.

El criterio de siempre: la constante guarda el texto BASE (que ademas es el dato de
la hoja para las CLAVES) y la traduccion va a una funcion que se llama al PINTAR.
"""
import io
from pathlib import Path

F = Path(r"C:\Users\diego\P1\survey_app\core\invoices_ui.py")
s = F.read_text(encoding="utf-8")

VIEJO = '''_EST_FMT = {
    "pendiente": ":gray[:material/schedule:] " + t("outstanding"),
    "parcial":   ":orange[:material/payments:] parcial",
    "cobrada":   ":green[:material/check_circle:] cobrada",
    "vencida":   ":red[:material/warning:] vencida",
    "anulada":   ":gray[:material/block:] anulada",
}'''

NUEVO = '''# ⚠️ Sin `t()`: este dict se construye al IMPORTAR el módulo, cuando todavía no hay
# sesión, así que la traducción quedaría CONGELADA en el idioma de ese instante (el
# fallo de `auth.SESION_OCUPADA`, v445 — y van cinco). Las CLAVES son además el DATO
# que devuelve `invoices.estado_cobro`. La traducción va en `_est_fmt()`, al pintar.
_EST_FMT = {
    "pendiente": (":gray[:material/schedule:]", "outstanding"),
    "parcial":   (":orange[:material/payments:]", "partial"),
    "cobrada":   (":green[:material/check_circle:]", "paid"),
    "vencida":   (":red[:material/warning:]", "overdue"),
    "anulada":   (":gray[:material/block:]", "voided"),
}


def _est_fmt(est: str) -> str:
    """El estado de cobro, con su icono, en el idioma de la PANTALLA."""
    _ic, _tx = _EST_FMT.get(str(est), ("", str(est)))
    return f"{_ic} {t(_tx)}".strip()'''

assert s.count(VIEJO) == 1, s.count(VIEJO)
s = s.replace(VIEJO, NUEVO, 1)

V2 = "{_EST_FMT.get(est, est)}"
assert s.count(V2) == 1, s.count(V2)
s = s.replace(V2, "{_est_fmt(est)}", 1)

F.write_text(s, encoding="utf-8")
print("invoices_ui: dict a texto BASE + `_est_fmt()` que traduce al pintar")
