# Analisis de Compatibilidad: Dashboard Docente y Actividades del Estudiante

## Resumen Ejecutivo

Este documento analiza en profundidad el sistema de trazabilidad cognitiva N4 que conecta las actividades del estudiante con el dashboard del docente. El objetivo es verificar si las actividades del estudiante quedan correctamente registradas para que el docente pueda realizar la trazabilidad de cursos y estudiantes especificos.

---

## 1. Arquitectura del Sistema de Trazabilidad

### 1.1 Flujo de Datos

El sistema implementa un flujo de datos bidireccional que conecta las interacciones del estudiante con el panel de supervision del docente:

```
Estudiante (DashboardPage)
    |
    v
AIGateway (Stateless)
    |
    +---> TraceCoordinator ---> CognitiveTraceDB (PostgreSQL)
    |
    +---> RiskCoordinator ---> RiskDB (PostgreSQL)
    |
    v
SessionDB (trace_count actualizado)
    |
    v
Docente (TeacherDashboardPage, StudentMonitoringPage)
```

### 1.2 Componentes Principales

El sistema se compone de los siguientes modulos:

**Backend:**
- `TraceCoordinator`: Gestiona la creacion y persistencia de trazas cognitivas
- `RiskCoordinator`: Analiza y persiste riesgos detectados
- `TrazabilidadN4Agent`: Agente de trazabilidad con 4 niveles (N1-N4)
- `TraceRepository`: Operaciones CRUD para trazas
- `RiskRepository`: Operaciones CRUD para riesgos

**Frontend:**
- `TeacherDashboardPage`: Panel principal del docente con metricas agregadas
- `StudentMonitoringPage`: Monitoreo en tiempo real con 4 vistas (Alertas, Sesiones, Comparacion, Trazabilidad)
- `teacherTraceabilityService`: Cliente API para endpoints de trazabilidad

---

## 2. Que se Registra Correctamente

### 2.1 Trazas Cognitivas (CognitiveTraceDB)

El sistema registra las siguientes dimensiones para cada interaccion:

| Dimension | Campos | Estado |
|-----------|--------|--------|
| Identificacion | `session_id`, `student_id`, `activity_id` | COMPLETO |
| Nivel | `trace_level` (N1-N4) | COMPLETO |
| Interaccion | `interaction_type` (9 tipos) | COMPLETO |
| Estado Cognitivo | `cognitive_state` (8 estados) | COMPLETO |
| Contenido | `content`, `context`, `trace_metadata` | COMPLETO |
| Analisis N4 | `cognitive_intent`, `decision_justification`, `alternatives_considered` | COMPLETO |
| Dependencia IA | `ai_involvement` (0.0-1.0) | COMPLETO |
| 6 Dimensiones N4 | `semantic_understanding`, `algorithmic_evolution`, `cognitive_reasoning`, `interactional_data`, `ethical_risk_data`, `process_data` | COMPLETO (JSONB) |
| Jerarquia | `parent_trace_id`, `agent_id` | COMPLETO |

### 2.2 Riesgos Detectados (RiskDB)

El sistema detecta y persiste los siguientes tipos de riesgo:

| Codigo | Tipo | Nivel | Descripcion |
|--------|------|-------|-------------|
| RC1 | COGNITIVE_DELEGATION | HIGH | Delegacion total - solicita soluciones completas |
| RC2 | AI_DEPENDENCY | MEDIUM | Dependencia excesiva de IA (>60%) |
| RC3 | LACK_JUSTIFICATION | LOW | Decisiones sin justificacion explicita |
| RE1 | ACADEMIC_INTEGRITY | HIGH | Integridad academica - uso no declarado de IA |
| REp1 | UNCRITICAL_ACCEPTANCE | MEDIUM | Aceptacion acritica sin cuestionar respuestas |

### 2.3 Sesiones (SessionDB)

Cada sesion registra:
- Estado activo/completado
- Timestamps de inicio/fin
- `trace_count`: Contador de trazas (actualizado dinamicamente)
- Modo de operacion (TUTOR, SIMULATOR, PRACTICE)

---

## 3. Que Puede Ver el Docente

