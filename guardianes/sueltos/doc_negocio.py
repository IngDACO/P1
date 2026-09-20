# -*- coding: utf-8 -*-
"""Pone al día el ESTADO DE HECHO de NEGOCIO.md (v75 → v481).

⚠️ Solo se toca lo factual: qué está construido y qué no. Las decisiones estratégicas
—pricing, ICP, mercado, diferenciación, roadmap comercial— son del chat estratégico y
NO se reescriben. Donde la realidad ya alcanzó a una fase del roadmap, se marca como
hecha y se dice desde cuándo, en vez de borrar lo que decidió el usuario.
"""
import io

P = "C:\\Users\\diego\\P1\\NEGOCIO.md"
s = io.open(P, encoding="utf-8").read()

# ── 1 · Funciones clave ──────────────────────────────────────────────────────
V_FUN = """## Funciones clave (ya construidas y desplegadas)
- **Survey + optimizador**: lee el plano (PDF), calcula límites y la mejor posición del elevador.
- **Plomadas** e **informe de corte de rieles** automáticos.
- **Informes con IA**: uno para el cliente (descargable) y uno técnico interno (auto por correo).
- **Gestión de proyectos**: cronograma (Gantt) + curva S; el campo actualiza avance; **curva S real vs
  planificada** + **proyección de días de adelanto/retraso** (earned value).
- **Documentos por proyecto** en Google Drive (plano, informes, fotos…).
- **Fichaje** (clock in/out) con horas atadas al proyecto.
- **Multi-empresa**: cada cliente/empresa es un grupo AISLADO.
"""

N_FUN = """## Funciones clave (ya construidas y desplegadas)

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
"""

# ── 2 · Estado actual ────────────────────────────────────────────────────────
V_EST = """## Estado actual
Desplegado en Streamlit Cloud (v75), funcional. App privada con login propio. Backend en Google
Sheets + Drive (gratis). Limitaciones actuales: cuota de Google Sheets (ok para pocos usuarios
concurrentes), sin login persistente (cookies), sin límite de "asientos" por empresa todavía.
"""

N_EST = """## Estado actual

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
"""

# ── 3 · Roadmap: marcar lo que la realidad ya alcanzó ────────────────────────
V_F2 = """2. **Fase 2:** nómina/payroll (ya se capturan horas por proyecto vía fichaje — extensión natural) +
   gestión legal/compliance de documentos (extensión natural de Documentos/Drive) + costeo por proyecto
   (extensión natural de curva S/EVM)."""

N_F2 = """2. **Fase 2:** nómina/payroll (ya se capturan horas por proyecto vía fichaje — extensión natural) +
   gestión legal/compliance de documentos (extensión natural de Documentos/Drive) + costeo por proyecto
   (extensión natural de curva S/EVM).
   > ✅ **HECHA** (chat técnico, 08/09/2026). Las tres están construidas y desplegadas: nóminas con
   > colilla en PDF, credenciales con vencimiento y avisos, y costeo por obra con P&L y rentabilidad.
   > ⚠️ Con un matiz que importa para la venta: **la nómina no es certificada** — no envía STP ni
   > interpreta *awards*. Hay que decidir si se conecta a un proveedor o se posiciona como costeo de
   > mano de obra."""

V_F3 = """3. **Fase 3:** contabilidad — **integrar con Xero/MYOB** (estándar en Australia) en vez de construir
   módulo propio (alta complejidad regulatoria/fiscal, mejor no asumirla)."""

N_F3 = """3. **Fase 3:** contabilidad — **integrar con Xero/MYOB** (estándar en Australia) en vez de construir
   módulo propio (alta complejidad regulatoria/fiscal, mejor no asumirla).
   > ⏭ **Es lo siguiente, y la decisión sigue siendo la correcta.** Cero líneas de Xero/MYOB en el
   > repositorio a día de hoy. Antes va lo que permite COBRAR (planes, asientos y alta de cliente),
   > que hoy no existe."""

for etq, a in (("funciones", V_FUN), ("estado", V_EST), ("fase 2", V_F2), ("fase 3", V_F3)):
    if s.count(a) != 1:
        raise SystemExit("ancla %s no unica: %d" % (etq, s.count(a)))

s = s.replace(V_FUN, N_FUN).replace(V_EST, N_EST).replace(V_F2, N_F2).replace(V_F3, N_F3)

# ── 4 · nota de mantenimiento, al final ──────────────────────────────────────
s = s.rstrip() + """

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
"""

io.open(P, "w", encoding="utf-8", newline="").write(s)
print("NEGOCIO.md: funciones, estado, fases 2-3 y nota de mantenimiento")
