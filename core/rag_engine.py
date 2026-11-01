from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.llm import get_llm
from core.vector_store import build_vector_store, load_vector_store, get_retriever

def format_docs(docs):
    return "\n\n".join(
        f"[Video: {doc.metadata.get('session_title') or doc.metadata.get('session_id', 'current')}]\n{doc.page_content}"
        for doc in docs
    )

def _build_chain(vector_store):
    """Create the common chain used for new and persisted transcript stores."""
    retriever = get_retriever(vector_store, k=4)
    return _build_chain_with_retriever(retriever)


def _build_chain_with_retriever(retriever):
    """Build a transcript Q&A chain from any LangChain-compatible retriever."""
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(

        [(
            "system",
            """You are an expert meeting assistant. Answer the user's question
based ONLY on the selected video transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the selected video transcripts."

Always be concise and precise. If quoting someone, mention it clearly.

Context from selected video transcripts:
{context}""",
        ),
        ("human", "{question}"),
    ]
    )

    #full LCEL Rag pipeline 

    rag_chain = (

        {"context" : retriever | RunnableLambda(format_docs),
         "question": RunnablePassthrough()
         }
         |prompt|llm|StrOutputParser()
    )

    return rag_chain


def build_rag_chain(
    transcript: str,
    session_id: str | None = None,
    session_title: str | None = None,
):
    """Create a RAG chain backed only by this transcript's collection."""
    if session_title:
        vector_store = build_vector_store(
            transcript,
            session_id=session_id,
            session_title=session_title,
        )
    else:
        vector_store = build_vector_store(transcript, session_id=session_id)
    return _build_chain(vector_store)


def load_rag_chain(session_id: str):
    """Recreate the same RAG chain for a previously processed session."""
    return _build_chain(load_vector_store(session_id))


def load_multi_session_rag_chain(session_ids: list[str], per_session_k: int = 2):
    """Build a balanced Q&A chain over several independently stored transcripts."""
    normalized_ids = list(dict.fromkeys(session_id.strip() for session_id in session_ids if session_id.strip()))
    if not normalized_ids:
        raise ValueError("Select at least one processed video for cross-video questions.")
    if len(normalized_ids) > 20:
        raise ValueError("A cross-video question can include at most 20 videos.")
    if per_session_k < 1:
        raise ValueError("Result count per video must be at least one.")

    stores = [(session_id, load_vector_store(session_id)) for session_id in normalized_ids]
    retrievers = [(session_id, get_retriever(store, k=per_session_k)) for session_id, store in stores]

    def retrieve(question: str):
        # Keep each video's contributions balanced rather than letting the
        # longest transcript dominate the combined context.
        per_video = [
            (session_id, retriever.invoke(question))
            for session_id, retriever in retrievers
        ]
        documents = []
        for position in range(per_session_k):
            for session_id, matches in per_video:
                if position < len(matches):
                    document = matches[position]
                    document.metadata = {**document.metadata, "session_id": session_id}
                    documents.append(document)
        return documents

    return _build_chain_with_retriever(RunnableLambda(retrieve))


def ask_question(rag_chain, question:str) -> str:
    if rag_chain is None:
        raise ValueError("The transcript question-answering session is not available.")
    if not question or not question.strip():
        raise ValueError("Please enter a question about the transcript.")
    return rag_chain.invoke(question.strip())
