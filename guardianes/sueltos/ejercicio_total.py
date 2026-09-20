"""Banco de pruebas: ejercita la superficie de ESCRITURA de la app contra la hoja real.

Por qué existe: `inventario_escrituras.py` mide que hay **75 mutadores públicos** y que
27 se han ejercitado alguna vez. Un test con datos que yo invento no prueba nada — los
4 fallos de v344, el doble pago de v364 y el avance que no subía de v372 salieron todos
de EJERCITAR contra la hoja, no de razonar sobre el código.

MÉTODO (el de v344, que es el que funcionó):
    foto antes (solo lectura) → ejercitar → verificar LEYENDO → deshacer → foto después

USO:
    python ejercicio_total.py --listar          qué bloques hay y qué cubren
    python ejercicio_total.py --seco            recorre sin escribir nada
    python ejercicio_total.py --bloque catalogo
    python ejercicio_total.py --todo

⚠️ SALVAGUARDAS, y no son adorno:
  · Solo corre sobre el grupo de DEMO. Si `GRUPO` no es el simulado, se niega.
  · Todo lo que crea lleva el prefijo `ZZZ PRUEBA` y se borra al final; lo que no se
    pueda borrar se REPORTA, nunca se deja en silencio.
  · Los ENVÍOS (email/Telegram) se interceptan: se cuentan, no salen. Hay personas
    reales detrás de esas alarmas.
  · `credentials.notify_expiring` NO se ejercita ni con envíos interceptados: además
    de mandar, ESCRIBE `UltimoAviso` en credenciales reales y falsearía el
    deduplicado de 25 días.
  · Nada de borrar documentos de Drive que no haya creado este mismo ejercicio.
"""
import argparse
import sys
import traceback

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

GRUPO = "cliente1"                  # la empresa simulada
MARCA = "ZZZ PRUEBA"                # todo lo creado aquí lo lleva
# ⚠️ Sufijo ÚNICO por corrida: sin él, buscar «lo que acabo de crear» por la marca
# devuelve lo de la corrida ANTERIOR, y se acaba verificando una fila vieja. Pasó con
# una factura ya anulada, y los dos «fallos» que dio no eran de la app.
import time as _t                                                 # noqa: E402
SELLO = _t.strftime("%H%M%S")

import streamlit as st              # noqa: E402
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": GRUPO,
                            "rol": "administrador", "nombre": "dmoreno"}

PROHIBIDAS = {
    "credentials.notify_expiring": "escribe UltimoAviso en credenciales REALES y "
                                   "falsearía el deduplicado de 25 días",
    "auth.delete_user": "solo sobre el usuario ZZZ que crea el propio ejercicio",
    "manuals.delete_manual": "borraría un manual real de Drive",
}

# ── plomería ────────────────────────────────────────────────────────────────
_envios = []


def _interceptar_envios():
    """Nada sale de aquí. Se cuenta lo que se habría mandado."""
    from core import notify
    for n in ("notify_user", "notify_assignment", "notify_induction",
              "send_email", "send_telegram"):
        if hasattr(notify, n):
            setattr(notify, n, (lambda nom: (lambda *a, **k: (_envios.append(nom), True)[1]))(n))


class Res:
    def __init__(self):
        self.ok, self.fallos, self.saltados, self.sucio = [], [], [], []

    def bien(self, q, extra=""):
        self.ok.append(q)
        print(f"    ok    {q}{('  · ' + str(extra)) if extra else ''}")

    def mal(self, q, e):
        self.fallos.append((q, str(e)[:140]))
        print(f"    FALLO {q}: {str(e)[:140]}")

    def salto(self, q, por):
        self.saltados.append((q, por))
        print(f"    -     {q}  (no se ejercita: {por})")

    def basura(self, q):
        self.sucio.append(q)
        print(f"    ⚠️ QUEDA SIN LIMPIAR: {q}")


R = Res()
SECO = False


def paso(nombre, fn, limpiar=None):
    """Ejercita `fn`; si da algo, lo verifica; y SIEMPRE intenta limpiar."""
    if nombre in PROHIBIDAS:
        R.salto(nombre, PROHIBIDAS[nombre])
        return None
    if SECO:
        print(f"    (seco) {nombre}")
        return None
    creado = None
    try:
        creado = fn()
        R.bien(nombre, creado if isinstance(creado, str) else "")
    except Exception as e:                                        # noqa: BLE001
        R.mal(nombre, e)
        if "-v" in sys.argv:
            traceback.print_exc()
    finally:
        if limpiar is not None and creado is not None:
            try:
                limpiar(creado)
            except Exception as e:                                # noqa: BLE001
                R.basura(f"{nombre} → {creado} ({str(e)[:70]})")
    return creado