### 3.1 Dashboard Principal (TeacherDashboardPage)

El dashboard del docente muestra correctamente:

- Estudiantes activos (total del mes)
- Sesiones totales con duracion promedio
- Alertas activas categorizadas por severidad
- Trazas N4 con distribucion de dependencia IA
- Uso de agentes IA (grafico de barras)
- Estados cognitivos detectados (global)
- Alertas recientes con acceso rapido a detalles

### 3.2 Monitoreo en Tiempo Real (StudentMonitoringPage)

El sistema ofrece 4 vistas especializadas:

**Vista Alertas:**
- Alertas filtradas por severidad (critical, high, medium)
- Metricas por alerta: riesgos criticos, dependencia IA, duracion
- Sugerencias de intervencion pedagogica
- Boton "Atender" para reconocer alertas

**Vista Sesiones Activas:**
- Lista de estudiantes trabajando en tiempo real
- Modo de sesion (TUTOR, SIMULATOR, PRACTICE)
- Tiempo de inicio y conteo de trazas
- Auto-actualizacion cada 30 segundos

**Vista Comparacion:**
- Comparativa de estudiantes por actividad
- Metricas agregadas: duracion promedio, interacciones, dependencia IA
- Tabla detallada por estudiante
- Top 5 riesgos mas frecuentes

**Vista Trazabilidad N4:**
- Total de trazas N4 por estudiante
- Distribucion de estados cognitivos global
- Alertas de trazabilidad (alta dependencia, estancamiento)
- Clasificacion de estudiantes por dependencia IA (alta/media/baja)
- Acceso a camino cognitivo individual

---

## 4. Analisis de Brechas y Mejoras Necesarias

### 4.1 Brecha: Persistencia de Reconocimiento de Alertas

**Situacion actual:** El endpoint `POST /teacher/alerts/{alert_id}/acknowledge` retorna confirmacion pero no persiste en base de datos. El comentario en el codigo indica que "en el MVP actual, esto solo retorna confirmacion".

**Impacto:** El docente no puede ver el historico de alertas atendidas, ni filtrar alertas ya reconocidas de las pendientes. Al reiniciar el servidor, todas las alertas vuelven a aparecer como no atendidas.

**Mejora propuesta:** Crear tabla `teacher_interventions` con campos:
- `id`, `alert_id`, `teacher_id`
- `acknowledged_at`, `notes`
- `intervention_type`, `resolution_status`

Esta tabla permitiria al docente llevar registro de sus intervenciones y filtrar alertas ya atendidas.

---

### 4.2 Brecha: Falta de Filtrado por Curso/Materia

**Situacion actual:** Los endpoints de trazabilidad permiten filtrar por `activity_id` pero no por `course_id` o `materia_id`. El docente debe conocer el ID exacto de cada actividad para filtrar.

**Impacto:** En un escenario con multiples cursos y materias, el docente no puede obtener facilmente una vista agregada por curso completo. Debe consultar actividad por actividad.

**Mejora propuesta:** Agregar filtro `course_id` a los endpoints:
- `GET /teacher/traceability/summary?course_id=xxx`
- `GET /teacher/students/compare?course_id=xxx`
- `GET /teacher/alerts?course_id=xxx`

Esto requiere agregar campo `course_id` a `SessionDB` o crear relacion `ActivityDB.course_id`.

---

### 4.3 Brecha: Sincronizacion de Conteo de Trazas

**Situacion actual:** El campo `trace_count` en sesiones se calcula en algunos lugares pero no siempre esta sincronizado con el conteo real de trazas en `cognitive_traces`.

**Impacto:** El dashboard del estudiante puede mostrar un conteo de "interacciones" que difiere del conteo real de trazas. Esto genera confusion en metricas.

**Mejora propuesta:** Implementar trigger en PostgreSQL que actualice automaticamente `sessions.trace_count` cada vez que se inserta una traza:

```sql
CREATE OR REPLACE FUNCTION update_trace_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET trace_count = trace_count + 1
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_trace_count
AFTER INSERT ON cognitive_traces
FOR EACH ROW
EXECUTE FUNCTION update_trace_count();
```

---

### 4.4 Brecha: Visualizacion de Camino Cognitivo en Tiempo Real

