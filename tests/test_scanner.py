"""
tests/test_scanner.py — Tests for utils/scanner.py
====================================================

Priority 1: Regression tests for the bug where scan_workspace
returned tuples instead of dicts. Also covers filtering logic.
"""

import os
import pytest
from utils.scanner import (
    scan_workspace,
    get_file_list,
    should_skip_file,
    SKIP_FILE_PATTERNS,
    SKIP_DIRS,
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE,
)


# ============================================================================
# scan_workspace — Return type & structure (BUG REGRESSION)
# ============================================================================

class TestScanWorkspaceReturnType:
    """Regression tests: scan_workspace MUST return dicts, not tuples."""

    def test_returns_tuple_of_list_and_int(self, tmp_workspace):
        result = scan_workspace(str(tmp_workspace))
        assert isinstance(result, tuple), "scan_workspace must return a tuple"
        assert len(result) == 2, "Tuple must have exactly 2 elements"
        assert isinstance(result[0], list), "First element must be a list"
        assert isinstance(result[1], int), "Second element must be an int"

    def test_items_are_dicts_not_tuples(self, tmp_workspace):
        """THE critical regression test for the bug fix."""
        results, _ = scan_workspace(str(tmp_workspace))
        assert len(results) > 0, "Should find at least one file"
        for item in results:
            assert isinstance(item, dict), (
                f"Each item must be a dict, got {type(item).__name__}: {item!r}"
            )
            # Explicitly verify it's NOT a tuple (the old bug)
            assert not isinstance(item, tuple), (
                f"BUG REGRESSION: item is a tuple! Got: {item!r}"
            )

    def test_dict_has_path_key(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        for item in results:
            assert "path" in item, f"Dict missing 'path' key: {item!r}"

    def test_dict_has_content_key(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        for item in results:
            assert "content" in item, f"Dict missing 'content' key: {item!r}"

    def test_path_is_string(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        for item in results:
            assert isinstance(item["path"], str)

    def test_content_is_string(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        for item in results:
            assert isinstance(item["content"], str)

    def test_path_is_relative_with_dot_prefix(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        for item in results:
            assert item["path"].startswith("./"), (
                f"Path should start with './', got: {item['path']}"
            )

    def test_count_matches_list_length(self, tmp_workspace):
        results, count = scan_workspace(str(tmp_workspace))
        assert count == len(results), (
            f"Count ({count}) must equal len(results) ({len(results)})"
        )


# ============================================================================
# scan_workspace — Content correctness
# ============================================================================

class TestScanWorkspaceContent:

    def test_reads_file_content_correctly(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        # Find main.py in results
        main_py = [r for r in results if r["path"].endswith("main.py")]
        assert len(main_py) == 1, "Should find exactly one main.py"
        assert "hello world" in main_py[0]["content"]

    def test_reads_nested_files(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        nested = [r for r in results if "utils.py" in r["path"]]
        assert len(nested) == 1, "Should find nested utils.py"
        assert "def helper" in nested[0]["content"]

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        results, count = scan_workspace(str(empty))
        assert results == []
        assert count == 0


# ============================================================================
# scan_workspace — File filtering
# ============================================================================

class TestScanWorkspaceFiltering:

    def test_skips_hidden_files(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any(".secret" in p for p in paths), "Hidden files should be skipped"

    def test_skips_hidden_directories(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any(".git" in p for p in paths), ".git dir should be skipped"

    def test_skips_node_modules(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any("node_modules" in p for p in paths)

    def test_skips_venv(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any("venv" in p for p in paths)

    def test_skips_env_file(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any(p.endswith(".env") for p in paths)

    def test_skips_lock_files(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any("package-lock.json" in p for p in paths)

    def test_skips_editor_memory_files(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any("editor_myproject.json" in p for p in paths)

    def test_skips_chat_memory(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any("chat_memory.json" in p for p in paths)

    def test_skips_unsupported_extensions(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        assert not any(p.endswith(".bin") for p in paths)

    def test_includes_supported_extensions(self, tmp_workspace):
        results, _ = scan_workspace(str(tmp_workspace))
        paths = [r["path"] for r in results]
        py_files = [p for p in paths if p.endswith(".py")]
        js_files = [p for p in paths if p.endswith(".js")]
        assert len(py_files) >= 1, "Should include .py files"
        assert len(js_files) >= 1, "Should include .js files"

    def test_skips_large_files(self, tmp_path):
        """Files larger than MAX_FILE_SIZE should be skipped."""
        big_file = tmp_path / "huge.py"
        big_file.write_text("x" * (MAX_FILE_SIZE + 1), encoding="utf-8")
        small_file = tmp_path / "small.py"
        small_file.write_text("print('ok')\n", encoding="utf-8")

        results, count = scan_workspace(str(tmp_path))
        paths = [r["path"] for r in results]
        assert any("small.py" in p for p in paths), "Small file should be included"
        assert not any("huge.py" in p for p in paths), "Huge file should be skipped"


# ============================================================================
# should_skip_file
# ============================================================================

class TestShouldSkipFile:

    @pytest.mark.parametrize("filename", [
        "chat_memory.json",
        "memory.json",
        "temp_cloud.json",
        ".env",
        ".env.example",
        ".env.local",
        "package-lock.json",
        "yarn.lock",
    ])
    def test_exact_match_skipped(self, filename):
        assert should_skip_file(filename) is True

    @pytest.mark.parametrize("filename", [
        "editor_myproject.json",
        "editor_belajar_langchain.json",
        "rag_something.json",
        "memory_backup.json",
    ])
    def test_prefix_pattern_skipped(self, filename):
        assert should_skip_file(filename) is True

    @pytest.mark.parametrize("filename", [
        "main.py",
        "config.py",
        "scanner.py",
        "editor.py",
        "README.md",
        "package.json",  # Not package-lock.json
    ])
    def test_normal_files_not_skipped(self, filename):
        assert should_skip_file(filename) is False

    # --- .env variant tests (H2 fix) ---

    @pytest.mark.parametrize("filename", [
        ".env.production",
        ".env.staging",
        ".env.development",
        ".env.test",
        ".env.secret",
        ".env.backup",
    ])
    def test_env_variants_skipped(self, filename):
        """Semua varian .env.* harus di-skip untuk mencegah kebocoran secret."""
        assert should_skip_file(filename) is True

    def test_env_without_dot_suffix_not_skipped(self):
        """File seperti .environment tidak boleh ter-skip (bukan .env.*)."""
        assert should_skip_file(".environment") is False

    def test_env_exact_match(self):
        """File .env harus di-skip."""
        assert should_skip_file(".env") is True

    # --- Existing tests ---

    def test_editor_prefix_without_json_suffix(self):
        """editor_foo.py should NOT be skipped (wrong suffix)."""
        assert should_skip_file("editor_foo.py") is False

    def test_json_without_editor_prefix(self):
        """data.json should NOT be skipped (no matching prefix)."""
        assert should_skip_file("data.json") is False


# ============================================================================
# get_file_list
# ============================================================================

class TestGetFileList:

    def test_returns_list_of_strings(self, tmp_workspace):
        result = get_file_list(str(tmp_workspace))
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    def test_consistent_with_scan_workspace(self, tmp_workspace):
        """get_file_list should return the same paths as scan_workspace."""
        scan_results, _ = scan_workspace(str(tmp_workspace))
        scan_paths = sorted([r["path"] for r in scan_results])
        file_list = sorted(get_file_list(str(tmp_workspace)))
        assert scan_paths == file_list

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = get_file_list(str(empty))
        assert result == []
