# -*- coding: utf-8 -*-
"""Bateria de roturas de v516. ⚠️ Verde de BASE primero: sin ese paso una tanda entera
sale «cazada» sin probar nada (v459). Y NO se lanza en paralelo con la suite, que
modifica los mismos ficheros (v455).

⚠️ Cada rotura lleva su RAZON al lado: si no se puede decir que fallo real imita, la
rotura no vale. Y el CONTROL tiene que ser un cambio DE VERDAD — uno que ponga el mismo
texto a los dos lados no prueba nada y parece cobertura (el fallo de v514).
"""
import io
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SCRW = os.path.dirname(os.path.abspath(__file__))
RAIZ = r"C:\Users\diego\P1\survey_app"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
G = "verif_v516"


def corre(g=G):
    r = subprocess.run([sys.executable, os.path.join(SCRW, g + ".py")],
                       cwd=RAIZ, capture_output=True, env=ENV)
    return r.returncode == 0


ROTURAS = [
    ("la hoja sale del LOTE (leeria vacia PARA SIEMPRE, sin error)",
     "core/hojas.py", '    "DailyLogs",\n', ""),

    ("se lee CON cabeceras (el lector pasaria a CREAR la hoja, v145)",
     "core/daily_log.py", "return hojas.registros(SHEET) or []",
     "return hojas.registros(SHEET, HEADERS) or []"),

    ("la fila se escribe con una columna de MENOS (todo se desplaza, v363)",
     "core/daily_log.py",
     'w.append_row([lid, str(grupo), str(pid), _dia, str(autor), _txt, MANUAL,',
     'w.append_row([lid, str(grupo), _dia, str(autor), _txt, MANUAL,'),

    ("el autor y el texto se cruzan de columna",
     "core/daily_log.py", "_dia, str(autor), _txt, MANUAL,", "_dia, _txt, str(autor), MANUAL,"),

    # ⚠️ Esta ancla MURIO en su primera tarde: decia `%Y-%m-%d %H:%M` y el arreglo del
    # empate le puso segundos, asi que la bateria la contaba como «??» mientras anunciaba
    # «19 de 19». No lo vi yo — lo cazo `check_anclas_roturas`, escrito ese mismo dia
    # para esto. Una bateria no avisa de sus propias anclas muertas: solo las salta.
    # ⚠️ v523 · Y murio OTRA vez, igual que las dos de abajo: la fila lleva ahora
    # `Reviewed`/`ReviewedBy` vacias al final, y el admin le pasa `extra=` a `_linea`. La
    # rotura es la MISMA; cambia solo el texto donde se ancla (lo cazo check_anclas_roturas).
    ("se guarda solo el DIA, sin la hora (dos partes del mismo dia dejan de ordenarse)",
     "core/daily_log.py", '_hoy.strftime("%Y-%m-%d %H:%M:%S"), "", ""]',
     '_hoy.strftime("%Y-%m-%d"), "", ""]'),

    ("un fallo de la hoja se cuenta como EXITO (el texto se perderia al vaciarse la caja)",
     "core/daily_log.py",
     '        logger.warning("daily_log.crear(%s): %s", pid, e)\n'
     '        return False, timeclock.motivo_sin_hoja()',
     '        logger.warning("daily_log.crear(%s): %s", pid, e)\n'
     '        return True, ""'),

    ("el motivo vuelve a ser «no esta configurado» aunque sea la cuota (v511)",
     "core/daily_log.py",
     "        return False, timeclock.motivo_sin_hoja()\n\n    try:\n        _hoy = clock.now(grupo)",
     '        return False, t("Google Sheets is not configured.")\n\n    try:\n        _hoy = clock.now(grupo)'),

    ("un parte VACIO entra en la hoja",
     "core/daily_log.py", 'if not _txt:\n        return False, t("Write what you did before saving.")',
     'if False:\n        return False, t("Write what you did before saving.")'),

    ("el tope de longitud se cae (un documento pegado ensucia el corpus)",
     "core/daily_log.py", "if len(_txt) > MAX_TEXTO:", "if len(_txt) > MAX_TEXTO * 1000:"),

    ("cualquiera puede borrar el parte de OTRO",
     "core/daily_log.py",
     '        if str(r.get("Author", "")) != str(quien):\n'
     '            return False, t("Only the person who wrote it can delete it.")',
     '        if False:\n'
     '            return False, t("Only the person who wrote it can delete it.")'),

    ("se puede borrar el parte de OTRO DIA (reescribir el registro de la obra)",
     "core/daily_log.py", 'if str(r.get("Date", "")) != _hoy:', "if False:"),

    ("borrar la obra deja los partes HUERFANOS (el fallo de v514)",
     "core/projects.py",
     "        from core import daily_log as _DL\n        _DL.borrar_de_obra(pid)",
     "        pass"),

    ("borrar de una obra va de ARRIBA ABAJO y se lleva filas de otra",
     "core/daily_log.py", "for fila in sorted(filas, reverse=True):",
     "for fila in sorted(filas):"),

    ("la lista se ordena por el DIA reportado, no por cuando se escribio",
     "core/daily_log.py",
     'key=lambda r: (str(r.get("Created", "")), str(r.get("ID", ""))),',
     'key=lambda r: str(r.get("Date", "")),'),

    # ⚠️ Las DOS mitades del fallo que encontro la hoja real, cada una por su lado: sin
    # segundos no hay con que distinguir dos partes del mismo minuto, y sin el ID de
    # desempate vuelve a mandar el orden de la hoja (`sorted` es estable). Arreglar una
    # sola dejaba el fallo vivo la mitad de las veces.
    ("`Created` vuelve a guardarse sin SEGUNDOS (dos partes del mismo minuto empatan)",
     "core/daily_log.py", '_hoy.strftime("%Y-%m-%d %H:%M:%S"), "", ""]',
     '_hoy.strftime("%Y-%m-%d %H:%M"), "", ""]'),

    ("se cae el ID de desempate (el mismo segundo vuelve a salir al reves)",
     "core/daily_log.py",
     'key=lambda r: (str(r.get("Created", "")), str(r.get("ID", ""))),',
     'key=lambda r: str(r.get("Created", "")),'),

    ("`dias_cubiertos` cuenta ENTRADAS (haria creer que hay mas corpus del que hay)",
     "core/daily_log.py",
     'return len({str(r.get("Date", "")) for r in partes(pid) if r.get("Date")})',
     "return len(partes(pid))"),

    ("la caja de texto se vacia ANTES de saber si se guardo (se pierde lo escrito)",
     "core/daily_log_ui.py",
     "        ok, msg = DL.crear(pid, grupo, txt, usuario, dia=dia)\n        if ok:",
     "        st.session_state.pop(_k, None)\n"
     "        ok, msg = DL.crear(pid, grupo, txt, usuario, dia=dia)\n        if ok:"),

    ("el admin pasa a poder BORRAR partes ajenos",
     "core/daily_log_ui.py",
     "        _linea(r, False, key_prefix, extra=lambda r=r: _estado_revision(r, pid))",
     "        _linea(r, True, key_prefix, extra=lambda r=r: _estado_revision(r, pid))\n"
     "        DL.borrar(r.get('ID'), 'admin') if False else None"),

    ("el campo pierde su seccion (la pantalla deja de existir)",
     "core/projects_ui.py", '"🏗 Avance", "📝 Parte", "🚨 Avisos"',
     '"🏗 Avance", "🚨 Avisos"'),
]

