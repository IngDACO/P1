# -*- coding: utf-8 -*-
"""Carga en LOTE de la biblioteca técnica (v520): la carpeta de obra del usuario.

Uso:
    python importar_biblioteca.py <carpeta> [--ensayo] [--limite N]

La carpeta la deja lista `preparar_biblioteca.py` (copias reducidas y SIN metadatos,
más `_indice.json`), y al lado vive `_clasificacion.py`, hecha MIRANDO las fotos. Ni lo
uno ni lo otro entra al repo: son datos, y el script de despliegue hace `git add` de
todo.

⚠️ Por qué no llama a `library.add_item` 750 veces: cada alta lee la hoja ENTERA para
calcular el ID (fresco, a propósito, v323). 750 lecturas contra un techo de 60 por
minuto son 13 minutos de 429 como poco. Aquí se lee una vez, los IDs se asignan en
memoria y se escribe con `append_rows` en tandas.

⚠️ Pero valida EXACTAMENTE lo que valida `add_item` —sección, tipo, título y una fila
del largo de HEADERS— y además que la cabecera REAL de la hoja sea HEADERS: la fila es
posicional, y con otra cabecera cada dato caería en la columna de al lado (v363). Una
carga en lote que se salta las reglas del alta es por donde entra la basura que la
pantalla nunca habría dejado pasar.

⚠️ Idempotente. La llave es `FileName` = «<clave>.jpg»: lo que ya está en la hoja no se
vuelve a escribir. Y lo que ya subió a Drive queda anotado en `_subida_estado.json`,
así que si se corta entre Drive y la hoja, la siguiente pasada no duplica archivos.

⚠️ El orden es el de la pantalla (`library_ui._guardar`, criterio v343): primero el
archivo, después la ficha. Una ficha sin archivo promete algo que no existe.
"""
import argparse
import importlib.util
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "survey_app"))
os.chdir(RAIZ)                       # secrets.toml se busca relativo al CWD (trampa nº19)
sys.path.insert(0, RAIZ)

from core import columnas, hojas, library as LIB, timeclock   # noqa: E402
from core import drive_store as dr                              # noqa: E402

SUBIDO_POR = "COPEX library import"
MIME = "image/jpeg"
TANDA = 100


def _drive_desde(ruta_toml):
    """Credenciales de Drive desde un .toml SUELTO, cuando el `secrets.toml` local no
    trae `[gdrive]` (el del Cloud sí: trampa nº11, lo local no es lo de producción).

    ⚠️ Solo se LEE, en memoria, para esta ejecución: ni se copia al repo ni se imprime.
    Es la MISMA credencial de la app (mismo cliente OAuth), y con el alcance
    `drive.file` eso importa: un archivo subido con OTRO cliente sería invisible para
    la app, que no podría ni previsualizarlo ni descargarlo.
    """
    import tomllib
    from google.oauth2.credentials import Credentials
    with open(ruta_toml, "rb") as fh:
        g = tomllib.load(fh)["gdrive"]
    # ⚠️ Igual que `drive_store._credentials`, con SUS constantes: otro alcance sería
    # otro permiso, y no el que tiene la app.
    cred = Credentials(None, refresh_token=g["refresh_token"],
                       client_id=g["client_id"], client_secret=g["client_secret"],
                       token_uri=dr._TOKEN_URI, scopes=dr.SCOPES)
    dr._credentials = lambda: cred


