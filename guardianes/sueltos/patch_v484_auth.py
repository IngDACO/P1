# -*- coding: utf-8 -*-
"""v484 · `PayrollID`: el identificador con el que el proveedor de nómina casa a la persona.

⚠️ Nuestra identidad es el LOGIN (v306/v413), pero un proveedor de nómina no lo conoce:
casa por nombre o por SU propio código de empleado. Y el nombre **puede repetirse** —ya
pasó con «Mei Chen»—, así que sin este campo un parte de horas de dos homónimos es
ambiguo: o se paga al que no es, o el proveedor rechaza la fila.

Va AL FINAL de la cabecera (migra sola), es OPCIONAL y cae al nombre.
"""
import io

P = "C:\\Users\\diego\\P1\\survey_app\\core\\auth.py"
s = io.open(P, encoding="utf-8").read()

# ── 1 · la columna, al final ────────────────────────────────────────────────
V1 = '''                 "StartedOn"]'''
N1 = '''                 "StartedOn",
                 # v484: código de empleado del proveedor de nómina (Xero Payroll,
                 # MYOB, Employment Hero…). ⚠️ El login es NUESTRA identidad y el
                 # proveedor no lo conoce; casa por nombre, y el nombre se repite.
                 # OPCIONAL: sin él el parte cae al nombre y AVISA de los homónimos.
                 # Al final → migra sola, como las 11 columnas anteriores.
                 "PayrollID"]'''
if s.count(V1) != 1:
    raise SystemExit("ancla LOGIN_HEADERS no unica: %d" % s.count(V1))
s = s.replace(V1, N1)

# ── 2 · un setter genérico, el mismo patrón que `set_group_setting` (v483) ──
ANCLA = '''def set_fecha_ingreso(usuario: str, fecha) -> tuple:'''
NUEVO = '''def set_login_setting(usuario: str, campo: str, valor) -> tuple:
    """Fija una columna de `Login` de esa persona. Escribe TEXTO.

    Hermano de `set_group_setting` (v483). ⚠️ La columna se valida contra `_COL`
    —que se DERIVA de `LOGIN_HEADERS` desde v433— así que un nombre mal escrito da
    error en vez de escribir en ninguna parte; y **los campos secretos están
    prohibidos**, porque un setter genérico que pueda tocar `Password` o
    `SessionToken` es una puerta que no hace falta abrir.

    ⚠️ NO se refactorizan `set_rate` / `set_fecha_ingreso` / `set_contact` para que
    deleguen aquí: cada una tiene su propia validación y su propio mensaje, y están
    en el camino del login. Esto existe para los campos NUEVOS, que es donde la
    duplicación todavía no ha nacido.
    """
    if campo in _CAMPOS_SECRETOS:
        return False, f"{t('That field cannot be edited here')}: {campo}"
    if campo not in _COL:
        return False, f"{t('The column')} {campo} {t('does not exist in the Login sheet.')}"
    lws, err = _get_login_ws()
    if err:
        return False, err
    row, rec = _find_row(lws, usuario)
    if row is None:
        return False, t("User not found.")
    _antes = dict(rec or {})
    _val = "" if valor is None else str(valor).strip()
    try:
        lws.update_cell(row, _COL[campo], _val)
    except Exception as e:
        return False, f"Error: {e}"
    _invalidate_login()
    # ⚠️ El apunte va DESPUÉS de escribir y fuera del try del guardado: el cambio ya
    # se hizo y no se puede deshacer porque falle el rastro (v343).
    try:
        from core import auditoria
        auditoria.registrar("usuario", usuario,
                            auditoria.diff(_antes, {campo: _val}),
                            grupo=str(_antes.get("Group", "")))
    except Exception as e:
        logger.warning("auth.set_login_setting: auditoría: %s", e)
    return True, t("Saved.")


def set_fecha_ingreso(usuario: str, fecha) -> tuple:'''
if s.count(ANCLA) != 1:
    raise SystemExit("ancla set_fecha_ingreso no unica: %d" % s.count(ANCLA))
s = s.replace(ANCLA, NUEVO)

compile(s, P, "exec")
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("auth: PayrollID + set_login_setting")

# ── 3 · y al rastro de cambios, en el MISMO lote ────────────────────────────
P2 = "C:\\Users\\diego\\P1\\survey_app\\core\\auditoria.py"
s2 = io.open(P2, encoding="utf-8").read()
V3 = '''    "HourlyRate", "Role", "Group", "Active", "StartedOn",'''
N3 = '''    # ⚠️ `PayrollID` (v484) decide a QUIÉN le paga el proveedor de nómina: no es un
    # importe, pero equivocarlo paga a otra persona. Si un campo mueve dinero entra
    # aquí en el MISMO lote en que se crea — la regla que v344, v352 y v373
    # aprendieron descubriendo campos de dinero sin rastro.
    "HourlyRate", "Role", "Group", "Active", "StartedOn", "PayrollID",'''
if s2.count(V3) != 1:
    raise SystemExit("ancla CAMPOS_CLAVE no unica: %d" % s2.count(V3))
s2 = s2.replace(V3, N3)
compile(s2, P2, "exec")
io.open(P2, "w", encoding="utf-8", newline="").write(s2)
print("auditoria: PayrollID en CAMPOS_CLAVE")
