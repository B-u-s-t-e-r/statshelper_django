from enum import Enum


class QueryCase(Enum):
    A = "Conceptual"
    B = "Computational"
    C = "Comprehensive"


CASE_A_KEYWORDS = [
    "why", "how does", "how do", "explain", "logic", "intuition",
    "understand", "concept", "idea behind", "reasoning", "make sense",
    "plain english", "behind", "work", "works", "purpose", "meaning"
]

CASE_B_KEYWORDS = [
    "calculate", "compute", "formula", "derive", "derivation",
    "numeric", "equation", "mathematically", "math", "solve",
    "proof", "step by step calculation", "give me the formula",
    "how to compute", "find the", "evaluate"
]

CASE_C_KEYWORDS = [
    "what is", "tell me about", "introduce", "introduction",
    "overview", "teach me", "learn about", "full explanation",
    "all about", "describe", "i want to know", "guide me",
    "when should i", "should i use", "which test"
]


def classify_query(query: str) -> QueryCase:
    q = query.lower()
    score_a = sum(1 for kw in CASE_A_KEYWORDS if kw in q)
    score_b = sum(1 for kw in CASE_B_KEYWORDS if kw in q)
    score_c = sum(1 for kw in CASE_C_KEYWORDS if kw in q)

    # "what is the formula/equation" -> formula wins over generic "what is"
    if any(kw in q for kw in ["formula", "equation", "derive"]) and score_a == 0:
        return QueryCase.B

    if score_a > 0 and score_b > 0:
        return QueryCase.C
    if score_b > score_a and score_b > score_c:
        return QueryCase.B
    if score_a > score_b and score_a >= score_c:
        return QueryCase.A
    return QueryCase.C


def get_case_label(case: QueryCase) -> str:
    return {
        QueryCase.A: "💡 Case A — Conceptual Inquiry (Intuition Focus)",
        QueryCase.B: "🔢 Case B — Computational Inquiry (Formula Focus)",
        QueryCase.C: "📚 Case C — Comprehensive Inquiry (Intuition + Formula)"
    }[case]