# ⚠️ El CONTROL tiene que ser un cambio REAL que NO pueda poner nada rojo. En v514 nacio
# vacio —el mismo texto a los dos lados— y paso sin probar nada, que es peor que no
# tenerlo porque parece cobertura.
CONTROL = ("CONTROL: un comentario inocuo no puede poner nada rojo",
           "core/daily_log.py", 'SHEET = "DailyLogs"',
           '# comentario inocuo del control\nSHEET = "DailyLogs"')


def aplica(rel, viejo, nuevo):
    p = os.path.join(RAIZ, rel.replace("/", os.sep))
    bak = io.open(p, encoding="utf-8").read()
    if bak.count(viejo) != 1:
        return None, bak, p, bak.count(viejo)
    io.open(p, "w", encoding="utf-8", newline="").write(bak.replace(viejo, nuevo, 1))
    return True, bak, p, 1


print("0. Verde de base")
if not corre():
    print("   ⚠️ el guardian YA esta rojo: la tanda entera saldria «cazada» sin probar nada")
    sys.exit(1)
print("   verde")

print("")
print("1. Roturas (cada una debe ponerse ROJA)")
cazadas = total = 0
# ⚠️ v519 · Una rotura que NO se puede aplicar pone la bateria en ROJO (ver romper_v519):
# antes desaparecia del recuento y el total anunciaba «N de N» sin haberla probado.
saltadas = []
for desc, rel, viejo, nuevo in ROTURAS:
    _ok, bak, p, n = aplica(rel, viejo, nuevo)
    if _ok is None:
        print("  ??      ancla %s en %s -> %s" % ("ausente" if n == 0 else "x%d" % n, rel, desc))
        saltadas.append(desc)
        continue
    total += 1
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)   # ⚠️ SIEMPRE se restaura
    cazadas += (not verde)
    print("  %s %s" % ("CAZADA  " if not verde else "ESCAPADA", desc))

print("")
print("2. Control (debe seguir VERDE)")
_d, _r, _v, _n = CONTROL
_ok, bak, p, n = aplica(_r, _v, _n)
if _ok is None:
    print("  ??      ancla del control %s" % ("ausente" if n == 0 else "x%d" % n))
else:
    try:
        verde = corre()
    finally:
        io.open(p, "w", encoding="utf-8", newline="").write(bak)
    print("  %s %s" % ("ok     " if verde else "MAL    ", _d))

print("")
print("=== %d de %d roturas cazadas ===" % (cazadas, total))
if saltadas:
    print("⚠️ %d rotura(s) NO se pudieron aplicar: la bateria no las ha probado"
          % len(saltadas))
sys.exit(0 if cazadas == total and not saltadas else 1)
