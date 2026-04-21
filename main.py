"""
main.py — Entry point utama project AI Agent.
Pilih agent yang mau dijalankan via menu interaktif.

Usage: 
    python main.py          # Menu interaktif
    python main.py basic    # Langsung jalankan agent tertentu
    python main.py rag .    # Agent RAG dengan target folder
"""

import sys


def show_menu():
    print("""
╔══════════════════════════════════════════╗
║         🤖 AI AGENT LAUNCHER            ║
╠══════════════════════════════════════════╣
║                                          ║
║  [1] Basic    — Test koneksi LLM         ║
║  [2] Memory   — Chat dengan memori lokal ║
║  [3] RAG      — Analisis codebase        ║
║  [4] Editor   — Baca & edit file         ║
║  [5] Cloud    — Chat dengan memori R2    ║
║                                          ║
║  [0] Exit                                ║
║                                          ║
╚══════════════════════════════════════════╝
""")


def main():
    # Cek apakah ada argument langsung
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
        arg_map = {
            "basic": "1", "1": "1",
            "memory": "2", "2": "2",
            "rag": "3", "3": "3",
            "editor": "4", "4": "4",
            "cloud": "5", "5": "5",
        }
        if choice in arg_map:
            run_agent(arg_map[choice])
            return
        else:
            print(f"❌ Agent '{choice}' tidak dikenal.")
            show_menu()
            return

    # Mode interaktif
    while True:
        show_menu()
        choice = input("Pilih agent [0-5]: ").strip()

        if choice == "0":
            print("Bye! 👋")
            break
        elif choice in ("1", "2", "3", "4", "5"):
            run_agent(choice)
        else:
            print("❌ Pilihan tidak valid. Coba lagi.")


def run_agent(choice):
    try:
        if choice == "1":
            from agents.basic import main as agent_main
            agent_main()
        elif choice == "2":
            from agents.memory import main as agent_main
            agent_main()
        elif choice == "3":
            from agents.rag import main as agent_main
            agent_main()
        elif choice == "4":
            from agents.editor import main as agent_main
            agent_main()
        elif choice == "5":
            from agents.cloud import main as agent_main
            agent_main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Agent dihentikan oleh user.")
    except Exception as e:
        print(f"\n❌ Error menjalankan agent: {e}")


if __name__ == "__main__":
    main()
