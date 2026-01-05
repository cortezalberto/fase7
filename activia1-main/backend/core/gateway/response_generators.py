"""
Response Generators - LLM-based response generation for pedagogical modes.

Cortez66: Extracted from ai_gateway.py (2,389 lines)

This module contains the 7 response type generators:
- Socratic questioning (socratic_questioning)
- Conceptual explanation (conceptual_explanation)
- Guided hints (guided_hints)
- Empathetic support (empathetic_support) - Cortez64
- Metacognitive guidance (metacognitive_guidance) - Cortez64
- Example-based (example_based) - Cortez64
- Clarification request (clarification_request) - Cortez64

Each generator follows the same pattern:
1. Load conversation history (if available)
2. Build system prompt with pedagogical instructions
3. Call LLM with appropriate parameters
4. Return response or fallback on failure
"""
import logging
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...llm.base import LLMMessage, LLMRole

if TYPE_CHECKING:
    from ...llm.base import LLMProvider
    from .protocols import TraceRepositoryProtocol

logger = logging.getLogger(__name__)


# =============================================================================
# SOCRATIC RESPONSE GENERATOR
# =============================================================================

async def generate_socratic_response(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
    model_override: Optional[str] = None,
) -> str:
    """
    Generate Socratic questioning response.

    Uses guiding questions to help the student discover the solution
    themselves, without giving direct answers.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages
        model_override: Optional model to use instead of default

    Returns:
        Generated response string
    """
    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content="""Eres un tutor socrático que guía mediante preguntas.

Tu rol es ayudar al estudiante a descubrir la solución por sí mismo, sin dar respuestas directas.

REGLAS ESTRICTAS:
1. NUNCA proporciones código completo ni soluciones directas
2. Usa preguntas abiertas que promuevan la reflexión
3. Guía hacia el descubrimiento, no hacia la respuesta
4. Si el estudiante está muy perdido, haz preguntas más específicas pero SIN dar la respuesta

Ejemplos de preguntas útiles:
- ¿Qué crees que debería pasar si...?
- ¿Cómo podrías descomponer este problema?
- ¿Qué estructura de datos crees que sería apropiada?
- ¿Has considerado qué pasa con casos límite como...?

Responde SIEMPRE en español. Máximo 300 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=prompt
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (socratic)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id
            }
        )

        llm_started_at = time.perf_counter()

        generate_kwargs = {
            "max_tokens": 500,
            "temperature": 0.7
        }
        if model_override:
            generate_kwargs["model"] = model_override

        response = await llm.generate(messages, **generate_kwargs)
        llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

        logger.info(
            "LLM response received (socratic)",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "duration_ms": llm_duration_ms
            }
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (socratic): %s", e, exc_info=True)
        from .fallback_responses import get_fallback_socratic_response
        return get_fallback_socratic_response(prompt, flow_id=flow_id)


# =============================================================================
# CONCEPTUAL EXPLANATION GENERATOR
# =============================================================================

async def generate_conceptual_explanation(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
    model_override: Optional[str] = None,
) -> str:
    """
    Generate conceptual explanation response.

    Explains the underlying concept without providing direct solutions.
    Uses analogies and real-world examples to clarify.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages
        model_override: Optional model to use instead of default

    Returns:
        Generated response string
    """
    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content="""Eres un tutor experto en explicar conceptos de programación.

Tu rol es explicar el CONCEPTO subyacente, no resolver el problema específico.

REGLAS:
1. Explica el concepto general primero
2. Usa analogías con situaciones de la vida real
3. Proporciona un ejemplo DIFERENTE al problema del estudiante
4. NO des la solución directa al problema planteado

Estructura tu respuesta así:
1. **Concepto clave**: [nombre del concepto]
2. **¿Qué es?**: Explicación clara y simple
3. **Analogía**: Comparación con algo cotidiano
4. **Ejemplo diferente**: Un caso similar pero NO el del estudiante

Responde SIEMPRE en español. Máximo 350 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=prompt
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (conceptual)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id
            }
        )

        llm_started_at = time.perf_counter()

        generate_kwargs = {
            "max_tokens": 600,
            "temperature": 0.6
        }
        if model_override:
            generate_kwargs["model"] = model_override

        response = await llm.generate(messages, **generate_kwargs)
        llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

        logger.info(
            "LLM response received (conceptual)",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "duration_ms": llm_duration_ms
            }
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (conceptual): %s", e, exc_info=True)
        from .fallback_responses import get_fallback_conceptual_explanation
        return get_fallback_conceptual_explanation(prompt, flow_id=flow_id)


