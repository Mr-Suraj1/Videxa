"""Regression coverage for chat recovery from a saved transcript."""

from langchain_core.runnables import RunnableLambda

import backend.services as services
import core.rag_engine as rag_engine
import core.session_catalog as catalog
import core.vector_store as vector_store


class DeterministicEmbeddings:
    """Tiny local embeddings keep this real-Chroma test offline."""

    @staticmethod
    def _embed(text: str) -> list[float]:
        normalized = text.lower()
        return [
            float(normalized.count("primary_token")),
            float(normalized.count("other_token")),
            1.0,
        ]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def test_chat_recovers_failed_analysis_session_without_cross_session_data(monkeypatch, tmp_path):
    database = tmp_path / "sessions.sqlite3"
    chroma_dir = tmp_path / "chroma"
    monkeypatch.setenv("VIDEXA_SESSION_DB", str(database))
    monkeypatch.setattr(vector_store, "CHROMA_DIR", str(chroma_dir))
    monkeypatch.setattr(vector_store, "get_embeddings", DeterministicEmbeddings)

    session_id = "analysis-failed-session"
    other_session_id = "other-session"
    transcript = "PRIMARY_TOKEN: The launch review is on Tuesday."
    other_transcript = "OTHER_TOKEN: The unrelated budget review is on Friday."

    # A persisted transcript with a failed analysis status mirrors a provider
    # rate-limit failure after transcription. Neither session has a Chroma collection.
    catalog.save_transcript(session_id, transcript)
    catalog.update_session_status(
        session_id,
        analysis_status="rate_limited",
        analysis_error="Gemini API is temporarily rate limited. Wait for the limit to reset, then retry.",
    )
    catalog.save_transcript(other_session_id, other_transcript)
    assert not chroma_dir.exists()

    prompts = []

    def answer_from_prompt(prompt):
        prompts.append(prompt.to_string())
        return "The launch review is on Tuesday."

    monkeypatch.setattr(rag_engine, "get_llm", lambda: RunnableLambda(answer_from_prompt))

    real_build = services.build_rag_chain
    build_calls = []

    def track_build(saved_transcript, session_id=None, session_title=None):
        build_calls.append((saved_transcript, session_id))
        return real_build(saved_transcript, session_id=session_id, session_title=session_title)

    monkeypatch.setattr(services, "build_rag_chain", track_build)

    question = "When is the launch review?"
    assert services.answer_question(session_id, question) == "The launch review is on Tuesday."
    assert services.answer_question(session_id, question) == "The launch review is on Tuesday."

    assert build_calls == [(transcript, session_id)]
    assert len(prompts) == 2
    for prompt in prompts:
        assert "PRIMARY_TOKEN" in prompt
        assert "Tuesday" in prompt
        assert "OTHER_TOKEN" not in prompt
        assert "Friday" not in prompt

    store = vector_store.load_vector_store(session_id)
    assert store._collection.name == f"{vector_store.COLLECTION_PREFIX}_{session_id}"
    assert store._collection.count() == 1
    stored = store._collection.get(include=["documents", "metadatas"])
    assert stored["documents"] == [transcript]
    assert {metadata["session_id"] for metadata in stored["metadatas"]} == {session_id}

    collections = {collection.name for collection in store._client.list_collections()}
    assert collections == {f"{vector_store.COLLECTION_PREFIX}_{session_id}"}
