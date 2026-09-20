"""F3-N · Los módulos pequeños: ubicación, plano por proyecto, guardar cálculo, app.py.

⚠️ `?start=` y `](https://t.me/` NO son texto: son trozos del enlace de vinculación de
Telegram y se conservan igual. `t.me/` tampoco se toca.
"""
TRAD = {
    # ── location_ui ────────────────────────────────────────────────
    ":material/place: Escribe la dirección y pulsa **Buscar**: la app la ubica sola. Si "
    "hay varias coincidencias, elige la correcta. (Opcional: clic en el mapa para "
    "afinar.)":
        ":material/place: Type the address and press **Search**: the app locates it on "
        "its own. If there are several matches, choose the right one. (Optional: click "
        "the map to fine-tune.)",
    "🎯 Precisión: **Google** (número de casa exacto).":
        "🎯 Accuracy: **Google** (exact street number).",
    "≈ Precisión aproximada (OpenStreetMap). Falta la API key de Google para ubicar el "
    "número exacto.":
        "≈ Approximate accuracy (OpenStreetMap). The Google API key is missing, so the "
        "exact street number cannot be located.",
    "Buscar dirección": "Search address",
    ":material/search: Buscar dirección…": ":material/search: Search address…",
    "Buscar": "Search",
    "No encontré esa dirección. Añade ciudad/estado/país, o haz clic en el mapa.":
        "I could not find that address. Add city/state/country, or click on the map.",
    ":material/place: Resultado (": ":material/place: Result (",
    ") — confírmalo o elige otro:": ") — confirm it or choose another:",
    "Mapa no disponible; ingresa las coordenadas a mano (las ves en Google Maps: clic "
    "derecho → coordenadas).":
        "The map is not available; enter the coordinates by hand (you can see them in "
        "Google Maps: right-click → coordinates).",
    "Lat": "Lat",
    "Lng": "Lng",
    "Coordenadas fijadas: **": "Coordinates set: **",
    "_Sin ubicación fijada aún._": "_No location set yet._",

    # ── plan_ui (el plano del proyecto) ────────────────────────────
    ":material/info: **Ficha primero en :material/schedule: Fichaje** eligiendo el "
    "proyecto en el que trabajas. Así la herramienta usa los datos de su plano y no "
    "tendrás que cargar el PDF.":
        ":material/info: **Clock in first at :material/schedule: Time clock**, choosing "
        "the project you are working on. That way the tool uses its drawing data and you "
        "will not have to upload the PDF.",
    "Proyecto": "Project",
    "** no tiene los datos del plano cargados. Cárgalos en el proyecto (:material/build: "
    "Mi grupo → abrir el proyecto → :material/attach_file: Archivos) o sube el PDF aquí "
    "abajo.":
        "** has no drawing data loaded. Load it on the project (:material/build: My "
        "company → open the project → :material/attach_file: Files) or upload the PDF "
        "below.",

    # ── tool_save_ui (guardar un cálculo) ──────────────────────────
    ":material/lock: Guardar en el proyecto requiere Google Sheets configurado.":
        ":material/lock: Saving to the project needs Google Sheets configured.",
    "No hay proyectos disponibles para asociar este cálculo.":
        "There are no projects available to attach this calculation to.",
    "No se pudo guardar: ": "It could not be saved: ",
    ":material/save: Se guardará en **": ":material/save: It will be saved to **",
    "** — donde fichaste.": "** — where you clocked in.",
    "¿Es de otro proyecto?": "Is it for a different project?",
    "Guardar en el elegido": "Save to the chosen one",
    "Aún no has fichado a un proyecto (:material/schedule: Fichaje). Elige uno:":
        "You have not clocked in to a project yet (:material/schedule: Time clock). "
        "Choose one:",
    "Guardar en el proyecto": "Save to the project",
    ":material/save: Guardar en el proyecto": ":material/save: Save to the project",
    ":material/download: Descargar ": ":material/download: Download ",
    " (PDF)": " (PDF)",

    # ── app.py ─────────────────────────────────────────────────────
    ":material/delete: Limpiar conversación": ":material/delete: Clear the conversation",
    " COPEX": " COPEX",
    ":material/lock: Tu sesión se cerró: esta cuenta se abrió en otro dispositivo (o "
    "expiró por inactividad). Vuelve a iniciar sesión.":
        ":material/lock: Your session was closed: this account was opened on another "
        "device (or it expired through inactivity). Sign in again.",
    "### :material/lock: Falta configurar tu contacto":
        "### :material/lock: Your contact details are missing",
    "Tu cuenta necesita **email y Telegram**. El **email lo carga tu administrador**; el "
    "Telegram lo enlazas tú con el paso de abajo.":
        "Your account needs **email and Telegram**. The **email is entered by your "
        "administrator**; you link the Telegram yourself with the step below.",
    "Tu cuenta necesita un **email**, y lo carga tu administrador. Avísale y vuelve a "
    "entrar — tú no puedes ponerlo desde aquí.":
        "Your account needs an **email**, and your administrator enters it. Let them "
        "know and sign in again — you cannot set it from here.",
    "Solo falta enlazar tu **Telegram**. Es un paso tuyo, aquí abajo.":
        "All that is left is linking your **Telegram**. That is your step, right below.",
    "**Tu paso:** abre el bot y pulsa **Start** → [t.me/":
        "**Your step:** open the bot and press **Start** → [t.me/",
    "Después tu administrador te vincula desde tu ficha.":
        "Your administrator then links you from your record.",
    ":material/sync: Ya está listo — revisar": ":material/sync: It is done — check again",
}
