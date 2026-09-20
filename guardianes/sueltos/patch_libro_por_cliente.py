"""v359 — un libro de Google por empresa cliente (mecanismo).

Decisión del usuario: dejarlo LISTO sin migrar nada, y una sola cuenta de servicio.

## El diseño, y por qué evita la migración

El libro actual sigue siendo **el maestro Y el libro de `cliente1`**. Los clientes nuevos
nacen cada uno con su archivo (`Grupos.SheetID`). Así **no se mueve ni una de las 21
hojas existentes** —el mayor riesgo del cambio desaparece— y el objetivo se cumple igual:
el segundo cliente tendrá sus datos en su propio fichero.

## Qué vive dónde

- **GLOBAL, siempre en el libro maestro**: `Login`, `Grupos`, `Rieles`, `Manuales`. Son el
  registro de la app, no datos de un cliente — y el login ocurre ANTES de saber a qué
  grupo perteneces, así que no pueden estar en el libro del grupo.
- **Todo lo demás**: en el libro del grupo (el suyo si tiene `SheetID`, si no el maestro).

## Cómo se resuelve el grupo

Igual que `clock.now()` con la zona horaria (v173): sale de la SESIÓN, con override
explícito. Así ninguna de las 21 llamadas a `get_sheet` cambia de firma.

⚠️ El orden importa: primero se mira si la hoja es GLOBAL y se devuelve el maestro **sin
consultar a `auth`**. Si no, `auth.group_sheet_id` leería `Grupos`… que es global →
recursión infinita.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 1) auth: la columna y sus accesores ─────────────────────────
a = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\auth.py")
s = a.read_text(encoding="utf-8")
if "SheetID" not in s:
    s = s.replace(
        '"SuperDefault", "RetencionDefault"]',
        '"SuperDefault", "RetencionDefault",\n'
        '                  # v359: libro de Google propio de este cliente. Vacío = el\n'
        '                  # maestro (así `cliente1` sigue donde estaba, sin migrar).\n'
        '                  "SheetID"]', 1)
    assert "SheetID" in s, "no se pudo añadir la columna"
    s += '''

# ── Libro propio por cliente (v359) ──────────────────────────────
def group_sheet_id(grupo: str) -> str:
    """ID del libro de Google de este grupo. Vacío = usa el maestro.

    ⚠️ Lee de `Grupos`, que es una hoja GLOBAL: `timeclock` la resuelve al maestro
    ANTES de preguntar aquí, o esto se llamaría a sí mismo sin fin.
    """
    if not grupo:
        return ""
    for g in _group_records():
        if str(g.get("Grupo", "")).strip().casefold() == str(grupo).strip().casefold():
            return str(g.get("SheetID", "") or "").strip()
    return ""


def set_group_sheet_id(grupo: str, sheet_id) -> tuple:
    """Enlaza el grupo con su libro. `sheet_id` vacío lo devuelve al maestro."""
    gws, err = _get_groups_ws()
    if err:
        return False, err
    sid = str(sheet_id or "").strip()
    # ⚠️ Se acepta la URL completa además del ID: es lo que se copia del navegador.
    if "/spreadsheets/d/" in sid:
        sid = sid.split("/spreadsheets/d/")[1].split("/")[0]
    if sid:
        otros = [str(g.get("Grupo")) for g in _group_records()
                 if str(g.get("SheetID", "")).strip() == sid
                 and str(g.get("Grupo", "")).strip().casefold() != str(grupo).strip().casefold()]
        if otros:
            # dos clientes en el mismo libro es justo lo que este cambio viene a evitar
            return False, f"Ese libro ya es de: {', '.join(otros)}."
    try:
        recs = gws.get_all_records(numericise_ignore=["all"])
    except Exception as e:
        return False, f"Error leyendo: {e}"
    for i, g in enumerate(recs):
        if str(g.get("Grupo", "")).strip().casefold() == str(grupo).strip().casefold():
            try:
                gws.update_cell(i + 2, GROUPS_HEADERS.index("SheetID") + 1, sid)
            except Exception as e:
                return False, f"Error guardando: {e}"
            _invalidate_groups()
            try:
                from core import timeclock
                timeclock.invalidar_libros()
            except Exception:
                pass
            return True, ("Libro enlazado." if sid else "Grupo devuelto al libro maestro.")
    return False, "Grupo no encontrado."
'''
    a.write_text(s, encoding="utf-8")
    print("✓ auth: Grupos.SheetID + group_sheet_id / set_group_sheet_id")

# ── 2) timeclock: el embudo, ahora por libro ────────────────────
t = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\timeclock.py")
s = t.read_text(encoding="utf-8")

VIEJO = '''@st.cache_resource(show_spinner=False)
def _cached_ws():
    """Abre y cachea la worksheet. Se autentica UNA vez (no en cada rerun).
    Si falla, lanza excepción → no se cachea → se reintenta en la próxima llamada."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_info = dict(st.secrets["gcp_service_account"])
    sheet_id   = st.secrets["TIMECLOCK_SHEET_ID"]
    creds  = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds, http_client=_http_client_cls())
    ws     = client.open_by_key(sheet_id).sheet1'''

NUEVO = '''# ── Un libro por empresa cliente (v359) ─────────────────────────
# Hojas que viven SIEMPRE en el libro maestro: son el registro de la app, no datos de
# un cliente. `Login` además se lee ANTES de saber a qué grupo perteneces.
SHEETS_GLOBALES = {"login", "grupos", "rieles", "manuales"}


