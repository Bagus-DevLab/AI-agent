"""
tests/test_rag_security.py — Tests for is_safe_path in agents/rag.py
=====================================================================

Test wrapper is_safe_path di rag agent yang menggunakan BASE_DIR dari config.
"""

import os
import pytest
from unittest.mock import patch

import agents.rag as rag_module


class TestRagIsSafePath:
    """Test path validation di RAG agent."""

    @pytest.fixture(autouse=True)
    def setup_base_dir(self, tmp_path):
        """Patch config.BASE_DIR yang digunakan oleh rag module."""
        self.base = tmp_path
        # rag.py imports BASE_DIR from config, lalu is_safe_path menggunakannya
        # Kita perlu patch BASE_DIR di module rag langsung
        with patch.object(rag_module, 'BASE_DIR', str(tmp_path)):
            yield

    def test_file_inside_base(self):
        target = os.path.join(str(self.base), "src", "main.py")
        assert rag_module.is_safe_path(target) is True

    def test_base_dir_itself(self):
        assert rag_module.is_safe_path(str(self.base)) is True

    def test_traversal_dotdot(self):
        target = os.path.join(str(self.base), "..", "..", "etc", "passwd")
        assert rag_module.is_safe_path(target) is False

    def test_absolute_path_outside(self):
        assert rag_module.is_safe_path("/etc/passwd") is False

    def test_root_path(self):
        assert rag_module.is_safe_path("/") is False

    def test_prefix_bypass_attack(self):
        """Sibling directory dengan prefix sama harus ditolak."""
        evil_path = str(self.base) + "_evil"
        os.makedirs(evil_path, exist_ok=True)
        evil_file = os.path.join(evil_path, "steal.py")
        assert rag_module.is_safe_path(evil_file) is False

    def test_symlink_escape(self):
        """Symlink ke luar base_dir harus ditolak."""
        link_path = self.base / "escape_link"
        try:
            link_path.symlink_to("/tmp")
            target = os.path.join(str(link_path), "something.py")
            assert rag_module.is_safe_path(target) is False
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

    def test_relative_path_inside(self, monkeypatch):
        """Relative path yang resolve ke dalam base_dir."""
        monkeypatch.chdir(str(self.base))
        assert rag_module.is_safe_path("./src/main.py") is True

    def test_nested_path_inside(self):
        """Path yang deeply nested tetap safe."""
        deep = os.path.join(str(self.base), "a", "b", "c", "file.py")
        assert rag_module.is_safe_path(deep) is True

    def test_empty_string(self):
        """Empty string tidak crash."""
        result = rag_module.is_safe_path("")
        assert isinstance(result, bool)


class TestRagUsesSharedSecurity:
    """Verifikasi bahwa rag.py menggunakan shared security function."""

    def test_rag_delegates_to_shared_is_safe_path(self, tmp_path):
        """
        Pastikan rag.is_safe_path memanggil utils.security.is_safe_path,
        bukan implementasi sendiri.
        """
        with patch('agents.rag._is_safe_path', return_value=True) as mock_safe:
            with patch.object(rag_module, 'BASE_DIR', str(tmp_path)):
                result = rag_module.is_safe_path("/some/path")
                mock_safe.assert_called_once_with("/some/path", str(tmp_path))
                assert result is True
