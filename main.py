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


def ask_folder_path(default="."):
    """Minta user input folder path untuk agent yang membutuhkan."""
    path = input(f"📂 Masukkan path folder (default: '{default}'): ").strip()
    if not path:
        path = default
    if not __import__("os").path.isdir(path):
        print(f"❌ Folder '{path}' tidak ditemukan.")
        return None
    return path


def run_agent(choice):
    try:
        if choice == "1":
            from agents.basic import main as agent_main
            agent_main()

        elif choice == "2":
            from agents.memory import main as agent_main
            agent_main()

        elif choice == "3":
            folder = ask_folder_path()
            if folder:
                from agents.rag import main as agent_main
                agent_main(folder_path=folder)

        elif choice == "4":
            folder = ask_folder_path()
            if folder:
                from agents.editor import main as agent_main
                agent_main(folder_path=folder)

        elif choice == "5":
            from agents.cloud import main as agent_main
            agent_main()

        else:
            print(f"❌ Pilihan '{choice}' tidak valid.")

    except KeyboardInterrupt:
        print("\n👋 Agent dihentikan.")
    except ImportError as e:
        print(f"\n❌ Dependency belum terinstall: {e}")
        print("   Jalankan: pip install -r requirements.txt")
    except Exception as e:
        print(f"\n❌ Error tidak terduga: {e}")


def main():
    # Validasi konfigurasi saat startup
    from config import validate_config
    errors = validate_config()
    if errors:
        print("⚠️  Peringatan konfigurasi:")
        for err in errors:
            print(f"   - {err}")
        print()

    while True:
        show_menu()
        choice = input("Pilih agent [0-5]: ").strip()
        if choice == "0":
            print("👋 Bye!")
            break
        elif choice in ["1", "2", "3", "4", "5"]:
            run_agent(choice)
            input("\nTekan Enter untuk kembali ke menu...")
        else:
            print(f"❌ Pilihan '{choice}' tidak valid. Masukkan angka 0-5.")


if __name__ == "__main__":
    main()
