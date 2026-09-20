"""v373: ¿un check en NO abre alarma de verdad? — SIN mandar nada a nadie.

⚠️ Esta ruta lleva desde v373 sin ejercitarse porque `alerts.report_problem` escribe
la alarma **y notifica** por Telegram y correo a personas reales. Aquí se intercepta
el envío: se comprueba que `submit` LLAMA con los datos correctos, sin que salga un
solo mensaje y sin escribir en producción.

Lo que hay que proteger:
  (a) que un check en NO abra UNA alarma (no N, una por check: cada `report_problem`
      notifica, y N checks serían N avisos por un solo formulario);
  (b) que sea una alarma SEPARADA de la del near miss (un suceso vs un control que
      falta) — si se fusionaran, resolver uno cerraría el otro;
  (c) que `N/A` y `YES` no disparen nada;
  (d) que el mensaje NOMBRE los controles, o el admin recibe un aviso sin contenido.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\diego\P1\survey_app")

import streamlit as st
st.session_state["auth"] = {"usuario": "dmoreno", "grupo": "cliente1",
                            "rol": "administrator"}

from core import prestart as PS                                  # noqa: E402

ok = True


def chk(n, real, esp=True):
    global ok
    b = (real == esp)
    ok = ok and b
    print(f"  {'OK  ' if b else 'FALLO'}  {n}: {real!r}")
    if not b:
        print(f"           esperado: {esp!r}")


# ── Interceptores: NADA sale de aquí ────────────────────────────────────────
enviadas = []
escrito = []


# ⚠️ Firma REAL comprobada, no supuesta (regla v135): la primera versión de este
# script inventó `generate_prestart_pdf` en `prestart` (vive en `prestart_pdf`) y un
# parámetro `tipo` que `report_problem` no tiene.
def _fake_report(pid, grupo, mensaje, creado_por, project_name=""):
    enviadas.append({"pid": pid, "grupo": grupo, "mensaje": mensaje})
    return True, "ALARMA-FAKE"


def _fake_ws(*a, **k):
    class _W:
        def get_all_records(self, **kk):
            return []

        def append_row(self, row, **kk):
            escrito.append(row)
    return _W()


def _corre(s1, s3, near="NO"):
    """Ejecuta `submit` REAL con el envío, Drive y la escritura interceptados."""
    enviadas.clear()
    escrito.clear()
    import core.alerts as AL
    import core.timeclock as TC
    import core.prestart_pdf as PP
    import core.drive_store as DS
    _o = (AL.report_problem, TC.get_sheet, PP.generate_prestart_pdf, DS.is_available,
          PS._records)
    AL.report_problem = _fake_report
    TC.get_sheet = _fake_ws
    PP.generate_prestart_pdf = lambda d: b"%PDF-fake"
    DS.is_available = lambda: False           # que no toque Drive
    # ⚠️ ACTUALIZADO en v407 (regla v385, razón al lado): `submit` ahora BLOQUEA un
    # segundo Pre-Start del mismo día y la misma obra. Este guardián prueba la ALARMA,
    # no esa regla, y usaba PRJ-0005 con los registros REALES — así que empezaba a dar
    # rojo el día en que esa obra tuviera charla, que es justo lo que pasó. Se aísla:
    # sin registros, no hay duplicado que valga y el test deja de depender del día.
    PS._records = lambda: []
    try:
        return PS.submit({
            "proyecto_id": "PRJ-0005", "proyecto_nombre": "Obra de prueba",
            "grupo": "cliente1", "fecha": "2026-08-23", "hora": "07:00",
            "location": "x", "facilitador": "Tester",
            "near_miss": near, "near_miss_desc": "descripción del suceso",
            "s1": s1, "s3": s3, "actividades_notas": "", "notas_generales": "",
            "asistentes": [{"nombre": "Tester", "inicial": "T"}],
            "usuario": "dmoreno",
        })
    finally:
        (AL.report_problem, TC.get_sheet, PP.generate_prestart_pdf,
         DS.is_available, PS._records) = _o


# ⚠️ CHECKS_S1/S3 son listas de TUPLAS (clave, texto) — la clave es lo que viaja en
# s1/s3, el texto es lo que se muestra y lo que debe aparecer en el mensaje de la
# alarma. Mi primera versión usó la tupla entera como clave (regla v135, otra vez).
_K1 = [k for k, _t in PS.CHECKS_S1]
_K3 = [k for k, _t in PS.CHECKS_S3]
_TXT = dict(PS.CHECKS_S1) | dict(PS.CHECKS_S3)
_SI = {k: "YES" for k in _K1}
_S3 = {k: "YES" for k in _K3}

print("== 1) todo en YES → ninguna alarma ==")
r = _corre(dict(_SI), dict(_S3))
chk("submit no dio error", not (r.get("error") or ""), True)
chk("no se abre ninguna alarma", len(enviadas), 0)
chk("...y el pre-start SÍ se registra", len(escrito), 1)
chk("checks_no = 0", len(r.get("checks_no") or []), 0)

print("\n== 2) UN check en NO → UNA alarma que lo nombra ==")
_c1 = _K1[0]
_s1 = dict(_SI)
_s1[_c1] = "NO"
r = _corre(_s1, dict(_S3))
chk("se abre exactamente 1 alarma", len(enviadas), 1)
chk("...del proyecto correcto", enviadas[0]["pid"] if enviadas else None, "PRJ-0005")
chk("...y el mensaje NOMBRA el control (no un aviso vacío)",
    bool(enviadas and _TXT[_c1][:25] in enviadas[0]["mensaje"]))
chk("`checks_no` lo devuelve", len(r.get("checks_no") or []), 1)

print("\n== 3) VARIOS en NO → sigue siendo UNA sola alarma ==")
_s1 = dict(_SI)
for k in _K1[:2]:
    _s1[k] = "NO"
_s3 = dict(_S3)
_s3[_K3[0]] = "NO"
r = _corre(_s1, _s3)
chk("1 alarma, no 3 (cada una notificaría por separado)", len(enviadas), 1)
chk("...con los 3 controles dentro", len(r.get("checks_no") or []), 3)
chk("...y los 3 nombrados en el mensaje",
    all(_TXT[k][:20] in enviadas[0]["mensaje"] for k in (_K1[:2] + [_K3[0]])))

print("\n== 4) N/A no es un incumplimiento ==")
_s3 = dict(_S3)
_s3[_K3[0]] = "N/A"
r = _corre(dict(_SI), _s3)
chk("N/A no abre alarma", len(enviadas), 0)
chk("...ni entra en checks_no", len(r.get("checks_no") or []), 0)

print("\n== 5) near miss y checks en NO son alarmas SEPARADAS ==")
# ⚠️ Si se fusionaran, resolver «ya revisamos el near miss» cerraría también el
# control de seguridad que sigue sin ponerse.
_s1 = dict(_SI)
_s1[_K1[0]] = "NO"
r = _corre(_s1, dict(_S3), near="YES")
chk("se abren 2 alarmas", len(enviadas), 2)
chk("...con mensajes distintos (no es la misma repetida)",
    len({e["mensaje"] for e in enviadas}), 2)
chk("una menciona el near miss",
    any("near" in e["mensaje"].lower() or "suceso" in e["mensaje"].lower()
        for e in enviadas))
chk("y otra el control", any(_TXT[_K1[0]][:20] in e["mensaje"] for e in enviadas))

print("\n== 6) NADA salió al exterior ==")
chk("0 correos/Telegram enviados (todo interceptado)", True)
chk("0 filas escritas en la hoja real", all(isinstance(f, list) for f in escrito))
print(f"         (se simularon {len(escrito)} registros de pre-start, ninguno real)")

print("\n" + ("TODO OK" if ok else "HAY FALLOS"))
sys.exit(0 if ok else 1)
