# Implementación de la Integración del Entrenador Digital

## Guía de Implementación en Prosa

Este documento describe en detalle cómo implementar cada fase de la integración del Entrenador Digital con el ecosistema de agentes de IA. A diferencia del documento técnico de propuesta, aquí explicamos el **por qué** y el **cómo** de cada decisión de implementación, con el objetivo de que cualquier desarrollador pueda comprender la lógica detrás de cada componente.

---

## Fase 1: Construcción de la Infraestructura Base

### El TrainingGateway: El Nuevo Orquestador

La primera pieza que debemos construir es el `TrainingGateway`, un componente que actúa como intermediario entre los endpoints del Entrenador Digital y el ecosistema de agentes. Actualmente, cuando un estudiante envía código o solicita una pista, la solicitud va directamente al `CodeEvaluator` o a la base de datos de pistas. Con el gateway, todas las solicitudes pasarán primero por un punto central que decidirá qué agentes involucrar.

El gateway no reemplaza la lógica existente; la envuelve. Pensemos en él como un decorador arquitectónico: el código actual sigue funcionando exactamente igual, pero ahora tiene la capacidad de invocar servicios adicionales antes y después de su ejecución principal.

La implementación del gateway debe seguir el principio de **responsabilidad única**: su único trabajo es decidir qué componentes invocar y en qué orden. No debe contener lógica de negocio del entrenamiento, ni lógica de los agentes. Solo orquesta.

```
Solicitud → TrainingGateway → [¿Qué necesita esta solicitud?]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ¿Trazabilidad?  ¿Análisis de    ¿Pista
                              riesgos?        contextual?
                    │               │               │
                    ▼               ▼               ▼
               TC-N4 Agent    AR-IA Agent    T-IA-Cog
```

Para implementar esto, creamos una clase `TrainingGateway` en `backend/core/training_gateway.py`. Esta clase recibe las dependencias necesarias (agentes, repositorios) mediante inyección de dependencias, siguiendo el patrón que ya usa el sistema con `get_llm_provider` y `get_db`.

El gateway expone métodos como `process_code_submission`, `process_hint_request` y `process_session_start`. Cada método encapsula la lógica de orquestación específica para ese tipo de operación. Internamente, estos métodos invocan a los agentes de forma asíncrona cuando es apropiado, permitiendo que operaciones independientes (como registrar una traza y analizar riesgos) ocurran en paralelo.

### El TrainingTraceCollector: Capturando el Proceso

El segundo componente fundamental es el `TrainingTraceCollector`, responsable de traducir los eventos del Entrenador Digital al modelo de trazabilidad N4 del sistema. Este componente entiende que un "intento de código" en el contexto de entrenamiento equivale a una traza cognitiva con ciertos atributos inferidos.

La dificultad principal aquí es que el Entrenador Digital no tiene acceso explícito al razonamiento del estudiante. Mientras que en el Modo Tutor el estudiante escribe "estoy pensando en usar una lista porque..." y eso se convierte directamente en una traza, en el Entrenador Digital solo tenemos el código enviado y el resultado de los tests.

El collector implementa una serie de heurísticas para inferir el estado cognitivo. Por ejemplo:

- Si es el primer intento y el código es similar al código inicial proporcionado, inferimos estado de **exploración**.
- Si el código cambió significativamente respecto al intento anterior, inferimos **cambio de estrategia**.
- Si el código tiene cambios mínimos y el error anterior era de sintaxis, inferimos **depuración**.
- Si todos los tests pasan, inferimos **validación exitosa**.

Estas inferencias no son perfectas, y por eso las marcamos con un nivel de confianza. Una traza inferida con confianza "media" indica que el sistema hizo su mejor estimación pero podría estar equivocado. Esto es importante para los análisis posteriores: no queremos tomar decisiones pedagógicas críticas basadas en inferencias de baja confianza.

El collector se implementa como un servicio stateless que recibe el contexto necesario en cada llamada. No mantiene estado entre invocaciones porque el estado ya está persistido en la base de datos y en Redis. Esto permite escalar horizontalmente sin preocuparnos por sincronización.

