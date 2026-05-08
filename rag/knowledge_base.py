import json
import os
from pathlib import Path


KB_PATH = Path(__file__).parent.parent / "data" / "stats_knowledge_base.json"


def load_knowledge_base() -> list[dict]:
    """Load all knowledge base entries from JSON."""
    with open(KB_PATH, "r") as f:
        return json.load(f)


def get_all_text_chunks(kb: list[dict]) -> list[dict]:
    """
    Convert each KB entry into a searchable text chunk.
    Returns list of dicts with 'id', 'text', 'metadata'.
    """
    chunks = []
    for entry in kb:
        # Build a rich text blob for embedding
        text_parts = [
            f"Concept: {entry['concept']}",
            f"Category: {entry['category']}",
            f"Keywords: {', '.join(entry['keywords'])}",
            f"When to use: {entry['when_to_use']}",
            f"Why: {entry['why']}",
            f"Scenario: {entry['mini_example']['scenario']}",
        ]
        text = " | ".join(text_parts)
        chunks.append({
            "id": entry["id"],
            "text": text,
            "metadata": entry  # keep the full entry for structured output
        })
    return chunks


def get_categories(kb: list[dict]) -> list[str]:
    """Return all unique categories in the KB."""
    return list(set(e["category"] for e in kb))


if __name__ == "__main__":
    kb = load_knowledge_base()
    print(f"Loaded {len(kb)} knowledge base entries.")
    for entry in kb:
        print(f"  - {entry['concept']} ({entry['category']})")