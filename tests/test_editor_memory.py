"""
tests/test_editor_memory.py — Tests for editor-specific memory in agents/editor.py
====================================================================================

Priority 5: Editor memory load/save with consistent user/ai format.
"""

import os
import json
import pytest
from unittest.mock import patch

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.editor import load_editor_memory, save_editor_memory


# ============================================================================
# load_editor_memory
# ============================================================================

class TestLoadEditorMemory:

    def test_nonexistent_file_returns_empty(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        result = load_editor_memory(path)
        assert result == []

    def test_valid_data(self, tmp_memory_file, sample_memory_data):
        with open(tmp_memory_file, "w") as f:
            json.dump(sample_memory_data, f)

        result = load_editor_memory(tmp_memory_file)
        assert len(result) == 4
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)
        assert result[0].content == "Hello"

    def test_corrupt_json_returns_empty(self, tmp_memory_file):
        with open(tmp_memory_file, "w") as f:
            f.write("not valid json!!!")

        result = load_editor_memory(tmp_memory_file)
        assert result == []

    def test_not_a_list_returns_empty(self, tmp_memory_file):
        with open(tmp_memory_file, "w") as f:
            json.dump({"not": "a list"}, f)

        result = load_editor_memory(tmp_memory_file)
        assert result == []

    def test_skips_unknown_roles(self, tmp_memory_file):
        data = [
            {"role": "user", "content": "hello"},
            {"role": "system", "content": "should be skipped"},
            {"role": "human", "content": "also skipped"},
            {"role": "ai", "content": "reply"},
        ]
        with open(tmp_memory_file, "w") as f:
            json.dump(data, f)

        result = load_editor_memory(tmp_memory_file)
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)

    def test_non_string_content_converted(self, tmp_memory_file):
        data = [
            {"role": "user", "content": 42},
            {"role": "ai", "content": ["list", "content"]},
        ]
        with open(tmp_memory_file, "w") as f:
            json.dump(data, f)

        result = load_editor_memory(tmp_memory_file)
        assert len(result) == 2
        # Content should be converted to string
        assert isinstance(result[0].content, str)
        assert isinstance(result[1].content, str)

    def test_empty_list_returns_empty(self, tmp_memory_file):
        with open(tmp_memory_file, "w") as f:
            json.dump([], f)

        result = load_editor_memory(tmp_memory_file)
        assert result == []


# ============================================================================
# save_editor_memory
# ============================================================================

class TestSaveEditorMemory:

    def test_saves_correct_format(self, tmp_memory_file):
        history = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi!"),
        ]
        save_editor_memory(history, tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert len(data) == 2  # SystemMessage excluded
        assert data[0] == {"role": "user", "content": "Hello"}
        assert data[1] == {"role": "ai", "content": "Hi!"}

    def test_skips_system_messages(self, tmp_memory_file):
        history = [
            SystemMessage(content="System 1"),
            SystemMessage(content="System 2"),
        ]
        save_editor_memory(history, tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert data == []

    def test_sliding_window(self, tmp_memory_file):
        history = []
        for i in range(100):
            history.append(HumanMessage(content=f"msg {i}"))
            history.append(AIMessage(content=f"reply {i}"))

        with patch("agents.editor.MAX_MEMORY_MESSAGES", 10):
            save_editor_memory(history, tmp_memory_file)

        with open(tmp_memory_file, "r") as f:
            data = json.load(f)

        assert len(data) == 10

    def test_roundtrip(self, tmp_memory_file):
        """Save then load should produce equivalent messages."""
        original = [
            HumanMessage(content="Question?"),
            AIMessage(content="Answer!"),
            HumanMessage(content="Follow-up"),
            AIMessage(content="More info"),
        ]
        save_editor_memory(original, tmp_memory_file)
        loaded = load_editor_memory(tmp_memory_file)

        assert len(loaded) == len(original)
        for orig, load in zip(original, loaded):
            assert type(orig) == type(load)
            assert orig.content == load.content
