

from rag.agent import get_agent
from rag.guardrail import GuardrailResult
from rag.structured_response import StructuredStatResponse


def answer_stats_question(question: str) -> dict:
    """
    Call the RAG agent and return a clean dict for the Django view.

    Always returns a dict with these keys:
      - 'success'  : bool
      - 'concept'  : str  (matched concept name, or empty)
      - 'category' : str
      - 'confidence': float
      - 'intuition': str
      - 'formula'  : str
      - 'formula_legend': dict
      - 'example'  : str  (scenario)
      - 'code'     : str
      - 'interpretation': str
      - 'assumptions': list[str]
      - 'common_mistakes': list[str]
      - 'effect_size': str or None
      - 'fallback_note': str or None
      - 'query_case': str  (Conceptual / Computational / Comprehensive)
      - 'out_of_scope_message': str  (only when success=False)
    """
    agent = get_agent()
    result = agent.query(question)

    # ── Out of scope ───────────────────────────────────────────────────
    if isinstance(result, GuardrailResult):
        return {
            'success': False,
            'out_of_scope_message': result.message,
            'closest_concept': result.closest_concept or '',
        }

    # ── In scope — structured response ────────────────────────────────
    resp: StructuredStatResponse = result
    return {
        'success': True,
        'concept': resp.concept,
        'category': resp.category,
        'confidence': resp.confidence,
        'query_case': resp.query_case.value,   # "Conceptual" / "Computational" / "Comprehensive"
        'intuition': resp.intuition,
        'formula': resp.formula_expression,
        'formula_legend': resp.formula_legend,
        'real_world_example': resp.real_world_example,
        'why': resp.why,
        'assumptions': resp.assumptions,
        'example_scenario': resp.scenario,
        'code': resp.code,
        'interpretation': resp.interpretation,
        'common_mistakes': resp.common_mistakes,
        'effect_size': resp.effect_size,
        'fallback_note': resp.fallback_note,
        'out_of_scope_message': '',
        'closest_concept': '',
    }