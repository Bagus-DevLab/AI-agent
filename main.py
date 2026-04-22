"""
main.py — Entry point utama untuk memilih dan menjalankan Agent.
"""

import os


# ---------------------------------------------------------------------------
# Menu & Input
# ---------------------------------------------------------------------------

MENU_TEXT = """
╔══════════════════════════════════════════╗
║         AI AGENT LAUNCHER               ║
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
"""

VALID_CHOICES = {"1", "2", "3", "4", "5"}

# Agent yang membutuhkan folder path sebagai input
AGENTS_NEED_FOLDER = {"3", "4"}


def ask_folder_path(default: str = ".") -> str | None:
    """Minta user input folder path. Return None jika folder tidak valid."""
    path = input(f"Masukkan path folder (default: '{default}'): ").strip()
    path = path or default

    if not os.path.isdir(path):
        print(f"Folder '{path}' tidak ditemukan.")
        return None

    return path


# ---------------------------------------------------------------------------
# Agent Runner
# ---------------------------------------------------------------------------

def run_agent(choice: str) -> None:
    """Jalankan agent berdasarkan pilihan user."""
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

    except KeyboardInterrupt:
        print("\nAgent dihentikan.")
    except Exception as e:
        print(f"\nError: {e}")


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------

def main() -> None:
    """Loop utama: tampilkan menu, terima input, jalankan agent."""
    while True:
        print(MENU_TEXT)
        choice = input("Pilih agent [0-5]: ").strip()

        if choice == "0":
            print("Bye!")
            break
        elif choice in VALID_CHOICES:
            run_agent(choice)
            input("\nTekan Enter untuk kembali ke menu...")
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    main()
