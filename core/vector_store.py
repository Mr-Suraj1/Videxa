import hashlib
import re
from pathlib import Path
from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_PREFIX = "meeting_transcript"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device" : 'cpu'}
    )

class VectorStoreUnavailableError(RuntimeError):
    """Raised when a requested transcript index is absent or empty."""


def session_id_for_transcript(transcript: str) -> str:
    """Return a stable, non-identifying collection suffix for a transcript."""
    if not transcript or not transcript.strip():
        raise ValueError("Cannot create a vector store for an empty transcript.")
    return hashlib.sha256(transcript.strip().encode("utf-8")).hexdigest()[:16]


def _collection_name(session_id: str) -> str:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", session_id).strip("_")
    if not safe_id:
        raise ValueError("A valid session ID is required for the vector store.")
    return f"{COLLECTION_PREFIX}_{safe_id}"


def build_vector_store(
    transcript: str,
    session_id: str | None = None,
    session_title: str | None = None,
) -> Chroma:
    """Upsert transcript chunks with stable IDs into this session's collection."""
    resolved_session_id = session_id or session_id_for_transcript(transcript)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50
    )
    chunks = splitter.split_text(transcript)
    if not chunks:
        raise ValueError("Cannot create a vector store for an empty transcript.")

    docs = []
    for i, chunk in enumerate(chunks):
        metadata = {"chunk_index": i, "session_id": resolved_session_id}
        if session_title:
            metadata["session_title"] = session_title[:500]
        docs.append(Document(page_content=chunk, metadata=metadata))

    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=_collection_name(resolved_session_id),
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    ids = [f"{resolved_session_id}_{index}" for index in range(len(docs))]
    # Delete existing docs with these IDs first so retry analysis doesn't crash
    try:
        vector_store._collection.delete(ids=ids)
    except Exception:
        pass
    vector_store.add_documents(documents=docs, ids=ids)

    return vector_store



def delete_vector_store(session_id: str) -> None:
    """Delete the ChromaDB collection for a session, silently if absent."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        client.delete_collection(_collection_name(session_id))
    except Exception:
        pass  # collection may not exist — that's fine


def load_vector_store(session_id: str) -> Chroma:
    """Load an existing non-empty, transcript-specific collection."""
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=_collection_name(session_id),
        embedding_function= embeddings,
        persist_directory=CHROMA_DIR
    )

    try:
        if vector_store._collection.count() == 0:
            raise VectorStoreUnavailableError(
                "No transcript index is available for this session. Process the video first."
            )
    except VectorStoreUnavailableError:
        raise
    except Exception as exc:
        raise VectorStoreUnavailableError(
            "The transcript index could not be opened for this session."
        ) from exc
    return vector_store

def get_retriever(vector_store : Chroma, k :int = 4):
    if vector_store is None:
        raise VectorStoreUnavailableError("A transcript vector store is required to answer questions.")
    if k < 1:
        raise ValueError("Retriever result count must be at least one.")
    return vector_store.as_retriever(
        search_type = 'similarity',
        search_kwargs = {"k":k}
    )
