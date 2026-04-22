"""
tests/test_editor_security.py — Tests for security & parsing in agents/editor.py
=================================================================================

Priority 2: Security-critical path validation and SAVE block parsing.
"""

import os
import pytest

# We need to set up the module-level BASE_DIR before importing
import agents.editor as editor_module


# ============================================================================
# is_safe_path — Security sandbox enforcement
# ============================================================================

class TestIsSafePath:
    """Test path traversal prevention in editor agent."""

    @pytest.fixture(autouse=True)
    def setup_basedir(self, tmp_path):
        """Set BASE_DIR to a temp directory for each test."""
        self.original_basedir = editor_module.BASE_DIR
        editor_module.BASE_DIR = str(tmp_path)
        self.base = tmp_path
        yield
        editor_module.BASE_DIR = self.original_basedir

    def test_file_inside_basedir(self):
        target = os.path.join(str(self.base), "src", "main.py")
        assert editor_module.is_safe_path(target) is True

    def test_basedir_itself(self):
        assert editor_module.is_safe_path(str(self.base)) is True

    def test_traversal_with_dotdot(self):
        target = os.path.join(str(self.base), "..", "..", "etc", "passwd")
        assert editor_module.is_safe_path(target) is False

    def test_absolute_path_outside(self):
        assert editor_module.is_safe_path("/etc/passwd") is False

    def test_absolute_path_root(self):
        assert editor_module.is_safe_path("/") is False

    def test_prefix_bypass_attack(self, tmp_path):
        """
        /home/user/project_evil should NOT pass check for /home/user/project.
        The os.sep check prevents this.
        """
        # BASE_DIR is tmp_path, e.g. /tmp/pytest-xxx/test_xxx/
        # Attack: path that starts with same prefix but is a sibling
        evil_path = str(self.base) + "_evil"
        os.makedirs(evil_path, exist_ok=True)
        evil_file = os.path.join(evil_path, "steal.py")
        assert editor_module.is_safe_path(evil_file) is False

    def test_symlink_escape(self, tmp_path):
        """Symlink pointing outside BASE_DIR should be rejected."""
        # Create a symlink inside base that points to /tmp
        link_path = self.base / "escape_link"
        try:
            link_path.symlink_to("/tmp")
            target = os.path.join(str(link_path), "something.py")
            assert editor_module.is_safe_path(target) is False
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

    def test_relative_path_inside(self, monkeypatch):
        """Relative path that resolves inside BASE_DIR."""
        monkeypatch.chdir(str(self.base))
        assert editor_module.is_safe_path("./src/main.py") is True

    def test_empty_string(self):
        """Empty string resolves to cwd — may or may not be inside BASE_DIR."""
        # Just verify it doesn't crash
        result = editor_module.is_safe_path("")
        assert isinstance(result, bool)


# ============================================================================
# extract_save_blocks — Parsing SAVE/SAVE tags
# ============================================================================

