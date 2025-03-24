import os
import hashlib
import pickle
import pymupdf  # PyMuPDF
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document

# Constants
CACHE_DIR = "cache/"
PDF_FOLDER = "downloaded_content/"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_path(cache_key, prefix=""):
    """Generate a file path for a cache item based on its key."""
    hashed = hashlib.md5(cache_key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{prefix}_{hashed}.pkl")


def cache_exists(cache_key, prefix=""):
    """Check if a cache file exists."""
    return os.path.exists(get_cache_path(cache_key, prefix))


def load_from_cache(cache_key, prefix=""):
    """Load data from cache."""
    try:
        with open(get_cache_path(cache_key, prefix), 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading from cache: {e}")
        return None


def save_to_cache(data, cache_key, prefix=""):
    """Save data to cache."""
    try:
        with open(get_cache_path(cache_key, prefix), 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return False


def extract_text_from_pdf(pdf_path):
    """Extract text from a single PDF with caching."""
    cache_key = f"{pdf_path}_{os.path.getmtime(pdf_path)}"

    if cache_exists(cache_key, "pdf_text"):
        return load_from_cache(cache_key, "pdf_text")

    text = ""
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        save_to_cache(text, cache_key, "pdf_text")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return text


def load_pdfs():
    """Loads text from all PDFs in the given folder."""
    folder_hash = "".join([f"{file}_{os.path.getmtime(os.path.join(PDF_FOLDER, file))}_"
                           for file in sorted(os.listdir(PDF_FOLDER)) if file.endswith(".pdf")])

    if cache_exists(folder_hash, "pdf_docs"):
        return load_from_cache(folder_hash, "pdf_docs")

    documents = []
    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(PDF_FOLDER, file)
            text = extract_text_from_pdf(pdf_path)
            if text.strip():
                documents.append(Document(page_content=text, metadata={"source": file}))

    save_to_cache(documents, folder_hash, "pdf_docs")
    return documents


def get_vector_store(chunks, embeddings):
    """Get or create FAISS vector store."""
    docs_content = "".join([doc.page_content[:100] for doc in chunks])
    cache_key = f"{docs_content}_{embeddings.model}"
    faiss_index_path = os.path.join(CACHE_DIR, f"faiss_index_{hashlib.md5(cache_key.encode()).hexdigest()}")

    if os.path.exists(faiss_index_path):
        print("Loading vector store from cache...")
        try:
            return FAISS.load_local(faiss_index_path, embeddings)
        except Exception as e:
            print(f"Error loading vector store from cache: {e}")

    print("Creating new vector store...")
    vector_store = FAISS.from_documents(chunks, embeddings)

    try:
        vector_store.save_local(faiss_index_path)
        print(f"Vector store saved to {faiss_index_path}")
    except Exception as e:
        print(f"Error saving vector store: {e}")

    return vector_store


def summarize_pdfs():
    """Summarizes all PDFs in the folder using RAG."""
    print("Loading PDFs...")
    docs = load_pdfs()
    if not docs:
        return "No PDFs found or failed to extract text."

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)

    embeddings = OllamaEmbeddings(model="llama3.2")
    vector_store = get_vector_store(chunks, embeddings)
    retriever = vector_store.as_retriever()

    llm = OllamaLLM(model="llama3.2")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)

    query = "Summarize the key insights from these documents."
    response = qa_chain.invoke({"query": query})

    return response["result"]
