import os
from typing import List, Optional, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.pdf_manager import list_uploaded_pdfs, load_pdf_documents, UPLOAD_DIR

CHROMA_DB_DIR = os.path.join("data", "chroma_db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embeddings = None
_vector_store = None

import streamlit as st

@st.cache_resource
def get_embeddings():
    # Load local HuggingFace embeddings once and cache in memory
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

@st.cache_resource
def get_vector_store():
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(
        collection_name="psychology_docs",
        embedding_function=embeddings,
        persist_directory=CHROMA_DB_DIR
    )

def index_pdf_file(file_path: str) -> int:
    """Indexes a single PDF into the local Chroma vector store."""
    docs = load_pdf_documents(file_path)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)
    if not chunks:
        return 0
    
    vector_store = get_vector_store()
    filename = os.path.basename(file_path)
    
    # Remove existing chunks for this file if present
    try:
        vector_store.delete(where={"source": filename})
    except Exception:
        pass
    
    vector_store.add_documents(chunks)
    return len(chunks)

def remove_pdf_from_index(filename: str):
    """Deletes all vector chunks associated with a specific filename."""
    vector_store = get_vector_store()
    try:
        vector_store.delete(where={"source": filename})
    except Exception as e:
        print(f"Error removing {filename} from vector store: {e}")

def reindex_all_pdfs() -> Dict[str, int]:
    """Clears vector store and re-indexes all PDFs in UPLOAD_DIR."""
    pdf_files = list_uploaded_pdfs()
    results = {}
    
    global _vector_store
    if _vector_store is not None:
        try:
            _vector_store.delete_collection()
        except Exception:
            pass
        _vector_store = None

    vector_store = get_vector_store()
    
    for filename in pdf_files:
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            num_chunks = index_pdf_file(file_path)
            results[filename] = num_chunks
        except Exception as e:
            print(f"Error indexing {filename}: {e}")
            results[filename] = 0
            
    return results

def search_docs(query: str, selected_filenames: Optional[List[str]] = None, k: int = 4) -> List[Document]:
    """Retrieves relevant document chunks filtered by selected_filenames."""
    vector_store = get_vector_store()
    
    filter_dict = None
    if selected_filenames:
        if len(selected_filenames) == 1:
            filter_dict = {"source": selected_filenames[0]}
        elif len(selected_filenames) > 1:
            filter_dict = {"source": {"$in": selected_filenames}}
            
    try:
        if filter_dict:
            results = vector_store.similarity_search(query, k=k, filter=filter_dict)
        else:
            results = vector_store.similarity_search(query, k=k)
        return results
    except Exception as e:
        print(f"Vector search error with filter {filter_dict}: {e}")
        # Fallback search without filter if Chroma filter syntax varies
        results = vector_store.similarity_search(query, k=k*2)
        if selected_filenames:
            results = [doc for doc in results if doc.metadata.get("source") in selected_filenames][:k]
        return results

def get_indexed_stats() -> Dict[str, Any]:
    """Returns statistics about indexed files and chunk counts."""
    vector_store = get_vector_store()
    try:
        col = vector_store._collection
        count = col.count()
        return {"total_chunks": count}
    except Exception:
        return {"total_chunks": 0}