### El TrainingRiskMonitor: Vigilancia en Tiempo Real

El tercer componente de la infraestructura base es el `TrainingRiskMonitor`, una versión especializada del agente AR-IA adaptada al contexto de ejercicios estructurados. Mientras que AR-IA analiza sesiones completas de tutoría buscando patrones complejos de delegación cognitiva, el monitor de entrenamiento se enfoca en señales más inmediatas y accionables.

Las señales que el monitor busca incluyen:

**Detección de copy-paste**: Si un estudiante envía 200 caracteres de código 3 segundos después de su último intento (que falló completamente), es físicamente imposible que haya escrito ese código. El monitor calcula la velocidad de escritura implícita y la compara con umbrales humanamente posibles. Cuando detecta una anomalía, no bloquea al estudiante pero registra una alerta que el docente puede revisar.

**Patrones de frustración**: Cinco intentos fallidos en dos minutos, todos con errores diferentes, sugieren que el estudiante está probando cosas al azar sin entender el problema. El monitor puede sugerir proactivamente una pista o incluso cambiar automáticamente a un ejercicio más simple si las políticas de la actividad lo permiten.

**Dependencia de pistas**: Si el estudiante solicita pista antes de cada intento, está usando las pistas como muleta en lugar de como andamiaje. El monitor puede reducir gradualmente el nivel de detalle de las pistas para forzar más autonomía.

La implementación del monitor sigue el patrón Observer: se suscribe a eventos del gateway y reacciona a ellos. Esto desacopla la lógica de detección de la lógica de entrenamiento principal, permitiendo agregar nuevos detectores sin modificar el código existente.

### Extensión de los Modelos de Datos

Para soportar la nueva funcionalidad, necesitamos extender los modelos existentes sin romper la compatibilidad hacia atrás. Esto significa agregar campos opcionales con valores por defecto sensatos.

En el modelo `ExerciseAttemptDB`, agregamos:
- `trace_id`: Referencia a la traza N4 correspondiente (nullable, porque los intentos anteriores no tendrán traza)
- `cognitive_state_inferred`: El estado cognitivo que el sistema infirió (nullable)
- `inference_confidence`: Qué tan seguro está el sistema de su inferencia (float, 0-1)
- `risk_flags`: JSON con cualquier alerta de riesgo detectada (nullable)

En el esquema `SesionEntrenamiento`, agregamos campos para tracking de trazabilidad que se mantienen en Redis junto con el resto de la sesión:
- `trace_sequence_id`: ID de la secuencia N4 que agrupa todas las trazas de esta sesión
- `cumulative_ai_involvement`: Score acumulado de cuánta ayuda de IA ha recibido
- `risk_alerts`: Lista de alertas activas

Estos campos se agregan mediante una migración de base de datos que usa `ALTER TABLE ... ADD COLUMN ... DEFAULT NULL`, garantizando que el sistema siga funcionando durante y después de la migración.

---

## Fase 2: Integración con el Tutor Cognitivo

### La Estrategia de Pistas Contextuales

Una vez que la infraestructura base está en su lugar, podemos abordar la integración más significativa: hacer que el Tutor Cognitivo (T-IA-Cog) genere las pistas en lugar de usar texto estático de la base de datos.

Creamos una nueva estrategia llamada `TrainingHintsStrategy` que extiende la estrategia `GuidedStrategy` existente. Esta nueva estrategia entiende el contexto específico de los ejercicios de entrenamiento:

- Conoce la consigna del ejercicio y los conceptos que se están practicando
- Tiene acceso al historial de intentos del estudiante (qué código envió, qué errores tuvo)
- Sabe cuántas pistas ya recibió y de qué nivel
- Puede ver el error específico del último intento

Con este contexto, la estrategia puede generar pistas verdaderamente personalizadas. Si un estudiante tiene un error de índice fuera de rango, la pista no será genérica ("revisa los límites de tus bucles") sino específica al código que escribió ("en la línea donde accedes a `lista[i]`, ¿qué valores puede tomar `i`? ¿Qué pasa cuando `i` es igual al largo de la lista?").

