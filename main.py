"""
main.py — Entry point utama untuk memilih Agent.
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
        else:
            print(f"❌ Pilihan '{choice}' tidak valid.")
    except KeyboardInterrupt:
        print("\n👋 Agent dihentikan.")
    except Exception as e:
        print(f"\n❌ Error tidak terduga: {e}")

def main():
    while True:
        show_menu()
        choice = input("Pilih agent [0-5]: ").strip()
        if choice == "0":
            print("👋 Bye!")
            break
        elif choice in ["1", "2", "3", "4", "5"]:
            run_agent(choice)
            input("\nTekan Enter untuk kembali ke menu...")

if __name__ == "__main__":
    main()