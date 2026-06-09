"""
rag/retriever.py

Returns a LangChain retriever backed by the ChromaDB vector store.
The retriever is used by the rag_tool node in the booking agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# Always load .env from project root regardless of CWD
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "sureride_faq"


def get_retriever(k: int = 2):
    """
    Load the persisted ChromaDB collection and return a retriever.

    Args:
        k: Number of documents to return per query.

    Returns:
        A LangChain VectorStoreRetriever.
    """
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )
    return vectorstore.as_retriever(search_kwargs={"k": k})
