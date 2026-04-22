"""
agents/basic.py — Agent sederhana untuk test koneksi LLM.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, SYSTEM_PROMPT_BASIC, validate_config


def main() -> None:
    print("=== TEST KONEKSI LLM ===\n")

    errors = validate_config()
    if errors:
        print("Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_BASIC),
        HumanMessage(content="Halo!"),
    ]

    print("Menghubungi AI...")
    try:
        response = llm.invoke(messages)
        print(f"\nAI: {response.content}")
    except Exception as e:
        print(f"Gagal terhubung: {e}")
        print("\nTips:")
        print("   - Pastikan ENOWXAI_KEY dan ENOWXAI_URL sudah benar di .env")
        print("   - Pastikan LLM_MODEL adalah nama model yang valid")


if __name__ == "__main__":
    main()
