# COPEX Elevator Survey Analyzer — Brief de negocio

> Documento para el chat ESTRATÉGICO. El chat TÉCNICO mantiene CLAUDE.md (detalle de implementación).

## Qué es
Plataforma web (Streamlit) para empresas que **instalan elevadores Schindler**. Digitaliza y
automatiza el trabajo de campo y de oficina de un survey de instalación.

## Problema que resuelve
Hoy el survey, el cálculo de posicionamiento, las plomadas, los cortes de riel y los informes se
hacen a mano / en Excel, con errores y tiempo perdido. La app lo automatiza a partir del **PDF del
plano**, y además ordena la **gestión del proyecto** (cronograma, avance, documentos, horas).

## Funciones clave (ya construidas y desplegadas)

> Puesto al día por el chat técnico el **08/09/2026 (v481)**. La lista anterior era de
> v75 y se había quedado corta en más de la mitad.

**Técnico de obra (el diferenciador)**
- **Survey + optimizador**: lee el plano (PDF), calcula límites y la mejor posición del elevador.
- **Cinco herramientas técnicas**: Survey · Plomadas · Corte de rieles · Corte de buffers · Belting,
  todas con diagramas a escala, PDF propio y guardado en el proyecto.
- **El plano se lee UNA vez** al crear la obra y alimenta a las cinco.
- **Informes con IA**: uno para el cliente (descargable) y uno técnico interno (auto por correo).

**Gestión de la obra**
- Cronograma (Gantt) + curva S real vs planificada + proyección de adelanto/retraso (earned value).
- **Cartera** de proyectos con salud, retraso, alarmas y presupuesto; agrupaciones (un edificio con
  varios elevadores) con fecha de entrega del conjunto.
- **Planificación de cuadrilla**: tablero semanal editable en sitio, vista por día con horarios,
  disponibilidad, cobertura, choques de turno y **plan vs real** contra lo fichado.
- **Ruta del día**: las obras en el mapa, ordenadas para ir a terreno, con navegación.
- **Localizaciones internas** (oficina, almacén, taller): se fichan y se les cargan gastos, pero
  **nunca** se facturan — su costo es estructura.

**Seguridad y personal**
- **Pre-Start diario** digitalizado, con **firma dibujada** por asistente, PDF archivado y alarma
  automática si hay *near miss* o un control en NO. Quien llega después también firma.
- **Credenciales/tickets** por persona con vencimiento, documento y avisos automáticos.
- **Ausencias**: el equipo pide vacaciones o día libre y avisa de bajas; al aprobar se escribe solo
  en el planificador y se paga en la nómina.
- **Fichaje de dos relojes** (jornada + proyecto) con corrección de olvidos revisada por el admin.

**Dinero**
- **Cotizaciones** desde un catálogo propio: se escribe la **ganancia** y el margen sale solo;
  aceptar una cotización **crea la obra** con su presupuesto y su precio pactado.
- **Facturas** con impuesto, cobros parciales y PDF; **nóminas** con colilla en PDF.
- **Costos por obra**: compras con recibo, mano de obra, presupuesto, órdenes de compra (dinero
  comprometido) y curva de gasto.
- **P&L del grupo** con comparación contra el periodo anterior, rentabilidad por obra y
  **conciliación de mano de obra** (lo que pagas vs lo que cargas a las obras).
- **Rastro de cambios** de todo lo que mueve dinero: quién tocó el margen, la tarifa o las fechas.

**Otros**
- **Inventario** de activos con etiqueta QR, movimientos, depreciación y alertas.
- **Contactos/CRM** de clientes, enlazado a obras, cotizaciones y facturas.
- **Biblioteca técnica** de fotos, manuales y fichas, con buscador y taxonomía marca/modelo/sección.
- **Asistente IA** por rol, con banco de manuales indexado.
- **Multi-empresa**: cada cliente es un grupo AISLADO, y desde v359 puede tener **su propio libro
  de Google**. La demo ya vive en uno aparte.
