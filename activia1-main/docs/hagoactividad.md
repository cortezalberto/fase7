# Flujo de Creacion de Actividades por el Profesor

Este documento describe en detalle el proceso completo de creacion de una actividad de aprendizaje por parte de un docente en el sistema AI-Native MVP, incluyendo las tablas de base de datos impactadas y el flujo de datos desde el frontend hasta la persistencia.

## Tabla de Contenidos

1. [Vision General del Proceso](#vision-general-del-proceso)
2. [Componentes Involucrados](#componentes-involucrados)
3. [Tablas de Base de Datos Impactadas](#tablas-de-base-de-datos-impactadas)
4. [Flujo Detallado de Datos](#flujo-detallado-de-datos)
5. [Modelo de Datos: ActivityDB](#modelo-de-datos-activitydb)
6. [Politicas Pedagogicas](#politicas-pedagogicas)
7. [Ciclo de Vida de una Actividad](#ciclo-de-vida-de-una-actividad)

---

## Vision General del Proceso

El proceso de creacion de actividades sigue el patron arquitectonico Maestro-Detalle implementado en el frontend. El profesor accede a traves de la ruta `/teacher/activities` donde encuentra un formulario dividido en dos secciones principales: los datos generales de la actividad (Maestro) y los ejercicios que la componen (Detalle).

La creacion de una actividad es una operacion que involucra una unica tabla principal en la base de datos: `activities`. Sin embargo, el sistema esta disenado para soportar relaciones con otras entidades como usuarios (docentes), sesiones de aprendizaje y trazabilidad cognitiva.

---

## Componentes Involucrados

### Frontend

El flujo comienza en el componente `ActivityManagementPage.tsx` ubicado en `frontEnd/src/pages/`. Este componente React implementa la interfaz completa para la gestion de actividades con las siguientes caracteristicas:

El estado del formulario se maneja mediante hooks de React (`useState`), almacenando temporalmente los datos de la actividad antes de enviarlos al servidor. El componente incluye validacion del lado del cliente, verificando que los campos obligatorios como `activity_id`, `title` e `instructions` esten completos antes de permitir el envio.

La comunicacion con el backend se realiza a traves del servicio `activitiesService`, una instancia singleton de la clase `ActivitiesService` que extiende `BaseApiService`. Este servicio encapsula todas las llamadas HTTP relacionadas con actividades, proporcionando metodos como `create()`, `update()`, `publish()`, `archive()` y `remove()`.

### Backend

En el backend, las solicitudes llegan al router de actividades definido en `backend/api/routers/activities.py`. Este router expone los endpoints REST necesarios para el CRUD completo de actividades, protegidos por autenticacion de rol docente mediante el decorador `require_teacher_role`.

El repositorio `ActivityRepository` en `backend/database/repositories/activity_repository.py` encapsula todas las operaciones de base de datos, siguiendo el patron Repository para mantener la separacion de responsabilidades. Este repositorio implementa bloqueo pesimista (`SELECT FOR UPDATE`) en las operaciones de actualizacion para prevenir condiciones de carrera en entornos concurrentes.

---

## Tablas de Base de Datos Impactadas

### Tabla Principal: `activities`

La tabla `activities` es la unica directamente impactada durante la creacion de una nueva actividad. Su estructura completa incluye:

**Columnas de identificacion:**
- `id` (VARCHAR 36, PK): UUID generado automaticamente como clave primaria interna
- `activity_id` (VARCHAR 100, UNIQUE, NOT NULL): Identificador de negocio definido por el docente, como "prog2_tp1_colas"

**Columnas de contenido:**
- `title` (VARCHAR 200, NOT NULL): Titulo descriptivo de la actividad
- `description` (TEXT, NULLABLE): Descripcion opcional mas detallada
- `instructions` (TEXT, NOT NULL): Consigna detallada que veran los estudiantes

**Columnas de metadatos academicos:**
- `subject` (VARCHAR 100, NULLABLE): Materia asociada, por ejemplo "Programacion II"
- `difficulty` (VARCHAR 20, NULLABLE): Nivel de dificultad con valores permitidos: INICIAL, INTERMEDIO, AVANZADO
- `estimated_duration_minutes` (INTEGER, NULLABLE): Duracion estimada en minutos
- `tags` (JSON): Array de etiquetas para categorizacion, por ejemplo ["colas", "estructuras"]

**Columnas de configuracion pedagogica:**
- `policies` (JSON, NOT NULL): Objeto JSON con las politicas pedagogicas configurables
- `evaluation_criteria` (JSON): Array de criterios de evaluacion definidos por el docente

**Columnas de relacion:**
- `teacher_id` (VARCHAR 36, FK -> users.id): Referencia al docente creador, con ON DELETE SET NULL

**Columnas de integracion LTI/Moodle (Cortez65.1):**
- `moodle_course_id` (VARCHAR 255, NULLABLE): context_id de Moodle para matching automatico
- `moodle_course_name` (VARCHAR 255, NULLABLE): Nombre del curso en Moodle
- `moodle_course_label` (VARCHAR 100, NULLABLE): Codigo de comision
- `moodle_resource_name` (VARCHAR 255, NULLABLE): Nombre del recurso en Moodle

**Columnas de estado y auditoria:**
- `status` (VARCHAR 20, DEFAULT 'draft'): Estado actual con valores: draft, active, archived
- `published_at` (DATETIME, NULLABLE): Timestamp de publicacion
- `created_at` (DATETIME, NOT NULL): Timestamp de creacion
- `updated_at` (DATETIME, NOT NULL): Timestamp de ultima modificacion

### Tabla Relacionada: `users`

Aunque no se modifica durante la creacion de la actividad, la tabla `users` esta relacionada mediante la columna `teacher_id`. Esta relacion permite:

- Identificar al docente propietario de cada actividad
- Filtrar actividades por docente en las consultas
- Mantener integridad referencial con ON DELETE SET NULL

La relacion se define en el ORM como:
```python
teacher = relationship("UserDB", back_populates="activities", foreign_keys=[teacher_id])
```

---

## Flujo Detallado de Datos

### Paso 1: Interaccion del Usuario en el Frontend

El profesor navega a `/teacher/activities` y hace clic en "Nueva Actividad". Esto activa el modal de creacion mediante el estado `showCreateModal`. El formulario presenta dos secciones:

**Seccion Maestro (Datos de la Actividad):**
- Campos de identificacion: ID de Actividad, Titulo, Materia
- Campos de contenido: Descripcion, Instrucciones Generales
- Campos de configuracion: Dificultad, Duracion, Nivel Maximo de Ayuda, Etiquetas
- Checkboxes de politicas: Bloquear soluciones, Requerir justificacion, Permitir fragmentos

**Seccion Detalle (Ejercicios):**
El profesor puede agregar multiples ejercicios, cada uno con un numero secuencial y un enunciado. Los ejercicios se almacenan en el estado local `exercises` como un array de objetos con la estructura:
```typescript
interface ExerciseDetail {
  id: string;       // ID temporal para React keys
  numero: number;   // Numero secuencial auto-incrementado
  enunciado: string; // Texto del enunciado
}
```

### Paso 2: Validacion y Envio

Al hacer clic en "Crear Actividad", se ejecuta la funcion `handleCreateActivity()`. Esta funcion:

1. Valida que los campos requeridos (`activity_id`, `title`, `instructions`) esten completos
2. Construye el objeto `ActivityCreate` con todos los datos del formulario
3. Invoca `activitiesService.create(createData)` para enviar la solicitud HTTP

El objeto enviado tiene la estructura:
```typescript
const createData: ActivityCreate = {
  activity_id: "prog2_tp1_colas",
  title: "Implementacion de Cola Circular",
  instructions: "Implementar una cola circular que...",
  teacher_id: user.id,
  description: "Trabajo practico sobre estructuras de datos",
  subject: "Programacion II",
  difficulty: "INTERMEDIO",
  estimated_duration_minutes: 120,
  tags: ["colas", "estructuras", "arreglos"],
  policies: {
    max_help_level: "MEDIO",
    block_complete_solutions: true,
    require_justification: true,
    allow_code_snippets: false,
    risk_thresholds: { cognitive_delegation: 0.7, ai_dependency: 0.6 }
  },
  evaluation_criteria: ["Correcta implementacion", "Manejo de overflow"]
};
```

### Paso 3: Llamada HTTP al Backend

El servicio `ActivitiesService` realiza una solicitud POST a `/api/v1/activities` con el cuerpo JSON. La clase base `BaseApiService` se encarga de:

- Anadir el token JWT en el header `Authorization: Bearer <token>`
- Serializar el cuerpo a JSON
- Manejar errores de red y respuestas de error del servidor

### Paso 4: Procesamiento en el Router

El endpoint `POST /activities` en `activities.py` recibe la solicitud. El flujo es:

1. **Autenticacion**: El decorador `require_teacher_role` verifica que el usuario tiene rol de docente
2. **Validacion de esquema**: Pydantic valida automaticamente el cuerpo contra `ActivityCreate`
3. **Verificacion de duplicados**: Se consulta si ya existe una actividad con el mismo `activity_id`
4. **Creacion en repositorio**: Se invoca `activity_repo.create(...)` con todos los parametros

### Paso 5: Persistencia en el Repositorio

El metodo `create()` del `ActivityRepository` ejecuta:

1. Genera un nuevo UUID para el campo `id`
2. Crea la instancia de `ActivityDB` con todos los campos
3. Establece el `status` inicial como "draft"
4. Ejecuta `db.add(activity)` para agregar al contexto de sesion
5. Ejecuta `db.commit()` para persistir en PostgreSQL
6. Ejecuta `db.refresh(activity)` para obtener los valores generados por la BD

### Paso 6: Respuesta al Frontend

El router retorna un objeto `APIResponse` con:
- `success: true`
- `data`: Los datos de la actividad creada (incluyendo `id`, `created_at`, `updated_at`)
- `message`: "Activity created successfully: prog2_tp1_colas"

El frontend recibe la respuesta, cierra el modal, limpia el formulario y recarga la lista de actividades mediante `loadActivities()`.

---

## Modelo de Datos: ActivityDB

El modelo ORM `ActivityDB` hereda de dos clases base:

**Base**: La clase declarativa de SQLAlchemy que proporciona la funcionalidad ORM basica.

**BaseModel**: Un mixin que agrega campos comunes:
- `id`: Clave primaria UUID
- `created_at`: Timestamp de creacion timezone-aware
- `updated_at`: Timestamp de actualizacion automatica

La clase incluye indices compuestos para optimizar consultas frecuentes:
- `idx_activity_teacher_status`: Para filtrar actividades por docente y estado
- `idx_activity_status_created`: Para listar actividades por estado ordenadas por fecha
- `idx_activity_subject_status`: Para buscar por materia y estado
- `idx_activity_moodle_match`: Para matching automatico en integracion LTI

Tambien incluye restricciones de integridad:
- `ck_activity_status_valid`: Asegura que status sea uno de: draft, active, archived
- `ck_activity_difficulty_valid`: Asegura que difficulty sea NULL o uno de: INICIAL, INTERMEDIO, AVANZADO

---

## Politicas Pedagogicas

Las politicas pedagogicas se almacenan como JSON en la columna `policies`. Esta estructura permite configurar el comportamiento de los agentes de IA cuando interactuan con estudiantes en el contexto de esta actividad:

**max_help_level**: Define el nivel maximo de ayuda que el sistema puede proporcionar. Los valores posibles son MINIMO, BAJO, MEDIO y ALTO, donde MINIMO implica respuestas puramente socraticas y ALTO permite pistas mas explicitas.

**block_complete_solutions**: Cuando esta activo, el agente T-IA-Cog nunca proporcionara soluciones completas, solo orientacion y pistas parciales.

**require_justification**: Cuando esta activo, el sistema pedira al estudiante que justifique sus decisiones de diseno y codigo antes de proporcionar asistencia adicional.

**allow_code_snippets**: Controla si el agente puede incluir fragmentos de codigo en sus respuestas o debe limitarse a explicaciones conceptuales.

**risk_thresholds**: Define umbrales para la deteccion de riesgos. Por ejemplo, un `ai_dependency` de 0.6 significa que se generara una alerta si el estudiante depende de la IA para mas del 60% de sus interacciones.

---

## Ciclo de Vida de una Actividad

Una actividad atraviesa tres estados posibles durante su existencia:

### Estado: draft (Borrador)

Este es el estado inicial cuando se crea la actividad. En este estado:
- La actividad no es visible para los estudiantes
- El docente puede editar todos los campos libremente
- No se generan sesiones de aprendizaje asociadas

### Estado: active (Activa)

Cuando el docente esta satisfecho con la configuracion, puede publicar la actividad mediante el endpoint `POST /activities/{id}/publish`. Al publicar:
- Se actualiza `status` a "active"
- Se registra `published_at` con el timestamp actual
- La actividad se vuelve visible para los estudiantes
- Los estudiantes pueden iniciar sesiones de aprendizaje en el contexto de esta actividad

### Estado: archived (Archivada)

Una actividad puede archivarse mediante `POST /activities/{id}/archive` o eliminarse mediante `DELETE /activities/{id}`. La eliminacion es un soft delete que simplemente cambia el estado a archived:
- La actividad deja de ser visible para los estudiantes
- Las sesiones historicas y trazas cognitivas asociadas se preservan
- El docente puede consultar el historico pero no puede reactivar directamente

---

## Observaciones sobre los Ejercicios en el Frontend

Es importante notar que los ejercicios definidos en la seccion Detalle del formulario actualmente se manejan solo en el estado local del frontend. La estructura `ExerciseDetail[]` no se persiste directamente en la base de datos como parte de la actividad.

Esta es una decision de diseno intencional: el sistema esta preparado para que los ejercicios se almacenen como entidades separadas vinculadas a la actividad, pero en la implementacion actual el campo `evaluation_criteria` y el campo `instructions` de la actividad son los que contienen la informacion sobre que debe hacer el estudiante.

Para una futura iteracion, se podria crear una tabla `exercise_items` relacionada con `activities` mediante una clave foranea, permitiendo almacenar cada ejercicio como una entidad independiente con su propio enunciado, criterios de evaluacion especificos y configuracion de ayuda.

---

## Resumen de Impacto en Base de Datos

| Tabla | Operacion | Momento |
|-------|-----------|---------|
| `activities` | INSERT | Al crear la actividad |
| `activities` | UPDATE | Al editar, publicar o archivar |
| `users` | SELECT (JOIN) | Para validar teacher_id |

La creacion de una actividad es una operacion atomica que afecta unicamente a la tabla `activities`. Las relaciones con otras tablas como sesiones, trazas cognitivas y riesgos se establecen posteriormente cuando los estudiantes interactuan con la actividad publicada.