# =============================================================================
# GUIDED HINTS GENERATOR
# =============================================================================

async def generate_guided_hints(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
    model_override: Optional[str] = None,
) -> str:
    """
    Generate guided hints response.

    Provides progressive hints that help without revealing the full solution.
    Implements scaffolding with 4 levels of increasing specificity.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages
        model_override: Optional model to use instead of default

    Returns:
        Generated response string
    """
    help_level = strategy.get("help_level", 1)

    level_instructions = {
        1: "Da pistas muy generales, solo la dirección correcta. No menciones estructuras de datos específicas.",
        2: "Puedes mencionar qué tipo de estructura de datos podría ser útil, pero no cómo usarla.",
        3: "Puedes dar pseudocódigo de alto nivel, pero NO código real.",
        4: "Puedes dar el esqueleto de la solución con comentarios indicando qué va en cada parte, pero NO el código completo."
    }

    level_instruction = level_instructions.get(help_level, level_instructions[1])

    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content=f"""Eres un tutor que proporciona pistas graduales.

NIVEL DE AYUDA ACTUAL: {help_level}/4

{level_instruction}

REGLAS GENERALES:
1. Sé específico pero NO des la solución completa
2. Sugiere un próximo paso concreto
3. Si el estudiante parece frustrado, sé más empático
4. Termina siempre con una pregunta guía

Responde SIEMPRE en español. Máximo 250 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=prompt
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (guided_hints)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id,
                "help_level": help_level
            }
        )

        llm_started_at = time.perf_counter()

        generate_kwargs = {
            "max_tokens": 450,
            "temperature": 0.65
        }
        if model_override:
            generate_kwargs["model"] = model_override

        response = await llm.generate(messages, **generate_kwargs)
        llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

        logger.info(
            "LLM response received (guided_hints)",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "duration_ms": llm_duration_ms,
                "help_level": help_level
            }
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (guided_hints): %s", e, exc_info=True)
        from .fallback_responses import get_fallback_guided_hints
        return get_fallback_guided_hints(prompt, flow_id=flow_id)


# =============================================================================
# EMPATHETIC SUPPORT GENERATOR (Cortez64)
# =============================================================================

async def generate_empathetic_support(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
) -> str:
    """
    Generate empathetic support response for frustrated students.

    FIX Cortez64: Recognizes frustration and provides emotional support
    while still guiding towards the solution.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages

    Returns:
        Generated response string
    """
    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content="""Eres un tutor empático especializado en ayudar a estudiantes frustrados.

El estudiante muestra signos de frustración o bloqueo. Tu prioridad es:
1. Reconocer y validar su frustración
2. Ayudarlo a desbloquear su pensamiento
3. Dar pistas más directas de lo usual

LO QUE DEBES HACER:
1. **Reconocer la frustracion** - "Entiendo que esto es frustrante..." / "Es normal sentirse trabado..."
2. **Normalizar la dificultad** - "Este es un problema que toma tiempo..." / "Todos nos trabamos con esto al principio..."
3. **Ofrecer perspectiva fresca** - Sugerir mirar el problema desde otro angulo
4. **Dar pistas mas directas** - Ser mas especifico de lo usual para ayudar a desbloquear
5. **Sugerir pasos pequenos** - Dividir en partes manejables
6. **Mantener tono alentador** - "Ya avanzaste en X, ahora veamos Y..."

PROHIBIDO:
- Dar codigo completo (pero si puedes ser mas especifico con conceptos)
- Minimizar su frustracion ("es facil", "no es para tanto")
- Dar la solucion directa

Puedes ser mas generoso con las pistas que en modo normal,
pero sin dar la solucion completa.

Se calido, paciente y constructivo. Maximo 200 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=f"Estudiante frustrado dice: {prompt}"
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (empathetic_support)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id
            }
        )

        llm_started_at = time.perf_counter()
        response = await llm.generate(
            messages,
            max_tokens=400,
            temperature=0.8  # More variety for empathy
        )
        llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

        logger.info(
            "LLM response received (empathetic_support)",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "duration_ms": llm_duration_ms
            }
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (empathetic_support): %s", e, exc_info=True)
        return get_fallback_empathetic_support(prompt, flow_id=flow_id)


# =============================================================================
# METACOGNITIVE GUIDANCE GENERATOR (Cortez64)
# =============================================================================

