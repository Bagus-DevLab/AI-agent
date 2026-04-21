"""
basic.py — Agent paling dasar untuk test koneksi ke LLM.
Pengganti agent_awal.py yang sudah di-refactor.

Usage: python -m agents.basic
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, SYSTEM_PROMPT_BASIC


def main():
    print("=== TEST KONEKSI LLM ===\n")

    # Inisialisasi LLM dari config terpusat
    llm = get_llm(temperature=0.7)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT_BASIC),
        HumanMessage(content="Halo! Perkenalkan dirimu dong."),
    ]

    print("🔌 Mengirim pesan ke LLM...")
    try:
        response = llm.invoke(messages)
        print(f"\n✅ AI: {response.content}\n")
    except Exception as e:
        print(f"\n❌ Error koneksi: {e}")
        print("Cek kembali ENOWXAI_KEY dan ENOWXAI_URL di file .env")


if __name__ == "__main__":
    main()
