"""
agents/basic.py — Agent sederhana untuk test koneksi LLM.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import get_llm, SYSTEM_PROMPT_BASIC, validate_config


def main():
    print("=== TEST KONEKSI LLM ===\n")

    # Validasi konfigurasi
    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT_BASIC),
        HumanMessage(content="Halo!")
    ]

    print("🔌 Menghubungi AI...")
    try:
        response = llm.invoke(messages)
        print(f"\n✅ AI: {response.content}")
    except Exception as e:
        print(f"❌ Gagal terhubung: {e}")
        print("\n💡 Tips:")
        print("   - Pastikan ENOWXAI_KEY dan ENOWXAI_URL sudah benar di .env")
        print("   - Pastikan LLM_MODEL adalah nama model yang valid")
        print(f"   - Model saat ini: {llm.model_name}")


if __name__ == "__main__":
    main()