class TestExtractSaveBlocks:

    def test_new_format_basic(self):
        """[SAVE: path]...[/SAVE] format."""
        text = (
            "Here is the fix:\n"
            "[SAVE: src/main.py]\n"
            "print('hello world')\n"
            "[/SAVE]\n"
            "Done!"
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 1
        filepath, content = blocks[0]
        assert filepath == "src/main.py"
        assert "print('hello world')" in content

    def test_new_format_strips_backtick_wrapper(self):
        """[SAVE: path] with optional backtick wrapper inside."""
        text = (
            "[SAVE: app.js]\n"
            "```javascript\n"
            "console.log('hi');\n"
            "```\n"
            "[/SAVE]"
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 1
        filepath, content = blocks[0]
        assert filepath == "app.js"
        assert "console.log('hi')" in content
        # Backtick markers should be stripped
        assert "```" not in content

    def test_multiple_save_blocks(self):
        text = (
            "[SAVE: file1.py]\n"
            "content1\n"
            "[/SAVE]\n"
            "\n"
            "[SAVE: file2.py]\n"
            "content2\n"
            "[/SAVE]"
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 2
        assert blocks[0][0] == "file1.py"
        assert blocks[1][0] == "file2.py"
        assert "content1" in blocks[0][1]
        assert "content2" in blocks[1][1]

    def test_no_save_blocks(self):
        text = "This is just a normal response with no file operations."
        blocks = editor_module.extract_save_blocks(text)
        assert blocks == []

    def test_legacy_format_with_backticks(self):
        """[SAVE: path] ```lang ... ``` format (no [/SAVE])."""
        text = (
            "Here:\n"
            "[SAVE: utils.py] ```python\n"
            "def foo():\n"
            "    return 42\n"
            "```\n"
            "Done."
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 1
        filepath, content = blocks[0]
        assert filepath == "utils.py"
        assert "def foo():" in content
        assert "return 42" in content

    def test_path_with_spaces_in_save_tag(self):
        """Extra spaces around path should be stripped."""
        text = (
            "[SAVE:   src/main.py  ]\n"
            "code here\n"
            "[/SAVE]"
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 1
        assert blocks[0][0] == "src/main.py"

    def test_nested_backticks_in_content(self):
        """Content containing nested backtick blocks."""
        text = (
            "[SAVE: README.md]\n"
            "# Title\n"
            "```python\n"
            "print('example')\n"
            "```\n"
            "End.\n"
            "[/SAVE]"
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 1
        # The content should preserve the inner backticks or at least
        # contain the meaningful content
        assert "Title" in blocks[0][1]

    def test_multiline_content_preserved(self):
        text = (
            "[SAVE: config.py]\n"
            "import os\n"
            "\n"
            "BASE_DIR = os.getcwd()\n"
            "DEBUG = True\n"
            "[/SAVE]"
        )
        blocks = editor_module.extract_save_blocks(text)
        assert len(blocks) == 1
        content = blocks[0][1]
        assert "import os" in content
        assert "BASE_DIR" in content
        assert "DEBUG = True" in content


# ============================================================================
# find_mentioned_files
# ============================================================================

class TestFindMentionedFiles:

    def test_finds_mentioned_file(self):
        docs = [
            {"path": "./src/scanner.py", "content": "..."},
            {"path": "./src/editor.py", "content": "..."},
            {"path": "./config.py", "content": "..."},
        ]
        result = editor_module.find_mentioned_files("fix the bug in scanner.py", docs)
        assert len(result) == 1
        assert result[0]["path"] == "./src/scanner.py"

    def test_no_mentioned_files(self):
        docs = [
            {"path": "./src/scanner.py", "content": "..."},
        ]
        result = editor_module.find_mentioned_files("explain the architecture", docs)
        assert result == []

    def test_multiple_mentioned_files(self):
        docs = [
            {"path": "./scanner.py", "content": "..."},
            {"path": "./editor.py", "content": "..."},
            {"path": "./config.py", "content": "..."},
        ]
        result = editor_module.find_mentioned_files(
            "compare scanner.py and editor.py", docs
        )
        assert len(result) == 2

    def test_case_insensitive_match(self):
        docs = [
            {"path": "./README.md", "content": "..."},
        ]
        result = editor_module.find_mentioned_files("update readme.md please", docs)
        assert len(result) == 1


# ============================================================================
# is_broad_query
# ============================================================================

class TestIsBroadQuery:

    @pytest.mark.parametrize("query", [
        "project structure",
        "overview",
        "struktur project",
        "all files",
        "daftar file",
        "file list",
    ])
    def test_explicit_broad_queries(self, query):
        assert editor_module.is_broad_query(query) is True

    @pytest.mark.parametrize("query", [
        "jelaskan semua file",       # action + subject
        "tampilkan struktur folder", # action + subject
        "list all files",            # action + subject
        "show project structure",    # action + subject
    ])
    def test_combined_broad_queries(self, query):
        assert editor_module.is_broad_query(query) is True

    @pytest.mark.parametrize("query", [
        "fix bug in scanner.py",
        "add error handling to the parse function",
        "what does line 42 do",
        "refactor the database connection",
    ])
    def test_specific_queries_not_broad(self, query):
        assert editor_module.is_broad_query(query) is False
