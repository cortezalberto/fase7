"""
Technical Interviewer Simulator (IT-IA) - Conducts technical interviews.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)
"""
from typing import Optional, Dict, Any, List
import logging

from .base import BaseSimulator, SimuladorType

logger = logging.getLogger(__name__)


class TechInterviewerSimulator(BaseSimulator):
    """
    Simulates a Technical Interviewer role.

    Evaluates:
    - Conceptual domain knowledge
    - Algorithmic analysis
    - Technical communication
    - Thinking aloud / structured reasoning
    """

    ROLE_NAME = "Senior Technical Interviewer"
    SYSTEM_PROMPT = """Eres un entrevistador tecnico senior evaluando candidatos.
Tu rol es hacer preguntas conceptuales sobre algoritmos y estructuras de datos,
pedir analisis de complejidad, y evaluar razonamiento en voz alta.
Debes hacer follow-up questions para profundizar, y valorar claridad en las explicaciones.
Evaluas: dominio conceptual, analisis algoritmico, comunicacion tecnica, razonamiento estructurado."""

    COMPETENCIES = [
        "dominio_conceptual",
        "analisis_algoritmico",
        "comunicacion_tecnica",
        "razonamiento_en_voz_alta"
    ]
    EXPECTS = ["explicacion_conceptual", "ejemplos", "analisis_complejidad"]

    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle interaction as Technical Interviewer."""
        validation_error = self.validate_input(student_input)
        if validation_error:
            return validation_error

        context = context or {}

        logger.info(
            "Tech Interviewer processing input",
            extra={
                "flow_id": self.flow_id,
                "input_length": len(student_input),
                "session_id": session_id,
            },
        )

        if self.llm_provider:
            return await self._generate_llm_response(
                student_input=student_input,
                context=context,
                session_id=session_id
            )

        return self.get_fallback_response()

    def get_fallback_response(self) -> Dict[str, Any]:
        """Return fallback response when LLM is unavailable."""
        return {
            "message": """
Pregunta tecnica:

Explicame la diferencia entre complejidad temporal O(n) y O(log n).
Dame un ejemplo concreto de cada caso.

Luego: como optimizarias una busqueda lineal en una lista ordenada?
Justifica tu respuesta con analisis de complejidad.
            """.strip(),
            "role": "tech_interviewer",
            "expects": self.EXPECTS,
            "metadata": {
                "competencies_evaluated": self.COMPETENCIES
            }
        }

    async def generar_pregunta_entrevista(
        self,
        tipo_entrevista: str,
        dificultad: str = "MEDIUM",
        contexto: str = ""
    ) -> str:
        """
        Generate a personalized technical interview question.

        Args:
            tipo_entrevista: CONCEPTUAL, ALGORITHMIC, DESIGN, BEHAVIORAL
            dificultad: EASY, MEDIUM, HARD
            contexto: Additional context (activity, previous questions, etc.)

        Returns:
            str: Question formulated by the interviewer
        """
        if not self.llm_provider:
            return self._get_fallback_question(tipo_entrevista, dificultad)

        try:
            from ...llm.base import LLMMessage, LLMRole

            system_prompt = f"""Eres un entrevistador tecnico senior evaluando candidatos para una posicion de desarrollador.

Tipo de entrevista: {tipo_entrevista}
Nivel de dificultad: {dificultad}

INSTRUCCIONES:
- Genera UNA pregunta especifica y desafiante apropiada para el tipo y dificultad
- Para CONCEPTUAL: pregunta sobre fundamentos, paradigmas, patrones de diseno
- Para ALGORITHMIC: pregunta sobre complejidad, estructuras de datos, algoritmos
- Para DESIGN: pregunta sobre diseno de sistemas, escalabilidad, arquitectura
- Para BEHAVIORAL: pregunta sobre experiencia, decisiones tecnicas pasadas

La pregunta debe ser:
- Clara y especifica
- Apropiada para el nivel ({dificultad})
- Que requiera razonamiento en voz alta
- Que permita evaluar profundidad tecnica

{contexto}

