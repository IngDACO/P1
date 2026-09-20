import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = Path(r"C:\Users\diego\P1\CLAUDE.md")
L = DOC.read_text(encoding="utf-8").splitlines(True)
# 28 y 29 quedaron ANTES del 27; se mueven detras (lineas 1-indexadas 346..364 -> tras 371)
bloque = L[345:364]
assert bloque[0].startswith("28. "), bloque[0][:40]
resto = L[:345] + L[364:]
i = next(k for k, l in enumerate(resto) if l.startswith("27. "))
j = next(k for k in range(i + 1, len(resto)) if resto[k].startswith("**Y la regla de siempre"))
nuevo = resto[:j] + bloque + resto[j:]
DOC.write_text("".join(nuevo), encoding="utf-8")
print("OK", len(nuevo), "lineas")