La implementación requiere construir un "prompt implícito" que represente lo que el estudiante está preguntando al solicitar una pista. El estudiante no escribe una pregunta textual; simplemente hace clic en "Pedir pista". Pero podemos inferir su pregunta implícita:

```python
def _build_implicit_prompt(self, exercise, last_error, attempt_count):
    if last_error and "SyntaxError" in last_error:
        return f"Tengo un error de sintaxis en mi código para {exercise.title}. El error dice: {last_error}. ¿Qué estoy haciendo mal?"
    elif attempt_count > 3:
        return f"Llevo {attempt_count} intentos en {exercise.title} y sigo sin lograrlo. Necesito orientación sobre el enfoque general."
    else:
        return f"Estoy trabajando en {exercise.title} y no sé cómo continuar."
```

Este prompt implícito se pasa al motor de generación del tutor, que aplica las mismas reglas pedagógicas que aplicaría en una conversación normal: no dar código completo, priorizar preguntas sobre respuestas, exigir justificación antes de dar más ayuda.

### El Endpoint Mejorado de Pistas

Implementamos un nuevo endpoint `/pista/v2` que usa la estrategia contextual. El endpoint original `/pista` sigue funcionando exactamente igual para mantener compatibilidad con clientes existentes.

El nuevo endpoint tiene esta lógica:

1. Verificar que la sesión existe y pertenece al usuario
2. Obtener el ejercicio actual y el historial de intentos
3. Decidir si usar T-IA-Cog o fallback a pista estática
4. Si hay intentos previos y el LLM está disponible, usar T-IA-Cog
5. Si no, usar la pista estática de la base de datos
6. Registrar una traza N4 de la solicitud de pista
7. Actualizar el contador de pistas usadas
8. Retornar la respuesta enriquecida con metadata

La decisión de cuándo usar T-IA-Cog y cuándo usar fallback es importante. Usamos la pista contextual cuando:
- El estudiante tiene al menos un intento previo (hay contexto para personalizar)
- El proveedor LLM está disponible y respondiendo
- La latencia del LLM está dentro de límites aceptables (< 3 segundos)

Si alguna de estas condiciones falla, caemos elegantemente a la pista estática. El estudiante siempre recibe una pista; solo cambia qué tan personalizada es.

### Templates de Prompts para Ejercicios

Para que el tutor genere buenas pistas, necesita instrucciones específicas sobre cómo actuar en el contexto de ejercicios. Creamos un archivo `backend/prompts/training_hints.md` con el system prompt especializado:

```markdown
# Rol: Tutor de Programación para Ejercicios Prácticos

Estás ayudando a un estudiante que trabaja en un ejercicio de programación estructurado.
Tu rol es dar pistas que guíen sin resolver el problema.

## Contexto del Ejercicio
- Título: {{exercise_title}}
- Objetivo de aprendizaje: {{learning_objectives}}
- Restricciones: {{constraints}}

## Estado del Estudiante
- Intentos realizados: {{attempt_count}}
- Último error (si hay): {{last_error}}
- Pistas ya recibidas: {{hints_used}}

## Reglas Inquebrantables
1. NUNCA des código que el estudiante pueda copiar directamente
2. Responde con preguntas que lo hagan pensar
3. Si das un ejemplo, que sea de un dominio diferente
4. Aumenta el detalle gradualmente según el nivel de pista solicitado

## Nivel de Pista Solicitado: {{hint_level}}
- Nivel 1: Solo preguntas orientadoras
- Nivel 2: Pistas conceptuales generales
- Nivel 3: Estrategia más específica, pseudocódigo de alto nivel
- Nivel 4: Orientación detallada sin código ejecutable
```

Este template se completa dinámicamente con el contexto del ejercicio y del estudiante antes de enviarse al LLM.

---

## Fase 3: Implementación de la Trazabilidad N4

### Integración en el Flujo de Inicio de Sesión

Cuando un estudiante inicia una sesión de entrenamiento (llama a `/training/iniciar`), ahora también creamos una secuencia de trazas N4. Esta secuencia agrupará todas las trazas generadas durante la sesión, permitiendo reconstruir el proceso completo posteriormente.

