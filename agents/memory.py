"""
memory.py — Agent dengan conversation memory (penyimpanan lokal).
Pengganti agent_memori.py yang sudah di-refactor.

Usage: python -m agents.memory
"""

from langchain_core.messages import HumanMessage
from config import get_llm, SYSTEM_PROMPT_MEMORY
from utils.memory import load_memori_lokal, simpan_memori_lokal


def main():
    print("=== AI DENGAN MEMORI PERMANEN ===")
    print("Ketik 'exit' untuk keluar.\n")

    # Inisialisasi
    llm = get_llm()
    chat_history = load_memori_lokal(system_prompt=SYSTEM_PROMPT_MEMORY)

    # Info jumlah pesan tersimpan
    msg_count = len([m for m in chat_history if not hasattr(m, 'type') or m.type != 'system'])
    if msg_count > 0:
        print(f"--- [INFO] Melanjutkan obrolan terakhir ({msg_count} pesan tersimpan) ---\n")

    while True:
        user_input = input("Lu: ")
        if user_input.lower() == "exit":
            print("Bye! 👋")
            break

        chat_history.append(HumanMessage(content=user_input))

        print("AI sedang berpikir...")
        try:
            response = llm.invoke(chat_history)
            from langchain_core.messages import AIMessage
            chat_history.append(AIMessage(content=response.content))

            # Simpan ke file
            simpan_memori_lokal(chat_history)

            print(f"\nAI: {response.content}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()
