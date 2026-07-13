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

## Preguntas estratégicas abiertas (para el chat de estrategia)
1. **¿Quién paga y cómo?** ¿La empresa instaladora (B2B) por licencias de usuario? ¿Suscripción mensual
   por asiento (admin vs campo con precios distintos)? ¿Por proyecto?
2. **Mercado**: ¿solo Schindler? ¿otras marcas? ¿qué países/regiones primero?
3. **Precio**: ¿cuánto vale una licencia de admin vs una de campo? ¿tiers (básico/pro)?
4. **Go-to-market**: ¿cómo se llega a las empresas instaladoras? ¿demo, prueba gratis?
5. **Diferenciación / competencia**: ¿qué hacen hoy? ¿por qué esto es mejor?
6. **Roadmap con valor comercial**: qué features justifican precio (¿la proyección de plazos? ¿los
   informes IA? ¿la trazabilidad de documentos/horas?).
7. **Límites técnicos a decidir**: ¿cuántos asientos por plan? → eso se implementa en el chat técnico.

## Cómo trabajan los dos chats
- **Estratégico** (este brief): negocio, precios, mercado, roadmap comercial.
- **Técnico** (CLAUDE.md): implementación. Cuando estrategia decida algo que requiera código
  (ej. planes/asientos, pasarela de pago), se lleva al chat técnico para construirlo.
