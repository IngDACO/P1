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
- **Survey + optimizador**: lee el plano (PDF), calcula límites y la mejor posición del elevador.
- **Plomadas** e **informe de corte de rieles** automáticos.
- **Informes con IA**: uno para el cliente (descargable) y uno técnico interno (auto por correo).
- **Gestión de proyectos**: cronograma (Gantt) + curva S; el campo actualiza avance; **curva S real vs
  planificada** + **proyección de días de adelanto/retraso** (earned value).
- **Documentos por proyecto** en Google Drive (plano, informes, fotos…).
- **Fichaje** (clock in/out) con horas atadas al proyecto.
- **Multi-empresa**: cada cliente/empresa es un grupo AISLADO.

## Roles (base del modelo de licencias)
- **Propietario**: dueño de la plataforma (COPEX). Ve todo, crea grupos (empresas) y administradores.
- **Administrador**: gestiona SU empresa/grupo (crea proyectos, asigna usuarios de campo, ve informes).
- **Campo**: técnico en obra. Actualiza avance de actividades, sube fotos, consulta documentos.

## Modelo de acceso ya implementado
- **Una sola sesión activa por cuenta** ("primero gana") → **no se pueden compartir cuentas** →
  base técnica para **vender licencias por usuario/tipo**.

## Estado actual
Desplegado en Streamlit Cloud (v75), funcional. App privada con login propio. Backend en Google
Sheets + Drive (gratis). Limitaciones actuales: cuota de Google Sheets (ok para pocos usuarios
concurrentes), sin login persistente (cookies), sin límite de "asientos" por empresa todavía.

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
3. **Fase 3:** contabilidad — **integrar con Xero/MYOB** (estándar en Australia) en vez de construir
   módulo propio (alta complejidad regulatoria/fiscal, mejor no asumirla).
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
