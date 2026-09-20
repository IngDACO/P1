"""Roturas de v459. Un guardián que solo aprueba el código bueno no demuestra nada."""
import os
import pathlib
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CORE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")
AQUI = pathlib.Path(__file__).parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

ROTURAS = [
    ("projects_ui.py",
     '''        return [u["Usuario"] for u in auth.list_users(grupo)
                if str(u.get("Rol", "")) == "campo"]
    except Exception:
        return []''',
     '''        return [u["Usuario"] for u in auth.list_users(grupo)]
    except Exception:
        return []''',
     "⚠️ head installer deja de filtrar por campo (ofreceria administradores)"),

    ("projects_ui.py",
     '''        return [str(u["Usuario"]) for u in auth.list_users(grupo)]
    except Exception as e:
        logger.warning("_usuarios_de: no se pudo leer''',
     '''        return [str(u["Usuario"]) for u in auth.list_users(grupo)
                if str(u.get("Rol", "")) == "campo"]
    except Exception as e:
        logger.warning("_usuarios_de: no se pudo leer''',
     "⚠️ el responsable de localizacion se limita al campo (deja fuera a administracion)"),

    ("projects_ui.py",
     '''            ing = c1.multiselect(
                t("Head installer/s"), campos,
                format_func=lambda u: _etq_us(campos).get(u, u),
                key=f"np_ing_{key}",
                help=(t("Field users of this company.") if campos else
                      t("No field users yet: create them in Planning → Users.")))''',
     '''            ing = [c1.text_input(t("Engineer in charge"), key=f"np_ing_{key}")]''',
     "vuelve el texto libre al crear la obra"),

    ("projects_ui.py",
     'ingeniero=";".join(ing)',
     'ingeniero=(ing[0] if ing else "")',
     "⚠️ al crear se guarda UNO solo, no varios head installers"),

    ("projects_ui.py",
     'ingeniero=";".join(resp)',
     'ingeniero=(resp[0] if resp else "")',
     "⚠️ la localizacion guarda UN responsable, no varios"),

    # ⚠️ Vuelve una COPIA del filtro: es el fallo que yo mismo cometí (tres definiciones
    # de «usuarios de campo» en el mismo módulo). No rompe nada hoy; diverge mañana.
    ("projects_ui.py",
     ("def _editar_localizacion(pid, grupo, prj):" + chr(10)
      + "    campos = _field_users(grupo)"),
     ("def _editar_localizacion(pid, grupo, prj):" + chr(10)
      + '    campos = [u["Usuario"] for u in auth.list_users(grupo)' + chr(10)
      + '              if str(u.get("Rol", "")) == "campo"]'),
     "⚠️ vuelve una copia inline del filtro «rol == campo»"),

    # ⚠️ El informe del CLIENTE volveria a decir «campo1;mchen» en vez de los nombres.
    ("survey_ui.py",
     '            st.session_state["ingeniero"] = _ing_sv',
     '            st.session_state["ingeniero"] = str(_prj_sv.get("Ingeniero", ""))',
     "⚠️ el informe del cliente vuelve a recibir los LOGIN crudos"),

    ("email_notify.py",
     "<strong>Head installer/s:</strong>",
     "<strong>Engineer:</strong>",
     "el correo vuelve a decir «Engineer»"),
]

cazadas = 0
for i, (mod, viejo, nuevo, desc) in enumerate(ROTURAS, 1):
    p = CORE / mod
    bak = p.read_text(encoding="utf-8")
    n = bak.count(viejo)
    if n != 1:
        print(f"{i}. ANCLA x{n} — la rotura no probaria nada: {desc}")
        continue
    p.write_text(bak.replace(viejo, nuevo, 1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(AQUI / "verif_v459.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=r"C:\Users\diego\P1\survey_app", env=ENV)
    p.write_text(bak, encoding="utf-8")
    ok = r.returncode != 0
    cazadas += ok
    print(f"{i}. {'CAZADA ' if ok else 'SE ESCAPA'} — {desc}")
    if not ok:
        print("     " + " | ".join(l.strip() for l in r.stdout.splitlines()
                                   if "FALLO" in l) or "     (ningun FALLO)")

print(f"\n{cazadas}/{len(ROTURAS)} roturas cazadas")
sys.exit(0 if cazadas == len(ROTURAS) else 1)