async def generate_metacognitive_guidance(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
) -> str:
    """
    Generate metacognitive guidance for students asking how to think.

    FIX Cortez64: Teaches the PROCESS of thinking, not the content.
    Helps students develop problem-solving strategies.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages

    Returns:
        Generated response string
    """
    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content="""Eres un tutor especializado en metacognicion y estrategias de aprendizaje.
El estudiante pregunta sobre COMO PENSAR o COMO ENCARAR un problema.

TU OBJETIVO: Ensenar el PROCESO de pensamiento, no el contenido.

LO QUE DEBES HACER:
1. **Estrategia de descomposicion** - "Primero, identifiquemos que sabemos y que nos piden..."
2. **Plan de accion** - "Un buen enfoque seria: 1) entender el input, 2) definir el output..."
3. **Tecnicas de resolucion** - Mencionar patrones como "dividir y conquistar", "casos base"
4. **Preguntas de autoevaluacion** - "Preguntate: que pasa si el input esta vacio?"
5. **Orden de pasos** - Dar una secuencia logica para abordar problemas similares

PROHIBIDO:
- Dar codigo o pseudocodigo detallado
- Resolver el problema especifico directamente

Ensenale a PESCAR, no le des el pescado.

Estructura tu respuesta como un plan de accion numerado.
Maximo 250 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=f"Estudiante pregunta sobre estrategia: {prompt}"
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (metacognitive_guidance)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id
            }
        )

        llm_started_at = time.perf_counter()
        response = await llm.generate(
            messages,
            max_tokens=450,
            temperature=0.6  # More structured
        )
        llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

        logger.info(
            "LLM response received (metacognitive_guidance)",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "duration_ms": llm_duration_ms
            }
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (metacognitive_guidance): %s", e, exc_info=True)
        return get_fallback_metacognitive_guidance(prompt, flow_id=flow_id)


# =============================================================================
# EXAMPLE-BASED GENERATOR (Cortez64)
# =============================================================================

async def generate_example_based(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
) -> str:
    """
    Generate example-based response with analogous examples.

    FIX Cortez64: Provides a similar but different example to help
    the student understand the pattern without giving the direct solution.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages

    Returns:
        Generated response string
    """
    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content="""Eres un tutor que ensena mediante ejemplos analogos.
El estudiante pidio un ejemplo para entender mejor.

TU OBJETIVO: Dar un ejemplo SIMILAR pero NO IDENTICO al problema.

LO QUE DEBES HACER:
1. **Ejemplo analogo** - Usar un caso diferente pero con la misma estructura
   - Si pregunta sobre ordenar numeros, dar ejemplo de ordenar palabras alfabeticamente
   - Si pregunta sobre listas, dar ejemplo con otra coleccion

2. **Explicar el ejemplo** - Paso a paso, conceptualmente
3. **Preguntas de transferencia** - "Ves como esto se aplica a tu problema?"
4. **Conexion explicita** - Ayudar a ver el paralelo con su problema

PROHIBIDO:
- Dar la solucion directa a SU problema
- Dar codigo copiable para su ejercicio especifico

El ejemplo debe iluminar el PATRON, no resolver el problema.

Ejemplo de estructura:
"Imagina que en lugar de [su problema] tenes [problema analogo]...
En ese caso, pensarias en... [explicacion]
Ahora, como aplicarias esta misma idea a tu problema?"

Maximo 300 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=f"Estudiante pide ejemplo: {prompt}"
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (example_based)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id
            }
        )

        llm_started_at = time.perf_counter()
        response = await llm.generate(
            messages,
            max_tokens=500,
            temperature=0.7
        )
        llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

        logger.info(
            "LLM response received (example_based)",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "duration_ms": llm_duration_ms
            }
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (example_based): %s", e, exc_info=True)
        return get_fallback_example_based(prompt, flow_id=flow_id)


# =============================================================================
# CLARIFICATION REQUEST GENERATOR (Cortez64)
# =============================================================================

