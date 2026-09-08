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

> Puesto al día por el chat técnico el **08/09/2026**. Lo que había aquí era de **v75**.

Desplegado en Streamlit Cloud, funcional y en uso con datos reales. **v481**: 90 módulos, ~39.000
líneas, 29 hojas de datos y **119 guardianes automáticos en verde** que se corren enteros antes de
cada despliegue. Backend en Google Sheets + Drive.

**Lo que ya está resuelto** (y en v75 no lo estaba): login persistente por cookie, sesión única por
cuenta, aislamiento entre empresas con cerrojo en el código (no solo en la interfaz), un libro de
Google por cliente, zona horaria por grupo y la app entera en inglés.

**Lo que NO existe todavía, dicho sin adornos** — es la lista que decide si se puede vender:

| | |
|---|---|
| **Planes y asientos** | La hoja `Groups` no tiene ni una columna de plan o de tope. El modelo de precios por asiento **no se puede hacer cumplir hoy** |
| **Cobro** | No hay pasarela ni estado de suscripción |
| **Contabilidad** | Cero integración con Xero/MYOB. Cada factura se teclearía dos veces |
| **Nómina** | Retención y *superannuation* son porcentajes editables: **no hay STP ni interpretación de awards**. Como costeo de mano de obra es sólido; como nómina certificada, no se puede vender |
| **Sin señal** | No funciona offline, y el campo trabaja en fosos y sótanos |
| **Cobro de obra** | Sin variaciones, sin *progress claims* y sin retenciones (el marco de *Security of Payment*) |
| **Portal del cliente** | El constructor o la administración del edificio no puede ver nada |
| **Mantenimiento/AMC** | No existe, y **es deliberado**: es un mercado adyacente bien atendido |

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
   > ⏭ **Es lo siguiente, y la decisión sigue siendo la correcta.** Cero líneas de Xero/MYOB en el
   > repositorio a día de hoy. Antes va lo que permite COBRAR (planes, asientos y alta de cliente),
   > que hoy no existe.
4. **Fase 4 (requiere escala):** modelos predictivos de proyección de instalación con la data histórica
   acumulada — no vender esto antes de tener volumen real de proyectos. Posible feature premium futuro:
   benchmarking entre clientes (con anonimización, cuidando privacidad de datos).

### 6. Pendiente para el chat técnico
- **Límites técnicos de los tramos de asientos** (cómo se implementan los planes/tramos de volumen y
  el enforcement de licencias) → se define en el chat técnico (CLAUDE.md) cuando se lleve esto a código.

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

*Última puesta al día del estado de hecho: 08/09/2026 (v481-v482).*