Responde SOLO con la pregunta, sin preambles ni explicaciones."""

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content=f"Genera una pregunta {tipo_entrevista} de nivel {dificultad}")
            ]

            response = await self.llm_provider.generate(
                messages=messages,
                temperature=0.8,
                max_tokens=300,
                is_code_analysis=False
            )

            logger.info(
                "Interview question generated",
                extra={"tipo": tipo_entrevista, "dificultad": dificultad}
            )

            return response.content.strip()

        except Exception as e:
            logger.error("Error generating interview question: %s", e, exc_info=True)
            return self._get_fallback_question(tipo_entrevista, dificultad)

    def _get_fallback_question(self, tipo_entrevista: str, dificultad: str) -> str:
        """Predefined fallback questions."""
        preguntas = {
            "CONCEPTUAL": {
                "EASY": "Que es un algoritmo? Cual es la diferencia entre un array y una lista enlazada?",
                "MEDIUM": "Explica la diferencia entre herencia y composicion. Cuando usarias cada una?",
                "HARD": "Como implementarias un sistema de cache distribuido? Que estrategias de invalidacion considerarias?"
            },
            "ALGORITHMIC": {
                "EASY": "Escribe una funcion que determine si un numero es primo. Cual es su complejidad temporal?",
                "MEDIUM": "Como invertirias una lista enlazada? Describe el proceso paso a paso y analiza la complejidad.",
                "HARD": "Dado un array de enteros, encuentra el subarreglo con la suma maxima (problema de Kadane). Optimiza la solucion."
            },
            "DESIGN": {
                "EASY": "Disena una clase para representar un stack. Que metodos incluirias?",
                "MEDIUM": "Como disenarias un sistema de URL shortener (como bit.ly)? Considera escalabilidad.",
                "HARD": "Disena un sistema de recomendaciones para un ecommerce con millones de usuarios. Que componentes incluirias?"
            },
            "BEHAVIORAL": {
                "EASY": "Contame sobre un proyecto tecnico del que estes orgulloso. Que desafios enfrentaste?",
                "MEDIUM": "Describe una situacion donde tuviste que debuggear un problema complejo. Como lo resolviste?",
                "HARD": "Hablame de una decision tecnica dificil que tomaste. Que alternativas consideraste y por que elegiste esa solucion?"
            }
        }

        return preguntas.get(tipo_entrevista, {}).get(
            dificultad,
            "Explica tu enfoque para resolver problemas tecnicos complejos."
        )

    async def evaluar_respuesta_entrevista(
        self,
        pregunta: str,
        respuesta: str,
        tipo_entrevista: str
    ) -> Dict[str, Any]:
        """
        Evaluate student's answer to an interview question.

        Returns:
            Dict with clarity_score, technical_accuracy, thinking_aloud,
            key_points_covered, feedback
        """
        if not self.llm_provider:
            return self._evaluate_response_heuristic(respuesta)

        try:
            from ...llm.base import LLMMessage, LLMRole
            import json

            system_prompt = f"""Eres un entrevistador tecnico senior evaluando una respuesta.

Pregunta formulada: {pregunta}
Tipo de entrevista: {tipo_entrevista}

EVALUA la respuesta del candidato en estas dimensiones:

1. **Claridad** (0.0-1.0): Se explica de forma clara y estructurada?
2. **Precision tecnica** (0.0-1.0): Es tecnicamente correcta?
3. **Razonamiento en voz alta** (true/false): Explica su proceso de pensamiento?
4. **Puntos clave cubiertos**: Lista de conceptos importantes mencionados