**Situacion actual:** El endpoint `GET /teacher/students/{student_id}/cognitive-path` retorna el camino cognitivo pero no hay visualizacion grafica en el frontend. Solo se muestran listas textuales de estados y transiciones.

**Impacto:** El docente no puede visualizar facilmente el "viaje cognitivo" del estudiante a lo largo del tiempo. Las transiciones entre estados son dificiles de interpretar sin un diagrama.

**Mejora propuesta:** Agregar componente de visualizacion tipo "timeline" o "sankey diagram" que muestre:
- Linea de tiempo con estados cognitivos
- Transiciones entre estados con duracion
- Indicadores de riesgo en puntos criticos
- Marcadores de intervencion del tutor

---

### 4.5 Brecha: Exportacion de Datos de Trazabilidad

**Situacion actual:** El sistema tiene metodo `export_for_evaluation()` en `TrazabilidadN4Agent` pero no hay endpoint REST expuesto ni funcionalidad en el frontend para exportar trazas.

**Impacto:** El docente no puede exportar datos de trazabilidad para analisis externo, reportes academicos o investigacion doctoral.

**Mejora propuesta:** Exponer endpoints de exportacion:
- `GET /teacher/students/{student_id}/export?format=json|csv`
- `GET /teacher/traceability/export?activity_id=xxx&format=json|csv`
- Agregar boton "Exportar" en `StudentTraceabilityViewer`

---

### 4.6 Brecha: Notificaciones Push de Alertas Criticas

**Situacion actual:** El sistema detecta alertas criticas pero el docente debe refrescar manualmente (o esperar 30 segundos de auto-refresh) para verlas. No hay notificaciones push.

**Impacto:** En sesiones criticas donde un estudiante esta bloqueado o muestra comportamiento de riesgo alto, el docente puede no enterarse a tiempo para intervenir.

**Mejora propuesta:** Implementar WebSockets para notificaciones en tiempo real:
- Backend: Agregar endpoint WebSocket `/ws/teacher/alerts`
- Frontend: Mostrar toast notification cuando llega alerta critica
- Opcional: Integracion con notificaciones del navegador (Web Push API)

---

### 4.7 Brecha: Historial de Estados Cognitivos del Estudiante

**Situacion actual:** El dashboard del estudiante (`DashboardPage`) muestra sesiones recientes con conteo de interacciones, pero no muestra el estado cognitivo actual ni historial de estados.

**Impacto:** El estudiante no tiene visibilidad de su propio proceso cognitivo. No puede reflexionar sobre en que fases pasa mas tiempo ni identificar patrones de estancamiento.

**Mejora propuesta:** Agregar seccion "Mi Proceso Cognitivo" en `DashboardPage`:
- Grafico de estados cognitivos de la ultima sesion
- Tiempo pasado en cada estado
- Indicadores de progreso (menos tiempo en ESTANCAMIENTO = mejora)
- Tips basados en patrones detectados

---

### 4.8 Brecha: Correlacion entre Actividades y Materias

**Situacion actual:** Las actividades (`activity_id`) son strings independientes sin relacion explicita con el modelo de materias y unidades (`SubjectDB`, `UnidadDB`).

**Impacto:** El docente no puede ver trazabilidad agrupada por materia ni unidad tematica. La gestion de contenido academico (`ContentManagementPage`) esta desconectada del sistema de trazabilidad.

**Mejora propuesta:** Crear relacion entre modelos:
- Agregar `subject_code` y `unidad_id` opcionales a `SessionDB` y `CognitiveTraceDB`
- Crear endpoint `/teacher/subjects/{code}/traceability` que agregue trazas por materia
- Mostrar trazabilidad en `ContentManagementPage` por unidad

---

### 4.9 Brecha: Metricas de Progreso Longitudinal

**Situacion actual:** El sistema muestra snapshots puntuales de trazabilidad pero no hay analisis de evolucion temporal. No se puede ver si un estudiante "mejora" o "empeora" en dependencia de IA a lo largo del semestre.

**Impacto:** El docente no puede evaluar el progreso real del estudiante ni identificar tendencias a largo plazo. Las intervenciones pedagogicas no pueden ser evaluadas en su efectividad.

