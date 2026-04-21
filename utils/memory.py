"""
memory.py — Modul untuk manajemen chat history / memori percakapan.
Mendukung penyimpanan lokal (JSON) dan cloud (Cloudflare R2).
"""

import json
import os
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import MEMORY_FILE, R2_BUCKET_NAME, CLOUD_FILE_NAME


def load_memori_lokal(system_prompt=""):
    """
    Load chat history dari file JSON lokal.
    
    Args:
        system_prompt: System message untuk inisialisasi jika belum ada history
        
    Returns:
        list: Chat history sebagai list of Messages
    """
    history = []
    if system_prompt:
        history.append(SystemMessage(content=system_prompt))

    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)

            for item in data:
                if item["role"] == "user":
                    history.append(HumanMessage(content=item["content"]))
                elif item["role"] == "ai":
                    history.append(AIMessage(content=item["content"]))

            print(f"📂 Memori lokal di-load ({len(data)} pesan)")
        except Exception as e:
            print(f"⚠️ Gagal load memori lokal: {e}")

    return history


def simpan_memori_lokal(history):
    """
    Simpan chat history ke file JSON lokal.
    
    Args:
        history: List of Messages (HumanMessage, AIMessage)
    """
    serializable = []
    for msg in history:
        if isinstance(msg, HumanMessage):
            serializable.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            serializable.append({"role": "ai", "content": msg.content})

    with open(MEMORY_FILE, "w") as f:
        json.dump(serializable, f, indent=4)


def load_memori_cloud(s3_client, system_prompt=""):
    """
    Load chat history dari Cloudflare R2.
    
    Args:
        s3_client: boto3 S3 client instance
        system_prompt: System message untuk inisialisasi
        
    Returns:
        list: Chat history sebagai list of Messages
    """
    from botocore.exceptions import ClientError

    history = []
    if system_prompt:
        history.append(SystemMessage(content=system_prompt))

    print("☁️ Mengecek memori di Cloudflare R2...")
    try:
        s3_client.download_file(R2_BUCKET_NAME, CLOUD_FILE_NAME, MEMORY_FILE)
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)

        for item in data:
            if item["role"] == "user":
                history.append(HumanMessage(content=item["content"]))
            elif item["role"] == "ai":
                history.append(AIMessage(content=item["content"]))

        print(f"✅ Memori cloud di-load ({len(data)} pesan)")
    except ClientError:
        print("ℹ️ Belum ada memori di Cloud, memulai lembaran baru.")

    return history


def simpan_memori_cloud(s3_client, history):
    """
    Simpan chat history ke Cloudflare R2.
    
    Args:
        s3_client: boto3 S3 client instance
        history: List of Messages
    """
    # Simpan lokal dulu
    simpan_memori_lokal(history)

    # Upload ke R2
    print("☁️ Membackup obrolan ke R2...")
    try:
        s3_client.upload_file(MEMORY_FILE, R2_BUCKET_NAME, CLOUD_FILE_NAME)
        print("✅ Backup Cloud selesai!")
    except Exception as e:
        print(f"⚠️ Gagal backup ke cloud: {e}")
