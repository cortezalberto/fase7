"""
Training Hints Strategy for Digital Trainer Integration.

Cortez50: New file for Digital Trainer integration with T-IA-Cog.

Extends GuidedStrategy to provide exercise-specific contextual hints
during training sessions. Builds "implicit prompts" from exercise context,
attempt history, and error information.

Key Features:
- Exercise-aware hint generation
- Implicit prompt construction
- Attempt history analysis
- Error-contextualized hints
- Integration with TrainingGateway
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from .base import (
    TutorModeStrategy,
    TutorModeContext,
    TutorResponse,
    TutorMode,
    HelpLevel,
)
from .guided import GuidedStrategy

logger = logging.getLogger(__name__)


@dataclass
class ExerciseContext:
    """
    Context for an exercise in the Digital Trainer.

    Contains all information needed to generate contextual hints.
    """
    exercise_id: str
    title: str
    description: str
    expected_concepts: List[str]
    difficulty: str  # "basico", "intermedio", "avanzado"
    language: str  # "python", "javascript", etc.
    hints_available: List[str]  # Static hints from exercise definition
    test_cases_summary: Optional[str] = None
    common_errors: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None


@dataclass
class AttemptContext:
    """
    Context from previous attempts.

    Used to understand student's progression and struggles.
    """
    attempt_number: int
    last_code: Optional[str] = None
    last_error: Optional[str] = None
    last_test_results: Optional[Dict[str, Any]] = None
    time_on_exercise_seconds: int = 0
    previous_hints_requested: int = 0
    errors_pattern: Optional[List[str]] = None  # Common error types
    progress_indicators: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingHintRequest:
    """
    Request for a contextual hint in training mode.

    Encapsulates all information for generating an exercise-specific hint.
    """
    session_id: str
    student_id: str
    hint_number: int  # 1, 2, 3, 4 (maps to help levels)
    exercise: ExerciseContext
    attempts: AttemptContext
    inferred_cognitive_state: Optional[str] = None
    risk_flags: Optional[List[str]] = None


class TrainingHintsStrategy(GuidedStrategy):
    """
    Training-specific hints strategy extending GuidedStrategy.

    Generates contextual hints for exercises by:
    1. Building an "implicit prompt" from exercise + attempt context
    2. Using exercise-specific information for personalization
    3. Analyzing error patterns to target specific misconceptions
    4. Respecting the 4 hint levels from GuidedStrategy

    Hint Levels:
    - Level 1 (MINIMO): Socratic questions about the exercise concept
    - Level 2 (BAJO): Conceptual hints related to expected concepts
    - Level 3 (MEDIO): Detailed hints + pseudocode for the approach
    - Level 4 (ALTO): Specific strategy without full solution

    Based on entrenador.md C4 Architecture proposal.
    """

    def __init__(self):
        """Initialize training hints strategy."""
        super().__init__()
        self._hint_cache: Dict[str, List[Dict[str, str]]] = {}

    @property
    def mode(self) -> TutorMode:
        return TutorMode.GUIADO

    @property
    def pedagogical_intent(self) -> str:
        return "exercise_scaffolding"

    async def generate_training_hint(
        self,
        request: TrainingHintRequest,
        llm_provider: Optional[Any] = None,
    ) -> TutorResponse:
        """
        Generate a contextual hint for a training exercise.

        This is the main entry point for the Digital Trainer.

        Args:
            request: TrainingHintRequest with exercise and attempt context
            llm_provider: Optional LLM provider for dynamic hints

        Returns:
            TutorResponse with contextual hint
        """
        # Build implicit prompt from exercise context
        implicit_prompt = self._build_implicit_prompt(request)

        # Map hint number to help level
        help_level = self._map_hint_to_level(request.hint_number)

        # Determine cognitive state
        cognitive_state = self._determine_cognitive_state(request)

        # Build strategy dict
        strategy = {
            "help_level": help_level,
            "student_level": self._infer_student_level(request),
            "exercise_context": {
                "exercise_id": request.exercise.exercise_id,
                "difficulty": request.exercise.difficulty,
                "concepts": request.exercise.expected_concepts,
            }
        }

        # Create TutorModeContext
        context = TutorModeContext(
            student_prompt=implicit_prompt,
            cognitive_state=cognitive_state,
            strategy=strategy,
            student_history=None,  # Training uses attempt history instead
            llm_provider=llm_provider,
            extra={
                "training_request": request,
                "is_training_mode": True,
            }
        )

        # Try LLM generation first
        if llm_provider:
            try:
                logger.info(
                    "Generating training hint with LLM for exercise %s",
                    request.exercise.exercise_id
                )
                response = await self._generate_training_hint_llm(context, request)
                if response:
                    return response
            except Exception as e:
                logger.warning(
                    "LLM training hint failed, using fallback: %s: %s",
                    type(e).__name__, e,
                    exc_info=True
                )

        # Fallback to template-based hints
        return self._generate_training_hint_template(context, request)

    def _build_implicit_prompt(self, request: TrainingHintRequest) -> str:
        """
        Build an implicit prompt representing what the student is asking.

        Constructs a natural language representation of the student's
        current situation based on exercise context and attempt history.

        Example output:
        "Estoy trabajando en un ejercicio sobre [concepto] en [lenguaje].
        He hecho [N] intentos. Mi ultimo error fue [error].
        Necesito ayuda para entender [area de dificultad]."
        """
        parts = []

        # Exercise context
        parts.append(
            f"Estoy trabajando en el ejercicio '{request.exercise.title}' "
            f"sobre {', '.join(request.exercise.expected_concepts[:3])} "
            f"en {request.exercise.language}."
        )

        # Attempt history
        if request.attempts.attempt_number > 0:
            parts.append(
                f"He realizado {request.attempts.attempt_number} intento(s)."
            )

        # Time context
        if request.attempts.time_on_exercise_seconds > 300:  # > 5 minutes
            minutes = request.attempts.time_on_exercise_seconds // 60
            parts.append(
                f"Llevo aproximadamente {minutes} minutos en este ejercicio."
            )

        # Error context
        if request.attempts.last_error:
            error_summary = self._summarize_error(request.attempts.last_error)
            parts.append(f"Mi ultimo error fue: {error_summary}")

        # Test results context
        if request.attempts.last_test_results:
            passed = request.attempts.last_test_results.get("passed", 0)
            total = request.attempts.last_test_results.get("total", 0)
            if total > 0:
                parts.append(f"Paso {passed} de {total} tests.")

        # Previous hints
        if request.attempts.previous_hints_requested > 0:
            parts.append(
                f"Ya solicite {request.attempts.previous_hints_requested} pista(s) anteriormente."
            )

        # Inferred difficulty
        difficulty_hint = self._infer_difficulty_area(request)
        if difficulty_hint:
            parts.append(f"Creo que mi dificultad esta en: {difficulty_hint}")

        return " ".join(parts)

    def _summarize_error(self, error: str, max_length: int = 100) -> str:
        """Summarize an error message for the implicit prompt."""
        # Common error patterns
        error_patterns = {
            "SyntaxError": "error de sintaxis",
            "IndentationError": "error de indentacion",
            "NameError": "variable o funcion no definida",
            "TypeError": "error de tipo de datos",
            "IndexError": "indice fuera de rango",
            "KeyError": "clave no encontrada",
            "ValueError": "valor invalido",
            "AttributeError": "atributo no encontrado",
            "ZeroDivisionError": "division por cero",
            "RecursionError": "recursion infinita",
            "AssertionError": "asercion fallida (test no paso)",
        }

        for pattern, description in error_patterns.items():
            if pattern in error:
                return description

        # Truncate if too long
        if len(error) > max_length:
            return error[:max_length] + "..."

        return error

    def _infer_difficulty_area(self, request: TrainingHintRequest) -> Optional[str]:
        """Infer the area where student is struggling."""
        if not request.attempts.errors_pattern:
            return None

        # Map error patterns to difficulty areas
        area_mapping = {
            "syntax": "la sintaxis del lenguaje",
            "logic": "la logica del algoritmo",
            "data_structure": "el uso de estructuras de datos",
            "loop": "el manejo de bucles",
            "condition": "las condiciones logicas",
            "function": "la definicion o llamada de funciones",
            "recursion": "el concepto de recursion",
            "edge_case": "los casos borde",
        }

        # Return first matching area
        for pattern in request.attempts.errors_pattern:
            if pattern in area_mapping:
                return area_mapping[pattern]

        return None

    def _map_hint_to_level(self, hint_number: int) -> HelpLevel:
        """Map hint number (1-4) to HelpLevel enum."""
        mapping = {
            1: HelpLevel.MINIMO,
            2: HelpLevel.BAJO,
            3: HelpLevel.MEDIO,
            4: HelpLevel.ALTO,
        }
        return mapping.get(hint_number, HelpLevel.MEDIO)

    def _determine_cognitive_state(self, request: TrainingHintRequest) -> str:
        """Determine cognitive state from request context."""
        if request.inferred_cognitive_state:
            return request.inferred_cognitive_state

        # Infer from attempt context
        attempts = request.attempts

        if attempts.attempt_number == 0:
            return "inicio"
        elif attempts.attempt_number == 1:
            return "exploracion"
        elif attempts.last_error:
            if "SyntaxError" in (attempts.last_error or ""):
                return "depuracion_sintaxis"
            return "depuracion"
        elif attempts.previous_hints_requested > 2:
            return "estancamiento"
        else:
            return "desarrollo"

    def _infer_student_level(self, request: TrainingHintRequest) -> str:
        """Infer student level from exercise difficulty and attempts."""
        from ..tutor_rules import CognitiveScaffoldingLevel

        difficulty = request.exercise.difficulty
        attempts = request.attempts.attempt_number

        # Simple heuristic
        if difficulty == "basico":
            if attempts > 5:
                return CognitiveScaffoldingLevel.PRINCIPIANTE
            return CognitiveScaffoldingLevel.INTERMEDIO
        elif difficulty == "avanzado":
            return CognitiveScaffoldingLevel.AVANZADO
        else:
            return CognitiveScaffoldingLevel.INTERMEDIO

    async def _generate_training_hint_llm(
        self,
        context: TutorModeContext,
        request: TrainingHintRequest,
    ) -> Optional[TutorResponse]:
        """Generate training hint using LLM."""
        help_level = context.strategy.get("help_level", HelpLevel.MEDIO)

        # Build specialized system prompt for training hints
        system_prompt = self._build_training_hint_prompt(request, help_level)

        response_text = await self.generate_with_llm(context, system_prompt)

        if not response_text:
            return None

        return TutorResponse(
            message=response_text,
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            requires_justification=True,
            help_level=help_level,
            hints_count=1,
            previous_hints_count=request.attempts.previous_hints_requested,
            metadata={
                "exercise_id": request.exercise.exercise_id,
                "hint_number": request.hint_number,
                "cognitive_state": context.cognitive_state,
                "generated_with_llm": True,
                "is_training_mode": True,
            }
        )

    def _build_training_hint_prompt(
        self,
        request: TrainingHintRequest,
        help_level: HelpLevel,
    ) -> str:
        """Build system prompt for training hint generation."""
        level_instructions = {
            HelpLevel.MINIMO: """