La integración es sutil: agregamos una llamada al `TrainingTraceCollector` después de crear la sesión pero antes de retornar la respuesta. Si la creación de la traza falla (por ejemplo, si la base de datos de trazas está temporalmente inaccesible), logueamos el error pero no fallamos la operación principal. La trazabilidad es valiosa pero no crítica para la funcionalidad básica del entrenamiento.

```python
async def iniciar_entrenamiento(request, db, current_user):
    # Lógica existente de creación de sesión...
    sesion_data = crear_sesion(...)
    guardar_sesion(session_id, sesion_data)

    # NUEVO: Crear secuencia de trazas
    try:
        trace_sequence = await trace_collector.create_sequence(
            student_id=str(current_user.id),
            session_id=session_id,
            activity_type="training",
            exercise_ids=[e['id'] for e in ejercicios_preparados]
        )
        sesion_data['trace_sequence_id'] = trace_sequence.id
        guardar_sesion(session_id, sesion_data)
    except Exception as e:
        logger.warning(f"No se pudo crear secuencia de trazas: {e}")
        # Continuamos sin trazabilidad

    return SesionEntrenamiento(...)
```

### Integración en el Flujo de Envío de Código

El punto más importante de captura es cuando el estudiante envía código. Aquí es donde ocurre el "trabajo cognitivo" principal, y donde podemos inferir más información sobre el proceso del estudiante.

Después de ejecutar los tests pero antes de retornar el resultado, capturamos una traza:

```python
async def submit_ejercicio(request, db, current_user, llm_provider):
    # Lógica existente de ejecución de tests...
    sandbox_result = ejecutar_tests(codigo, tests)

    # Lógica existente de evaluación con Alex...
    evaluation = await code_evaluator.evaluate(...)

    # NUEVO: Capturar traza del intento
    sesion = obtener_sesion(request.session_id)
    attempt_number = len(sesion.get('resultados', [])) + 1

    cognitive_trace = await trace_collector.trace_code_attempt(
        session_id=request.session_id,
        student_id=str(current_user.id),
        exercise_id=ejercicio_actual['id'],
        code=request.codigo,
        result=sandbox_result,
        attempt_number=attempt_number,
        previous_code=sesion.get('ultimo_codigo'),
        time_since_last=calcular_tiempo_desde_ultimo(sesion)
    )

    # Guardar referencia a la traza en el resultado
    resultado = ResultadoEjercicio(
        ...,
        trace_id=cognitive_trace.id
    )

    # NUEVO: Actualizar último código para comparación futura
    sesion['ultimo_codigo'] = request.codigo
    sesion['ultimo_intento_timestamp'] = datetime.now().isoformat()
    guardar_sesion(request.session_id, sesion)

    return resultado
```

El collector analiza el código enviado comparándolo con el código anterior (si existe) para inferir qué tipo de cambio hizo el estudiante: ¿agregó código nuevo? ¿modificó código existente? ¿eliminó código? ¿el cambio fue pequeño (typo fix) o grande (reestructuración)?

### El Endpoint de Análisis de Proceso

Para que la trazabilidad sea útil, necesitamos exponerla. Creamos un nuevo endpoint `/training/sesion/{id}/proceso` que retorna un análisis del proceso de resolución:

```python
@router.get("/sesion/{session_id}/proceso")
async def obtener_analisis_proceso(session_id: str, db, current_user):
    # Verificar permisos
    sesion = obtener_sesion(session_id)
    if sesion['user_id'] != current_user.id and not es_docente(current_user):
        raise HTTPException(403, "No autorizado")

    # Obtener trazas de la sesión
    traces = trace_repo.get_by_session(session_id)

    # Reconstruir camino cognitivo
    cognitive_path = reconstruir_camino(traces)

    # Calcular métricas
    metrics = calcular_metricas_proceso(traces)

    return ProcesoEntrenamientoReport(
        session_id=session_id,
        cognitive_path=cognitive_path,
        total_attempts=metrics.total_attempts,
        total_hints_used=metrics.hints_used,
        time_to_first_success=metrics.time_to_success,
        autonomy_score=metrics.autonomy_score,
        strategy_changes=metrics.strategy_changes,
        recommendations=generar_recomendaciones(metrics)
    )
```

