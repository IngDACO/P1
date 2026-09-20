"""Prueba el guardián de v430 contra el CÓDIGO ROTO.

Un guardián que solo aprueba lo que ya funciona no demuestra nada (lección v410):
se rompe el código a propósito, se comprueba que el guardián lo caza, y se restaura.
Si una rotura no se caza, el guardián tiene un agujero.
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(r"C:\Users\diego\P1\survey_app")
GUARD = Path(__file__).with_name("verif_v430.py")

CASOS = [
    ("la hoja sale del LOTE (leería vacío para siempre)",
     "core/hojas.py",
     '"MovimientosActivo", "Ausencias",', '"MovimientosActivo",'),

    ("la enfermedad pasa a exigir aprobación previa",
     "core/ausencias.py",
     '"aprobacion": False, "pagado": True,  "dias_anio": 10',
     '"aprobacion": True, "pagado": True,  "dias_anio": 10'),

    ("`resolver` vuelve a aceptar cualquier estado vigente",
     "core/ausencias.py",
     "    if actual != PENDIENTE:", "    if actual not in VIGENTES:"),

    ("la ausencia se suma a `Base` (rompería la conciliación de v313)",
     "core/payroll.py",
     'base = round(_num(info["horas"]) * tarifa, 2)',
     'base = round((_num(info["horas"]) + _num((aus.get(clave) or {}).get("horas"))) * tarifa, 2)'),

    ("el concepto de ausencia pierde su `origen`",
     "core/payroll.py",
     '"tipo": "devengo", "monto": monto_aus, "origen": "ausencia"})',
     '"tipo": "devengo", "monto": monto_aus})'),

    ("la nómina vuelve a recorrer SOLO lo fichado (quien estuvo fuera todo el "
     "periodo se queda sin colilla)",
     "core/payroll.py",
     "for clave in sorted(set(horas) | set(aus)):",
     "for clave in sorted(set(horas)):"),

    ("la retención y el super dejan de aplicarse a la ausencia pagada",
     "core/payroll.py",
     '"tipo": "deduccion", "monto": round(bruto * ret_pct / 100.0, 2)})',
     '"tipo": "deduccion", "monto": round(base * ret_pct / 100.0, 2)})'),

    ("`costo_real` pierde las ausencias (dinero que sale de caja y no se ve)",
     "core/finance.py",
     '"costo_real":         round(base_nom + ausencias + aportes, 2),',
     '"costo_real":         round(base_nom + aportes, 2),'),

    ("la vista de la conciliación deja de pintar la fila",
     "core/projects_ui.py",
     '_fil.append(("+ ausencias pagadas (vacaciones, bajas)",',
     '_fil.append(("+ nada",'),

    ("lo pagado se recuenta por su cuenta (12 días de saldo, 8 pagados)",
     "core/ausencias.py",
     "        _d = [d for d in dias_del_rango(r.get(\"Desde\"), r.get(\"Hasta\"),\n"
     "                                        incluye_findes(r))",
     "        _d = [d for d in dias_del_rango(r.get(\"Desde\"), r.get(\"Hasta\"))"),

    ("el selectbox vuelve a pintar `:material/` (saldria literal en pantalla)",
     "core/ausencias_ui.py",
     "AU.TIPOS[t]['emoji']", "':material/sick:'"),

    ("v432: la ausencia vuelve a pagar la jornada entera aunque se fichara ese dia",
     "core/ausencias.py",
     "            _pag = max(0.0, HORAS_DIA - _ya)",
     "            _pag = HORAS_DIA"),

    ("v432: el recorte deja de informarse (ajuste de dinero invisible)",
     "core/payroll.py",
     '"solapadas": solapadas, "recortes": recortes}',
     '"solapadas": solapadas}'),

    ("v432: asignar personal deja de mirar las ausencias",
     "core/projects_ui.py",
     "from core import ausencias as _AU", "from core import clock as _AU"),

    ("v432: cancelar una aprobada deja de avisar al admin",
     "core/ausencias_ui.py",
     "                            _avisar_cancelacion(grupo, nombre, r)",
     "                            pass"),

    ("v433: dias_usados vuelve a contar la ausencia entera en su anio de inicio",
     "core/ausencias.py",
     "        tot += sum(1 for d in dias_del_rango(r.get(\"Desde\"), r.get(\"Hasta\"),",
     "        tot += 0 * sum(1 for d in dias_del_rango(r.get(\"Desde\"), r.get(\"Hasta\"),"),

    ("v433: el saldo deja de ir por aniversario",
     "core/ausencias.py",
     "        fi = auth.fecha_ingreso(usuario)", "        fi = None"),

    ("v433: la pantalla deja de decir de que periodo habla",
     "core/ausencias_ui.py",
     "Tu año de vacaciones va del ", "Saldo "),

    ("v433: mover la fecha de alta deja de auditarse",
     "core/auditoria.py",
     '"Activo", "FechaIngreso",', '"Activo",'),

    ("v433: `auth._COL` vuelve a escribirse a mano (la escritura moriria con KeyError)",
     "core/auth.py",
     "_COL = {h: i + 1 for i, h in enumerate(LOGIN_HEADERS)}",
     '_COL = {"Usuario": 1, "Password": 2, "Rol": 3, "Nombre": 4, "Activo": 5, "Grupo": 6, "SessionToken": 7, "SessionTime": 8, "Email": 9, "TelegramChatID": 10, "TarifaHora": 11}'),

    ("v434: `list_users` vuelve a proyectar columnas a mano (se come las nuevas)",
     "core/auth.py",
     "    _campos = [h for h in LOGIN_HEADERS if h not in _CAMPOS_SECRETOS]",
     "    _campos = ['Usuario', 'Rol', 'Nombre', 'Grupo', 'Activo', 'Email', 'TelegramChatID', 'TarifaHora']"),

    ("`_next_id` vuelve a contar filas (el fallo real de v428)",
     "core/ausencias.py",
     "    mx = 0\n    for r in recs:", "    mx = len(recs)\n    for r in []:"),

    ("la caché deja de llevar el libro en la clave (fuga entre inquilinos, v378)",
     "core/ausencias.py",
     "def _records_cached(libro: str) -> list:", "def _records_cached(_libro: str) -> list:"),

    ("un mensaje de éxito vuelve a perderse en el rerun (v365)",
     "core/ausencias_ui.py",
     "                        flash.exito(msg)", "                        st.success(msg)"),

    ("el campo pierde su sección de ausencias",
     "core/home_ui.py",
     '    ("ausencias",    ":material/event_busy: Mis ausencias"),', "    "),

    ("la bandeja del admin se descablea del despachador",
     "core/home_ui.py",
     '    elif sub == "🌴 Ausencias":\n        from core import ausencias_ui\n'
     '        ausencias_ui.render_bandeja(grupo)\n',
     ""),
]


def correr():
    r = subprocess.run([sys.executable, str(GUARD)], cwd=str(RAIZ),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**__import__("os").environ,
                                              "PYTHONIOENCODING": "utf-8"})
    fallos = [l.strip() for l in (r.stdout or "").splitlines() if "FALLO" in l]
    return r.returncode, fallos


print("Estado SANO:")
rc, f = correr()
if rc != 0:
    print("  !! el guardián ya falla sin romper nada:", f)
    sys.exit(1)
print("  OK   pasa\n")

malos = []
for i, (titulo, rel, viejo, nuevo) in enumerate(CASOS, 1):
    p = RAIZ / rel
    orig = p.read_text(encoding="utf-8")
    if viejo not in orig:
        print(f"{i}. {titulo}\n     !! NO SE PUDO ROMPER (el ancla no existe en {rel})")
        malos.append(titulo)
        continue
    try:
        p.write_text(orig.replace(viejo, nuevo, 1), encoding="utf-8")
        rc, fallos = correr()
    finally:
        p.write_text(orig, encoding="utf-8")
    if rc == 0:
        print(f"{i}. {titulo}\n     !! NO SE CAZA — agujero en el guardián")
        malos.append(titulo)
    else:
        print(f"{i}. {titulo}\n     cazado: {fallos[0][:88] if fallos else '(sin línea)'}")

print("\nEstado restaurado:")
rc, f = correr()
print("  " + ("OK   el guardián vuelve a pasar" if rc == 0 else f"!! sigue fallando: {f}"))
print(f"\n{len(CASOS) - len(malos)}/{len(CASOS)} roturas cazadas"
      + ("" if not malos else f"\nSE ESCAPAN: {malos}"))
sys.exit(0 if (not malos and rc == 0) else 1)
