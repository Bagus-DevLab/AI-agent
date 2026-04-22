"""
agents/cloud.py — Agent dengan Cloud Memory via Cloudflare R2.
"""

import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import (
    get_llm, validate_r2_config,
    R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET_NAME,
    R2_MEMORY_KEY, MAX_MEMORY_MESSAGES, SYSTEM_PROMPT_MEMORY,
)

FILE_LOKAL = "temp_cloud.json"
FILE_REMOTE = R2_MEMORY_KEY


# ---------------------------------------------------------------------------
# R2 Client & Operations
# ---------------------------------------------------------------------------

def build_s3_client():
    """Buat boto3 S3 client untuk Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
    )


def load_dari_cloud(s3, chat_history: list) -> list:
    """Download dan load riwayat percakapan dari R2."""
    s3.download_file(R2_BUCKET_NAME, FILE_REMOTE, FILE_LOKAL)

    with open(FILE_LOKAL, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Format memori cloud tidak valid.")

    for item in data:
        if not isinstance(item, dict) or "role" not in item or "content" not in item:
            continue
        if item["role"] == "user":
            chat_history.append(HumanMessage(content=item["content"]))
        elif item["role"] == "ai":
            chat_history.append(AIMessage(content=item["content"]))

    return chat_history


def simpan_ke_cloud(s3, chat_history: list) -> None:
    """Serialisasi history, simpan ke lokal, lalu upload ke R2."""
    data = []
    for m in chat_history:
        if isinstance(m, HumanMessage):
            data.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            data.append({"role": "ai", "content": m.content})

    # Sliding window
    if len(data) > MAX_MEMORY_MESSAGES:
        data = data[-MAX_MEMORY_MESSAGES:]

    # Tulis ke file lokal
    try:
        with open(FILE_LOKAL, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except (IOError, OSError) as e:
        raise IOError(f"Gagal menulis file lokal '{FILE_LOKAL}': {e}")

    # Upload ke R2
    try:
        s3.upload_file(FILE_LOKAL, R2_BUCKET_NAME, FILE_REMOTE)
        print("Memori berhasil disimpan ke cloud.")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise ClientError(
            e.response,
            f"Upload ke R2 gagal (kode: {error_code}) — cek credential dan permission bucket",
        )
    except Exception as e:
        raise RuntimeError(f"Upload ke R2 gagal: {e}")


def cleanup_temp() -> None:
    """Hapus file temporary lokal."""
    if os.path.exists(FILE_LOKAL):
        os.remove(FILE_LOKAL)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== AI CLOUD MEMORY (R2) ===\n")

    errors = validate_r2_config()
    if errors:
        print("Konfigurasi R2 tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    llm = get_llm()
    s3 = build_s3_client()
    chat_history = [SystemMessage(content=SYSTEM_PROMPT_MEMORY)]

    # Load memory dari cloud
    print("Mengambil memori dari cloud...")
    try:
        chat_history = load_dari_cloud(s3, chat_history)
        msg_count = len([m for m in chat_history if not isinstance(m, SystemMessage)])
        print(f"Memori sinkron. {msg_count} pesan dimuat.")
    except s3.exceptions.NoSuchKey:
        print("Belum ada memori di cloud. Memulai obrolan baru.")
    except (ClientError, BotoCoreError) as e:
        print(f"Gagal terhubung ke R2: {e}")
        print("   Melanjutkan tanpa memori cloud.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Format memori cloud corrupt: {e}")
        print("   Memulai obrolan baru.")
    except (IOError, OSError) as e:
        print(f"Gagal membaca file lokal: {e}")

    print("Ketik 'exit' untuk keluar.\n")

    try:
        while True:
            try:
                user_input = input("Lu: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nBye!")
                break

            if not user_input:
                continue

            if user_input.lower() == "exit":
                print("Bye!")
                break

            chat_history.append(HumanMessage(content=user_input))

            try:
                response = llm.invoke(chat_history)
                print(f"\nAI: {response.content}\n")
                chat_history.append(AIMessage(content=response.content))
            except Exception as e:
                print(f"Error LLM: {e}\n")
                chat_history.pop()

    finally:
        # Upload sekali saat exit + cleanup
        print("\nMenyimpan memori ke cloud...")
        try:
            simpan_ke_cloud(s3, chat_history)
        except (ClientError, BotoCoreError) as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            print(f"Gagal upload ke R2 (kode: {error_code}): {e}")
        except RuntimeError as e:
            print(f"{e}")
        except (IOError, OSError) as e:
            print(f"Gagal menulis file lokal: {e}")
        finally:
            cleanup_temp()


if __name__ == "__main__":
    main()