- **Interfaz en inglés** (idioma base) y móvil medido a 375 px para la cuenta de campo.

## Roles (base del modelo de licencias)
- **Propietario**: dueño de la plataforma (COPEX). Ve todo, crea grupos (empresas) y administradores.
- **Administrador**: gestiona SU empresa/grupo (crea proyectos, asigna usuarios de campo, ve informes).
- **Campo**: técnico en obra. Actualiza avance de actividades, sube fotos, consulta documentos.

## Modelo de acceso ya implementado
- **Una sola sesión activa por cuenta** ("primero gana") → **no se pueden compartir cuentas** →
  base técnica para **vender licencias por usuario/tipo**.

## Estado actual

> Puesto al día por el chat técnico el **21/09/2026**. Lo que había aquí era de **v484**; antes de
> eso había estado en **v75**. Van dos veces que este documento se queda atrás, así que la pregunta
> ya no es «¿se actualizó?» sino si la regla de actualizarlo a mano es realista.

Desplegado en Streamlit Cloud, funcional y en uso con datos reales. **v511**: 104 módulos, ~45.110
líneas, 30 hojas de datos y **144 guardianes automáticos en verde** que se corren enteros antes de
cada despliegue. Backend en Google Sheets + Drive.

✅ **La cadena del dinero está recorrida de punta a punta con datos reales (v511, 21/09/2026)**:
catálogo → cotización → obra → avance → reclamación → PDF → variación → retención → liberación, más
la propuesta desde el plano y el expediente de entrega. Hasta aquí cada módulo estaba verificado por
separado pero la cadena entera nunca se había probado, porque el catálogo del cliente de prueba
estaba vacío. ⚠️ Destapó un fallo que ningún test podía encontrar: al agotar la cuota de Google, la
app culpaba a la configuración («*Google Sheets is not configured*») de un problema pasajero.

⚠️ **La suite y el script de despliegue viven ahora DENTRO del repo** (`guardianes/`,
`backup_survey.ps1`, 20/09/2026). Antes estaban en una carpeta temporal y en el home: se arregló un
fallo del script y ese arreglo no dejaba rastro en ningún sitio.

**Lo que ya está resuelto** (y en v75 no lo estaba): login persistente por cookie, sesión única por
cuenta, aislamiento entre empresas con cerrojo en el código (no solo en la interfaz), un libro de
Google por cliente, zona horaria por grupo y la app entera en inglés.

**Lo que NO existe todavía, dicho sin adornos** — es la lista que decide si se puede vender:

| | |
|---|---|
| **Planes y asientos** | La hoja `Groups` no tiene ni una columna de plan o de tope. El modelo de precios por asiento **no se puede hacer cumplir hoy** |
| **Cobro** | No hay pasarela ni estado de suscripción |
| ~~**Identidad fiscal**~~ | ✅ **CERRADO en v483**: hasta entonces el PDF decía «TAX INVOICE» **sin ABN ni razón social**, o sea que los clientes emitían documentos incompletos ante la ATO. Ya se configuran por empresa, junto al plazo de pago |
| **Contabilidad** | ⚠️ **Parcial desde v483 (08/09/2026)**: hay **exportación a CSV** para Xero y MYOB (facturas y gastos, con el proyecto como categoría de seguimiento). **Desde v488 (15/09/2026) las facturas van a Xero por API**, y desde v495-v496 **los cobros vuelven de Xero a COPEX**, probado EN PRODUCCIÓN con un pago parcial. Falta: llevar por API los **gastos** y el **parte de horas**; MYOB sigue solo por CSV |
| **Nómina** | ⚠️ Sigue sin **STP ni interpretación de awards**, así que como nómina certificada no se puede vender. Lo que v484 añade es el puente: **parte de horas exportable** (jornada + ausencias pagadas, persona × día) para que lo procese un proveedor certificado. ⚠️ Y ese trabajo **no se tira decida lo que se decida** — conectar con un proveedor y renombrar el módulo a «costeo de mano de obra» necesitan los dos lo mismo primero |
| **Sin señal** | No funciona offline, y el campo trabaja en fosos y sótanos. ⚠️ Tras el estudio del 20/09/2026 este es **el hueco que define la arquitectura**: es el único de la lista que no se resuelve añadiendo una pantalla, porque Streamlit ejecuta en el servidor y una app que no arranca sin red no se arregla con un caché. Decidirlo (¿app nativa de captura? ¿solo pre-start y avance?) es una decisión de producto, no una tarea |
| ~~**Cobro de obra**~~ | ✅ **CERRADO en v507-v508 (20/09/2026)**: variaciones, *progress claims* y retención. `valor = contrato + variaciones aprobadas`; `bruto = valor × avance − lo ya reclamado`; `neto = bruto − retención`. Una reclamación **congela** sus números y una variación *propuesta* no es dinero. **Completado en v510 (21/09/2026)**: el **PDF que se le manda al cliente** —con las variaciones aprobadas detalladas una a una— y la **liberación de la retención**, parcial, porque en AU va en dos mitades (*practical completion* y fin del periodo de defectos). ⚠️ El documento **no invoca ninguna ley**: el texto de *Security of Payment* cambia por estado y declararlo mal tiene efectos legales, así que lo pone quien sepa, en la nota |
| **Portal del cliente** | El constructor o la administración del edificio no puede ver nada |
| **Mantenimiento/AMC** | No existe, y **es deliberado**: es un mercado adyacente bien atendido |

**Lo construido entre v485 y v509** (15-20/09/2026), que es lo que mueve el argumento de venta:

- **Gestión de instalación, los cinco huecos cerrados** (v499-v505): el plan encadena actividades con
  **predecesoras y ruta crítica**; la fecha de fin sale de la **cadena** y no de una regla de tres
  (una obra con el 50% hecho y la actividad que bloquea sin empezar salía «en plazo» y son **+10 d**);
  hay **línea base** congelada para defender por qué se retrasó una entrega; cada actividad tiene
  **responsable**; y una **orden de compra bloquea** la actividad que espera ese material. Juntos
  responden qué va tarde, cuánto, contra qué plan, de quién es y por qué.
- **Expediente de entrega AS1735 / NSW DoE** (v506): trece ítems del estándar REAL de *practical
  completion*, cinco evidenciados con lo que la app ya guardaba y ocho de terceros que ⚠️ **nunca
  pasan por cálculo**. No certifica nada, y lo dice. Lo difícil de copiar no es juntar PDFs: es
  **cruzar** el registro técnico con el de personas y fechas.
- **Cotizar leyendo el plano** (v509): del PDF salen paradas, modelo y riel, y el catálogo dice qué
  ítem depende de cuál. ⚠️ Si el plano no lo dice, la línea entra en **cero y marcada** — nunca
  omitida, porque sub-cotizar en silencio se descubre al facturar, cuando ya se firmó.

⚠️ **Lo que bloquea a tres módulos a la vez, y no es código:** el catálogo de la empresa de prueba
está **vacío**. Sin artículos con su costo no hay cotización, ni propuesta desde el plano, ni base de
contrato para las reclamaciones. Es trabajo de datos del cliente, no de desarrollo, y conviene pedirlo
en la primera conversación de cada piloto.

**La cuota de Google Sheets ya no es el cuello de botella que se creía.** Desde v339 todas las hojas
de un libro se traen en **una sola llamada** cacheada y compartida; medido, el consumo sostenido está
muy por debajo del techo. Desde v482 la app **mide su propio consumo** y lo enseña en el panel del
propietario, así que la decisión de cambiar de base de datos se tomará con números y no por intuición.

## Decisiones estratégicas (actualizado 2026-07-13)

### 1. Modelo de pago
Suscripción mensual **por asiento**, con **dos tipos de licencia independientes** (admin/campo no van
atados en bloques fijos — cada uno tiene su propia curva de volumen):