# ⚠️ Estas funciones devuelven `(ok, mensaje)`, no un dict con el id. Y el mensaje no
# siempre trae el ID. Así que el id NO se deduce del retorno: se busca leyendo la lista
# por la marca — que además VERIFICA que la fila llegó a la hoja, que es el punto.
def _ok(r):
    """`(ok, msg)` → (bool, texto). Acepta también dict o None por si algún día cambia."""
    if isinstance(r, tuple) and r:
        return bool(r[0]), str(r[1] if len(r) > 1 else "")
    if isinstance(r, dict):
        return bool(r.get("ok", True)), str(r.get("error", "") or r.get("id", ""))
    return bool(r), str(r)


def _crear_y_localizar(nombre_paso, crear, listar, campo, valor, limpiar=None):
    """Crea, comprueba el `(ok,msg)` y LOCALIZA la fila leyendo — no fiándose del retorno."""
    if nombre_paso in PROHIBIDAS:
        R.salto(nombre_paso, PROHIBIDAS[nombre_paso])
        return None
    if SECO:
        print(f"    (seco) {nombre_paso}")
        return None
    try:
        ok, msg = _ok(crear())
        if not ok:
            R.mal(nombre_paso, msg or "devolvió False")
            return None
        fila = next((x for x in listar() if str(x.get(campo, "")) == valor), None)
        if not fila:
            R.mal(nombre_paso, "creado pero NO se encuentra al leer de vuelta")
            return None
        _id = str(fila.get("ID", ""))
        R.bien(nombre_paso, _id)
        return _id
    except Exception as e:                                        # noqa: BLE001
        R.mal(nombre_paso, e)
        if "-v" in sys.argv:
            traceback.print_exc()
        return None


def _acc(nombre, fn, comprobar=None):
    """Una acción suelta: se ejercita y, si se da un `comprobar`, se LEE de vuelta."""
    if nombre in PROHIBIDAS:
        R.salto(nombre, PROHIBIDAS[nombre])
        return
    if SECO:
        print(f"    (seco) {nombre}")
        return
    try:
        ok, msg = _ok(fn())
        if not ok:
            R.mal(nombre, msg or "devolvió False")
            return
        if comprobar is not None:
            real = comprobar()
            if not real[0]:
                R.mal(nombre + " — no se LEE de vuelta", real[1])
                return
            R.bien(nombre, real[1])
        else:
            R.bien(nombre)
    except Exception as e:                                        # noqa: BLE001
        R.mal(nombre, e)
        if "-v" in sys.argv:
            traceback.print_exc()


# ── bloques ─────────────────────────────────────────────────────────────────
def bloque_catalogo():
    """catalogo: crear · actualizar · desactivar · reactivar (la vuelta de v340)."""
    from core import catalogo as C
    nom = f"{MARCA} riel"
    cid = _crear_y_localizar(
        "catalogo.crear",
        lambda: C.crear(GRUPO, nom, "producto", costo_unit=100.0, unidad="ud",
                        categoria="Material", creado_por="dmoreno"),
        lambda: C.list_items(GRUPO, incluir_inactivos=True), "Nombre", nom)
    if not cid:
        return
    try:
        _acc("catalogo.actualizar", lambda: C.actualizar(cid, {"CostoUnit": 123.5}),
             lambda: (str(C.get_item(cid).get("CostoUnit", "")).startswith("123"),
                      C.get_item(cid).get("CostoUnit")))
        _acc("catalogo.set_activo(False)", lambda: C.set_activo(cid, False),
             lambda: (str(C.get_item(cid).get("Activo", "")).upper() != "SI",
                      C.get_item(cid).get("Activo")))
        _acc("catalogo.set_activo(True) — se puede volver",
             lambda: C.set_activo(cid, True),
             lambda: (str(C.get_item(cid).get("Activo", "")).upper() == "SI",
                      C.get_item(cid).get("Activo")))
    finally:
        # no hay borrado de artículos: se deja desactivado y se DICE
        try:
            C.set_activo(cid, False)
            print(f"    (limpieza) {cid} queda desactivado — el catálogo no borra)")
        except Exception:
            R.basura(f"catalogo {cid}")


def bloque_clientes():
    """clientes: crear · actualizar · archivar · restaurar."""
    from core import clientes as CL
    nom = f"{MARCA} SA"
    cid = _crear_y_localizar(
        "clientes.create_cliente",
        lambda: CL.create_cliente(GRUPO, nom, contacto="Ana", email="a@b.c",
                                  creado_por="dmoreno"),
        lambda: CL.list_clientes(GRUPO, incluir_inactivos=True), "Nombre", nom)
    if not cid:
        return
    try:
        _acc("clientes.update_cliente", lambda: CL.update_cliente(cid, {"Contacto": "Luis"}),
             lambda: (CL.get_cliente(cid).get("Contacto") == "Luis",
                      CL.get_cliente(cid).get("Contacto")))
        _acc("clientes.set_activo(False)", lambda: CL.set_activo(cid, False))
        _acc("clientes.set_activo(True) — la vuelta de v340",
             lambda: CL.set_activo(cid, True),
             lambda: (str(CL.get_cliente(cid).get("Activo", "")).upper() == "SI",
                      CL.get_cliente(cid).get("Activo")))
    finally:
        try:
            CL.set_activo(cid, False)
            print(f"    (limpieza) {cid} queda archivado")
        except Exception:
            R.basura(f"cliente {cid}")


