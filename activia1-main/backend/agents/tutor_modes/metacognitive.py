"""
Metacognitive Mode Strategy for T-IA-Cog.

Cortez46: Extracted from tutor.py (1,422 lines)

Implements metacognitive reflection approach, helping students
think about their thinking and learning processes.
"""
from typing import List, Dict, Any
import logging

from .base import (
    TutorModeStrategy,
    TutorModeContext,
    TutorResponse,
    TutorMode,
    HelpLevel,
)

logger = logging.getLogger(__name__)


class MetacognitiveStrategy(TutorModeStrategy):
    """
    Metacognitive reflection strategy.

    Promotes self-regulation and reflection on learning process.
    Helps students understand their own cognitive processes.

    Based on:
    - Metacognition theory (Flavell, 1979)
    - Self-regulation (Zimmerman, 2002)
    - Reflective practice (Schon, 1983)
    """

    @property
    def mode(self) -> TutorMode:
        return TutorMode.METACOGNITIVO

    @property
    def pedagogical_intent(self) -> str:
        return "promote_self_reflection"

    async def generate_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """
        Generate metacognitive reflection response.

        First attempts LLM generation, falls back to templates.
        """
        # Try LLM generation first
        if context.llm_provider:
            try:
                logger.info(
                    "Generating metacognitive response with LLM for: %s...",
                    context.student_prompt[:50]
                )
                response = await self._generate_with_llm(context)
                if response:
                    return response
            except Exception as e:
                logger.warning(
                    "LLM metacognitive generation failed, using fallback: %s: %s",
                    type(e).__name__, e,
                    exc_info=True
                )

        # Fallback to template-based response
        return self._generate_template_response(context)

    async def _generate_with_llm(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate metacognitive response using LLM."""
        from ..tutor_rules import InterventionType

        system_prompt = self.get_system_prompt(
            context,
            InterventionType.REFLEXION_METACOGNITIVA
        )

        response_text = await self.generate_with_llm(context, system_prompt)

        if not response_text:
            return None

        return TutorResponse(
            message=response_text,
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            help_level=HelpLevel.MEDIO,
            metadata={
                "cognitive_state": context.cognitive_state,
                "promotes_reflection": True,
                "generated_with_llm": True
            }
        )

    def _generate_template_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate template-based metacognitive response."""
        # Select appropriate template based on cognitive state
        if context.cognitive_state == "frustrado":
            message = self._generate_frustration_template(context)
        elif context.cognitive_state == "bloqueado":
            message = self._generate_blocked_template(context)
        elif context.cognitive_state == "exitoso":
            message = self._generate_success_template(context)
        else:
            message = self._generate_generic_template(context)

        questions = self._generate_reflection_questions(context.cognitive_state)

        return TutorResponse(
            message=message.strip(),
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            help_level=HelpLevel.MEDIO,
            questions=questions,
            metadata={
                "cognitive_state": context.cognitive_state,
                "promotes_reflection": True,
            }
        )

    def _generate_generic_template(self, context: TutorModeContext) -> str:
        """Generic metacognitive reflection template."""
        return """
## Reflexion sobre tu Proceso de Aprendizaje

Antes de continuar, tomemos un momento para reflexionar sobre como estas abordando este problema.

### Sobre tu Proceso

Responde estas preguntas para ti mismo:

1. **Estrategia actual**: Cual es tu enfoque para resolver este problema? Por que elegiste ese camino?

2. **Comprension**: Que partes del problema sientes que entiendes bien? Cuales te generan mas dudas?

3. **Recursos**: Que conocimientos previos estas aplicando? Que necesitas aprender?

4. **Autoevaluacion**: Si tuvieras que explicarle tu solucion a un companero, podrias hacerlo claramente?

### Proximo Paso

Basandote en esta reflexion, que aspecto te gustaria trabajar primero?
Intenta ser especifico sobre que necesitas ayuda.
"""

    def _generate_frustration_template(self, context: TutorModeContext) -> str:
        """Template for frustrated cognitive state."""
        return """
## Gestionando la Frustracion

Es normal sentirse frustrado cuando un problema no cede. Esto es parte del proceso de aprendizaje.

### Pausa y Respira

Antes de continuar, considera:

1. **Reconocer el progreso**: Que has logrado hasta ahora, por mas pequeno que sea?

2. **Identificar el bloqueo**: Cual es el punto exacto donde te estas trabando?

3. **Perspectiva**: Este problema es realmente tan dificil, o quizas necesitas un enfoque diferente?

### Estrategias para Avanzar

- **Simplificar**: Podes resolver una version mas simple del problema primero?
- **Descansar**: A veces alejarse unos minutos ayuda a ver las cosas con claridad
- **Rubber duck**: Explica el problema en voz alta, paso a paso

### Cuando estes listo

Contame: cual es el punto especifico donde te sentis trabado?
No necesitas tener la solucion, solo identificar donde esta la dificultad.
"""

    def _generate_blocked_template(self, context: TutorModeContext) -> str:
        """Template for blocked cognitive state."""
        return """
## Superando el Bloqueo

Estar bloqueado significa que tu mente esta procesando el problema, pero aun no encontro el camino.

### Analiza el Bloqueo

1. **Tipo de bloqueo**: Es conceptual (no entiendo la teoria) o tecnico (no se como implementarlo)?

2. **Ultimo punto claro**: Cual fue el ultimo paso que pudiste dar con confianza?

3. **Hipotesis**: Que creias que iba a funcionar y no funciono?

### Tecnicas de Desbloqueo

- **Divide y venceras**: Cual es el subproblema mas pequeno que podrias resolver?
- **Analogia**: Resolviste antes algo parecido? Que diferencias hay?
- **Reversa**: Empeza desde el resultado esperado y trabaja hacia atras

### Tu Turno

Describime:
1. Que tipo de bloqueo crees que estas experimentando?
2. Cual fue el ultimo paso que te salio bien?
"""

    def _generate_success_template(self, context: TutorModeContext) -> str:
        """Template for successful cognitive state."""
        return """
## Consolidando tu Exito

Excelente! Has logrado avanzar. Ahora es momento de consolidar lo aprendido.

### Reflexion Post-Exito

1. **Que funciono**: Cual fue la clave para resolver el problema?

2. **Proceso**: Que pasos seguiste que podrias replicar en problemas similares?

3. **Obstaculos superados**: Que dificultades encontraste y como las resolviste?

4. **Transferencia**: En que otros contextos podrias aplicar lo que aprendiste?

### Para Futuras Situaciones

- Que harias diferente si enfrentaras un problema similar?
- Que senales te indicaron que ibas por buen camino?

### Cierre

Describime en tus palabras:
1. Cual fue el concepto clave que aprendiste?
2. Que consejo le darias a alguien enfrentando el mismo problema?
"""

    def _generate_reflection_questions(
        self,
        cognitive_state: str
    ) -> List[str]:
        """Generate reflection questions based on cognitive state."""
        base_questions = [
            "Que estas pensando sobre el problema en este momento?",
            "Que estrategia estas usando y por que la elegiste?",
            "Si pudieras empezar de nuevo, que harias diferente?",
        ]

        state_questions = {
            "frustrado": [
                "Que te esta generando frustración especificamente?",
                "Que necesitarias para sentirte menos trabado?",
            ],
            "bloqueado": [
                "Cual es el ultimo punto donde te sentias seguro?",
                "Que informacion te falta para avanzar?",
            ],
            "exitoso": [
                "Que fue lo que te permitio resolver el problema?",
                "Como podrias aplicar esto en otros contextos?",
            ],
            "exploracion": [
                "Que aspectos del problema te resultan mas interesantes?",
                "Que hipotesis estas considerando?",
            ],
            "depuracion": [
                "Que metodologia estas usando para encontrar el error?",
                "Que hipotesis descartaste y por que?",
            ],
        }

        additional = state_questions.get(cognitive_state, [])
        return base_questions + additional


class ClarificationStrategy(TutorModeStrategy):
    """
    Clarification request strategy.

    Used when the prompt is ambiguous and needs more information.
    """

    @property
    def mode(self) -> TutorMode:
        return TutorMode.SOCRATICO

    @property
    def pedagogical_intent(self) -> str:
        return "promote_specificity"

    async def generate_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate clarification request response."""
        message = """
## Necesito Mas Informacion

Para poder ayudarte de manera efectiva, necesito que seas mas especifico:

### Contexto del Problema
- Que parte exacta te genera dificultad?
- Que entendes que tenes que lograr?

### Lo que Intentaste
- Que enfoque probaste?
- Que codigo escribiste hasta ahora?
- Que resultado obtuviste vs. que esperabas?

### Tu Hipotesis
- Que crees que podria estar causando el problema?
- Que soluciones consideraste?

Por favor, reformula tu consulta incluyendo esta informacion.
"""

        return TutorResponse(
            message=message.strip(),
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            metadata={
                "cognitive_state": context.cognitive_state,
                "requires_clarification": True,
            }
        )