**Asiento Admin**
| Tramo | Cantidad | Precio/mes |
|---|---|---|
| 1 | 1–2 | US$200 |
| 2 | 3–4 | US$170 (−15%) |
| 3 | 5+ | US$140 (−30%, tope de descuento) |

**Asiento Campo**
| Tramo | Cantidad | Precio/mes |
|---|---|---|
| 1 | 1–10 | US$50 |
| 2 | 11–20 | US$42.5 (−15%) |
| 3 | 21+ | US$35 (−30%, tope de descuento) |

- Moneda de referencia: **AUD** (mercado de arranque es Australia) — convertir cuando se defina el
  precio final de lista (aprox. Admin AUD 300/255/210, Campo AUD 75/64/52, sujeto a validación).
- **Mensaje de venta del asiento campo** (no vender como "app de fichaje cara"): reemplaza
  simultáneamente 3 cosas que hoy están dispersas o se pagan aparte — control de horas/asistencia,
  gestión de fotos/documentos por proyecto, y acceso técnico en terreno (plomadas/cortes/avance).
- **⚠️ Estos números son una hipótesis de valor, NO validados con clientes reales todavía.** Antes de
  publicarlos, probar en las conversaciones de los primeros pilotos (ver punto 4).

**⚠️ Lo que encontró el estudio del 20/09/2026 (brecha 3): el problema está en el asiento de CAMPO,
no en el de admin.** Está **1,5× a 2,5× por encima del mercado generalista**. Un contratista del ICP
—2 admin y 20 técnicos— pagaría del orden de **A$1.500/mes solo en asientos de campo**, antes del
primer admin; **AroFlo son ~A$960** por esos mismos 20, y en ServiceM8 esa cantidad de técnicos
directamente no entra en el precio. El asiento de admin, en cambio, se defiende solo: es donde está
el motor técnico que nadie más tiene.

- Salida recomendada: **campo incluido por tramos** — el asiento de admin trae N técnicos y se cobra
  el exceso. Alinea el precio con el TAMAÑO de la empresa en vez de castigar la adopción, que es lo
  que hace hoy cobrar por cada técnico que entra.
- Lo accionable ya, sin tocar un número: **separar el discurso de precio** entre los dos asientos
  antes de las conversaciones de piloto. Presentarlos juntos invita a comparar el total con una app
  de fichaje.
- ⚠️ **Y el límite de ese hallazgo:** los precios de la competencia salen de reseñas y comparadores,
  **no de propuestas reales** (Simpro ni publica tarifas), y **no se entrevistó a ningún cliente**.
  Compara precios de lista, no disposición a pagar.

### 2. Cliente ideal (ICP)
- **Perfil objetivo:** contratista con **2+ admin y 10+ técnicos de campo**, varios proyectos
  simultáneos — el que sufre de verdad la coordinación dispersa en Excel entre oficina y terreno.
- **No se cierra la puerta a instaladores chicos**: existe un plan de entrada más liviano (1 admin +
  3-4 campo) para bajar la fricción inicial; el crecimiento hacia el ICP ocurre naturalmente vía los
  tramos de volumen, no se fuerza un mínimo alto de entrada.
- Comprador típico: dueño/gerente de operaciones o de ingeniería.
- Disparador de compra: la empresa está creciendo más rápido de lo que puede coordinar a mano, o tuvo
  un error costoso reciente (corte mal hecho, atraso no detectado a tiempo).

### 3. Mercado y canal de arranque
- **Geografía inicial: Sydney, Australia** — decisión basada en que hay **red de contactos propia ya
  establecida** en el rubro ahí (no arranca de cero).
- **Canal: contacto directo / referidos** de esa red — no ferias, no canal Schindler, no marketing
  digital por ahora (bajo volumen de proveedores del rubro + alta confianza necesaria = venta referida
  convierte mejor que fría).