def bloque_rieles():
    """rails: alta, edición y borrado del catálogo de rieles."""
    from core import rails
    ref = f"{MARCA}-T99"
    _acc("rails.add_riel", lambda: rails.add_riel(ref, 10, 62),
         lambda: (bool(rails.get_rail(ref)), rails.get_rail(ref)))
    # ⚠️ `get_rail` devuelve {referencia, ancho, altura} en minúsculas — NO los nombres
    # de columna de la hoja. Comprobarlo por `AlturaDiente` daba None y parecía un fallo
    # de la app cuando era del test (regla v135, esta vez en la FORMA del dato).
    _acc("rails.update_riel", lambda: rails.update_riel(ref, 11, 63),
         lambda: ((rails.get_rail(ref) or {}).get("altura") == 63.0,
                  (rails.get_rail(ref) or {}).get("altura")))
    _acc("rails.delete_riel", lambda: rails.delete_riel(ref),
         lambda: (not rails.get_rail(ref), "ya no está"))


def bloque_roster():
    """roster: catálogo de trabajos (alta, edición, baja)."""
    from core import roster as RO
    nom = f"{MARCA} traslado"
    tid = _crear_y_localizar(
        "roster.add_trabajo",
        lambda: RO.add_trabajo(GRUPO, "99", nom, "#2e6da4", ""),
        lambda: RO.list_trabajos(GRUPO, incluir_inactivos=True), "Nombre", nom)
    if not tid:
        return
    try:
        _acc("roster.update_trabajo",
             lambda: RO.update_trabajo(tid, {"Nombre": f"{MARCA} curso"}))
        _acc("roster.set_activo_trabajo", lambda: RO.set_activo_trabajo(tid, False))
    finally:
        try:
            RO.set_activo_trabajo(tid, False)
            print(f"    (limpieza) {tid} queda desactivado — un trabajo asignado NO se "
                  "borra, rompería el histórico (v295)")
        except Exception:
            R.basura(f"trabajo {tid}")


def bloque_inventario():
    """inventory: categorías (alta/baja)."""
    from core import inventory as INV
    cat = f"{MARCA} cat"
    _acc("inventory.add_categoria", lambda: INV.add_categoria(GRUPO, cat),
         lambda: (cat in [str(x) for x in INV.categorias(GRUPO)], "está en la lista"))
    _acc("inventory.del_categoria", lambda: INV.del_categoria(GRUPO, cat),
         lambda: (cat not in [str(x) for x in INV.categorias(GRUPO)], "ya no está"))


def bloque_proyecto():
    """El ciclo entero de una obra: crear → actividades → documentos → agrupación → borrar."""
    from core import projects as P
    nom = f"{MARCA} obra"
    pid = _crear_y_localizar(
        "projects.create_project",
        lambda: P.create_project(GRUPO, nom, cliente=f"{MARCA} SA",
                                 creado_por="dmoreno", tipo="Otro"),
        lambda: P.list_projects(GRUPO, incluir_archivados=True), "Nombre", nom)
    if not pid:
        return
    try:
        _acc("projects.add_activity",
             lambda: P.add_activity(pid, f"{MARCA} actividad", 3, 1.0),
             lambda: (bool(P.list_activities(pid)), f"{len(P.list_activities(pid))} act."))
        acts = P.list_activities(pid)
        if acts:
            orden = acts[-1].get("Orden")
            _acc("projects.update_activity_progress",
                 lambda: P.update_activity_progress(pid, orden, 50),
                 lambda: (any(str(x.get("Avance")) .startswith("50")
                              for x in P.list_activities(pid)), "avance 50 leído"))
            _acc("projects.save_activities",
                 lambda: P.save_activities(pid, [{"orden0": orden,
                                                  "Nombre": f"{MARCA} act2",
                                                  "Días": 4, "Peso": 2.0}]))
            _acc("projects.delete_activity", lambda: P.delete_activity(pid, orden))
        _acc("projects.add_document",
             lambda: P.add_document(pid, f"{MARCA}.pdf", "otro", "drv-de-prueba", "dmoreno"),
             lambda: (any(d.get("DriveID") == "drv-de-prueba"
                          for d in P.list_documents(pid)), "documento leído"))
        _acc("projects.delete_document_record",
             lambda: P.delete_document_record(pid, "drv-de-prueba"),
             lambda: (not any(d.get("DriveID") == "drv-de-prueba"
                              for d in P.list_documents(pid)), "ya no está"))

        gnom = f"{MARCA} torre"
        gid = _crear_y_localizar(
            "projects.create_grouping",
            lambda: P.create_grouping(GRUPO, gnom, "prueba"),
            lambda: P.list_groupings(GRUPO), "Nombre", gnom)
        if gid:
            _acc("projects.set_grouping_members",
                 lambda: P.set_grouping_members(gid, {pid: 1.0}, GRUPO))
            _acc("projects.delete_grouping", lambda: P.delete_grouping(gid))
    finally:
        try:
            P.delete_project(pid)
            print(f"    (limpieza) {pid} borrado")
        except Exception:
            R.basura(f"proyecto {pid}")


