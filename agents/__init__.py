"""
agents/ — Package untuk semua AI agents.
Menggunakan lazy import untuk menghindari loading semua dependency sekaligus.
"""

# Lazy imports — hanya load saat benar-benar dipanggil
__all__ = ["run_basic", "run_memory", "run_rag", "run_editor", "run_cloud"]


def run_basic():
    from agents.basic import main
    main()


def run_memory():
    from agents.memory import main
    main()


def run_rag(*args, **kwargs):
    from agents.rag import main
    main(*args, **kwargs)


def run_editor(*args, **kwargs):
    from agents.editor import main
    main(*args, **kwargs)


def run_cloud():
    from agents.cloud import main
    main()