- **Sin filtrar pilotos por marca de elevador** — el mensaje de valor (ver punto 5) es el mismo para
  cualquier marca; Schindler solo tiene menos fricción operativa hoy por la auto-extracción del PDF,
  pero eso no es criterio de selección de clientes.
- **Oferta piloto propuesta:** primeros 2-3 clientes de la red con descuento fuerte (ej. 50%) o primer
  mes gratis, a cambio de feedback estructurado + autorización para usarlos como caso de referencia.
  Meta simple: ~5-10 conversaciones → 2-3 pilotos activos.

### 4. Diferenciación / competencia
**El diferenciador NO es el extractor de PDF de Schindler** (eso es solo una ventaja operativa — menos
carga manual de datos hoy, nada más). El diferenciador real es la **especialización técnica de
instalación de elevadores + la integración entre el cálculo técnico de terreno y la gestión del
proyecto** en una sola herramienta.

Investigación de mercado (2026-07-13) confirma un hueco real:
- **Categoría 1 — CRMs de servicio/mantenimiento** (FIELDBOSS, Lift Keeper, ElevatorPlus, Klipboard,
  eFLEXS, Field Force Tracker, BuildOps, Contractor+): pensados para negocios de mantenimiento/AMC;
  algunos tienen Gantt de avance de instalación, pero **ninguno hace cálculo técnico** (posicionamiento,
  plomada, corte de riel).
- **Categoría 2 — software de diseño/cálculo técnico** (CompuLift, FineLIFT/4M, Elevatorportal/Liwetec):
  hacen cálculos de ingeniería pero son herramientas **pre-fabricación para fabricantes/diseñadores**,
  sin conexión a gestión de proyecto/terreno.
- Nadie combina ambas cosas → hueco de mercado confirmado, no solo percibido.
- **Riesgo:** el módulo de gestión de proyecto solo (Gantt/curva S) sí compite de frente con jugadores
  grandes y financiados (FIELDBOSS, BuildOps) — el mensaje de venta debe anclar siempre en el motor
  técnico + la integración, nunca en el Gantt aislado. Y si el modelo se valida, Schindler u otro grande
  podría copiarlo — la ventaja real es velocidad para conseguir clientes y datos antes que ellos.

