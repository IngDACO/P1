"""Los `except: pass` que se tragan un apunte de auditoría, con rastro (regla v323).

⚠️ `auditoria.registrar` ya logea sus propios fallos, pero el `except` del CALL-SITE
también atrapa lo que revienta en `auditoria.diff` o en el import — y ahí el apunte
se perdía sin dejar nada. El histórico se quedaría con un hueco inexplicable.

Se toca SOLO el except que sigue a un `auditoria.registrar(...)`, no los otros 120
`except: pass` del repo, que son de lectura/display y ahí el silencio es correcto.
"""
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = pathlib.Path(r"C:\Users\diego\P1\survey_app\core")

PAT = re.compile(
    r"(auditoria\.registrar\((?:[^()]|\([^()]*\))*\)\s*\n)(\s*)except Exception:\n\s*pass\n")

for f in sorted(BASE.glob("*.py")):
    src = f.read_text(encoding="utf-8")
    if "auditoria.registrar" not in src:
        continue
    if "logger" not in src:
        print(f"   ⚠️ {f.name}: NO tiene logger — se salta (sería un NameError escondido)")
        continue

    def _rep(m):
        ind = m.group(2)
        return (m.group(1)
                + f"{ind}except Exception as e:\n"
                + f"{ind}    # Deja RASTRO (regla v323): si falla `diff` o el import, el\n"
                + f"{ind}    # apunte se perdía en silencio y el histórico quedaba con un\n"
                + f"{ind}    # hueco que nadie podía explicar.\n"
                + f"{ind}    logger.warning(\"{f.stem}: no se pudo auditar: %s\", e)\n")

    nuevo, n = PAT.subn(_rep, src)
    if n:
        f.write_text(nuevo, encoding="utf-8")
        print(f"   ✓ {f.name}: {n} except(s) con rastro")