**Mejora propuesta:** Crear endpoint y visualizacion de tendencias:
- `GET /teacher/students/{student_id}/trends?period=week|month|semester`
- Grafico de evolucion de dependencia IA en el tiempo
- Comparacion de estados cognitivos entre primeras y ultimas sesiones
- Indicadores de mejora/deterioro

---

### 4.10 Brecha: Integracion con Sistema de Evaluacion

**Situacion actual:** Las trazas N4 incluyen `decision_justification` y analisis cognitivo, pero no hay conexion con el sistema de evaluacion formal. El evaluador (`E-IA-Proc`) no consume datos de trazabilidad para generar calificaciones.

**Impacto:** La evaluacion basada en proceso (objetivo central del proyecto) no esta completamente implementada. El docente debe evaluar manualmente usando la informacion de trazabilidad.

**Mejora propuesta:** Integrar TC-N4 con sistema de evaluacion:
- Agregar campo `evaluation_weight` a tipos de riesgo
- Generar score de proceso automatico basado en:
  - Diversidad de estados cognitivos visitados
  - Proporcion de decisiones justificadas
  - Nivel de dependencia IA
  - Tiempo en estados productivos vs estancamiento
- Exponer en `ReportsPage` para docentes

---

## 5. Lo Que Funciona Bien

El sistema tiene fortalezas significativas que deben preservarse:

1. **Arquitectura Stateless:** El `AIGateway` es completamente stateless, persistiendo todo a PostgreSQL. Esto permite escalabilidad horizontal y recuperacion ante fallos.

2. **Modelo de 6 Dimensiones N4:** Las columnas JSONB (`semantic_understanding`, `algorithmic_evolution`, etc.) permiten analisis cognitivo profundo sin limitar el esquema.

3. **Deteccion de Riesgos en Tiempo Real:** El `RiskCoordinator` detecta 5 tipos de riesgo con cada interaccion y genera alertas inmediatas.

4. **Batch Loading para N+1:** El `TraceRepository` implementa `get_by_session_ids()` y `get_by_student_activity_pairs()` para evitar N+1 queries.

5. **Auto-Refresh del Dashboard:** El `StudentMonitoringPage` actualiza cada 30 segundos con `AbortController` para cleanup.

6. **Indices Optimizados:** El modelo `CognitiveTraceDB` tiene indices compuestos para queries frecuentes y GIN para columnas JSONB.

---

## 6. Recomendaciones Priorizadas

### Alta Prioridad (Sprint Siguiente)

1. **Persistir reconocimiento de alertas** - Crear tabla `teacher_interventions`
2. **Agregar filtro por curso** - Campo `course_id` en sesiones
3. **Trigger para trace_count** - Sincronizacion automatica

### Media Prioridad (2-3 Sprints)

4. **Timeline visual de camino cognitivo** - Componente React con D3.js o similar
5. **Exportacion de trazabilidad** - Endpoints REST + botones en frontend
6. **Notificaciones push** - WebSockets para alertas criticas

### Baja Prioridad (Backlog)

7. **Dashboard cognitivo para estudiante** - Seccion "Mi Proceso"
8. **Correlacion materias-actividades** - Relacion entre modelos
9. **Metricas longitudinales** - Endpoint de tendencias
10. **Integracion con evaluacion** - Score de proceso automatico

---

## 7. Conclusion

El sistema de trazabilidad N4 esta bien disenado y captura correctamente las actividades del estudiante. El docente puede acceder a informacion detallada sobre estados cognitivos, dependencia de IA, riesgos detectados y caminos de resolucion de problemas.

Las principales brechas estan relacionadas con:
- Persistencia de acciones del docente (alertas atendidas)
- Filtrado jerarquico (curso > materia > actividad)
- Visualizaciones avanzadas (timelines, tendencias)
- Integracion con el sistema de evaluacion formal

Implementando las mejoras propuestas, el sistema cumplira completamente con el objetivo de la tesis doctoral: evaluacion basada en proceso con trazabilidad cognitiva N4.

---

*Documento generado: Enero 2026*
*Version: Cortez82*