**Segundo estudio (20/09/2026) — el hueco sigue siendo real, y aparecieron tres brechas.** Estudio
completo en el documento [Estudio de mercado COPEX · septiembre
2026](https://claude.ai/code/artifact/06d37e72-4d84-4b3a-9db3-e6dc5c2c3083). Lo que cambió respecto
de julio:

1. **Sin señal** — la que ordena a las demás, porque **condiciona la arquitectura**: lo que se
   construya para campo antes de decidirlo puede haber que rehacerlo. Y es el argumento con el que se
   **pierde una demo de campo**. ⚠️ FIELDBOSS lo vende con nuestro mismo vocabulario y **no es
   folleto**: corre sobre Dynamics 365 con motor Resco, verificado en Microsoft Marketplace. El
   offline en campo es además **estándar de categoría** (ServiceTitan, Fieldwire, crewOS,
   Synchroteam), y los comparadores usan «sótanos sin señal» como el caso de manual — justo el
   nuestro.
2. **Cobro de obra** — ✅ **cerrada el mismo día (v507-v508)**. Se pierde más tarde que el offline,
   cuando el contratista ya está dentro y descubre que su reclamación mensual la sigue armando en
   Excel: duele después, pero duele.
3. **El precio** — ver el punto 1 de este documento: el asiento de campo, no el de admin.

**Y tres cosas que hoy no puede hacer NADIE del sector, ya construidas** (20/09/2026): el
**expediente de entrega** cruzando el registro técnico con el de personas y fechas (v506), el **cobro
de obra** ligado al avance real de las actividades (v507-v508) y **cotizar leyendo el plano** (v509).
Las tres nacen del mismo activo que nadie más tiene: la app ya extrae el PDF técnico y ya sabe quién
trabajó, cuándo y en qué. Son el argumento de venta, no funciones sueltas.

⚠️ **Lo que el estudio NO puede decir:** si un contratista de Sydney pagaría A$300 por un asiento de
admin, ni cuánto pesa de verdad el offline en una decisión de compra — o si es una objeción que se
resuelve con «el móvil funciona fuera del foso». Eso solo sale de las conversaciones de piloto.

### 5. Roadmap comercial de largo plazo (north star, no para los próximos 12 meses)
Visión: ir invadiendo más actividades del contratista para aumentar dependencia del servicio
(volverse el sistema de registro central) y usar la data acumulada para modelos cada vez más precisos
de proyección de instalación. Secuencia recomendada (cada paso aprovecha data que el módulo anterior
ya captura, no se construye todo en paralelo):

1. **Fase 1 (0-12 meses, foco actual):** consolidar pilotos técnicos + gestión de proyecto, generar
   data limpia y casos de referencia. Sin esto, ningún paso siguiente tiene base.
2. **Fase 2:** nómina/payroll (ya se capturan horas por proyecto vía fichaje — extensión natural) +
   gestión legal/compliance de documentos (extensión natural de Documentos/Drive) + costeo por proyecto
   (extensión natural de curva S/EVM).
   > ✅ **HECHA** (chat técnico, 08/09/2026). Las tres están construidas y desplegadas: nóminas con
   > colilla en PDF, credenciales con vencimiento y avisos, y costeo por obra con P&L y rentabilidad.
   > ⚠️ Con un matiz que importa para la venta: **la nómina no es certificada** — no envía STP ni
   > interpreta *awards*. Hay que decidir si se conecta a un proveedor o se posiciona como costeo de
   > mano de obra.
3. **Fase 3:** contabilidad — **integrar con Xero/MYOB** (estándar en Australia) en vez de construir
   módulo propio (alta complejidad regulatoria/fiscal, mejor no asumirla).
   > 🟡 **EMPEZADA (v483, 08/09/2026), y la decisión sigue siendo la correcta.** Están hechas la
   > **identidad fiscal** (ABN y razón social en la factura) y la **exportación a CSV** para los
   > dos, que cubre la mayor parte del dolor. Falta la **API**, y ahí la elección está tomada con
   > datos: **Xero** — ~60 % del mercado AU contra ~20-25 % de MYOB, y ⚠️ el archivo de MYOB
   > AccountRight puede vivir **en el escritorio del cliente**, donde su API solo responde en la
   > red local: una app en la nube no lo alcanza. Antes va lo que permite COBRAR (planes, asientos
   > y alta de cliente), que sigue sin existir.
   > 🟡 **2.2-A hecha (v484)**: hay parte de horas exportable. ⚠️ Y se descubrió algo que cambia el plan: **Xero Payroll AU no importa partes por CSV** —su propia petición de esa función sigue abierta—, así que conectar las horas con Xero exige la **API**, el mismo OAuth que las facturas. Se hacen de una.
   > ⚠️ Y la pregunta abierta que no decide el código: **nómina, ¿conectar o renombrar?** Sigue sin
   > STP ni interpretación de *awards*, así que como nómina no se puede vender. Las dos salidas
   > necesitan primero lo mismo —exportar el **parte de horas**, no la colilla—, así que ese trabajo
   > no se tira decida lo que decida.
4. **Fase 4 (requiere escala):** modelos predictivos de proyección de instalación con la data histórica
   acumulada — no vender esto antes de tener volumen real de proyectos. Posible feature premium futuro:
   benchmarking entre clientes (con anonimización, cuidando privacidad de datos).
   > ⏸ **APLAZADA a propósito (20/09/2026).** Se especificó el «escalón agentico» —que la app no solo
   > muestre el retraso sino que **recomiende qué hacer**: a quién mover, qué actividad adelantar, qué
   > pedir primero— y sería **reglas deterministas sobre los datos, no un modelo entrenado**. Se
   > frenó por una razón concreta, no por tiempo: **no hay obras terminadas sobre las que recomendar**.
   > Una recomendación sacada de un histórico vacío no es una recomendación, es una opinión con
   > interfaz. Se retoma cuando los pilotos hayan cerrado obras reales.

### 6. Pendiente para el chat técnico
- **Límites técnicos de los tramos de asientos** (cómo se implementan los planes/tramos de volumen y
  el enforcement de licencias) → se define en el chat técnico (CLAUDE.md) cuando se lleve esto a código.
- ⚠️ **Decidir el offline, y decidirlo PRIMERO** (brecha 1 del estudio del 20/09/2026). No es una
  tarea que se pueda encargar: es una decisión de producto con consecuencias de arquitectura —
  Streamlit ejecuta en el servidor, así que «que funcione sin red» no se arregla con un caché. Las
  opciones a evaluar en el chat técnico: app nativa de captura solo para lo de terreno (pre-start,
  avance, fotos) que sincroniza al recuperar señal, o asumir que el offline no es requisito y decirlo
  en la venta. Lo que no es opción es seguir construyendo pantallas de campo sin haberlo decidido.
- ~~**Cerrar el flanco del cobro de obra**~~ → ✅ **hecho en v510 (21/09/2026)**.

## Cómo trabajan los dos chats
- **Estratégico** (este brief): negocio, precios, mercado, roadmap comercial.
- **Técnico** (CLAUDE.md): implementación. Cuando estrategia decida algo que requiera código
  (ej. planes/asientos, pasarela de pago), se lleva al chat técnico para construirlo.

---

## Mantenimiento de este documento

⚠️ Este brief llegó a estar **400 versiones desfasado** (decía «v75» en septiembre de 2026, con la
app en v481) y colocaba en «fase futura» tres módulos que llevaban meses desplegados. Un documento
de negocio que describe un producto que ya no existe hace tomar decisiones comerciales sobre una
foto vieja.

Cuando el chat técnico cierre algo que este documento da por pendiente, lo actualiza aquí **en el
mismo lote**, con la fecha. Y cuando alguien pregunte «¿qué falta?», la respuesta se audita contra
el repositorio, no contra la memoria de este fichero.

⚠️ **Y volvió a pasar**: entre el 14 y el 20/09/2026 se cerraron seis huecos de gestión de
instalación, el cobro de obra entero y dos oportunidades del estudio, y este documento seguía
diciendo v484. La regla de «actualizarlo en el mismo lote» **no se cumplió** — ni esta vez ni la
anterior. La conclusión honesta es que una regla que depende de que alguien se acuerde no es un
mecanismo.

✅ **Desde el 21/09/2026 hay un guardián: `guardianes/check_negocio_al_dia.py`.** Compara la
versión que declara la línea de abajo con `survey_app/VERSION` y **se pone rojo** cuando la
distancia pasa del número de versiones que `CLAUDE.md` mantiene a la vista (hoy 15, derivado del
propio fichero y no fijado a mano). Corre dentro de la suite, así que se ejecuta antes de cada
despliegue y no se puede ignorar.

⚠️ **Su límite, escrito para que el verde no tranquilice:** mide una FORMA — que el número
coincida—, no el fondo. Un verde significa «la versión está al día», **no** «el brief es cierto»:
no detecta que una fila de «lo que NO existe todavía» siga diciendo que falta algo construido ayer.
Esa tabla sigue siendo responsabilidad de quien cierra la versión. El guardián caza el desfase de
25 o de 400 versiones, que es el fallo que de verdad ocurrió dos veces.

⚠️ **Y por eso la línea de abajo es carga estructural, no decoración**: el guardián la lee. Si se
borra o se le cambia el formato, el resultado es ROJO —no verde—, a propósito: sin ella no se puede
saber a qué versión corresponde este documento.

*Última puesta al día del estado de hecho: 21/09/2026 (v485-v511).*