def _obra_temporal():
    """Crea una obra de usar y tirar, y devuelve (pid, borrar). None si no se pudo.

    ⚠️ Todo lo de esta tanda se ejercita SOBRE ELLA, no sobre obras reales:
    `limpiar_proyecto` borra asignaciones del planificador y `clock_in` escribe
    fichajes. Hacerlo sobre una obra de verdad ensuciaría datos que sí se miran.
    """
    from core import projects as P
    nom = f"{MARCA} obra tanda"
    ok, msg = _ok(P.create_project(GRUPO, nom, creado_por="dmoreno", tipo="Otro"))
    if not ok:
        R.mal("obra temporal", msg)
        return None, None
    fila = next((x for x in P.list_projects(GRUPO, incluir_archivados=True)
                 if str(x.get("Nombre", "")) == nom), None)
    if not fila:
        R.mal("obra temporal", "creada pero no se encuentra")
        return None, None
    return str(fila.get("ID", "")), (lambda p=str(fila.get("ID", "")): P.delete_project(p))


def bloque_alarmas():
    """alerts: abrir una alarma y resolverla.

    ⚠️ Se usa `create_alert`, NO `report_problem`: el segundo manda email y Telegram a
    personas reales. Comprobado en el código que estas dos no notifican.
    """
    from core import alerts as AL
    pid, borrar = _obra_temporal()
    if not pid:
        return
    try:
        _acc("alerts.create_alert",
             lambda: AL.create_alert(pid, GRUPO, "admin", "cambio",
                                     f"{MARCA} alarma de ejercicio", "dmoreno"),
             lambda: (bool(AL.list_alerts(pid)), f"{len(AL.list_alerts(pid))} alarma(s)"))
        _al = AL.list_alerts(pid)
        if _al:
            aid = str(_al[0].get("ID", ""))
            _acc("alerts.resolve_alert", lambda: AL.resolve_alert(aid, "dmoreno"),
                 lambda: (all(str(a.get("Estado", "")).lower() != "abierta"
                              for a in AL.list_alerts(pid)), "queda resuelta"))
        print("    (limpieza) la alarma NO se borra: `alerts` no tiene borrado; "
              "queda resuelta y colgando de una obra que se elimina")
    finally:
        if borrar:
            borrar()


def bloque_calculos_y_rastro():
    """toolruns: registrar un cálculo · auditoria: dejar rastro de un cambio."""
    from core import auditoria as AU
    from core import toolruns as TR
    pid, borrar = _obra_temporal()
    if not pid:
        return
    try:
        _acc("toolruns.registrar",
             lambda: TR.registrar(pid, GRUPO, "plomada", f"{MARCA} cálculo",
                                  {"entradas": {"bks": 1200}, "resultados": {"dbp": 1262}},
                                  "dmoreno"),
             lambda: (bool(TR.list_for(pid)), f"{len(TR.list_for(pid))} cálculo(s)"))
        _e = TR.entradas_de(TR.list_for(pid)[0]) if TR.list_for(pid) else {}
        (R.bien if _e.get("bks") == 1200 else R.mal)(
            "toolruns: las ENTRADAS se releen (reabrir un cálculo, v148)", _e)
        _acc("auditoria.registrar",
             lambda: AU.registrar("proyecto", pid, {"MargenMO": ("10", "25")},
                                  GRUPO, "editar"),
             lambda: (bool(AU.historial(GRUPO, "proyecto", pid)), "rastro leído"))
        print("    (limpieza) ni el cálculo ni el rastro se borran: son registro "
              "histórico y no hay función para quitarlos")
    finally:
        if borrar:
            borrar()


def bloque_inventario_activo():
    """inventory.update_activo sobre un activo REAL, restaurando lo que había."""
    from core import inventory as INV
    act = (INV.list_activos(GRUPO, incluir_baja=True) or [])
    if not act:
        R.salto("inventory.update_activo", "no hay activos en la demo")
        return
    a = act[0]
    aid = str(a.get("ID", ""))
    campo = "Nota"
    antes = str(a.get(campo, ""))
    print(f"    (sobre {aid}, {campo}={antes!r} — se restaura al final)")
    try:
        _acc("inventory.update_activo",
             lambda: INV.update_activo(aid, {campo: f"{MARCA} tocado"}),
             lambda: (str((INV.get_activo(aid) or {}).get(campo, "")).startswith(MARCA),
                      (INV.get_activo(aid) or {}).get(campo)))
    finally:
        try:
            INV.update_activo(aid, {campo: antes})
            print(f"    (limpieza) {campo} restaurado a {antes!r}")
        except Exception:
            R.basura(f"activo {aid}.{campo}")