Responde SOLO en formato JSON:
{{
  "clarity_score": 0.0-1.0,
  "technical_accuracy": 0.0-1.0,
  "thinking_aloud": true/false,
  "key_points_covered": ["punto1", "punto2", ...],
  "feedback": "Feedback breve y constructivo (2-3 oraciones)"
}}"""

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content=f"Respuesta del candidato:\n{respuesta}")
            ]

            response = await self.llm_provider.generate(
                messages=messages,
                temperature=0.3,
                max_tokens=400,
                is_code_analysis=False
            )

            try:
                evaluation = json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM response as JSON")
                return self._evaluate_response_heuristic(respuesta)

            logger.info(
                "Interview response evaluated",
                extra={
                    "clarity": evaluation.get("clarity_score"),
                    "accuracy": evaluation.get("technical_accuracy")
                }
            )

            return evaluation

        except Exception as e:
            logger.error("Error evaluating interview response: %s", e, exc_info=True)
            return self._evaluate_response_heuristic(respuesta)

    def _evaluate_response_heuristic(self, respuesta: str) -> Dict[str, Any]:
        """Simple heuristic evaluation as fallback."""
        words = respuesta.split()
        length = len(words)

        clarity = min(length / 50.0, 1.0) if length > 10 else 0.3
        has_technical = any(term in respuesta.lower() for term in [
            "complejidad", "algoritmo", "estructura", "patron", "o(n)", "o(log n)"
        ])
        technical_accuracy = 0.7 if has_technical else 0.4
        thinking_aloud = any(word in respuesta.lower() for word in ["primero", "luego", "entonces", "porque"])

        return {
            "clarity_score": clarity,
            "technical_accuracy": technical_accuracy,
            "thinking_aloud": thinking_aloud,
            "key_points_covered": ["respuesta proporcionada"],
            "feedback": "Evaluacion basica. Para evaluacion completa, configure un LLM provider."
        }

    async def generar_evaluacion_entrevista(
        self,
        preguntas: List[Dict[str, Any]],
        respuestas: List[Dict[str, Any]],
        tipo_entrevista: str
    ) -> Dict[str, Any]:
        """
        Generate final evaluation of the complete interview.

        Returns:
            Dict with overall_score, breakdown, feedback
        """
        if not respuestas:
            return {
                "overall_score": 0.0,
                "breakdown": {},
                "feedback": "No se registraron respuestas en la entrevista."
            }

        # Calculate average scores (scale 0-1 internally, convert to 0-10 for output)
        # FIX Cortez73 (HIGH-005): Normalize scores to 0-10 scale for consistency
        clarity_scores = [r.get("evaluation", {}).get("clarity_score", 0.5) for r in respuestas]
        accuracy_scores = [r.get("evaluation", {}).get("technical_accuracy", 0.5) for r in respuestas]
        thinking_aloud_count = sum(1 for r in respuestas if r.get("evaluation", {}).get("thinking_aloud", False))

        avg_clarity = sum(clarity_scores) / len(clarity_scores)
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        communication_score = min((thinking_aloud_count / len(respuestas)) * 1.2, 1.0)

        # Weighted global score (0-1 scale internally)
        overall_score_raw = (avg_clarity * 0.3 + avg_accuracy * 0.5 + communication_score * 0.2)

        # FIX Cortez73: Convert to 0-10 scale for consistency with EvaluationDB and evaluator.py
        overall_score = overall_score_raw * 10

        breakdown = {
            "clarity": round(avg_clarity * 10, 1),  # Now 0-10
            "technical_accuracy": round(avg_accuracy * 10, 1),  # Now 0-10
            "communication": round(communication_score * 10, 1),  # Now 0-10
            "thinking_aloud_percentage": round((thinking_aloud_count / len(respuestas)) * 100, 1)
        }

        feedback = self._generate_fallback_feedback(overall_score, breakdown)

        if self.llm_provider:
            try:
                from ...llm.base import LLMMessage, LLMRole

                # FIX Cortez73: Update prompt to use 0-10 scale
                system_prompt = f"""Eres un entrevistador tecnico senior proporcionando feedback final.

Tipo de entrevista: {tipo_entrevista}
Numero de preguntas: {len(preguntas)}
Score global: {overall_score:.1f} / 10

Scores por dimension (escala 0-10):
- Claridad: {breakdown['clarity']:.1f}/10
- Precision tecnica: {breakdown['technical_accuracy']:.1f}/10
- Comunicacion: {breakdown['communication']:.1f}/10

Genera un feedback narrativo (4-5 oraciones) que:
1. Resuma el desempeno general
2. Destaque fortalezas especificas
3. Identifique areas de mejora
4. Sea constructivo y motivador

Responde SOLO con el feedback, sin formato JSON."""

                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                    LLMMessage(role=LLMRole.USER, content="Genera el feedback final de la entrevista")
                ]

                response = await self.llm_provider.generate(
                    messages=messages,
                    temperature=0.6,
                    max_tokens=300,
                    is_code_analysis=False
                )

                feedback = response.content.strip()

            except Exception as e:
                logger.error("Error generating final feedback: %s", e, exc_info=True)

        logger.info(
            "Final interview evaluation generated",
            extra={"overall_score": overall_score, "num_questions": len(preguntas)}
        )

        return {
            "overall_score": round(overall_score, 2),
            "breakdown": breakdown,
            "feedback": feedback
        }

    def _generate_fallback_feedback(self, overall_score: float, breakdown: Dict[str, float]) -> str:
        """Generate basic feedback without LLM.

        Args:
            overall_score: Score on 0-10 scale (FIX Cortez73)
            breakdown: Score breakdown with 0-10 values
        """
        # FIX Cortez73: Update thresholds for 0-10 scale
        if overall_score >= 8.0:
            level = "Excelente desempeno"
        elif overall_score >= 6.0:
            level = "Buen desempeno"
        elif overall_score >= 4.0:
            level = "Desempeno aceptable"
        else:
            level = "Necesita mejorar"

        return f"""{level} en la entrevista tecnica.
Claridad de comunicacion: {breakdown.get('clarity', 0):.1f}/10.
Precision tecnica: {breakdown.get('technical_accuracy', 0):.1f}/10.
Se recomienda practicar razonamiento en voz alta y profundizar conceptos tecnicos."""
