"""
agents/ — Package untuk semua AI agents.

Lazy imports agar tidak load semua dependency sekaligus.
"""

__all__ = ["run_basic", "run_memory", "run_rag", "run_editor", "run_cloud"]


def run_basic():
    from agents.basic import main
    main()


def run_memory():
    from agents.memory import main
    main()


def run_rag(**kwargs):
    from agents.rag import main
    main(**kwargs)


def run_editor(**kwargs):
    from agents.editor import main
    main(**kwargs)


def run_cloud():
    from agents.cloud import main
    main()
