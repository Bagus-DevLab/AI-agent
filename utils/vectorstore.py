"""
utils/vectorstore.py — Helper untuk membuat vector store dari dokumen.
Digunakan oleh RAG agent untuk semantic search.
"""

from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import get_embeddings, CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVER_TOP_K


def build_vectorstore(file_list: list[dict]) -> FAISS:
    """
    Bangun FAISS vector store dari list file yang sudah di-scan.
    
    Args:
        file_list: List of {"path": str, "content": str}
        
    Returns:
        FAISS vector store yang siap diquery
        
    Raises:
        ValueError: Jika file_list kosong
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
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(chunks, embeddings)
        print(f"   ✅ Vector store siap! ({len(chunks)} chunks indexed)")
        return vectorstore
    except Exception as e:
        raise RuntimeError(f"Gagal build vector store: {e}")


def get_retriever(vectorstore: FAISS, top_k: int = None):
    """
    Buat retriever dari vector store.
    
    Args:
        vectorstore: FAISS vector store
        top_k: Jumlah dokumen yang di-retrieve (default dari config)
        
    Returns:
        Retriever object
    """
    k = top_k if top_k is not None else RETRIEVER_TOP_K
    return vectorstore.as_retriever(search_kwargs={"k": k})
