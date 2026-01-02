"""
Socratic Mode Strategy for T-IA-Cog.

Cortez46: Extracted from tutor.py (1,422 lines)

Implements Socratic questioning approach to promote student reasoning
and problem decomposition skills.
"""
from typing import List
import logging

from .base import (
    TutorModeStrategy,
    TutorModeContext,
    TutorResponse,
    TutorMode,
    HelpLevel,
)

logger = logging.getLogger(__name__)


class SocraticStrategy(TutorModeStrategy):
    """
    Socratic questioning strategy.

    Promotes reasoning through carefully crafted questions that guide
    the student to discover solutions themselves.

    Based on:
    - Socratic method (guided discovery)
    - Problem decomposition techniques
    - Metacognitive questioning
    """

    @property
    def mode(self) -> TutorMode:
        return TutorMode.SOCRATICO

    @property
    def pedagogical_intent(self) -> str:
        return "promote_decomposition_and_planning"

    async def generate_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """
        Generate Socratic response with guiding questions.

        First attempts LLM generation, falls back to templates.
        """
        # Try LLM generation first
        if context.llm_provider:
            try:
                logger.info(
                    "Attempting Socratic response with LLM for: %s...",
                    context.student_prompt[:50]
                )
                response = await self._generate_with_llm(context)
                if response:
                    return response
            except Exception as e:
                logger.warning(
                    "LLM Socratic generation failed, using fallback: %s",
                    e
                )

        # Fallback to template-based response
        return self._generate_template_response(context)

    async def _generate_with_llm(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate Socratic response using LLM."""
        from ..tutor_rules import InterventionType

        system_prompt = self.get_system_prompt(
            context,
            InterventionType.PREGUNTA_SOCRATICA
        )

        response_text = await self.generate_with_llm(context, system_prompt)

        if not response_text:
            return None

        return TutorResponse(
            message=response_text,
            mode=self.mode,
            pedagogical_intent="socratic_questioning",
            requires_student_response=True,
            help_level=context.strategy.get("help_level", HelpLevel.BAJO),
            metadata={
                "cognitive_state": context.cognitive_state,
                "generated_with_llm": True
            }
        )

    def _generate_template_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate template-based Socratic response."""
        questions = self._formulate_socratic_questions(
            context.student_prompt,
            context.cognitive_state
        )

        message = f"""
## Analisis del Problema

Para guiarte efectivamente, necesito comprender tu proceso de pensamiento.
Por favor, responde las siguientes preguntas:

{self._format_questions(questions)}

**Importante**: No estoy evitando ayudarte. Estas preguntas son fundamentales
para que desarrolles tu capacidad de descomposicion y analisis de problemas,
que es mas valiosa que cualquier solucion especifica.

Una vez que compartas tu razonamiento, podre orientarte de manera precisa.
"""

        return TutorResponse(
            message=message.strip(),
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            help_level=HelpLevel.MINIMO,
            questions=questions,
            metadata={
                "cognitive_state": context.cognitive_state,
                "help_level": HelpLevel.MINIMO,
            }
        )

    def _formulate_socratic_questions(
        self,
        prompt: str,
        cognitive_state: str
    ) -> List[str]:
        """
        Formula Socratic questions adapted to context.

        Args:
            prompt: Student's question
            cognitive_state: Current cognitive state

        Returns:
            List of Socratic questions
        """
        base_questions = [
            "Que entendes que te estan pidiendo resolver en este problema?",
            "Que conceptos o estructuras de datos consideras relevantes?",
            "Podes describir con tus palabras como funcionaria una solucion?",
            "Que intentaste hasta ahora? Que resultado obtuviste?",
        ]

        # Adapt based on cognitive state
        if cognitive_state == "exploracion":
            base_questions.insert(
                1,
                "Que partes del enunciado te resultan claras y cuales confusas?"
            )
        elif cognitive_state == "depuracion":
            base_questions = [
                "Que comportamiento esperabas y que obtuviste?",
                "En que punto especifico falla tu codigo?",
                "Que hipotesis tenes sobre la causa del error?",
                "Que pruebas hiciste para verificar tu hipotesis?",
            ]
        elif cognitive_state == "implementacion":
            base_questions = [
                "Cual es el paso actual en el que te encontras?",
                "Que decision de diseno estas considerando?",
                "Cuales son las ventajas y desventajas de cada opcion?",
                "Como probarias que tu implementacion funciona correctamente?",
            ]

        return base_questions

    def _format_questions(self, questions: List[str]) -> str:
        """Format list of questions for display."""
        return "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