def bloque_roster_limpiar():
    """roster.limpiar_proyecto — ⚠️ en una SEMANA LEJANA, nunca sobre lo planificado.

    Esta función borra del planificador todas las celdas de un proyecto. Ejercitarla
    sobre una semana real se llevaría por delante la planificación de la cuadrilla.
    """
    import datetime as _dt
    from core import clock, roster as RO
    pid, borrar = _obra_temporal()
    if not pid:
        return
    lunes = RO.lunes_de(clock.today(GRUPO)) + _dt.timedelta(days=140)   # ~5 meses
    usr = "campo1"
    try:
        _acc("roster.guardar_persona (semana lejana)",
             lambda: RO.guardar_persona(GRUPO, lunes, usr,
                                        {"lun": {"items": [{"a": pid, "i": "", "f": ""}]}}),
             lambda: (len(RO.celda_items(RO.get_semana(GRUPO, lunes), usr, "lun")) == 1,
                      "asignación puesta"))
        n = RO.limpiar_proyecto(GRUPO, pid)
        RO._invalidate()
        quedan = len(RO.celda_items(RO.get_semana(GRUPO, lunes), usr, "lun"))
        (R.bien if quedan == 0 else R.mal)(
            f"roster.limpiar_proyecto (quitó {n})", f"quedan {quedan}")
    finally:
        try:
            RO.guardar_persona(GRUPO, lunes, usr, {})
            print(f"    (limpieza) semana {lunes} vaciada")
        except Exception:
            R.basura(f"roster {lunes} {usr}")
        if borrar:
            borrar()


def bloque_fichaje():
    """timeclock: clock_in y clock_out, y las filas se BORRAN al terminar.

    ⚠️ Un fichaje de prueba que se quede suma horas al costo de una obra y al P&L.
    Por eso aquí no basta con cerrar la sesión: hay que quitar las filas.
    """
    from core import timeclock as T
    pid, borrar = _obra_temporal()
    if not pid:
        return
    nombre, usr = f"{MARCA} tester", f"{MARCA}-usr"
    try:
        _acc("timeclock.clock_in",
             lambda: T.clock_in(nombre, f"{MARCA} obra tanda", "", GRUPO,
                                tipo=T.TIPO_PROYECTO, usuario=usr, proyecto_id=pid),
             lambda: (bool(T.open_sessions(nombre, GRUPO, usr).get(T.TIPO_PROYECTO)),
                      "sesión abierta"))
        _acc("timeclock.clock_out",
             lambda: T.clock_out(nombre, GRUPO, tipo=T.TIPO_PROYECTO, usuario=usr),
             lambda: (not T.open_sessions(nombre, GRUPO, usr).get(T.TIPO_PROYECTO),
                      "sesión cerrada"))
    finally:
        try:
            ws, err = T._get_worksheet()
            filas = ws.get_all_records(numericise_ignore=["all"]) if not err else []
            idxs = [i for i, r in enumerate(filas) if str(r.get("Usuario", "")) == usr]
            for i in reversed(idxs):
                ws.delete_rows(i + 2)
            T._invalidate_records()
            print(f"    (limpieza) {len(idxs)} fichaje(s) de prueba borrados")
        except Exception as e:                                    # noqa: BLE001
            R.basura(f"fichajes de {usr} ({str(e)[:50]})")
        if borrar:
            borrar()


def bloque_credenciales():
    """credentials: alta y borrado de una credencial de prueba.

    ⚠️ NO se toca `notify_expiring`: manda correo y Telegram Y escribe `UltimoAviso`
    en credenciales reales, falseando el deduplicado de 25 días.
    """
    from core import credentials as CR
    usr = "campo1"
    antes = len(CR.list_for(usr))
    _acc("credentials.add",
         lambda: CR.add(usr, GRUPO, "Otro", numero=f"{MARCA}-1",
                        vencimiento="2027-01-01", nota=MARCA,
                        actualizado_por="dmoreno"),
         lambda: (len(CR.list_for(usr)) == antes + 1, f"{len(CR.list_for(usr))} credenciales"))
    nueva = next((c for c in CR.list_for(usr)
                  if str(c.get("Numero", "")).startswith(MARCA)), None)
    if not nueva:
        R.mal("credentials.add", "creada pero no se encuentra")
        return
    _acc("credentials.delete", lambda: CR.delete(str(nueva.get("ID", ""))),
         lambda: (len(CR.list_for(usr)) == antes, "vuelve a estar como antes"))
    R.salto("credentials.notify_expiring", PROHIBIDAS["credentials.notify_expiring"])


