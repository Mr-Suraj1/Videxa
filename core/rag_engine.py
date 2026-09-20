from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.llm import get_llm
from core.vector_store import build_vector_store, load_vector_store, get_retriever

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])

def _build_chain(vector_store):
    """Create the common chain used for new and persisted transcript stores."""
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(

        [(
            "system",
            """You are an expert meeting assistant. Answer the user's question 
based ONLY on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
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


def build_rag_chain(transcript: str, session_id: str | None = None):
    """Create a RAG chain backed only by this transcript's collection."""
    return _build_chain(build_vector_store(transcript, session_id=session_id))


def load_rag_chain(session_id: str):
    """Recreate the same RAG chain for a previously processed session."""
    return _build_chain(load_vector_store(session_id))


def ask_question(rag_chain, question:str) -> str:
    if rag_chain is None:
        raise ValueError("The transcript question-answering session is not available.")
    if not question or not question.strip():
        raise ValueError("Please enter a question about the transcript.")
    return rag_chain.invoke(question.strip())
