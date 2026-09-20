"""Quita los BACKSPACE literales (0x08) que el heredoc metió donde iba `\\b`.

⚠️ Es la trampa de v436, repetida: escribir `\\b` dentro de un heredoc de bash lo
convierte en el carácter 0x08, así que el regex queda pidiendo un backspace y no casa
NUNCA — sin dar ningún error. Aquí dejó pasar una etiqueta de plomada en español.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(__file__).with_name("verif_v438.py")
s = p.read_text(encoding="utf-8")
n = s.count("\x08")
if n:
    s = s.replace("\x08", chr(92) + "b")
    p.write_text(s, encoding="utf-8")
print(f"{n} backspaces sustituidos por \\b de regex")
