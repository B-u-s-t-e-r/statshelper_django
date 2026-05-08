from dataclasses import dataclass, field
from typing import Optional
from rag.query_classifier import QueryCase, classify_query, get_case_label


@dataclass
class StructuredStatResponse:
    query: str
    query_case: QueryCase
    concept: str
    category: str
    confidence: float

    # Core content
    intuition: str
    formula_expression: str
    formula_legend: dict
    real_world_example: str
    why: str
    assumptions: list[str]
    scenario: str
    code: str
    interpretation: str
    common_mistakes: list[str]
    effect_size: Optional[str] = None
    fallback_note: Optional[str] = None


def format_response(query: str, entry: dict, score: float, fallback: bool = False) -> StructuredStatResponse:
    """Map a KB entry + query into a StructuredStatResponse with Case logic."""
    example = entry.get("mini_example", {})
    formula = entry.get("formula", {})
    case = classify_query(query)

    return StructuredStatResponse(
        query=query,
        query_case=case,
        concept=entry["concept"],
        category=entry["category"],
        confidence=round(score * 100, 1),
        intuition=entry.get("intuition", ""),
        formula_expression=formula.get("expression", ""),
        formula_legend=formula.get("legend", {}),
        real_world_example=entry.get("real_world_example", ""),
        why=entry.get("why", ""),
        assumptions=entry.get("assumptions", []),
        scenario=example.get("scenario", ""),
        code=example.get("code", ""),
        interpretation=example.get("interpretation", ""),
        common_mistakes=entry.get("common_mistakes", []),
        effect_size=entry.get("effect_size"),
        fallback_note="Low confidence match. Consider rephrasing." if fallback else None
    )


def render_response(resp: StructuredStatResponse) -> str:
    """Render full structured response for CLI mode."""
    D = "═" * 65
    T = "─" * 65
    case = resp.query_case
    show_intuition = case in (QueryCase.A, QueryCase.C)
    show_formula   = case in (QueryCase.B, QueryCase.C)

    lines = [
        f"\n{D}",
        f"  📊 STATISTICS RAG AGENT — STRUCTURED RESPONSE",
        f"{D}",
        f"",
        f"🔍 QUERY:  {resp.query}",
        f"🎯 MODE:   {get_case_label(case)}",
        f"",
        f"{T}",
        f"✅ RECOMMENDED: {resp.concept}  [{resp.category}]  Confidence: {resp.confidence}%",
        f"",
    ]

    if resp.fallback_note:
        lines += [f"  ⚠️  {resp.fallback_note}", ""]

    # ── Case A / C: Intuition ──────────────────────────────────────────
    if show_intuition and resp.intuition:
        lines += [
            f"{T}",
            f"💡 INTUITION",
            f"  {resp.intuition}",
            f"",
        ]

    # ── Case B / C: Formula ───────────────────────────────────────────
    if show_formula and resp.formula_expression:
        lines += [
            f"{T}",
            f"🔢 FORMULA",
            f"  {resp.formula_expression}",
            f"",
            f"  Legend:",
        ]
        for var, desc in resp.formula_legend.items():
            lines.append(f"    • {var} : {desc}")
        lines.append("")

    # ── Real World Example (always shown) ─────────────────────────────
    if resp.real_world_example:
        lines += [
            f"{T}",
            f"🌍 REAL-WORLD EXAMPLE",
            f"  {resp.real_world_example}",
            f"",
        ]

    # ── Assumptions ───────────────────────────────────────────────────
    lines += [f"{T}", f"📋 ASSUMPTIONS TO CHECK"]
    for i, a in enumerate(resp.assumptions, 1):
        lines.append(f"  {i}. {a}")
    lines.append("")

    # ── Mini Example ──────────────────────────────────────────────────
    lines += [f"{T}", f"🧮 MINI EXAMPLE"]
    if resp.scenario:
        lines.append(f"  Scenario: {resp.scenario}")
    lines.append("")
    if resp.code:
        lines.append("  Python Code:")
        lines.append(f"  {'─'*40}")
        for l in resp.code.split("\n"):
            lines.append(f"  {l}")
        lines.append(f"  {'─'*40}")
    if resp.interpretation:
        lines.append(f"  Interpretation: {resp.interpretation}")
    lines.append("")

    # ── Common Mistakes ───────────────────────────────────────────────
    lines += [f"{T}", f"⚠️  COMMON MISTAKES"]
    for i, m in enumerate(resp.common_mistakes, 1):
        lines.append(f"  {i}. {m}")
    lines.append("")

    # ── Effect Size ───────────────────────────────────────────────────
    if resp.effect_size:
        lines += [f"{T}", f"📏 EFFECT SIZE", f"  {resp.effect_size}", ""]

    lines.append(D)
    return "\n".join(lines)