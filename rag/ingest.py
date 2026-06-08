"""
rag/ingest.py

Reads the SureRide FAQ document, chunks it, embeds it with Google Gemini,
and stores it in a local ChromaDB vector store.

Run once (or whenever the FAQ changes):
    python rag/ingest.py
"""
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

FAQ_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "sureride_faq.txt")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "sureride_faq"


def ingest():
    print(f"📄 Loading FAQ from: {FAQ_PATH}")
    loader = TextLoader(FAQ_PATH, encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
    chunks = splitter.split_documents(docs)
    print(f"✂️  Split into {len(chunks)} chunks")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_PATH,
    )
    print(f"✅ Stored {len(chunks)} chunks in ChromaDB at: {CHROMA_PATH}")


if __name__ == "__main__":
    ingest()