Genera SOLO preguntas socraticas que orienten al estudiante.
NO des explicaciones ni codigo.
Haz 2-3 preguntas que ayuden a razonar sobre el problema.
""",
            HelpLevel.BAJO: """
Proporciona pistas conceptuales generales.
NO des codigo ni soluciones directas.
Menciona conceptos relevantes sin explicar como aplicarlos.
""",
            HelpLevel.MEDIO: """
Da pistas mas detalladas sobre el enfoque.
Podes incluir pseudocodigo de alto nivel.
NO des codigo funcional ni la solucion completa.
""",
            HelpLevel.ALTO: """
Proporciona una estrategia detallada para resolver el problema.
Podes dar fragmentos conceptuales y estructuras.
Sigue sin dar la solucion completa.
El estudiante debe escribir el codigo final.
""",
        }

        level_text = level_instructions.get(help_level, level_instructions[HelpLevel.MEDIO])

        # Build context section
        error_context = ""
        if request.attempts.last_error:
            error_context = f"""
Error reciente del estudiante:
{request.attempts.last_error[:500]}
"""

        code_context = ""
        if request.attempts.last_code:
            code_context = f"""
Codigo actual del estudiante (fragmento):
```{request.exercise.language}
{request.attempts.last_code[:1000]}
```
"""

        prompt = f"""Eres T-IA-Cog, un tutor cognitivo especializado en programacion.

