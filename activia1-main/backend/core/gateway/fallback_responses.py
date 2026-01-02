"""
Fallback Response Generators - Circuit breaker responses when LLM is unavailable.

Cortez42: Extracted from ai_gateway.py (1,996 lines)

These fallback responses provide pedagogically valid content when
the LLM service (Ollama) is temporarily unavailable, ensuring the
system remains functional and educational.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_fallback_socratic_response(prompt: str, flow_id: Optional[str] = None) -> str:
    """
    Fallback when Ollama is unavailable - Socratic Response.

    Uses a bank of generic but pedagogically valid guiding questions.

    Args:
        prompt: Student's original prompt (for context logging)
        flow_id: Optional flow ID for tracing

    Returns:
        A pedagogical fallback response with guiding questions
    """
    logger.warning(
        "Using fallback Socratic response (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """⚠️ El sistema de IA está experimentando dificultades temporales, pero puedo ayudarte con estas preguntas guía:

**Para ayudarte mejor, necesito entender tu proceso de pensamiento:**

1. ¿Qué entendés que te están pidiendo resolver?
2. ¿Qué conceptos creés que son relevantes para este problema?
3. ¿Cómo funcionaría una solución ideal?
4. ¿Qué has intentado hasta ahora y qué resultados obtuviste?

💡 **Tip**: Intenta descomponer el problema en partes más pequeñas y manejables.

_Responde estas preguntas y podremos continuar cuando el sistema se recupere._"""


def get_fallback_conceptual_explanation(prompt: str, flow_id: Optional[str] = None) -> str:
    """
    Fallback when Ollama is unavailable - Conceptual Explanation.

    Provides a structure for exploring concepts independently.

    Args:
        prompt: Student's original prompt (for context logging)
        flow_id: Optional flow ID for tracing

    Returns:
        A pedagogical fallback response with concept exploration structure
    """
    logger.warning(
        "Using fallback conceptual explanation (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """⚠️ El sistema de IA está temporalmente fuera de servicio.

**Mientras tanto, aquí tienes una estructura para explorar el concepto:**

**Concepto clave**: [Identifica el concepto central de tu pregunta]

**Principio fundamental**:
- ¿Por qué es importante este concepto en programación?
- ¿Qué problema resuelve?

**Ejemplo simple**:
- Busca en tu material de estudio un ejemplo concreto
- Intenta relacionarlo con situaciones de la vida real

**Aplicación práctica**:
- ¿Cómo lo usarías en un proyecto real?
- ¿Qué ventajas te daría?

📚 **Recomendación**: Consulta la documentación oficial del lenguaje o framework que estás usando.

_El sistema estará disponible nuevamente en breve._"""


def get_fallback_guided_hints(prompt: str, flow_id: Optional[str] = None) -> str:
    """
    Fallback when Ollama is unavailable - Guided Hints.

    Provides general problem-solving strategy.

    Args:
        prompt: Student's original prompt (for context logging)
        flow_id: Optional flow ID for tracing

    Returns:
        A pedagogical fallback response with problem-solving hints
    """
    logger.warning(
        "Using fallback guided hints (LLM unavailable)",
        extra={"flow_id": flow_id} if flow_id else None
    )
    return """⚠️ El asistente de IA está temporalmente inaccesible.

**Aquí tienes una estrategia general de resolución de problemas:**

**Pista 1 - Descomponer**:
- Divide el problema en subproblemas más pequeños
- Resuelve cada parte por separado

**Pista 2 - Estructuras de datos**:
- ¿Qué estructura (lista, diccionario, conjunto) facilitaría la solución?
- ¿Necesitas acceso rápido, orden, o valores únicos?

**Pista 3 - Casos especiales**:
- No olvides casos límite (vacío, un solo elemento, valores extremos)
- Prueba tu lógica con ejemplos simples primero

**Pista 4 - Algoritmo paso a paso**:
- Escribe en pseudocódigo antes de programar
- Verifica cada paso con un ejemplo concreto

**Próximo paso**: Intenta escribir el esqueleto de la solución primero, sin preocuparte por los detalles.

🔧 **Herramientas**: Usa print() o debugger para entender qué está haciendo tu código en cada paso.

_El sistema de IA volverá pronto. Mientras tanto, estos pasos pueden ayudarte a avanzar._"""


def get_blocked_response_message(reason: str) -> str:
    """
    Generate a pedagogical message when a request is blocked.

    Args:
        reason: The reason for blocking the request

    Returns:
        A message explaining why the request was blocked and how to reformulate
    """
    return f"""
He detectado que tu solicitud implica una delegación total del problema a la IA.

{reason}

Para poder ayudarte efectivamente, necesito que:

1. **Expliques tu comprensión del problema**: ¿Qué te piden resolver?
2. **Descompongas el problema**: ¿Qué partes identificas?
3. **Compartas tu plan inicial**: ¿Cómo pensás abordarlo?
4. **Identifiques tus dudas específicas**: ¿Qué parte específica te genera dificultad?

Esto no es una limitación arbitraria: el objetivo es que desarrolles tu capacidad de razonamiento y resolución de problemas, que son competencias fundamentales.

¿Podés reformular tu consulta siguiendo estas pautas?
""".strip()
