import pytest

import core.vector_store as vector_store


class FakeCollection:
    def __init__(self, count=1):
        self._count = count

    def count(self):
        return self._count


class FakeChroma:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._collection = FakeCollection()
        FakeChroma.created.append(self)

    @classmethod
    def from_documents(cls, **kwargs):
        return cls(**kwargs)

    def as_retriever(self, **kwargs):
        return kwargs


@pytest.fixture(autouse=True)
def fake_chroma(monkeypatch, tmp_path):
    FakeChroma.created = []
    monkeypatch.setattr(vector_store, "Chroma", FakeChroma)
    monkeypatch.setattr(vector_store, "get_embeddings", lambda: "embeddings")
    monkeypatch.setattr(vector_store, "CHROMA_DIR", str(tmp_path / "db"))


def test_build_uses_distinct_session_collection_names():
    first = vector_store.build_vector_store("first transcript", session_id="first")
    second = vector_store.build_vector_store("second transcript", session_id="second")
    assert first.kwargs["collection_name"] != second.kwargs["collection_name"]
    assert first.kwargs["documents"][0].metadata["session_id"] == "first"


def test_load_and_retriever_creation():
    store = vector_store.load_vector_store("session-a")
    assert store.kwargs["collection_name"] == "meeting_transcript_session-a"
    assert vector_store.get_retriever(store, k=2)["search_kwargs"] == {"k": 2}


def test_missing_store_is_reported(monkeypatch):
    class EmptyChroma(FakeChroma):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._collection = FakeCollection(0)

    monkeypatch.setattr(vector_store, "Chroma", EmptyChroma)
    with pytest.raises(vector_store.VectorStoreUnavailableError):
        vector_store.load_vector_store("missing")


def test_retriever_rejects_missing_store():
    with pytest.raises(vector_store.VectorStoreUnavailableError):
        vector_store.get_retriever(None)