EJERCICIO: {request.exercise.title}
DESCRIPCION: {request.exercise.description}
CONCEPTOS ESPERADOS: {', '.join(request.exercise.expected_concepts)}
DIFICULTAD: {request.exercise.difficulty}
LENGUAJE: {request.exercise.language}

CONTEXTO DEL ESTUDIANTE:
- Intento numero: {request.attempts.attempt_number}
- Pistas previas solicitadas: {request.attempts.previous_hints_requested}
- Tiempo en ejercicio: {request.attempts.time_on_exercise_seconds // 60} minutos
{error_context}
{code_context}

NIVEL DE AYUDA: {help_level.value.upper()}
{level_text}

REGLAS PEDAGOGICAS INQUEBRANTABLES:
1. NUNCA des la solucion completa
2. NUNCA escribas codigo funcional que resuelva el ejercicio
3. Siempre termina con una pregunta que requiera reflexion
4. Adapta el lenguaje al nivel del estudiante

Genera una pista apropiada para este nivel de ayuda.
"""
        return prompt

    def _generate_training_hint_template(
        self,
        context: TutorModeContext,
        request: TrainingHintRequest,
    ) -> TutorResponse:
        """Generate template-based training hint."""
        help_level = context.strategy.get("help_level", HelpLevel.MEDIO)
        if isinstance(help_level, str):
            help_level = HelpLevel(help_level)

        # Check if we have static hints available
        static_hints = request.exercise.hints_available
        if static_hints and request.hint_number <= len(static_hints):
            # Use static hint as base, but wrap with pedagogical structure
            base_hint = static_hints[request.hint_number - 1]
            hints = self._wrap_static_hint(base_hint, help_level, request)
        else:
            # Generate generic hints based on level and context
            hints = self._generate_exercise_hints(help_level, request)

        # Build message
        message = self._format_training_hints_message(hints, help_level, request)

        return TutorResponse(
            message=message,
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            requires_justification=True,
            help_level=help_level,
            hints_provided=hints,
            hints_count=len(hints),
            previous_hints_count=request.attempts.previous_hints_requested,
            metadata={
                "exercise_id": request.exercise.exercise_id,
                "hint_number": request.hint_number,
                "cognitive_state": context.cognitive_state,
                "generated_with_llm": False,
                "is_training_mode": True,
                "uses_static_hint": bool(static_hints and request.hint_number <= len(static_hints)),
            }
        )

    def _wrap_static_hint(
        self,
        static_hint: str,
        level: HelpLevel,
        request: TrainingHintRequest,
    ) -> List[Dict[str, str]]:
        """Wrap a static hint with pedagogical scaffolding."""
        hints = []

        # Add contextual setup
        if level == HelpLevel.MINIMO:
            hints.append({
                "level": 1,
                "type": "question",
                "content": f"Antes de ver la pista, pensemos: {self._generate_prereq_question(request)}"
            })

        # Add the static hint
        hints.append({
            "level": level.value,
            "type": "static_hint",
            "content": static_hint
        })

        # Add follow-up based on error context
        if request.attempts.last_error:
            hints.append({
                "level": level.value,
                "type": "error_connection",
                "content": self._connect_hint_to_error(static_hint, request.attempts.last_error)
            })

        return hints

    def _generate_prereq_question(self, request: TrainingHintRequest) -> str:
        """Generate a prerequisite question before showing hint."""
        concepts = request.exercise.expected_concepts
        if concepts:
            concept = concepts[0]
            return f"Que sabes sobre '{concept}'? Como crees que se aplica aqui?"
        return "Que intentaste hacer en tu ultimo intento? Que esperabas que pasara?"

    def _connect_hint_to_error(self, hint: str, error: str) -> str:
        """Connect the hint to the student's recent error."""
        error_type = self._summarize_error(error)
        return f"Relacionando esto con tu error ({error_type}): Como podria esta pista ayudarte a resolverlo?"

    def _generate_exercise_hints(
        self,
        level: HelpLevel,
        request: TrainingHintRequest,
    ) -> List[Dict[str, str]]:
        """Generate exercise-specific hints when no static hints available."""
        exercise = request.exercise
        attempts = request.attempts

        if level == HelpLevel.MINIMO:
            return self._generate_exercise_level1(exercise, attempts)
        elif level == HelpLevel.BAJO:
            return self._generate_exercise_level2(exercise, attempts)
        elif level == HelpLevel.MEDIO:
            return self._generate_exercise_level3(exercise, attempts)
        else:
            return self._generate_exercise_level4(exercise, attempts)

    def _generate_exercise_level1(
        self,
        exercise: ExerciseContext,
        attempts: AttemptContext,
    ) -> List[Dict[str, str]]:
        """Level 1 - Socratic questions about the exercise."""
        questions = []

        # Concept-based question
        if exercise.expected_concepts:
            concept = exercise.expected_concepts[0]
            questions.append({
                "level": 1,
                "type": "question",
                "content": f"Este ejercicio involucra '{concept}'. Podes explicar con tus palabras que es y para que sirve?"
            })

        # Problem decomposition
        questions.append({
            "level": 1,
            "type": "question",
            "content": "Si tuvieras que dividir este problema en pasos mas pequenos, cuales serian?"
        })

        # Input/output understanding
        questions.append({
            "level": 1,
            "type": "question",
            "content": "Que datos recibe tu solucion como entrada? Que debe producir como salida?"
        })

        return questions

    def _generate_exercise_level2(
        self,
        exercise: ExerciseContext,
        attempts: AttemptContext,
    ) -> List[Dict[str, str]]:
        """Level 2 - Conceptual hints related to expected concepts."""
        hints = []

        # Concept hints
        for concept in exercise.expected_concepts[:2]:
            hints.append({
                "level": 2,
                "type": "conceptual",
                "content": f"El concepto '{concept}' es clave aqui. Pensa en como se usa tipicamente en {exercise.language}."
            })

        # Error-specific hint if available
        if attempts.last_error:
            error_type = self._summarize_error(attempts.last_error)
            hints.append({
                "level": 2,
                "type": "error_hint",
                "content": f"Tu error ({error_type}) es comun. Revisa que los tipos de datos sean los correctos para cada operacion."
            })

        return hints

    def _generate_exercise_level3(
        self,
        exercise: ExerciseContext,
        attempts: AttemptContext,
    ) -> List[Dict[str, str]]:
        """Level 3 - Detailed hints with pseudocode structure."""
        hints = []

        # Problem decomposition
        hints.append({
            "level": 3,
            "type": "decomposition",
            "content": f"""Para resolver '{exercise.title}', considera estos pasos:
1. Primero, procesa la entrada
2. Luego, aplica la logica principal usando {exercise.expected_concepts[0] if exercise.expected_concepts else 'el concepto clave'}
3. Finalmente, retorna el resultado en el formato esperado"""
        })

        # High-level pseudocode
        hints.append({
            "level": 3,
            "type": "pseudocode",
            "content": f"""```
// Estructura sugerida para {exercise.language}
funcion resolver(entrada):
    // Paso 1: Validar/preparar datos

    // Paso 2: Logica principal
    // (aqui va tu algoritmo)

    // Paso 3: Retornar resultado
    retornar resultado
```"""
        })

        return hints

    def _generate_exercise_level4(
        self,
        exercise: ExerciseContext,
        attempts: AttemptContext,
    ) -> List[Dict[str, str]]:
        """Level 4 - Detailed strategy without solution."""
        hints = []

        # Detailed strategy
        hints.append({
            "level": 4,
            "type": "detailed_strategy",
            "content": f"""Estrategia recomendada para '{exercise.title}':

1. **Entrada**: Identifica el tipo de datos que recibes
2. **Transformacion**: Usa {exercise.expected_concepts[0] if exercise.expected_concepts else 'estructuras apropiadas'} para procesar
3. **Casos borde**: No olvides manejar entradas vacias o valores limite
4. **Salida**: Asegurate que el formato coincida con lo esperado"""
        })

        # Pattern suggestion based on concepts
        if exercise.expected_concepts:
            concept = exercise.expected_concepts[0]
            hints.append({
                "level": 4,
                "type": "pattern",
                "content": f"Un patron comun cuando trabajas con '{concept}' es [estructura tipica]. Pensa en como esto se aplica a tu problema."
            })

        # If multiple attempts, add encouragement with specific feedback
        if attempts.attempt_number > 3:
            hints.append({
                "level": 4,
                "type": "encouragement",
                "content": f"Llevas {attempts.attempt_number} intentos - eso muestra persistencia. Revisa tu ultimo codigo linea por linea comparando con esta estrategia."
            })

        return hints

    def _format_training_hints_message(
        self,
        hints: List[Dict[str, str]],
        level: HelpLevel,
        request: TrainingHintRequest,
    ) -> str:
        """Format training hints for display."""
        icons = {
            "question": "?",
            "conceptual": "*",
            "static_hint": ">",
            "error_connection": "!",
            "error_hint": "!",
            "decomposition": "#",
            "pseudocode": "<>",
            "detailed_strategy": "=>",
            "pattern": "[]",
            "encouragement": "+"
        }

        # Header
        header = f"""## Pista {request.hint_number} de 4 - Nivel {level.value.upper()}

**Ejercicio**: {request.exercise.title}
**Tu progreso**: {request.attempts.attempt_number} intento(s)
"""

        # Format hints
        formatted_hints = []
        for i, hint in enumerate(hints, 1):
            icon = icons.get(hint["type"], "-")
            hint_type = hint["type"].replace("_", " ").title()
            formatted_hints.append(f"### {icon} {hint_type}\n{hint['content']}")

        hints_text = "\n\n".join(formatted_hints)

        # Footer with reflection question
        footer = self._generate_training_followup(level, request)

        return f"{header}\n{hints_text}\n\n---\n\n{footer}"

    def _generate_training_followup(
        self,
        level: HelpLevel,
        request: TrainingHintRequest,
    ) -> str:
        """Generate follow-up question for training context."""
        if request.attempts.previous_hints_requested >= 3:
            return """**Reflexion importante**: Ya usaste varias pistas. Antes de pedir mas ayuda:
1. Revisa las pistas anteriores
2. Intenta aplicar lo aprendido
3. Si aun tenes dificultades, describe especificamente donde te trabas"""

        if level == HelpLevel.MINIMO:
            return """**Tu turno**: Responde las preguntas anteriores en voz alta o por escrito.
El proceso de articular tu pensamiento te ayudara a encontrar la solucion."""

        elif level == HelpLevel.BAJO:
            return """**Siguiente paso**: Basandote en estos conceptos, intenta escribir una primera version.
No tiene que ser perfecta - el objetivo es practicar."""

        elif level == HelpLevel.MEDIO:
            return """**Desafio**: Usa el pseudocodigo como guia para escribir tu solucion.
Que parte implementarias primero y por que?"""

        else:
            return """**Accion**: Con esta estrategia detallada, deberias poder avanzar.
Intenta implementar paso a paso. Si aun te trabas, el problema probablemente
esta en un detalle especifico - identifica cual es."""


# Factory function for integration with TrainingGateway
def create_training_hints_strategy() -> TrainingHintsStrategy:
    """Create and return a TrainingHintsStrategy instance."""
    return TrainingHintsStrategy()
