"""
Guided/Hints Mode Strategy for T-IA-Cog.

Cortez46: Extracted from tutor.py (1,422 lines)

Implements graduated hints with cognitive scaffolding approach.
Provides adaptive scaffolding based on student history.
"""
from typing import List, Dict, Any, Optional
import logging

from .base import (
    TutorModeStrategy,
    TutorModeContext,
    TutorResponse,
    TutorMode,
    HelpLevel,
)

logger = logging.getLogger(__name__)


class GuidedStrategy(TutorModeStrategy):
    """
    Guided hints strategy with cognitive scaffolding.

    Provides graduated hints without revealing complete solutions.
    Adapts help level based on student history and AI involvement.

    Levels:
    - Level 1 (MINIMO): Socratic orienting questions
    - Level 2 (BAJO): General conceptual hints
    - Level 3 (MEDIO): Detailed hints + high-level pseudocode
    - Level 4 (ALTO): Conceptual fragments + detailed strategy

    Based on:
    - Scaffolding theory (Wood, Bruner & Ross, 1976)
    - Zone of Proximal Development (Vygotsky)
    - Adaptive learning systems
    """

    @property
    def mode(self) -> TutorMode:
        return TutorMode.GUIADO

    @property
    def pedagogical_intent(self) -> str:
        return "scaffolding"

    async def generate_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """
        Generate guided hints response with adaptive scaffolding.

        First attempts LLM generation, falls back to templates.
        """
        # Try LLM generation first
        if context.llm_provider:
            try:
                logger.info(
                    "Generating guided hints with LLM for: %s...",
                    context.student_prompt[:50]
                )
                response = await self._generate_with_llm(context)
                if response:
                    return response
            except Exception as e:
                logger.warning(
                    "LLM hints generation failed, using fallback: %s: %s",
                    type(e).__name__, e,
                    exc_info=True
                )

        # Fallback to template-based response
        return self._generate_template_response(context)

    async def _generate_with_llm(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate guided hints using LLM."""
        from ..tutor_rules import InterventionType

        help_level = self._determine_adaptive_help_level(context)

        system_prompt = self.get_system_prompt(
            context,
            InterventionType.PISTAS_GUIADAS
        )

        # Add previous hints context to prompt
        previous_hints = self._count_previous_hints(context.student_history)
        enhanced_prompt = f"""
{system_prompt}

Contexto adicional:
- Nivel de ayuda actual: {help_level.value}
- Pistas previas recibidas: {previous_hints}
- Estado cognitivo: {context.cognitive_state}
"""

        response_text = await self.generate_with_llm(context, enhanced_prompt)

        if not response_text:
            return None

        return TutorResponse(
            message=response_text,
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            requires_justification=True,
            help_level=help_level,
            metadata={
                "cognitive_state": context.cognitive_state,
                "generated_with_llm": True
            }
        )

    def _generate_template_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate template-based guided hints response."""
        # Determine adaptive help level
        help_level = self._determine_adaptive_help_level(context)

        # Count previous hints
        previous_hints_count = self._count_previous_hints(context.student_history)

        # Generate hints based on level
        hints = self._generate_hints_by_level(
            help_level,
            context.student_prompt,
            context.cognitive_state
        )

        # Build message
        message = f"""
## Pistas Graduadas - Nivel {help_level.value.upper()}

{self._format_hints_message(hints, help_level)}

---

{self._generate_followup_question(help_level, previous_hints_count)}
"""

        return TutorResponse(
            message=message.strip(),
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            requires_justification=True,
            help_level=help_level,
            hints_provided=hints,
            hints_count=len(hints),
            previous_hints_count=previous_hints_count,
            metadata={
                "cognitive_state": context.cognitive_state,
                "provides_code": False,
                "provides_pseudocode": help_level in [HelpLevel.MEDIO, HelpLevel.ALTO],
                "adaptive_level": help_level.value,
            }
        )

    def _determine_adaptive_help_level(
        self,
        context: TutorModeContext,
    ) -> HelpLevel:
        """
        Determine help level adaptively based on:
        1. Strategy suggested by CRPE
        2. History of hints received (reduce detail if many)
        3. Accumulated AI involvement level
        """
        # Base level from strategy
        strategy_level = context.strategy.get("help_level", HelpLevel.MEDIO)
        if isinstance(strategy_level, str):
            strategy_level = HelpLevel(strategy_level)

        if not context.student_history:
            return strategy_level

        # Count previous hints
        hints_received = self._count_previous_hints(context.student_history)

        # If too many hints (>5), reduce level to encourage autonomy
        if hints_received > 5:
            if strategy_level == HelpLevel.ALTO:
                return HelpLevel.MEDIO
            elif strategy_level == HelpLevel.MEDIO:
                return HelpLevel.BAJO

        # Calculate average AI involvement
        try:
            avg_ai_involvement = sum(
                getattr(t, 'ai_involvement', 0.5) for t in context.student_history
            ) / len(context.student_history)
        except (TypeError, ZeroDivisionError):
            avg_ai_involvement = 0.5

        # If high dependency (>0.6), reduce help level
        if avg_ai_involvement > 0.6:
            if strategy_level == HelpLevel.ALTO:
                return HelpLevel.MEDIO
            elif strategy_level == HelpLevel.MEDIO:
                return HelpLevel.BAJO

        return strategy_level

    def _count_previous_hints(
        self,
        student_history: Optional[List[Any]]
    ) -> int:
        """Count how many hints the student has received."""
        if not student_history:
            return 0

        count = 0
        for trace in student_history:
            try:
                metadata = getattr(trace, 'metadata', {}) or {}
                response_metadata = metadata.get("response_metadata", {})
                if "hints_provided" in response_metadata:
                    count += 1
            except (AttributeError, TypeError):
                continue

        return count

    def _generate_hints_by_level(
        self,
        level: HelpLevel,
        prompt: str,
        cognitive_state: str
    ) -> List[Dict[str, str]]:
        """Generate hints based on help level."""
        if level == HelpLevel.MINIMO:
            return self._generate_level1_hints(prompt, cognitive_state)
        elif level == HelpLevel.BAJO:
            return self._generate_level2_hints(prompt, cognitive_state)
        elif level == HelpLevel.MEDIO:
            return self._generate_level3_hints(prompt, cognitive_state)
        else:  # ALTO
            return self._generate_level4_hints(prompt, cognitive_state)

    def _generate_level1_hints(
        self,
        prompt: str,
        cognitive_state: str
    ) -> List[Dict[str, str]]:
        """Level 1 - MINIMO: Only Socratic orienting questions."""
        return [
            {
                "level": 1,
                "type": "question",
                "content": "Que pasos crees que son necesarios para resolver este problema?"
            },
            {
                "level": 1,
                "type": "question",
                "content": "Que conceptos o estructuras de datos podrian ser relevantes aqui?"
            },
            {
                "level": 1,
                "type": "question",
                "content": "Podes describir con tus palabras como funcionaria una solucion ideal?"
            }
        ]

    def _generate_level2_hints(
        self,
        prompt: str,
        cognitive_state: str
    ) -> List[Dict[str, str]]:
        """Level 2 - BAJO: General conceptual hints."""
        return [
            {
                "level": 2,
                "type": "conceptual",
                "content": "Pensa en descomponer el problema en partes mas pequenas. Cuales serian esas partes?"
            },
            {
                "level": 2,
                "type": "conceptual",
                "content": "Considera que estructura de datos se adapta mejor a las operaciones que necesitas realizar."
            },
            {
                "level": 2,
                "type": "reflection",
                "content": "Que casos especiales o de borde deberias tener en cuenta?"
            }
        ]

    def _generate_level3_hints(
        self,
        prompt: str,
        cognitive_state: str
    ) -> List[Dict[str, str]]:
        """Level 3 - MEDIO: Hints with detail + high-level pseudocode."""
        return [
            {
                "level": 3,
                "type": "decomposition",
                "content": "Dividi el problema en estas etapas: 1) Inicializacion, 2) Operacion principal, 3) Validacion"
            },
            {
                "level": 3,
                "type": "strategy",
                "content": "Una estrategia comun es usar [concepto general] para gestionar [aspecto del problema]"
            },
            {
                "level": 3,
                "type": "pseudocode",
                "content": """```
// Estructura general (alto nivel)
funcion resolver():
    // Paso 1: Preparar datos
    // Paso 2: Procesar elemento por elemento
    // Paso 3: Retornar resultado
```"""
            }
        ]

    def _generate_level4_hints(
        self,
        prompt: str,
        cognitive_state: str
    ) -> List[Dict[str, str]]:
        """Level 4 - ALTO: Conceptual fragments + detailed strategy."""
        return [
            {
                "level": 4,
                "type": "detailed_strategy",
                "content": "Considera este enfoque: [descripcion detallada de estrategia sin codigo especifico]"
            },
            {
                "level": 4,
                "type": "pattern",
                "content": "Un patron util aqui es [nombre del patron], que consiste en [explicacion conceptual]"
            },
            {
                "level": 4,
                "type": "conceptual_fragment",
                "content": """Para gestionar [aspecto especifico]:
- Opcion A: [ventajas y desventajas]
- Opcion B: [ventajas y desventajas]
Cual elegirias y por que?"""
            }
        ]

    def _format_hints_message(
        self,
        hints: List[Dict[str, str]],
        level: HelpLevel
    ) -> str:
        """Format hints for display."""
        icons = {
            "question": "?",
            "conceptual": "*",
            "reflection": "~",
            "decomposition": "#",
            "strategy": "->",
            "pseudocode": "<>",
            "detailed_strategy": "=>",
            "pattern": "[]",
            "conceptual_fragment": "()"
        }

        formatted = []
        for i, hint in enumerate(hints, 1):
            icon = icons.get(hint["type"], "-")
            hint_type = hint["type"].replace("_", " ").title()
            formatted.append(f"### {icon} Pista {i}: {hint_type}\n{hint['content']}")

        return "\n\n".join(formatted)

    def _generate_followup_question(
        self,
        level: HelpLevel,
        hints_count: int
    ) -> str:
        """Generate follow-up question based on context."""
        if hints_count > 5:
            return """**Nota**: Has recibido varias pistas ya. Es momento de que intentes
avanzar de forma mas autonoma. Que vas a hacer con la informacion que tenes?"""
        elif level == HelpLevel.MINIMO:
            return """**Pregunta para vos**: Responde primero estas preguntas antes de
solicitar mas ayuda. La clave esta en tu razonamiento, no en la respuesta de la IA."""
        elif level in [HelpLevel.MEDIO, HelpLevel.ALTO]:
            return """**Pregunta para vos**: Basandote en estas pistas, cual seria tu
proximo paso concreto? Que decision de diseno tomarias y **por que**?"""
        else:
            return """**Proximo paso**: Intenta formular un plan basandote en estas pistas.
Que harias primero?"""