def _clasificacion(carpeta):
    spec = importlib.util.spec_from_file_location(
        "clasificacion", os.path.join(carpeta, "_clasificacion.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _plan(carpeta):
    """Lo que se va a subir, validado ANTES de tocar nada."""
    fotos = json.load(open(os.path.join(carpeta, "_indice.json"), encoding="utf-8"))["fotos"]
    cl = _clasificacion(carpeta)
    if cl.pendientes():
        raise SystemExit("Hay %d fotos sin sección decidida: %s…"
                         % (len(cl.pendientes()), cl.pendientes()[:5]))
    plan, errores = [], []
    for f in fotos:
        k = f["clave"]
        if k not in cl.C:
            errores.append("%s: sin clasificar" % k)
            continue
        sec, tipo, titulo, notas, _marca, modelo = cl.C[k]
        if sec not in LIB.SECCIONES:
            errores.append("%s: sección inválida %r" % (k, sec))
        if tipo not in LIB.TIPOS:
            errores.append("%s: tipo inválido %r" % (k, tipo))
        if not str(titulo).strip():
            errores.append("%s: sin título" % k)
        ruta = os.path.join(carpeta, f["archivo"])
        if not os.path.isfile(ruta):
            errores.append("%s: no está el archivo %s" % (k, ruta))
        plan.append({"clave": k, "ruta": ruta, "seccion": sec, "tipo": tipo,
                     "titulo": str(titulo).strip(), "notas": str(notas or "").strip(),
                     "marca": cl.marca_final(k), "modelo": str(modelo or "").strip(),
                     "filename": k + ".jpg"})
    if errores:
        raise SystemExit("La clasificación no pasa las reglas del alta:\n  "
                         + "\n  ".join(errores[:40]))
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--ensayo", action="store_true", help="valida y cuenta; no escribe nada")
    ap.add_argument("--limite", type=int, default=0, help="subir solo N (prueba corta)")
    ap.add_argument("--gdrive", default="", help=".toml con [gdrive] si secrets.toml no lo trae")
    a = ap.parse_args()
    if a.gdrive:
        _drive_desde(a.gdrive)

    plan = _plan(a.carpeta)
    print("plan: %d fotos validadas contra las reglas del alta" % len(plan))

    ws, err = LIB._ws()
    if err:
        raise SystemExit(err)
    cab = ws.row_values(1)
    if cab[:len(LIB.HEADERS)] != LIB.HEADERS:
        raise SystemExit("La cabecera REAL de %s no es HEADERS: %s" % (LIB.SHEET, cab))
    actuales = columnas.canonizar(ws.get_all_records(numericise_ignore=["all"]))
    ya = {str(r.get("FileName", "")).strip() for r in actuales}
    mx = 0
    for r in actuales:
        u = str(r.get("ID", ""))
        if u.startswith("LIB-"):
            try:
                mx = max(mx, int(u.split("-")[1]))
            except ValueError:
                pass
    try:
        usados = hojas.ids_referenciados("LIB-", LIB.SHEET)
    except Exception as e:
        print("  aviso: sin comprobar IDs referenciados (%s)" % e)
        usados = set()

    pend = [p for p in plan if p["filename"] not in ya]
    if a.limite:
        pend = pend[:a.limite]
    print("en la hoja ya: %d filas (%d de esta carga) · por subir: %d · último ID: LIB-%04d"
          % (len(actuales), len(plan) - len([p for p in plan if p["filename"] not in ya]),
             len(pend), mx))
    if a.ensayo or not pend:
        return

    # 1) Marcas que falten en el catálogo: sin ellas el filtro por marca no las ofrece.
    tienen = {m.lower() for m in LIB.marcas(incluir_inactivos=True)}
    for marca in sorted({p["marca"] for p in pend if p["marca"]}):
        if marca.lower() not in tienen:
            ok, msg = LIB.add_modelo(marca, "")
            print("  catálogo: %s -> %s" % (marca, msg))

    # 2) Archivos a Drive, anotando cada uno (si se corta, no se duplica).
    ruta_estado = os.path.join(a.carpeta, "_subida_estado.json")
    estado = json.load(open(ruta_estado, encoding="utf-8")) if os.path.isfile(ruta_estado) else {}
    carpeta_id = dr.folder(LIB.FOLDER_NAME)
    t0, subidas = time.time(), 0
    for i, p in enumerate(pend, 1):
        if p["clave"] in estado:
            continue
        with open(p["ruta"], "rb") as fh:
            datos = fh.read()
        for intento in range(4):
            try:
                estado[p["clave"]] = dr.upload_to(carpeta_id, p["filename"], datos, MIME)
                break
            except Exception as e:
                print("  %s: fallo de Drive (%s), reintento %d" % (p["clave"], e, intento + 1))
                time.sleep(5 * (intento + 1))
        else:
            json.dump(estado, open(ruta_estado, "w", encoding="utf-8"), indent=0)
            raise SystemExit("Drive no acepta %s; el estado quedó guardado." % p["clave"])
        subidas += 1
        if subidas % 25 == 0:
            json.dump(estado, open(ruta_estado, "w", encoding="utf-8"), indent=0)
            print("  drive: %d/%d (%.0f s)" % (i, len(pend), time.time() - t0), flush=True)
    json.dump(estado, open(ruta_estado, "w", encoding="utf-8"), indent=0)
    print("drive: %d subidas nuevas en %.0f s" % (subidas, time.time() - t0))

    # 3) Las fichas, en tandas. IDs en memoria, saltando los referenciados (v427).
    n, filas = mx, []
    for p in pend:
        n += 1
        while "LIB-%04d" % n in usados:
            n += 1
        fila = ["LIB-%04d" % n, p["marca"], p["modelo"], p["seccion"], p["tipo"],
                p["titulo"], p["notas"], estado[p["clave"]], p["filename"], MIME,
                SUBIDO_POR, timeclock._now()]
        if len(fila) != len(LIB.HEADERS):
            raise SystemExit("fila de %d != HEADERS de %d" % (len(fila), len(LIB.HEADERS)))
        filas.append(fila)
    for i in range(0, len(filas), TANDA):
        tanda = filas[i:i + TANDA]
        ws.append_rows(tanda, value_input_option="RAW")
        print("  hoja: %d/%d filas" % (i + len(tanda), len(filas)), flush=True)
        time.sleep(3)
    LIB._invalidate()
    print("hecho: %s … %s" % (filas[0][0], filas[-1][0]))


if __name__ == "__main__":
    main()
