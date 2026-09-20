import hashlib
import re
from pathlib import Path
from langchain_chroma import Chroma 
from langchain_community.embeddings import HuggingFaceEmbeddings
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


def build_vector_store(transcript: str, session_id: str | None = None) -> Chroma:
    """Build a transcript-specific Chroma collection without touching old data."""
    resolved_session_id = session_id or session_id_for_transcript(transcript)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50
    )
    chunks = splitter.split_text(transcript)
    if not chunks:
        raise ValueError("Cannot create a vector store for an empty transcript.")

    docs = [
        Document(page_content=chunk, metadata={'chunk_index': i, 'session_id': resolved_session_id})
        for i,chunk in enumerate(chunks)
    ]

    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents= docs,
        embedding=embeddings,
        collection_name=_collection_name(resolved_session_id),
        persist_directory=CHROMA_DIR
    )

    return vector_store



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
