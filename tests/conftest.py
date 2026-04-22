"""
tests/conftest.py — Shared fixtures for all test modules.
"""

import os
import json
import pytest


@pytest.fixture
def tmp_workspace(tmp_path):
    """
    Create a temporary workspace with sample files for scanner tests.
    Returns the path to the workspace directory.
    """
    # Python file
    py_file = tmp_path / "main.py"
    py_file.write_text("print('hello world')\n", encoding="utf-8")

    # JS file
    js_file = tmp_path / "app.js"
    js_file.write_text("console.log('hello');\n", encoding="utf-8")

    # Nested directory
    sub = tmp_path / "src"
    sub.mkdir()
    nested_py = sub / "utils.py"
    nested_py.write_text("def helper(): pass\n", encoding="utf-8")

    # Hidden file (should be skipped)
    hidden = tmp_path / ".secret"
    hidden.write_text("SECRET_KEY=abc\n", encoding="utf-8")

    # .env file (should be skipped)
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=xyz\n", encoding="utf-8")

    # node_modules dir (should be skipped)
    nm = tmp_path / "node_modules"
    nm.mkdir()
    nm_file = nm / "index.js"
    nm_file.write_text("module.exports = {}\n", encoding="utf-8")

    # venv dir (should be skipped)
    venv = tmp_path / "venv"
    venv.mkdir()
    venv_file = venv / "activate.py"
    venv_file.write_text("# venv\n", encoding="utf-8")

    # Lock file (should be skipped)
    lock = tmp_path / "package-lock.json"
    lock.write_text("{}\n", encoding="utf-8")

    # Editor memory file (should be skipped)
    editor_mem = tmp_path / "editor_myproject.json"
    editor_mem.write_text("[]", encoding="utf-8")

    # chat_memory.json (should be skipped)
    chat_mem = tmp_path / "chat_memory.json"
    chat_mem.write_text("[]", encoding="utf-8")

    # Unsupported extension (should be skipped)
    bin_file = tmp_path / "data.bin"
    bin_file.write_bytes(b"\x00\x01\x02")

    # .git directory (should be skipped)
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    git_file = git_dir / "config"
    git_file.write_text("[core]\n", encoding="utf-8")

    return tmp_path


@pytest.fixture
def tmp_memory_file(tmp_path):
    """Return a path for a temporary memory JSON file."""
    return str(tmp_path / "test_memory.json")


@pytest.fixture
def sample_memory_data():
    """Sample valid memory data."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "ai", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "ai", "content": "I'm doing well!"},
    ]
