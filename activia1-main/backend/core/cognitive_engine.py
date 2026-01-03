"""
Motor de Razonamiento Cognitivo-Pedagógico (CRPE)
Componente central del ai-gateway que coordina todos los submodelos
"""
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from ..models.trace import CognitiveTrace, InteractionType, CognitiveState


class AgentMode(str, Enum):
    """
    Modos operativos del motor cognitivo.

    IMPORTANTE: Valores en MAYÚSCULAS para consistencia con API y database.
    Se unificó con SessionMode (que fue deprecado) para evitar duplicación.
    """
    TUTOR = "TUTOR"  # T-IA-Cog
    EVALUATOR = "EVALUATOR"  # E-IA-Proc
    SIMULATOR = "SIMULATOR"  # S-IA-X
    RISK_ANALYST = "RISK_ANALYST"  # AR-IA
    GOVERNANCE = "GOVERNANCE"  # GOV-IA
    PRACTICE = "PRACTICE"  # Modo práctica libre (sin asistencia activa)


# NOTE: CognitiveState moved to models.trace to avoid circular dependencies
# (repositories shouldn't import from core). Re-exported here for backward compatibility.
# New code should import directly from models.trace


class CognitiveReasoningEngine:
    """
    Motor de Razonamiento Cognitivo-Pedagógico (CRPE)

    Coordina la interacción entre todos los submodelos AI-Native y determina
    el comportamiento del sistema según el contexto pedagógico.
    """

    def __init__(self, llm_provider=None, config: Optional[Dict[str, Any]] = None):
        self.llm_provider = llm_provider
        self.config = config or {}
        self.current_mode: AgentMode = AgentMode.TUTOR
        self.current_state: Optional[CognitiveState] = None

        # Políticas pedagógicas configurables
        self.pedagogical_policies = {
            "max_help_level": self.config.get("max_help_level", 0.7),  # 0-1
            "require_justification": self.config.get("require_justification", True),
            "block_total_delegation": self.config.get("block_total_delegation", True),
            "adaptive_difficulty": self.config.get("adaptive_difficulty", True),
        }

    def classify_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clasifica el prompt del estudiante y determina el estado cognitivo.

        FIX Cortez64: Ampliación significativa de señales de detección para
        mejorar la inferencia del estado cognitivo y tipo de respuesta.

        Args:
            prompt: El prompt enviado por el estudiante
            context: Contexto de la actividad

        Returns:
            Diccionario con clasificación y metadata
        """
        prompt_lower = prompt.lower()

        # ============================================================
        # 1. DETECCIÓN DE DELEGACIÓN TOTAL (prioridad máxima)
        # ============================================================
        delegation_signals = [
            # Señales originales
            "dame el código completo",
            "hacé todo",
            "resolvelo por mí",
            "código entero",
            "implementa todo",
            # Nuevas señales - solicitud directa de código
            "hazme el programa",
            "escribí el código",
            "escribime el código",
            "pasame la solución",
            "pasame el código",
            "dame la solución",
            "necesito el código funcionando",
            "código que funcione",
            "dame algo que funcione",
            # Nuevas señales - delegación explícita
            "terminá esto por mí",
            "hacelo vos",
            "hacelo por mí",
            "no quiero pensar",
            "solo dame la respuesta",
            "dame la respuesta",
            "copiá y pegá",
            "resolvé esto",
            "completá el ejercicio",
            "completá el código",
            # Nuevas señales - urgencia/presión
            "necesito que me lo hagas",
            "solo necesito el código",
            "dame todo el código",
            "quiero el código completo",
        ]
        is_total_delegation = any(signal in prompt_lower for signal in delegation_signals)

        # ============================================================
        # 2. DETECCIÓN DE FRUSTRACIÓN / ESTANCAMIENTO
        # ============================================================
        frustration_signals = [
            "no me sale",
            "me rindo",
            "esto es imposible",
            "llevo horas",
            "ya intenté todo",
            "estoy perdido",
            "no avanzo",
            "me trabé",
            "estoy atascado",
            "no puedo más",
            "es muy difícil",
            "no sirvo para esto",
            "esto no funciona",
            "no funciona nada",
            "me frustro",
            "estoy frustrado",
            "no sé qué más hacer",
            "ya probé de todo",
            "sigo sin entender",
            "cada vez peor",
        ]
        is_frustrated = any(signal in prompt_lower for signal in frustration_signals)

        # ============================================================
        # 3. DETECCIÓN DE SOLICITUD DE VALIDACIÓN / VERIFICACIÓN
        # ============================================================
        validation_signals = [
            # Señales originales
            "funciona",
            "correcto",
            # Nuevas señales - verificación de código
            "está bien esto",
            "es correcto",
            "así está bien",
            "está bien así",
            "revisá mi código",
            "chequeá esto",
            "mirá si funciona",
            "validá mi solución",
            "tiene errores",
            "qué le falta",
            "qué está mal",
            "por qué no funciona",
            "por qué falla",
            "dónde está el error",
            "encontrá el error",
            "revisame esto",
            "está correcto esto",
            "lo hice bien",
            "me quedó bien",
        ]
        requests_validation = any(signal in prompt_lower for signal in validation_signals)

        # ============================================================
        # 4. DETECCIÓN DE CONFUSIÓN CONCEPTUAL
        # ============================================================
        confusion_signals = [
            # Señales originales
            "no entiendo",
            "no sé",
            # Nuevas señales - confusión
            "no me queda claro",
            "me confunde",
            "cuál es la diferencia",
            "es lo mismo que",
            "para qué sirve",
            "cuándo uso",
            "en qué casos",
            "me perdí",
            "no sigo",
            "no capto",
            "no comprendo",
            "qué significa",
            "qué quiere decir",
            "a qué se refiere",
            "cómo es eso",
            "no veo la relación",
            "qué tiene que ver",
        ]
        is_confused = any(signal in prompt_lower for signal in confusion_signals)

        # ============================================================
        # 5. DETECCIÓN DE SOLICITUD DE EJEMPLOS
        # ============================================================
        example_signals = [
            "dame un ejemplo",
            "mostrame un ejemplo",
            "mostrame cómo",
            "un caso práctico",
            "cómo sería",
            "podés ejemplificar",
            "algo similar",
            "ejemplo de",
            "un ejemplo",
            "ejemplos de",
            "por ejemplo",
            "cómo se vería",
            "cómo quedaría",
            "a ver un ejemplo",
            "necesito un ejemplo",
        ]
        requests_example = any(signal in prompt_lower for signal in example_signals)

        # ============================================================
        # 6. DETECCIÓN DE METACOGNICIÓN / REFLEXIÓN
        # ============================================================
        metacognition_signals = [
            "qué debería pensar",
            "por dónde empiezo",
            "qué pasos sigo",
            "cómo organizo",
            "qué me falta entender",
            "qué estoy haciendo mal",
            "cómo debería encarar",
            "cuál es el enfoque",
            "cómo pienso esto",
            "qué estrategia uso",
            "cómo lo encaro",
            "por dónde arranco",
            "cuál es el primer paso",
            "cómo me organizo",
            "qué orden sigo",
        ]
        is_metacognitive = any(signal in prompt_lower for signal in metacognition_signals)

        # ============================================================
        # 7. DETECCIÓN DE TIPO DE SOLICITUD GENERAL
        # ============================================================
        question_signals = [
            "cómo", "por qué", "qué", "cuál", "explica", "ayuda",
            "dónde", "cuándo", "quién", "podrías", "podés", "puedo"
        ]
        is_question = any(signal in prompt_lower for signal in question_signals)

        # ============================================================
        # 8. DETECCIÓN DE SOLICITUD DE EXPLICACIÓN
        # ============================================================
        explanation_signals = [
            "explica", "no entiendo", "ayuda a entender",
            "por qué", "qué es", "qué son",
            "explicame", "explicá", "contame",
            "decime qué es", "qué significa",
            "cómo funciona", "para qué es",
        ]
        requests_explanation = any(signal in prompt_lower for signal in explanation_signals)

        # ============================================================
        # 9. DETECCIÓN DE OPTIMIZACIÓN / MEJORA
        # ============================================================
        optimization_signals = [
            "cómo mejoro",
            "es eficiente",
            "hay forma más rápida",
            "se puede optimizar",
            "cómo lo hago más rápido",
            "es óptimo",
            "mejor manera",
            "hay otra forma",
            "alternativa más",
            "se puede mejorar",
        ]
        requests_optimization = any(signal in prompt_lower for signal in optimization_signals)

        # ============================================================
        # 10. DETECCIÓN DE COMPARACIÓN
        # ============================================================
        comparison_signals = [
            "qué es mejor",
            "cuál conviene",
            "diferencia entre",
            "comparar",
            "versus",
            "o es mejor",
            "qué elegir",
            "cuál usar",
            "cuál es más",
        ]
        requests_comparison = any(signal in prompt_lower for signal in comparison_signals)

        # ============================================================
        # DETERMINAR ESTADO COGNITIVO (orden de prioridad)
        # ============================================================
        if is_frustrated:
            cognitive_state = CognitiveState.ATASCADO
        elif is_confused or "no entiendo" in prompt_lower or "no sé" in prompt_lower:
            cognitive_state = CognitiveState.EXPLORACION
        elif is_metacognitive or "por dónde empiezo" in prompt_lower:
            cognitive_state = CognitiveState.PLANIFICACION
        elif "cómo implemento" in prompt_lower or "cómo hago" in prompt_lower:
            cognitive_state = CognitiveState.PLANIFICACION
        elif requests_validation or "error" in prompt_lower or "bug" in prompt_lower or "falla" in prompt_lower:
            cognitive_state = CognitiveState.DEPURACION
        elif requests_optimization:
            cognitive_state = CognitiveState.VALIDACION
        elif "funciona" in prompt_lower or "correcto" in prompt_lower:
            cognitive_state = CognitiveState.VALIDACION
        else:
            cognitive_state = CognitiveState.IMPLEMENTACION

        # ============================================================
        # CONSTRUIR RESULTADO CON METADATA ENRIQUECIDA
        # ============================================================
        return {
            # Flags principales
            "is_total_delegation": is_total_delegation,
            "is_question": is_question,
            "requests_explanation": requests_explanation,
            "cognitive_state": cognitive_state,
            "requires_intervention": is_total_delegation and self.pedagogical_policies["block_total_delegation"],
            # Nuevos flags (FIX Cortez64)
            "is_frustrated": is_frustrated,
            "is_confused": is_confused,
            "requests_validation": requests_validation,
            "requests_example": requests_example,
            "is_metacognitive": is_metacognitive,
            "requests_optimization": requests_optimization,
            "requests_comparison": requests_comparison,
            # Tipo de respuesta sugerida
            "suggested_response_type": self._determine_response_type(
                is_total_delegation, is_question, requests_explanation,
                is_frustrated, is_metacognitive, requests_example
            )
        }

    def _determine_response_type(
        self,
        is_delegation: bool,
        is_question: bool,
        requests_explanation: bool,
        is_frustrated: bool = False,
        is_metacognitive: bool = False,
        requests_example: bool = False
    ) -> str:
        """
        Determina el tipo de respuesta apropiada según la clasificación del prompt.

        FIX Cortez64: Ampliado con nuevos tipos de respuesta para cubrir
        más casos pedagógicos (frustración, metacognición, ejemplos).

        Args:
            is_delegation: Si el estudiante intenta delegar completamente
            is_question: Si es una pregunta general
            requests_explanation: Si pide explicación conceptual
            is_frustrated: Si muestra señales de frustración (FIX Cortez64)
            is_metacognitive: Si hace preguntas metacognitivas (FIX Cortez64)
            requests_example: Si pide ejemplos específicos (FIX Cortez64)

        Returns:
            Tipo de respuesta: socratic_questioning, conceptual_explanation,
            guided_hints, empathetic_support, metacognitive_guidance,
            example_based, clarification_request
        """
        import logging
        logger = logging.getLogger(__name__)
        # FIX Cortez36: Use lazy logging formatting
        logger.info(
            "Determining response type: delegation=%s, question=%s, explanation=%s, "
            "frustrated=%s, metacognitive=%s, example=%s",
            is_delegation, is_question, requests_explanation,
            is_frustrated, is_metacognitive, requests_example
        )

        # Prioridad 1: Delegación total -> Preguntas socráticas (bloqueo pedagógico)
        if is_delegation:
            return "socratic_questioning"

        # Prioridad 2: Frustración -> Respuesta empática + pistas más directas
        if is_frustrated:
            return "empathetic_support"

        # Prioridad 3: Metacognición -> Guía de proceso de pensamiento
        if is_metacognitive:
            return "metacognitive_guidance"

        # Prioridad 4: Solicitud de ejemplos -> Respuesta basada en ejemplos
        if requests_example:
            return "example_based"

        # Prioridad 5: Solicitud de explicación -> Explicación conceptual
        if requests_explanation:
            return "conceptual_explanation"

        # Prioridad 6: Pregunta general -> Pistas guiadas
        if is_question:
            return "guided_hints"

        # Default: Solicitar clarificación
        return "clarification_request"

    def should_block_response(self, classification: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Determina si debe bloquearse la respuesta según políticas de gobernanza

        Returns:
            (should_block, reason)
        """
        if classification["is_total_delegation"] and self.pedagogical_policies["block_total_delegation"]:
            return True, "Delegación total detectada. Se requiere descomposición del problema."

        return False, None

    def generate_pedagogical_response_strategy(
        self,
        prompt: str,
        classification: Dict[str, Any],
        student_history: Optional[List[CognitiveTrace]] = None
    ) -> Dict[str, Any]:
        """
        Genera la estrategia de respuesta pedagógica.

        FIX Cortez64: Ampliado con estrategias para nuevos tipos de respuesta
        (empathetic_support, metacognitive_guidance, example_based).

        Args:
            prompt: Prompt del estudiante
            classification: Clasificación del prompt
            student_history: Historial de trazas del estudiante

        Returns:
            Estrategia de respuesta con instrucciones para el LLM
        """
        response_type = classification["suggested_response_type"]
        cognitive_state = classification["cognitive_state"]

        # Construir estrategia base
        strategy = {
            "response_type": response_type,
            "cognitive_state": cognitive_state,
            "max_help_level": self.pedagogical_policies["max_help_level"],
            "instructions": [],
            "constraints": [],
            "expected_elements": [],
            # Nuevos campos (FIX Cortez64)
            "classification_flags": {
                "is_frustrated": classification.get("is_frustrated", False),
                "is_confused": classification.get("is_confused", False),
                "is_metacognitive": classification.get("is_metacognitive", False),
                "requests_example": classification.get("requests_example", False),
                "requests_validation": classification.get("requests_validation", False),
                "requests_optimization": classification.get("requests_optimization", False),
                "requests_comparison": classification.get("requests_comparison", False),
            }
        }

        # ============================================================
        # INSTRUCCIONES SEGÚN TIPO DE RESPUESTA
        # ============================================================

        if response_type == "socratic_questioning":
            strategy["instructions"] = [
                "No proporcionar código completo",
                "Hacer preguntas que guíen el razonamiento",
                "Solicitar que el estudiante explique su comprensión del problema",
                "Pedir que descomponga el problema en pasos"
            ]
            strategy["expected_elements"] = [
                "preguntas_guia",
                "solicitud_explicacion",
                "descomposicion_problema"
            ]

        elif response_type == "conceptual_explanation":
            strategy["instructions"] = [
                "Explicar conceptos fundamentales relevantes",
                "Usar ejemplos simples y analogías",
                "Evitar dar la implementación específica",
                "Conectar con conocimientos previos"
            ]
            strategy["expected_elements"] = [
                "explicacion_conceptual",
                "ejemplos",
                "principios_fundamentales"
            ]

        elif response_type == "guided_hints":
            strategy["instructions"] = [
                "Proporcionar pistas graduadas",
                "Sugerir dirección sin revelar la solución",
                "Ofrecer pseudocódigo de alto nivel si es apropiado",
                "Pedir que el estudiante justifique sus próximos pasos"
            ]
            strategy["expected_elements"] = [
                "pistas_graduadas",
                "direccion_general",
                "solicitud_justificacion"
            ]

        # ============================================================
        # NUEVOS TIPOS DE RESPUESTA (FIX Cortez64)
        # ============================================================

        elif response_type == "empathetic_support":
            # Para estudiantes frustrados o atascados
            strategy["instructions"] = [
                "Reconocer la frustración del estudiante con empatía",
                "Normalizar que trabarse es parte del aprendizaje",
                "Ofrecer un enfoque fresco o alternativo al problema",
                "Proporcionar pistas más directas para desbloquear",
                "Sugerir dividir el problema en partes más pequeñas",
                "Mantener tono alentador y positivo"
            ]
            strategy["expected_elements"] = [
                "reconocimiento_empatico",
                "normalizacion",
                "enfoque_alternativo",
                "pistas_desbloqueadoras",
                "motivacion"
            ]
            # Aumentar nivel de ayuda para frustración
            strategy["max_help_level"] = min(0.8, self.pedagogical_policies["max_help_level"] + 0.15)

        elif response_type == "metacognitive_guidance":
            # Para preguntas sobre cómo pensar/encarar el problema
            strategy["instructions"] = [
                "Guiar el proceso de pensamiento, no el contenido",
                "Enseñar estrategias de resolución de problemas",
                "Ayudar a identificar qué sabe y qué le falta",
                "Proponer un plan de acción paso a paso",
                "Fomentar la autoevaluación del progreso",
                "Sugerir técnicas como dividir y conquistar"
            ]
            strategy["expected_elements"] = [
                "estrategia_pensamiento",
                "plan_accion",
                "tecnicas_resolucion",
                "autoevaluacion",
                "pasos_ordenados"
            ]

        elif response_type == "example_based":
            # Para solicitudes de ejemplos
            strategy["instructions"] = [
                "Proporcionar un ejemplo análogo, NO la solución directa",
                "Usar un caso similar pero diferente al problema actual",
                "Explicar el ejemplo paso a paso",
                "Pedir al estudiante que identifique similitudes",
                "Guiar la transferencia del ejemplo al problema real",
                "Evitar que el estudiante copie directamente"
            ]
            strategy["expected_elements"] = [
                "ejemplo_analogo",
                "explicacion_ejemplo",
                "preguntas_transferencia",
                "conexion_problema_actual"
            ]

        elif response_type == "clarification_request":
            strategy["instructions"] = [
                "Pedir más contexto sobre lo que intenta hacer",
                "Solicitar que muestre su código actual si aplica",
                "Preguntar qué parte específica no entiende",
                "Aclarar el objetivo del estudiante"
            ]
            strategy["expected_elements"] = [
                "preguntas_clarificadoras",
                "solicitud_contexto",
                "solicitud_codigo"
            ]

        # ============================================================
        # RESTRICCIONES COMUNES
        # ============================================================
        strategy["constraints"] = [
            "No generar código completo sin mediación",
            "Exigir justificación de decisiones",
            "Registrar todo en trazabilidad N4",
            "Promover la autorregulación"
        ]

        # Ajustar restricciones según estado
        if classification.get("is_frustrated"):
            # Relajar un poco las restricciones para frustración
            strategy["constraints"].append(
                "Permitir pistas más directas para desbloquear al estudiante"
            )

        # ============================================================
        # AJUSTAR SEGÚN HISTORIAL DEL ESTUDIANTE
        # ============================================================
        if student_history:
            strategy["student_context"] = self._analyze_student_history(student_history)

        return strategy

    def _analyze_student_history(self, history: List[CognitiveTrace]) -> Dict[str, Any]:
        """Analiza el historial del estudiante para personalizar la respuesta"""
        if not history:
            return {"level": "beginner", "patterns": []}

        # Contar patrones
        delegation_count = sum(
            1 for t in history
            if "delegación" in t.content.lower() or "código completo" in t.content.lower()
        )
        self_correction_count = sum(
            1 for t in history
            if t.interaction_type == InteractionType.SELF_CORRECTION
        )

        return {
            "total_interactions": len(history),
            "delegation_tendency": delegation_count / len(history) if history else 0,
            "self_correction_rate": self_correction_count / len(history) if history else 0,
            "suggested_difficulty_adjustment": "increase" if self_correction_count > 3 else "maintain"
        }

    def set_mode(self, mode: AgentMode) -> None:
        """Cambia el modo operativo del motor"""
        self.current_mode = mode

    def get_current_mode(self) -> AgentMode:
        """Retorna el modo operativo actual"""
        return self.current_mode