Este endpoint es útil tanto para el estudiante (para reflexionar sobre su proceso) como para el docente (para entender cómo sus estudiantes abordan los ejercicios).

### Dashboard de Proceso en el Frontend

La trazabilidad no sirve de nada si no se visualiza. Creamos un componente de frontend que muestra el proceso de resolución de forma visual:

```
┌─────────────────────────────────────────────────────────────┐
│  Tu Proceso de Resolución                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏱️ Tiempo total: 12 minutos                                │
│  📝 Intentos: 5                                             │
│  💡 Pistas usadas: 2                                        │
│  🎯 Autonomía: 72%                                          │
│                                                             │
│  Línea de tiempo:                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🔍 ──▶ 💻 ──▶ 💻 ──▶ 💡 ──▶ 💻 ──▶ 🐛 ──▶ ✅          │   │
│  │ exp    impl   impl   pista  impl   debug  éxito      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  Observaciones:                                             │
│  • Buen progreso incremental                                │
│  • Solicitaste pista en momento apropiado                   │
│  • Corregiste el error rápidamente después de la pista      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Este dashboard usa iconos y una línea de tiempo para representar visualmente el camino cognitivo, haciendo tangible algo que normalmente es invisible.

---

## Fase 4: Integración del Análisis de Riesgos

### Monitoreo en Tiempo Real Durante Submit

En la fase final, conectamos el `TrainingRiskMonitor` al flujo de envío de código. El monitor analiza cada intento buscando señales de alerta:

```python
async def submit_ejercicio(request, db, current_user, llm_provider):
    # ... lógica existente ...

    # NUEVO: Análisis de riesgos
    risk_alerts = await risk_monitor.analyze_attempt(
        student_id=str(current_user.id),
        exercise_id=ejercicio_actual['id'],
        code=request.codigo,
        time_since_last=calcular_tiempo_desde_ultimo(sesion),
        attempt_history=obtener_historial_intentos(sesion)
    )

    # Si hay alertas de alta severidad, agregarlas a la respuesta
    if any(r.severity == 'high' for r in risk_alerts):
        resultado.warnings = [r.message for r in risk_alerts if r.severity == 'high']

    # Persistir alertas para revisión posterior
    for alert in risk_alerts:
        await risk_repo.create(alert)

    return resultado
```

Las alertas de baja severidad se registran silenciosamente para análisis posterior. Las de alta severidad pueden mostrarse al estudiante (de forma pedagógica, no punitiva) o notificarse al docente en tiempo real.

### Alertas para Docentes

Implementamos un sistema de notificaciones WebSocket que permite a los docentes ver alertas en tiempo real mientras sus estudiantes trabajan:

```
┌─────────────────────────────────────────────────────────────┐
│  Panel del Docente - Alertas en Vivo                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔴 Juan Pérez (hace 2 min)                                 │
│     Posible copy-paste: 180 caracteres en 2 segundos        │
│     Ejercicio: U1-VAR-03                                    │
│     [Ver detalle] [Contactar]                               │
│                                                             │
│  🟡 María García (hace 5 min)                               │
│     Frustración detectada: 6 intentos fallidos consecutivos │
│     Ejercicio: U2-COND-01                                   │
│     [Ver detalle] [Ofrecer ayuda]                           │
│                                                             │
│  🟢 Sin alertas recientes para los demás estudiantes        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

El docente puede hacer clic en "Ver detalle" para ver el código del estudiante y el historial de intentos, permitiéndole intervenir de forma informada si lo considera necesario.

### Reportes Agregados

Además del monitoreo en tiempo real, generamos reportes agregados que muestran patrones a nivel de curso:

```python
@router.get("/teacher/reports/training-risks")
async def obtener_reporte_riesgos(course_id: str, date_range: str, db, current_user):
    require_teacher_role(current_user)

    # Obtener todos los riesgos del período
    risks = risk_repo.get_by_course_and_period(course_id, date_range)

    # Agregar por tipo
    risk_summary = agregar_por_tipo(risks)

    # Identificar estudiantes con patrones recurrentes
    recurring_patterns = identificar_patrones_recurrentes(risks)

    return TrainingRiskReport(
        period=date_range,
        total_sessions=contar_sesiones(course_id, date_range),
        risk_summary=risk_summary,
        students_of_concern=recurring_patterns,
        recommendations=generar_recomendaciones_curso(risk_summary)
    )
```

Este reporte ayuda al docente a identificar si hay problemas sistémicos (por ejemplo, un ejercicio que genera mucha frustración en muchos estudiantes podría indicar que está mal diseñado) o problemas individuales que requieren atención personalizada.

---

## Consideraciones de Implementación

### Feature Flags y Migración Gradual

Toda la nueva funcionalidad se implementa detrás de feature flags, permitiendo activarla gradualmente:

```python
TRAINING_FEATURES = {
    "use_tutor_hints": os.getenv("TRAINING_USE_TUTOR_HINTS", "false") == "true",
    "enable_n4_tracing": os.getenv("TRAINING_N4_TRACING", "false") == "true",
    "enable_risk_monitor": os.getenv("TRAINING_RISK_MONITOR", "false") == "true",
}
```

La migración recomendada es:
1. **Semanas 1-2**: Desplegar código con flags desactivados. Verificar que nada se rompe.
2. **Semanas 3-4**: Activar `enable_n4_tracing` en staging. Verificar que las trazas se generan correctamente y no afectan la performance.
3. **Semanas 5-6**: Activar `use_tutor_hints` en staging. Medir latencia y calidad de las pistas generadas.
4. **Semanas 7-8**: Activar todo en producción con monitoreo intensivo.

### Manejo de Errores y Fallbacks

Cada integración tiene un fallback robusto:
- Si T-IA-Cog falla → Usamos pista estática
- Si el TraceCollector falla → Continuamos sin trazas (logueamos error)
- Si el RiskMonitor falla → Continuamos sin análisis de riesgos
- Si todo falla → El entrenamiento básico sigue funcionando como antes

Esto garantiza que los estudiantes nunca se queden sin poder practicar, incluso si hay problemas con los componentes nuevos.

### Performance y Escalabilidad

Las nuevas operaciones agregan latencia. Para mantenerla bajo control:
- Las trazas se escriben de forma asíncrona (fire-and-forget con callback de error)
- El análisis de riesgos usa caché para umbrales y configuración
- Las pistas contextuales tienen timeout de 3 segundos; si el LLM tarda más, usamos fallback
- Las consultas a la base de datos de trazas usan índices optimizados

Con estas optimizaciones, el overhead esperado es:
- `/iniciar`: +50ms (creación de secuencia de trazas)
- `/submit-ejercicio`: +100ms (traza + análisis de riesgos en paralelo)
- `/pista`: +0-2000ms (dependiendo de si usa LLM o fallback)

---

## Conclusión

La implementación de estas cuatro fases transforma el Entrenador Digital de un módulo aislado a un componente integrado del ecosistema AI-Native. Cada fase construye sobre la anterior:

1. **Infraestructura** establece los cimientos y las abstracciones
2. **Integración con T-IA-Cog** aporta inteligencia pedagógica a las pistas
3. **Trazabilidad N4** hace visible el proceso cognitivo
4. **Análisis de riesgos** habilita intervención temprana

El resultado es un Entrenador Digital que no solo evalúa si el código funciona, sino que también observa cómo el estudiante llegó a ese código, detecta problemas en tiempo real, y proporciona ayuda genuinamente personalizada.

Esta integración cierra la brecha entre la práctica estructurada y el aprendizaje profundo, permitiendo que incluso en ejercicios con respuestas "correctas" definidas, el sistema capture y desarrolle las habilidades cognitivas de orden superior que son el verdadero objetivo del sistema AI-Native.

---

*Documento de implementación - Diciembre 2025*