async def generate_clarification_request(
    llm: "LLMProvider",
    prompt: str,
    strategy: Dict[str, Any],
    session_id: str = None,
    flow_id: Optional[str] = None,
    conversation_history: List[LLMMessage] = None,
) -> str:
    """
    Generate clarification request for ambiguous prompts.

    FIX Cortez64: Updated to async with LLM for more natural responses.
    Asks specific questions to understand the student's needs.

    Args:
        llm: LLM provider instance
        prompt: Student's prompt
        strategy: Strategy dict from cognitive engine
        session_id: Current session ID
        flow_id: Flow ID for tracing
        conversation_history: Previous conversation messages

    Returns:
        Generated response string
    """
    messages = [
        LLMMessage(
            role=LLMRole.SYSTEM,
            content="""Eres un tutor que necesita mas informacion para ayudar.
El mensaje del estudiante es ambiguo o le falta contexto.

TU OBJETIVO: Pedir clarificacion de manera amable y especifica.

LO QUE DEBES HACER:
1. Reconocer que queres ayudar
2. Explicar que informacion te falta
3. Hacer preguntas especificas:
   - Que parte exacta no entendes?
   - Que intentaste hasta ahora?
   - Podes mostrar tu codigo actual?
   - Que resultado esperabas vs. que obtuviste?

Se amable y especifico. Maximo 100 palabras."""
        )
    ]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append(
        LLMMessage(
            role=LLMRole.USER,
            content=f"Mensaje ambiguo: {prompt}"
        )
    )

    try:
        logger.info(
            "Sending messages to LLM (clarification_request)",
            extra={
                "session_id": session_id,
                "messages_count": len(messages),
                "flow_id": flow_id
            }
        )

        response = await llm.generate(
            messages,
            max_tokens=200,
            temperature=0.5
        )

        return response.content.strip()
    except Exception as e:
        logger.error("LLM generation failed (clarification_request): %s", e, exc_info=True)
        return get_fallback_clarification_request(prompt, flow_id=flow_id)


# =============================================================================
# FALLBACKS FOR NEW TYPES (Cortez64)
# =============================================================================

def get_fallback_empathetic_support(prompt: str, flow_id: Optional[str] = None) -> str:
    """Fallback for empathetic response when LLM is unavailable."""
    logger.warning(
        "Using fallback empathetic support (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """Entiendo que te sentis frustrado/a, y es completamente normal.
Todos nos trabamos en algun momento cuando aprendemos a programar.

Tomemos un respiro y miremos esto desde otro angulo:

1. **Que parte SI entendes del problema?** Empeza por ahi.
2. **Podes dividirlo en partes mas pequenas?** A veces ayuda resolver pedacitos.
3. **Que fue lo ultimo que funciono?** Volvamos a ese punto.

No te rindas. Cada error es un paso hacia la solucion.
Por donde te gustaria empezar de nuevo?"""


def get_fallback_metacognitive_guidance(prompt: str, flow_id: Optional[str] = None) -> str:
    """Fallback for metacognitive guidance when LLM is unavailable."""
    logger.warning(
        "Using fallback metacognitive guidance (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """Para encarar este tipo de problemas, te sugiero seguir estos pasos:

**Plan de Accion:**

1. **Entender el problema**
   - Que datos de entrada tenes?
   - Que resultado necesitas obtener?

2. **Identificar lo que sabes**
   - Que conceptos ya conoces que podrian servir?
   - Resolviste algo similar antes?

3. **Descomponer en pasos**
   - Cual seria el primer paso mas pequeno?
   - Que necesitas resolver primero?

4. **Probar con ejemplos simples**
   - Que pasaria con un caso muy sencillo?
   - Y con un caso borde (vacio, un solo elemento)?

Podes empezar describiendo que entendes del problema en tus palabras?"""


def get_fallback_example_based(prompt: str, flow_id: Optional[str] = None) -> str:
    """Fallback for example-based response when LLM is unavailable."""
    logger.warning(
        "Using fallback example-based response (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """Te doy un ejemplo analogo para que veas el patron:

**Problema similar:** Imagina que tenes que ordenar cartas de un mazo.

- Primero, necesitas un criterio de orden (por numero? por palo?)
- Luego, comparas de a pares para decidir cual va primero
- Repetis hasta que todo este ordenado

**La pregunta clave:** Como decidis si un elemento va antes que otro?

Ahora pensa en tu problema:
- Cual es tu "criterio de orden"?
- Como compararias dos elementos?

Ves la conexion entre este ejemplo y tu problema?"""


def get_fallback_clarification_request(prompt: str, flow_id: Optional[str] = None) -> str:
    """Fallback for clarification request when LLM is unavailable."""
    logger.warning(
        "Using fallback clarification request (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """Para poder ayudarte mejor, necesito que seas mas especifico:

- Que parte exacta del problema te genera dificultad?
- Que intentaste hasta ahora?
- Que resultado esperabas vs. que obtuviste?

Si tenes codigo, compartilo para poder ver donde esta el problema.
Por favor, reformula tu pregunta con mas detalles."""