def bloque_facturas():
    """invoices: emitir, cobrar y anular — sobre una obra de usar y tirar."""
    from core import invoices as I
    pid, borrar = _obra_temporal()
    if not pid:
        return
    fid = ""
    try:
        # ⚠️ La línea es {concepto, importe, proyecto_id} — NO {cantidad, precio}.
        # Con las claves equivocadas el subtotal salía 0, el total 0, y el cobro no
        # podía ser «parcial»: parecían dos fallos de la app y eran del test.
        _lineas = [{"concepto": f"{MARCA} servicio", "importe": 1000.0,
                    "proyecto_id": pid}]
        _cli = f"{MARCA} SA {SELLO}"
        ok, msg = _ok(I.create_factura(GRUPO, "", _cli, _lineas,
                                       impuesto_pct=10.0, creado_por="dmoreno"))
        f = next((x for x in I.list_facturas(GRUPO)
                  if str(x.get("ClienteNombre", "")) == _cli), None)
        if not ok or not f:
            R.mal("invoices.create_factura", msg or "no se encuentra al releer")
            return
        fid = str(f.get("ID", ""))
        R.bien("invoices.create_factura", fid)
        _t = float(str(f.get("Total", 0)) or 0)
        (R.bien if abs(_t - 1100.0) < 0.01 else R.mal)(
            "el total lleva el impuesto (1000 + 10%)", _t)
        _acc("invoices.registrar_cobro (parcial)",
             lambda: I.registrar_cobro(fid, 400.0),
             lambda: (I.estado_cobro(I.get_factura(fid)) == "parcial",
                      I.estado_cobro(I.get_factura(fid))))
        _acc("invoices.anular", lambda: I.anular(fid),
             lambda: (str(I.get_factura(fid).get("Estado", "")).lower() == "anulada",
                      I.get_factura(fid).get("Estado")))
        print("    (limpieza) la factura queda ANULADA: anular es el borrado del "
              "dominio (una factura emitida no se borra, se anula)")
    finally:
        if borrar:
            borrar()


def bloque_gastos():
    """expenses: cargar una compra y borrarla."""
    from core import expenses as E
    pid, borrar = _obra_temporal()
    if not pid:
        return
    try:
        _acc("expenses.add",
             lambda: E.add(pid, GRUPO, 250.0, categoria="Materiales",
                           proveedor=f"{MARCA} proveedor", descripcion=MARCA,
                           creado_por="dmoreno"),
             lambda: (bool(E.list_for(pid)), f"{len(E.list_for(pid))} compra(s)"))
        g = (E.list_for(pid) or [{}])[0]
        _acc("expenses.delete", lambda: E.delete(str(g.get("ID", ""))),
             lambda: (not E.list_for(pid), "ya no está"))
        R.salto("expenses.upload_receipt",
                "sube a Drive y desde aquí no hay credenciales [gdrive]")
    finally:
        if borrar:
            borrar()


