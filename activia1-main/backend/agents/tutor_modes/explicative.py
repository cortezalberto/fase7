"""
Explicative/Conceptual Mode Strategy for T-IA-Cog.

Cortez46: Extracted from tutor.py (1,422 lines)

Implements conceptual explanation approach that reduces extraneous cognitive
load while promoting germane load (Sweller, 1988).
"""
import logging

from .base import (
    TutorModeStrategy,
    TutorModeContext,
    TutorResponse,
    TutorMode,
    HelpLevel,
)

logger = logging.getLogger(__name__)


class ExplicativeStrategy(TutorModeStrategy):
    """
    Explicative/Conceptual explanation strategy.

    Provides conceptual explanations without specific implementations,
    focusing on understanding principles and patterns.

    Based on:
    - Cognitive Load Theory (Sweller, 1988)
    - Reducing extraneous load
    - Promoting germane load for schema construction
    """

    @property
    def mode(self) -> TutorMode:
        return TutorMode.EXPLICATIVO

    @property
    def pedagogical_intent(self) -> str:
        return "conceptual_understanding"

    async def generate_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """
        Generate conceptual explanation response.

        First attempts LLM generation, falls back to templates.
        """
        # Try LLM generation first
        if context.llm_provider:
            try:
                logger.info(
                    "Generating conceptual explanation with LLM for: %s...",
                    context.student_prompt[:50]
                )
                response = await self._generate_with_llm(context)
                if response:
                    return response
            except Exception as e:
                logger.warning(
                    "LLM conceptual generation failed, using fallback: %s: %s",
                    type(e).__name__, e,
                    exc_info=True
                )

        # Fallback to template-based response
        return self._generate_template_response(context)

    async def _generate_with_llm(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate conceptual explanation using LLM."""
        from ..tutor_rules import InterventionType

        system_prompt = self.get_system_prompt(
            context,
            InterventionType.CORRECCION_CONCEPTUAL
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
                "provides_code": False,
                "generated_with_llm": True
            }
        )

    def _generate_template_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """Generate template-based conceptual explanation."""
        # Adapt template based on cognitive state
        if context.cognitive_state == "depuracion":
            message = self._generate_debugging_template(context)
        elif context.cognitive_state == "optimizacion":
            message = self._generate_optimization_template(context)
        else:
            message = self._generate_generic_template(context)

        return TutorResponse(
            message=message.strip(),
            mode=self.mode,
            pedagogical_intent=self.pedagogical_intent,
            requires_student_response=True,
            help_level=HelpLevel.MEDIO,
            metadata={
                "cognitive_state": context.cognitive_state,
                "provides_code": False,
            }
        )

    def _generate_generic_template(self, context: TutorModeContext) -> str:
        """Generic conceptual explanation template."""
        return """
## Conceptos Fundamentales

Vamos a abordar esto desde los conceptos fundamentales, sin adelantarnos a la implementacion.

### Concepto Clave

[El concepto principal que necesitas comprender para resolver este problema]

### Principios Importantes

1. **Principio 1**: [Explicacion del principio]
2. **Principio 2**: [Explicacion del principio]

### Ejemplo Simple

[Analogia o ejemplo simple que ilustra el concepto]

### Conexion con tu Problema

Para tu caso especifico, estos conceptos significan que...

---

**Proximo paso**: Ahora que tenes mas claros estos conceptos, como
pensas aplicarlos a tu problema? Que parte queres que profundice?
"""

    def _generate_debugging_template(self, context: TutorModeContext) -> str:
        """Conceptual template for debugging scenarios."""
        return """
## Conceptos de Depuracion

Cuando encontramos un error, es importante entender el flujo de datos y la logica antes de hacer cambios.

### Proceso de Depuracion Sistematico

1. **Reproducir**: Confirmar que podemos reproducir el error consistentemente
2. **Aislar**: Reducir el problema al minimo codigo necesario
3. **Diagnosticar**: Identificar la causa raiz, no solo el sintoma
4. **Corregir**: Aplicar la solucion minima necesaria
5. **Verificar**: Confirmar que la solucion no introduce nuevos problemas

### Preguntas Clave

- Que datos de entrada causan el error?
- Cual es el ultimo punto donde los datos son correctos?
- Que transformacion introduce el problema?

### Para tu Caso

Basandote en estos principios, cual seria tu primer paso de diagnostico?
Que hipotesis tenes sobre donde podria estar el problema?
"""

    def _generate_optimization_template(self, context: TutorModeContext) -> str:
        """Conceptual template for optimization scenarios."""
        return """
## Conceptos de Optimizacion

Antes de optimizar, es fundamental comprender donde esta el cuello de botella real.

### Principios de Optimizacion

1. **Medir primero**: No optimizar sin datos de rendimiento
2. **Algoritmo > Micro-optimizaciones**: La complejidad algoritmica importa mas que trucos de codigo
3. **Trade-offs**: Toda optimizacion tiene un costo (memoria vs tiempo, legibilidad vs velocidad)

### Complejidades Comunes

- O(1): Acceso directo
- O(log n): Busqueda binaria
- O(n): Recorrido lineal
- O(n^2): Loops anidados

### Para tu Caso

Cual es la operacion que crees que consume mas tiempo?
Podrias describir la complejidad actual de tu solucion?
"""