def _sheet_maestro() -> str:
    return str(st.secrets["TIMECLOCK_SHEET_ID"])


def sheet_id_para(title: str = "", grupo: str = None) -> str:
    """El libro que le toca a esta hoja. Vacío/desconocido → el maestro.

    ⚠️ La comprobación de GLOBAL va PRIMERO y devuelve sin consultar a `auth`: si no,
    `auth.group_sheet_id` leería `Grupos` —que es global— y se llamaría sin fin.
    """
    maestro = _sheet_maestro()
    if str(title).strip().lower() in SHEETS_GLOBALES:
        return maestro
    g = grupo
    if g is None:
        try:                                  # como `clock.now()`: sale de la sesión (v173)
            g = str((st.session_state.get("auth") or {}).get("grupo", "") or "")
        except Exception:
            g = ""
    if not g:
        return maestro                        # propietario o sin sesión → el maestro
    try:
        from core import auth                 # perezoso: `auth` importa este módulo
        return auth.group_sheet_id(g) or maestro
    except Exception as e:
        logger.warning("timeclock: no se pudo resolver el libro de %r: %s", g, e)
        return maestro


def invalidar_libros():
    """Tras enlazar/desenlazar un libro hay que soltar los handles cacheados."""
    for fn in (_abrir, _cached_ws, _libro, get_sheet):
        try:
            fn.clear()
        except Exception as e:
            logger.warning("timeclock.invalidar_libros: %s: %s", fn, e)
    try:
        from core import hojas
        hojas.invalidar()
    except Exception:
        pass


@st.cache_resource(show_spinner=False)
def _abrir(sheet_id: str):
    """El Spreadsheet, cacheado POR LIBRO. Se autentica una vez por proceso."""
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    client = gspread.authorize(creds, http_client=_http_client_cls())
    return client.open_by_key(sheet_id)


