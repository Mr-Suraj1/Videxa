import pytest
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

import core.rag_engine as rag_engine


def test_build_and_load_share_the_same_chain_builder(monkeypatch):
    calls = []
    monkeypatch.setattr(rag_engine, "build_vector_store", lambda transcript, session_id=None: "new-store")
    monkeypatch.setattr(rag_engine, "load_vector_store", lambda session_id: "saved-store")
    monkeypatch.setattr(rag_engine, "_build_chain", lambda store: calls.append(store) or store)
    assert rag_engine.build_rag_chain("transcript", "one") == "new-store"
    assert rag_engine.load_rag_chain("one") == "saved-store"
    assert calls == ["new-store", "saved-store"]


def test_rag_chain_constructs_with_mocked_retriever_and_llm(monkeypatch):
    monkeypatch.setattr(
        rag_engine,
        "get_retriever",
        lambda store, k: RunnableLambda(lambda _: [Document(page_content="meeting context")]),
    )
    monkeypatch.setattr(rag_engine, "get_llm", lambda: RunnableLambda(lambda _: "mocked answer"))
    assert rag_engine._build_chain(object()).invoke("What happened?") == "mocked answer"


@pytest.mark.parametrize("question", ["", "   "])
def test_ask_question_rejects_empty_question(question):
    with pytest.raises(ValueError):
        rag_engine.ask_question(object(), question)


def test_ask_question_rejects_missing_chain():
    with pytest.raises(ValueError):
        rag_engine.ask_question(None, "question")
