"""
agents/ — Package untuk semua AI agent.
Import dari sini untuk akses mudah ke semua agent.
"""

from agents.basic import main as run_basic
from agents.memory import main as run_memory
from agents.rag import main as run_rag
from agents.editor import main as run_editor
from agents.cloud import main as run_cloud

__all__ = ["run_basic", "run_memory", "run_rag", "run_editor", "run_cloud"]
