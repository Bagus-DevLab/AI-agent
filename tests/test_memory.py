"""
tests/test_memory.py — Tests for utils/memory.py
==================================================

Priority 4: Memory load/save and trim functions.
"""

import os
import json
import pytest
from unittest.mock import patch

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from utils.memory import load_memori_lokal, simpan_memori_lokal, trim_history


# ============================================================================
# load_memori_lokal
# ============================================================================

class TestLoadMemoriLokal:

    def test_nonexistent_file_returns_system_only(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        result = load_memori_lokal("You are helpful.", path)
        assert len(result) == 1
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "You are helpful."

    def test_valid_data_loads_correctly(self, tmp_memory_file, sample_memory_data):
        with open(tmp_memory_file, "w") as f:
            json.dump(sample_memory_data, f)

        result = load_memori_lokal("System prompt", tmp_memory_file)
        # 1 system + 4 messages
        assert len(result) == 5
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
        assert isinstance(result[2], AIMessage)
        assert result[1].content == "Hello"
        assert result[2].content == "Hi there!"

    def test_corrupt_json_returns_system_only(self, tmp_memory_file):
        with open(tmp_memory_file, "w") as f:
            f.write("{{{invalid json")

        result = load_memori_lokal("System", tmp_memory_file)
        assert len(result) == 1
        assert isinstance(result[0], SystemMessage)

    def test_json_not_a_list_returns_system_only(self, tmp_memory_file):
        with open(tmp_memory_file, "w") as f:
            json.dump({"key": "value"}, f)

        result = load_memori_lokal("System", tmp_memory_file)
        assert len(result) == 1

    def test_skips_items_without_role(self, tmp_memory_file):
        data = [
            {"content": "no role here"},
            {"role": "user", "content": "valid"},
        ]
        with open(tmp_memory_file, "w") as f:
            json.dump(data, f)

        result = load_memori_lokal("System", tmp_memory_file)
        assert len(result) == 2  # system + 1 valid

    def test_skips_non_dict_items(self, tmp_memory_file):
        data = [
            "just a string",
            42,
            {"role": "user", "content": "valid"},
        ]
        with open(tmp_memory_file, "w") as f:
            json.dump(data, f)

        result = load_memori_lokal("System", tmp_memory_file)
        assert len(result) == 2  # system + 1 valid

    def test_empty_list_returns_system_only(self, tmp_memory_file):
        with open(tmp_memory_file, "w") as f:
            json.dump([], f)

        result = load_memori_lokal("System", tmp_memory_file)
        assert len(result) == 1


# ============================================================================
# simpan_memori_lokal
# ============================================================================

class TestSimpanMemoriLokal:

    def test_creates_file_with_correct_json(self, tmp_memory_file):
        history = [
            SystemMessage(content="System"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi!"),
        ]
        simpan_memori_lokal(history, tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert len(data) == 2  # SystemMessage excluded
        assert data[0] == {"role": "user", "content": "Hello"}
        assert data[1] == {"role": "ai", "content": "Hi!"}

    def test_skips_system_messages(self, tmp_memory_file):
        history = [
            SystemMessage(content="System 1"),
            SystemMessage(content="System 2"),
            HumanMessage(content="Hello"),
        ]
        simpan_memori_lokal(history, tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["role"] == "user"

    def test_sliding_window_trims_old_messages(self, tmp_memory_file):
        """Only MAX_MEMORY_MESSAGES most recent messages are kept."""
        history = [SystemMessage(content="System")]
        # Add more messages than the limit
        for i in range(100):
            history.append(HumanMessage(content=f"msg {i}"))
            history.append(AIMessage(content=f"reply {i}"))

        with patch("utils.memory.MAX_MEMORY_MESSAGES", 10):
            simpan_memori_lokal(history, tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert len(data) == 10

    def test_empty_history_creates_empty_list(self, tmp_memory_file):
        simpan_memori_lokal([], tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert data == []


# ============================================================================
# trim_history
# ============================================================================

class TestTrimHistory:

    def test_preserves_system_message(self):
        history = [
            SystemMessage(content="System"),
            HumanMessage(content="msg1"),
            AIMessage(content="reply1"),
        ]
        result = trim_history(history, max_messages=10)
        assert isinstance(result[0], SystemMessage)

    def test_trims_excess_messages(self):
        history = [SystemMessage(content="System")]
        for i in range(20):
            history.append(HumanMessage(content=f"msg {i}"))
            history.append(AIMessage(content=f"reply {i}"))

        result = trim_history(history, max_messages=4)
        # 1 system + 4 chat messages
        assert len(result) == 5
        assert isinstance(result[0], SystemMessage)

    def test_keeps_most_recent(self):
        history = [
            SystemMessage(content="System"),
            HumanMessage(content="old"),
            AIMessage(content="old reply"),
            HumanMessage(content="new"),
            AIMessage(content="new reply"),
        ]
        result = trim_history(history, max_messages=2)
        assert len(result) == 3  # system + 2 recent
        assert result[1].content == "new"
        assert result[2].content == "new reply"

    def test_no_trim_needed(self):
        history = [
            SystemMessage(content="System"),
            HumanMessage(content="hello"),
        ]
        result = trim_history(history, max_messages=10)
        assert len(result) == 2

    def test_multiple_system_messages_preserved(self):
        """All SystemMessages should be preserved (edge case)."""
        history = [
            SystemMessage(content="System 1"),
            SystemMessage(content="System 2"),
            HumanMessage(content="hello"),
            AIMessage(content="hi"),
        ]
        result = trim_history(history, max_messages=10)
        system_msgs = [m for m in result if isinstance(m, SystemMessage)]
        assert len(system_msgs) == 2
