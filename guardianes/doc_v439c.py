"""Trampa nº28 en el bloque de TRAMPAS DE VERIFICACIÓN (es la tercera reincidencia)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DOC = Path(r"C:\Users\diego\P1\CLAUDE.md")
s = DOC.read_text(encoding="utf-8")

ANCLA = ("27. ⚠️ **Un barrido del FUENTE no mide lo que se ve.**")
assert s.count(ANCLA) == 1, f"ancla: {s.count(ANCLA)}"

NUEVO = """28. ⚠️ **Un detector por IDIOMA no sirve para decir «ya no queda español».** El
    barrido de i18n busca acentos y palabras funcionales, así que **«Fichar», «Firma»,
    «Iniciales», «Pendientes», «Sitios», «Registrados», «Planificado» o «Mis ausencias»
    son invisibles para él**: no llevan ni acento ni artículo. Con ese detector di F2
    por terminada y quedaban **47 etiquetas**; el mismo agujero dejó pasar una etiqueta
    de plomada en v438 y una rotura del guardián en v439 — **tres veces**. → Para
    afirmar «no queda nada sin traducir» hay que medir por **POSICIÓN**, no por idioma:
    todo literal que llega a una función de display y NO está envuelto en `t()`, y
    revisarlo a mano para separar ETIQUETA de DATO (una clave de dict y un texto se ven
    igual en el AST). Y para los chequeos, **afirmaciones POSITIVAS**: que el inglés
    esperado ESTÉ, en vez de que el español no esté.
29. ⚠️ **«Compila e importa» no verifica NADA de una traducción.** Los dos
    `UnboundLocalError` de v439 —uno dejaba «Mis ausencias» sin abrir— y las 47
    etiquetas convivieron con `compileall` en verde y los cuatro módulos importando sin
    queja. **Importar no ejecuta** (v378). Lo que las encontró fue LLAMAR a las
    funciones con las dependencias de Sheets sustituidas y mirar lo que pintan. Si al
    traducir aparece una llamada `t(...)` en una función donde `t` ya era una variable,
    Python la marca local en el ámbito ENTERO y revienta — y nada de lo anterior lo ve.

"""
s = s.replace(ANCLA, NUEVO + ANCLA, 1)
DOC.write_text(s, encoding="utf-8")
print(f"OK — CLAUDE.md {len(s.splitlines())} líneas")
