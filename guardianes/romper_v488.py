# -*- coding: utf-8 -*-
"""¿verif_v488 CAZA sus fallos? Cada rotura contra el guardián, con verde de BASE primero
y un CONTROL que debe pasar. Copia a disco, restore VERIFICADO y ABORTO si falla (v484).
"""
import io
import os
import subprocess
import sys
import time

RAIZ = os.path.join("C:" + os.sep, "Users", "diego", "P1", "survey_app")
AQUI = os.path.dirname(os.path.abspath(__file__))
GUARDIANES = ["verif_v488.py"]
NL = chr(10)

ROTURAS = [
    ("core/xero.py", "sin filtro por el evento de autorizacion", [
        ('params={"authEventId": evento} if evento else None,', "params=None,")]),
    ("core/xero.py", "se canjea un state de otro usuario", [
        ('if _norm(datos.get("g")) != _norm(grupo) or _norm(datos.get("u")) != _norm(usuario):',
         'if _norm(datos.get("g")) != _norm(grupo):')]),
    ("core/xero.py", "un cerrojo NUEVO por llamada (no serializa)", [
        ("        return _CERROJOS.setdefault(_norm(grupo), threading.RLock())",
         "        return threading.RLock()")]),
    ("core/xero.py", "se envia aunque la comprobacion previa falle", [
        ("        if err:" + NL + "            # ⚠️ Sin poder comprobar",
         "        if False:" + NL + "            # ⚠️ Sin poder comprobar")]),
    ("core/xero.py", "importes CON impuesto", [
        ('"LineAmountTypes": "Exclusive"', '"LineAmountTypes": "Inclusive"')]),
    ("core/xero.py", "el token entra en la cache de pantalla", [
        ('if k != "TokenEnc"}', 'if k != "TokenEncX"}')]),
    ("core/xero.py", "una factura BORRADA en Xero bloquea el numero", [
        ('_VIVAS = {"DRAFT", "SUBMITTED", "AUTHORISED", "PAID"}',
         '_VIVAS = {"DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "DELETED"}')]),
    ("core/xero.py", "el token renovado va al log", [
        ("            paquete = _paquete(js, paquete)",
         '            paquete = _paquete(js, paquete); logger.info("xero: renovado %s", paquete)')]),
    ("core/xero.py", "desconectar no quita la conexion en Xero", [
        ("        if ok and cid:", "        if False:")]),
    ("core/xero.py", "se manda el nombre de categoria de COPEX y no el de Xero", [
        ('    return str(cat.get("Name") or categoria), mapa, avisos',
         "    return categoria, mapa, avisos")]),
    ("core/invoices.py", "marcar_xero escribe por posicion canonica", [
        ('    if "XeroInvoiceID" not in cab or "XeroSentAt" not in cab or "ID" not in cab:',
         '    if "ID" not in cab:'),
        ('    ci, cx, cs = cab.index("ID"), cab.index("XeroInvoiceID"), cab.index("XeroSentAt")',
         '    ci, cx, cs = cab.index("ID"), _FCOL["XeroInvoiceID"] - 1, _FCOL["XeroSentAt"] - 1')]),
    ("core/contable.py", "documento_venta redondea el impuesto linea a linea", [
        ("    impuestos = reparte_impuesto([_num(ln.get(\"importe\")) for ln in lineas],"
         + NL + "                                 _num(f.get(\"Tax\")))",
         "    impuestos = [round(_num(ln.get(\"importe\")) * pct / 100.0, 2) for ln in lineas]")]),
    ("app.py", "la vuelta desde Xero no se procesa", [
        ("    _xui.procesar_retorno(_ROL, _GRUPO)", "    pass")]),
    ("core/timeclock.py", "la pestana de Xero deja de ser global", [
        ('                   "xeroconnections"}', '                   "xeroconnectionsX"}')]),
    ("core/xero_ui.py", "cualquier rol procesa la vuelta", [
        ('    if rol != "administrator":' + NL + "        return",
         "    if False:" + NL + "        return")]),
    ("core/xero_ui.py", "un rerun vuelve a canjear el codigo", [
        ('    if st.session_state.get("_xero_retorno") == state:' + NL + "        return",
         "    if False:" + NL + "        return")]),
    ("core/xero.py", "CONTROL: solo un comentario nuevo", [
        ("def _norm(s) -> str:", "# comentario inocuo" + NL + "def _norm(s) -> str:")]),
]


def _leer(r):
    with io.open(r, encoding="utf-8") as f:
        return f.read()


def _escribir(r, txt):
    with io.open(r, "w", encoding="utf-8", newline="") as f:
        f.write(txt)


def _restaurar(r, orig, que):
    for i in range(5):
        try:
            _escribir(r, orig)
            if _leer(r) == orig:
                return True
        except OSError as e:
            print("       (reintento %d: %s)" % (i + 1, e))
        time.sleep(1.0)
    print("  *** NO SE PUDO RESTAURAR %s tras «%s» — SE ABORTA" % (r, que))
    return False


def corre():
    peor = 0
    for g in GUARDIANES:
        rc = subprocess.run([sys.executable, os.path.join(AQUI, g)], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            env=dict(os.environ, PYTHONIOENCODING="utf-8")).returncode
        peor = peor or rc
    return peor


for _f in {f for f, *_ in ROTURAS}:
    _escribir(os.path.join(AQUI, "_v488r_" + _f.replace("/", "_")), _leer(os.path.join(RAIZ, _f)))

base = corre()
print("verde de BASE: %s" % ("OK" if base == 0 else "*** ROJO: la tanda no valdria nada ***"))
if base != 0:
    sys.exit(2)
print("")

mal = 0
for fich, que, pares in ROTURAS:
    ruta = os.path.join(RAIZ, fich)
    orig = _leer(ruta)
    nuevo = orig
    ancla_mal = False
    for viejo, reemplazo in pares:
        if nuevo.count(viejo) != 1:
            print("  ??   %-55s ANCLA aparece %d veces: %r" % (que[:55], nuevo.count(viejo), viejo[:50]))
            ancla_mal = True
            break
        nuevo = nuevo.replace(viejo, reemplazo, 1)
    if ancla_mal:
        mal += 1
        continue
    cod = None
    try:
        _escribir(ruta, nuevo)
        cod = corre()
    finally:
        if not _restaurar(ruta, orig, que):
            sys.exit(2)
    ctrl = que.startswith("CONTROL")
    bien = (cod == 0) if ctrl else (cod != 0)
    mal += 0 if bien else 1
    print("  %s %-55s (%s)" % ("ok  " if bien else "ESCAPA", que[:55], "pasa" if cod == 0 else "rojo"))
    time.sleep(3)

print("")
print("%d mal" % mal)
sys.exit(0 if mal == 0 else 1)
