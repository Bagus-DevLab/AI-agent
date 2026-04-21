"""
agents/memory.py — Agent dengan memori percakapan persisten lokal.
"""

from langchain_core.messages import HumanMessage, AIMessage
from config import get_llm, SYSTEM_PROMPT_MEMORY, validate_config
from utils.memory import load_memori_lokal, simpan_memori_lokal, trim_history


def main():
    print("=== AI DENGAN MEMORI LOKAL ===\n")

    # Validasi konfigurasi
    errors = validate_config()
    if errors:
        print("❌ Konfigurasi tidak lengkap:")
        for err in errors:
            print(f"   - {err}")
        return

    llm = get_llm()
    chat_history = load_memori_lokal(SYSTEM_PROMPT_MEMORY)

    msg_count = len([m for m in chat_history if not isinstance(m, __import__('langchain_core.messages', fromlist=['SystemMessage']).SystemMessage)])
    if msg_count > 0:
        print(f"📝 Memuat {msg_count} pesan dari memori sebelumnya.")

    print("Ketik 'exit' untuk keluar, 'clear' untuk hapus memori.\n")

    while True:
        try:
            user_input = input("Lu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("👋 Bye!")
            break
        if user_input.lower() == "clear":
            from langchain_core.messages import SystemMessage
            chat_history = [SystemMessage(content=SYSTEM_PROMPT_MEMORY)]
            simpan_memori_lokal(chat_history)
            print("🗑️ Memori dihapus.\n")
            continue

        chat_history.append(HumanMessage(content=user_input))

        # Trim history sebelum kirim ke LLM untuk hindari token limit
        trimmed = trim_history(chat_history)

        try:
            response = llm.invoke(trimmed)
            print(f"\nAI: {response.content}\n")
            chat_history.append(AIMessage(content=response.content))
            simpan_memori_lokal(chat_history)
        except Exception as e:
            print(f"❌ Error: {e}\n")
            # Hapus pesan user terakhir jika gagal
            chat_history.pop()


if __name__ == "__main__":
    main()
