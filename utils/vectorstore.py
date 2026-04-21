"""
utils/vectorstore.py — Helper untuk membuat dan menyimpan vector store.
Digunakan oleh RAG agent untuk semantic search.
"""

import os
from typing import List, Dict, Optional

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import get_embeddings, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_TOP_K


def build_vectorstore(file_list: List[Dict], embeddings=None) -> FAISS:
    """
    Bangun FAISS vector store dari list file yang sudah di-scan.
    
    Args:
        file_list: List of dict dengan keys 'path' dan 'content'
        embeddings: Optional embedding model (default dari config)
    
    Returns:
        FAISS vector store
    """
    if not file_list:
        raise ValueError("Tidak ada file untuk di-index. Pastikan folder berisi file kode.")

    # Buat dokumen dengan metadata
    documents = []
    for f in file_list:
        doc = Document(
            page_content=f"// File Path: {f['path']}\n{f['content']}",
            metadata={"source": f["path"]},
        )
        documents.append(doc)

    print(f"   📄 {len(documents)} file → splitting chunks...")

    # Split jadi chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\nclass ", "\ndef ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    print(f"   🧩 {len(chunks)} chunks → building embeddings...")

    # Bangun vector store
    try:
        emb_model = embeddings if embeddings else get_embeddings()
        vectorstore = FAISS.from_documents(chunks, emb_model)
        print(f"   ✅ Vector store siap! ({len(chunks)} chunks indexed)")
        return vectorstore
    except Exception as e:
        raise RuntimeError(f"Gagal build vector store: {e}")


def save_vectorstore(vectorstore: FAISS, folder_path: str = "faiss_index"):
    """Simpan vector store ke lokal."""
    try:
        vectorstore.save_local(folder_path)
        print(f"   💾 Vector store disimpan ke: {folder_path}")
    except Exception as e:
        print(f"   ❌ Gagal menyimpan vector store: {e}")


def load_vectorstore(folder_path: str = "faiss_index") -> Optional[FAISS]:
    """Load vector store dari penyimpanan lokal."""
    try:
        embeddings = get_embeddings()
        return FAISS.load_local(
            folder_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        print(f"   ❌ Gagal memuat vector store: {e}")
        return None


def get_retriever(vectorstore: FAISS, top_k: int = None):
    """Buat retriever dari vector store."""
    k = top_k if top_k is not None else RETRIEVER_TOP_K
    return vectorstore.as_retriever(search_kwargs={"k": k})