def bloque_nominas():
    """payroll: generar, editar conceptos y anular.

    ⚠️ `generar` crea una nómina por CADA persona con horas en el periodo, así que no
    se puede lanzar sobre un periodo real sin llenar la hoja. Se usa una ventana en el
    FUTURO, donde nadie tiene horas salvo el fichaje de prueba que crea este bloque —
    y al terminar se borran las dos filas.
    """
    import datetime as _dt
    from core import auth, clock, payroll as PY, timeclock as T
    # alguien con tarifa: sin ella `generar` lo SALTA a propósito (v346)
    con_tarifa = next((u for u in auth.list_users()
                       if str(u.get("Grupo")) == GRUPO
                       and str(u.get("TarifaHora", "")).strip() not in ("", "0")), None)
    if not con_tarifa:
        R.salto("payroll.generar", "nadie tiene tarifa/hora: `generar` los saltaría")
        return
    nom, usr = str(con_tarifa.get("Nombre", "")), str(con_tarifa.get("Usuario", ""))
    pid, borrar = _obra_temporal()
    if not pid:
        return
    d0 = clock.today(GRUPO) + _dt.timedelta(days=200)
    ini = f"{d0.isoformat()} 07:00:00"
    fin = f"{d0.isoformat()} 15:00:00"
    ws, err = T._get_worksheet()
    nid = ""
    try:
        if err:
            R.mal("payroll: fichaje de apoyo", err)
            return
        # ⚠️ La fila se arma POR NOMBRE de columna, no adivinando el orden: al
        # adivinarlo, los datos cayeron en columnas equivocadas y `generar` no vio
        # ninguna hora — el fallo de la fila posicional de v363, cometido en el test.
        _v = {"Nombre": nom, "Proyecto": f"{MARCA} obra tanda", "Clock In": ini,
              "Clock Out": fin, "Horas": "8.0", "Estado": "cerrado", "Grupo": GRUPO,
              "Usuario": usr, "Tipo": T.TIPO_GENERAL, "ProyectoID": pid}
        ws.append_row([_v.get(c, "") for c in T.HEADERS], value_input_option="RAW")
        T._invalidate_records()
        res = PY.generar(GRUPO, d0.isoformat(), d0.isoformat(), super_pct=11.5,
                         ret_pct=10.0, creado_por="dmoreno")
        creadas = res.get("creadas", 0) if isinstance(res, dict) else 0
        (R.bien if creadas else R.mal)("payroll.generar (ventana futura)", res)
        n = next((x for x in PY.list_nominas(GRUPO)
                  if str(x.get("PeriodoDesde", "")) == d0.isoformat()), None)
        if not n:
            R.mal("payroll.generar", "creada pero no se encuentra")
            return
        nid = str(n.get("ID", ""))
        _acc("payroll.update_conceptos",
             lambda: PY.update_conceptos(nid, [{"tipo": "devengo", "nombre": MARCA,
                                                "monto": 50.0}]),
             lambda: (any(str(c.get("nombre", "")) == MARCA
                          for c in PY.conceptos_de(PY.get_nomina(nid))), "concepto leído"))
        _acc("payroll.marcar_pagada", lambda: PY.marcar_pagada(nid),
             lambda: (str(PY.get_nomina(nid).get("Estado", "")).lower() == "pagada",
                      PY.get_nomina(nid).get("Estado")))
        _acc("payroll.anular", lambda: PY.anular(nid),
             lambda: (str(PY.get_nomina(nid).get("Estado", "")).lower() == "anulada",
                      PY.get_nomina(nid).get("Estado")))
    finally:
        # ⚠️ Se BORRAN las dos filas: una nómina de prueba mueve el P&L, y un fichaje
        # en el futuro descuadraría cualquier cuenta que mire ese periodo.
        try:
            filas = ws.get_all_records(numericise_ignore=["all"])
            idxs = [i for i, r in enumerate(filas)
                    if str(r.get("Proyecto", "")).startswith(MARCA)]
            for i in reversed(idxs):
                ws.delete_rows(i + 2)
            T._invalidate_records()
            print(f"    (limpieza) {len(idxs)} fichaje(s) de apoyo borrados")
        except Exception as e:                                    # noqa: BLE001
            R.basura(f"fichaje de apoyo ({str(e)[:50]})")
        if nid:
            try:
                w2 = PY._ws() if hasattr(PY, "_ws") else None
                w2 = w2[0] if isinstance(w2, tuple) else w2
                fs = w2.get_all_records(numericise_ignore=["all"])
                j = next((i for i, r in enumerate(fs) if str(r.get("ID", "")) == nid), -1)
                if j >= 0:
                    w2.delete_rows(j + 2)
                    PY._invalidate()
                    print(f"    (limpieza) nómina {nid} borrada")
            except Exception as e:                                # noqa: BLE001
                R.basura(f"nómina {nid} ({str(e)[:50]})")
        if borrar:
            borrar()


