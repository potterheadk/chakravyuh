import os
import pymupdf  # PyMuPDF
import hashlib
import pickle
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaLLM
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain_ollama import OllamaEmbeddings

# Folder containing PDFs
PDF_FOLDER = "downloaded_content/"
CACHE_DIR = "cache/"  # Directory to store cache files

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_path(cache_key, prefix=""):
    """Generate a file path for a cache item based on its key."""
    hashed = hashlib.md5(cache_key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{prefix}_{hashed}.pkl")


def cache_exists(cache_key, prefix=""):
    """Check if a cache file exists."""
    cache_path = get_cache_path(cache_key, prefix)
    return os.path.exists(cache_path)


def load_from_cache(cache_key, prefix=""):
    """Load data from cache."""
    cache_path = get_cache_path(cache_key, prefix)
    try:
        with open(cache_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading from cache: {e}")
        return None


def save_to_cache(data, cache_key, prefix=""):
    """Save data to cache."""
    cache_path = get_cache_path(cache_key, prefix)
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return False


def extract_text_from_pdf(pdf_path):
    """Extracts text from a single PDF with caching."""
    # Create cache key based on file path and modification time
    mtime = os.path.getmtime(pdf_path)
    cache_key = f"{pdf_path}_{mtime}"

    # Check if cached version exists
    if cache_exists(cache_key, "pdf_text"):
        return load_from_cache(cache_key, "pdf_text")

    # Extract text if not cached
    text = ""
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        # Save to cache
        save_to_cache(text, cache_key, "pdf_text")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text


def load_pdfs(pdf_folder):
    """Loads text from all PDFs in the given folder."""
    # Create a cache key based on folder contents and modification times
    folder_hash = ""
    for file in sorted(os.listdir(pdf_folder)):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, file)
            mtime = os.path.getmtime(pdf_path)
            folder_hash += f"{file}_{mtime}_"

    # Check if cached version exists
    if cache_exists(folder_hash, "pdf_docs"):
        return load_from_cache(folder_hash, "pdf_docs")

    # Process PDFs if not cached
    documents = []
    for file in os.listdir(pdf_folder):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, file)
            text = extract_text_from_pdf(pdf_path)
            if text.strip():
                documents.append(Document(page_content=text, metadata={"source": file}))

    # Save to cache
    save_to_cache(documents, folder_hash, "pdf_docs")
    return documents


def get_or_create_vector_store(chunks, embeddings):
    """Get vector store from cache or create a new one."""
    # Create a cache key based on document content
    docs_content = "".join([doc.page_content[:100] for doc in chunks])
    cache_key = f"{docs_content}_{embeddings.model}"
    faiss_index_path = os.path.join(CACHE_DIR, f"faiss_index_{hashlib.md5(cache_key.encode()).hexdigest()}")

    # Check if the FAISS index exists on disk
    if os.path.exists(faiss_index_path):
        print("Loading vector store from cache...")
        try:
            # Use FAISS's built-in load method instead of pickle
            return FAISS.load_local(faiss_index_path, embeddings)
        except Exception as e:
            print(f"Error loading vector store from cache: {e}")
            # Fall back to creating a new one

    print("Creating new vector store...")
    vector_store = FAISS.from_documents(chunks, embeddings)

    # Save using FAISS's built-in save method
    try:
        vector_store.save_local(faiss_index_path)
        print(f"Vector store saved to {faiss_index_path}")
    except Exception as e:
        print(f"Error saving vector store: {e}")

    return vector_store


# Load and process PDFs
print("Loading PDFs...")
docs = load_pdfs(PDF_FOLDER)
if not docs:
    print("No PDFs found or failed to extract text.")
    exit()

# Text chunking for better retrieval
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(docs)

# Create embeddings and vector store
print("Setting up embeddings and vector store...")
embeddings = OllamaEmbeddings(model="llama3.2")
vector_store = get_or_create_vector_store(chunks, embeddings)
retriever = vector_store.as_retriever()

# Initialize LLM and RAG pipeline
print("Setting up LLM and RAG pipeline...")
llm = OllamaLLM(model="llama3.2")
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)


# Cache for query results
def get_cached_response(query, retriever_id):
    """Get cached response for a query if it exists."""
    cache_key = f"{query}_{retriever_id}"
    if cache_exists(cache_key, "query_result"):
        print("Loading query result from cache...")
        return load_from_cache(cache_key, "query_result")
    return None


def cache_response(response, query, retriever_id):
    """Cache a response for a query."""
    cache_key = f"{query}_{retriever_id}"
    print("Caching query result...")
    return save_to_cache(response, cache_key, "query_result")


# Query for summarization
query = "Summarize the key insights from these documents."

# Create a unique identifier for the retriever
retriever_id = hashlib.md5(chunks[0].page_content[:500].encode()).hexdigest()
# Check if we have a cached response
cached_response = get_cached_response(query, retriever_id)
if cached_response:
    response = cached_response
else:
    # Update to use the invoke method instead of calling directly
    response = qa_chain.invoke({"query": query})
    # Cache the response
    cache_response(response, query, retriever_id)

# Output Summary
print("\n### Summary:\n", response["result"])