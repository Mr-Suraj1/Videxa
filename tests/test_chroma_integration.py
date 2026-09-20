"""Offline integration coverage for Chroma persistence and Videxa RAG."""

import gc

from langchain_core.runnables import RunnableLambda

import core.rag_engine as rag_engine
import core.vector_store as vector_store


class DeterministicEmbeddings:
    """Small local embedding model that keeps Alpha and Bravo orthogonal."""

    @staticmethod
    def _embed(text: str) -> list[float]:
        normalized = text.lower()
        return [
            float(normalized.count("alpha_token")),
            float(normalized.count("bravo_token")),
            1.0,
        ]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def test_real_chroma_persists_isolates_sessions_and_powers_mocked_rag(monkeypatch, tmp_path):
    """Exercise disk-backed Chroma and RAG without model or network calls."""
    persistence_dir = tmp_path / "chroma"
    monkeypatch.setattr(vector_store, "CHROMA_DIR", str(persistence_dir))
    monkeypatch.setattr(vector_store, "get_embeddings", DeterministicEmbeddings)

    session_a = "session-a"
    session_b = "session-b"
    store_a = vector_store.build_vector_store(
        "ALPHA_TOKEN belongs only to session A.", session_id=session_a
    )
    store_b = vector_store.build_vector_store(
        "BRAVO_TOKEN belongs only to session B.", session_id=session_b
    )

    a_results = vector_store.get_retriever(store_a, k=1).invoke("ALPHA_TOKEN")
    b_results = vector_store.get_retriever(store_b, k=1).invoke("BRAVO_TOKEN")
    assert "ALPHA_TOKEN" in a_results[0].page_content
    assert "BRAVO_TOKEN" not in a_results[0].page_content
    assert "BRAVO_TOKEN" in b_results[0].page_content
    assert "ALPHA_TOKEN" not in b_results[0].page_content

    # Discard open wrappers, then rebuild them from the on-disk collection.
    del store_a, store_b
    gc.collect()
    reloaded_a = vector_store.load_vector_store(session_a)
    reloaded_results = vector_store.get_retriever(reloaded_a, k=1).invoke("ALPHA_TOKEN")
    assert "ALPHA_TOKEN" in reloaded_results[0].page_content

    seen_prompts = []

    def mocked_llm(prompt):
        seen_prompts.append(prompt.to_string())
        return "mocked answer"

    monkeypatch.setattr(rag_engine, "get_llm", lambda: RunnableLambda(mocked_llm))
    rag_chain = rag_engine._build_chain(reloaded_a)
    assert rag_engine.ask_question(rag_chain, "Where is ALPHA_TOKEN?") == "mocked answer"
    assert "ALPHA_TOKEN" in seen_prompts[0]
    assert "BRAVO_TOKEN" not in seen_prompts[0]