@st.cache_resource(show_spinner=False)
def _cached_ws(sheet_id: str = ""):
    """Abre y cachea la worksheet del FICHAJE del libro que toque.

    ⚠️ `Sheet1` es por cliente, así que depende del grupo en sesión."""
    sheet_id = sheet_id or sheet_id_para("Sheet1")
    ws = _abrir(sheet_id).sheet1'''

assert VIEJO in s, "ancla de _cached_ws no encontrada"
s = s.replace(VIEJO, NUEVO)

# _libro y get_sheet, por libro
s = s.replace('''@st.cache_resource(show_spinner=False)
def _libro():''', '''@st.cache_resource(show_spinner=False)
def _libro(sheet_id: str = ""):''')
s = s.replace('''    ss = _cached_ws().spreadsheet
    hojas = {w.title.strip().lower(): w for w in ss.worksheets()}''',
              '''    ss = _abrir(sheet_id or sheet_id_para("Sheet1"))
    hojas = {w.title.strip().lower(): w for w in ss.worksheets()}''')
s = s.replace('''@st.cache_resource(show_spinner=False)
def get_sheet(title: str, headers: tuple):''',
              '''@st.cache_resource(show_spinner=False)
def get_sheet(title: str, headers: tuple, grupo: str = None):''')
s = s.replace('''    hojas, cabeceras = _libro()
    clave = title.strip().lower()''',
              '''    # v359: cada hoja se busca en SU libro (global → maestro; si no, el del grupo).
    _sid = sheet_id_para(title, grupo)
    hojas, cabeceras = _libro(_sid)
    clave = title.strip().lower()''')
s = s.replace('''        ss = _cached_ws().spreadsheet
        w = ss.add_worksheet(title=title, rows=500, cols=len(headers))''',
              '''        ss = _abrir(_sid)
        w = ss.add_worksheet(title=title, rows=500, cols=len(headers))''')
t.write_text(s, encoding="utf-8")
print("✓ timeclock: _abrir/_cached_ws/_libro/get_sheet parametrizados por libro")

# ── 3) hojas: el lote, por libro ────────────────────────────────
h = pathlib.Path(r"C:\Users\diego\P1\survey_app\core\hojas.py")
s = h.read_text(encoding="utf-8")
s = s.replace('''def _libro():
    """El objeto Spreadsheet, cacheado por proceso (ya lo hace `timeclock`)."""
    ws = timeclock._cached_ws()          # hoja1; de ahí colgamos el libro
    return ws.spreadsheet if ws is not None else None''',
              '''def _libro(sheet_id: str = ""):
    """El Spreadsheet del libro que toque (v359: uno por cliente)."""
    return timeclock._abrir(sheet_id or timeclock.sheet_id_para("Sheet1"))''')
s = s.replace('''def _existentes() -> set:''', '''def _existentes(sheet_id: str = "") -> set:''')
s = s.replace('''        hojas, _cab = timeclock._libro()
        return set(hojas or {})''',
              '''        hojas, _cab = timeclock._libro(sheet_id or timeclock.sheet_id_para("Sheet1"))
        return set(hojas or {})''')
s = s.replace('''@st.cache_data(ttl=120, show_spinner=False)
def _lote() -> dict:''', '''@st.cache_data(ttl=120, show_spinner=False)
def _lote(sheet_id: str = "") -> dict:''')
s = s.replace('''    lib = _libro()
    if lib is None:
        return {}
    try:
        hay = _existentes()''', '''    # ⚠️ v359: el lote se cachea POR LIBRO. Con una sola entrada, el segundo cliente
    # leería los datos del primero — justo lo que este cambio viene a impedir.
    sheet_id = sheet_id or timeclock.sheet_id_para("Sheet1")
    lib = _libro(sheet_id)
    if lib is None:
        return {}
    try:
        hay = _existentes(sheet_id)''')
s = s.replace('''def registros(titulo: str, cabeceras=None):''',
              '''def registros(titulo: str, cabeceras=None, grupo: str = None):''')
s = s.replace('''    datos = _lote().get(titulo)''',
              '''    datos = _lote(timeclock.sheet_id_para(titulo, grupo)).get(titulo)''')
s = s.replace('''            w = timeclock.get_sheet(titulo, tuple(cabeceras))''',
              '''            w = timeclock.get_sheet(titulo, tuple(cabeceras), grupo=grupo)''')
h.write_text(s, encoding="utf-8")
print("✓ hojas: el lote se cachea por libro")