def bloque_auth():
    """auth: grupo y usuario de usar y tirar — ⚠️ NUNCA sobre los reales.

    Esta es la tanda delicada: aquí se cambian contraseñas, roles y accesos. Dos
    reglas que no se negocian:
      · se crea un GRUPO propio y toda la configuración (zona, margen, impuesto) se
        toca ahí, jamás en `cliente1`: cambiarle el margen movería todas sus cifras;
      · se crea un USUARIO propio y solo se borra ese. ⚠️ Y nunca se vacía la hoja
        `Login`, que reabriría el bootstrap de «crear propietario» (v53).
    """
    from core import auth
    g = f"ZZZ-{SELLO}"
    u = f"zzz{SELLO}"
    creado_g = creado_u = False
    try:
        # ── grupo ────────────────────────────────────────────────────────────
        _acc("auth.add_group", lambda: auth.add_group(g, "ejercicio", "Australia/Sydney"),
             lambda: (any(str(x.get("Grupo", "")) == g for x in auth.list_groups()),
                      "está en la lista"))
        creado_g = any(str(x.get("Grupo", "")) == g for x in auth.list_groups())
        if not creado_g:
            return
        _acc("auth.set_group_timezone",
             lambda: auth.set_group_timezone(g, "America/Bogota"),
             lambda: (auth.group_timezone(g) == "America/Bogota", auth.group_timezone(g)))
        _acc("auth.set_group_margin_default",
             lambda: auth.set_group_margin_default(g, 33),
             lambda: (abs(float(auth.group_margin_default(g)) - 33) < 0.01,
                      auth.group_margin_default(g)))
        _acc("auth.set_group_tax_default", lambda: auth.set_group_tax_default(g, 21),
             lambda: (abs(float(auth.group_tax_default(g)) - 21) < 0.01,
                      auth.group_tax_default(g)))
        _acc("auth.set_group_num_setting",
             lambda: auth.set_group_num_setting(g, "MargenDefault", 12),
             lambda: (abs(float(auth.group_margin_default(g)) - 12) < 0.01,
                      auth.group_margin_default(g)))

        # ── usuario ──────────────────────────────────────────────────────────
        _acc("auth.add_user",
             lambda: auth.add_user(u, "Prueba-1234", "campo", f"{MARCA} tester", g),
             lambda: (bool(auth.get_user(u)), "está en Login"))
        creado_u = bool(auth.get_user(u))
        if not creado_u:
            return
        # ⚠️ la contraseña se comprueba INTENTANDO ENTRAR, que es lo que importa:
        # que `set_password` escriba un hash es un detalle; que deje entrar, no.
        _acc("auth.set_password", lambda: auth.set_password(u, "Otra-5678"),
             lambda: (bool((auth.verify_login(u, "Otra-5678") or {}).get("ok", True))
                      and not (auth.verify_login(u, "Prueba-1234") or {}).get("ok", False),
                      "entra con la nueva y no con la vieja"))
        _acc("auth.set_role", lambda: auth.set_role(u, "administrador"),
             lambda: (str(auth.get_user(u).get("Rol")) == "administrador",
                      auth.get_user(u).get("Rol")))
        _acc("auth.set_active", lambda: auth.set_active(u, False),
             lambda: (str(auth.get_user(u).get("Activo", "")).upper() != "SI",
                      auth.get_user(u).get("Activo")))
        _acc("auth.set_group", lambda: auth.set_group(u, GRUPO),
             lambda: (str(auth.get_user(u).get("Grupo")) == GRUPO,
                      auth.get_user(u).get("Grupo")))
        _acc("auth.end_session", lambda: auth.end_session(u) or (True, "ok"))
    finally:
        if creado_u:
            try:
                auth.delete_user(u)
                print(f"    (limpieza) usuario {u} borrado: "
                      f"{'sigue' if auth.get_user(u) else 'ya no está'}")
            except Exception as e:                                # noqa: BLE001
                R.basura(f"usuario {u} ({str(e)[:50]})")
        if creado_g:
            try:
                auth.delete_group(g)
                print(f"    (limpieza) grupo {g} borrado")
            except Exception as e:                                # noqa: BLE001
                R.basura(f"grupo {g} ({str(e)[:50]})")


BLOQUES = {
    "catalogo": bloque_catalogo,
    "clientes": bloque_clientes,
    "rieles": bloque_rieles,
    "roster": bloque_roster,
    "inventario": bloque_inventario,
    "proyecto": bloque_proyecto,
    # tanda «obra» (v407+)
    "alarmas": bloque_alarmas,
    "calculos": bloque_calculos_y_rastro,
    "activo": bloque_inventario_activo,
    "roster_limpiar": bloque_roster_limpiar,
    "fichaje": bloque_fichaje,
    "credenciales": bloque_credenciales,
    # tanda «dinero»
    "facturas": bloque_facturas,
    "gastos": bloque_gastos,
    "nominas": bloque_nominas,
    # tanda «auth» — la delicada
    "auth": bloque_auth,
}


def main():
    global SECO
    ap = argparse.ArgumentParser()
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--seco", action="store_true")
    ap.add_argument("--bloque", default="")
    ap.add_argument("--todo", action="store_true")
    a, _ = ap.parse_known_args()
    SECO = a.seco

    if a.listar:
        print(f"{len(BLOQUES)} bloques:")
        for k, f in BLOQUES.items():
            print(f"  {k:<12} {(f.__doc__ or '').splitlines()[0]}")
        print("\nNO se ejercitan:")
        for k, v in PROHIBIDAS.items():
            print(f"  {k:<28} {v}")
        return 0

    # ⚠️ salvaguarda: esto escribe de verdad
    if st.session_state["auth"]["grupo"] != GRUPO:
        print("ABORTADO: solo se ejercita el grupo de demo.")
        return 2
    _interceptar_envios()

    elegidos = ([a.bloque] if a.bloque else list(BLOQUES)) if (a.bloque or a.todo) else []
    if not elegidos:
        print("Nada que hacer. Usa --listar, --seco, --bloque X o --todo.")
        return 0
    for nom in elegidos:
        if nom not in BLOQUES:
            print(f"(bloque desconocido: {nom})")
            continue
        print(f"\n== {nom} ==")
        try:
            BLOQUES[nom]()
        except Exception as e:                                    # noqa: BLE001
            R.mal(f"bloque {nom}", e)
            traceback.print_exc()

    print(f"\n=== {len(R.ok)} ok · {len(R.fallos)} fallos · {len(R.saltados)} saltados "
          f"· {len(R.sucio)} sin limpiar · {len(_envios)} envíos interceptados ===")
    for q, e in R.fallos:
        print(f"  FALLO  {q}: {e}")
    for q in R.sucio:
        print(f"  SUCIO  {q}")
    return 1 if (R.fallos or R.sucio) else 0


if __name__ == "__main__":
    sys.exit(main())
