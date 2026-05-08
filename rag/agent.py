import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.knowledge_base import load_knowledge_base, get_all_text_chunks
from rag.embedder import embed_query, load_cached_embeddings, embed_texts, save_embeddings
from rag.retriever import retrieve, load_index, build_index, keyword_fallback
from rag.structured_response import format_response, render_response, StructuredStatResponse
from rag.query_classifier import classify_query, QueryCase
from rag.guardrail import check_scope, GuardrailResult

SEMANTIC_THRESHOLD = 0.30


class StatisticsAgent:

    def __init__(self):
        self.kb = None
        self.chunks = None
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return

        print("Initializing Statistics RAG Agent...")
        self.kb = load_knowledge_base()
        self.chunks = get_all_text_chunks(self.kb)

        index, _ = load_index()
        if index is None:
            print("Building index from scratch...")
            embs, cached_chunks = load_cached_embeddings()
            if embs is None:
                print("Computing embeddings (first time only)...")
                texts = [c["text"] for c in self.chunks]
                embs = embed_texts(texts)
                save_embeddings(embs, self.chunks)
            build_index(embs, self.chunks)
        else:
            print("FAISS index loaded from cache.")

        self._initialized = True
        print(f"Agent ready. {len(self.kb)} concepts loaded.\n")

    def query(self, user_query: str):
        """
        Main query method.
        Returns either:
          - StructuredStatResponse (in-scope query)
          - GuardrailResult        (out-of-scope query)
        Callers must check result type.
        """
        if not self._initialized:
            self.initialize()

        # ── Layer 1 Guardrail: pre-retrieval keyword check ──────────────
        pre_check = check_scope(user_query)
        if not pre_check.is_in_scope:
            return pre_check  # return guardrail result immediately

        # ── Embed and retrieve ──────────────────────────────────────────
        q_embedding = embed_query(user_query)
        results = retrieve(q_embedding, top_k=3)

        fallback_used = False
        if results and results[0]["score"] >= SEMANTIC_THRESHOLD:
            best = results[0]
        else:
            fallback_results = keyword_fallback(user_query, self.chunks, top_k=1)
            if fallback_results:
                best = fallback_results[0]
                fallback_used = True
            elif results:
                best = results[0]
                fallback_used = True
            else:
                # Nothing found at all
                return check_scope(
                    user_query,
                    retrieval_confidence=0.0,
                    closest_concept=None
                )

        confidence = best["score"] * 100
        closest_concept = best["entry"]["concept"]

        # ── Layer 2 Guardrail: post-retrieval confidence check ──────────
        post_check = check_scope(
            user_query,
            retrieval_confidence=confidence,
            closest_concept=closest_concept
        )
        if not post_check.is_in_scope:
            return post_check  # return guardrail result with closest concept hint

        # ── Format and return structured response ───────────────────────
        return format_response(
            query=user_query,
            entry=best["entry"],
            score=best["score"],
            fallback=fallback_used
        )

    def query_and_print(self, user_query: str):
        """Query and print result to console — handles both response types."""
        result = self.query(user_query)

        if isinstance(result, GuardrailResult):
            print("\n" + "=" * 65)
            print(result.message)
            print("=" * 65)
        else:
            print(render_response(result))

        return result

    def list_available_concepts(self) -> list[str]:
        if not self._initialized:
            self.initialize()
        return [e["concept"] for e in self.kb]


# ── Singleton ─────────────────────────────────────────────────────────────────

_agent_instance = None

def get_agent() -> StatisticsAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = StatisticsAgent()
        _agent_instance.initialize()
    return _agent_instance


# ── CLI Mode ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = StatisticsAgent()
    agent.initialize()

    print("\n" + "=" * 65)
    print("  Statistics RAG Chatbot — CLI Mode")
    print("  Type 'quit' to exit | 'list' to see all covered concepts")
    print("=" * 65)

    while True:
        try:
            user_input = input("\nYour question: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break
            if user_input.lower() == "list":
                print("\nCovered concepts:")
                for c in agent.list_available_concepts():
                    print(f"  • {c}")
                continue
            agent.query_and_print(user_input)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")