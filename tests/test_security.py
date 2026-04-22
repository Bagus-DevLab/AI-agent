"""
tests/test_security.py — Direct tests for utils/security.py
=============================================================

Test langsung untuk shared is_safe_path function dengan berbagai
kombinasi base_dir, bukan hanya lewat wrapper agent.
"""

import os
import pytest
from utils.security import is_safe_path


class TestIsSafePathDirect:
    """Test is_safe_path dengan berbagai base_dir."""

    def test_file_inside_base(self, tmp_path):
        target = os.path.join(str(tmp_path), "src", "main.py")
        assert is_safe_path(target, str(tmp_path)) is True

    def test_base_dir_itself(self, tmp_path):
        assert is_safe_path(str(tmp_path), str(tmp_path)) is True

    def test_file_outside_base(self, tmp_path):
        assert is_safe_path("/etc/passwd", str(tmp_path)) is False

    def test_root_path(self, tmp_path):
        assert is_safe_path("/", str(tmp_path)) is False

    def test_traversal_dotdot(self, tmp_path):
        target = os.path.join(str(tmp_path), "..", "..", "etc", "passwd")
        assert is_safe_path(target, str(tmp_path)) is False

    def test_prefix_bypass_attack(self, tmp_path):
        """
        /base/project_evil tidak boleh lolos dari check /base/project.
        os.sep check mencegah ini.
        """
        evil_path = str(tmp_path) + "_evil"
        os.makedirs(evil_path, exist_ok=True)
        evil_file = os.path.join(evil_path, "steal.py")
        assert is_safe_path(evil_file, str(tmp_path)) is False

    def test_symlink_escape(self, tmp_path):
        """Symlink yang mengarah ke luar base_dir harus ditolak."""
        link_path = tmp_path / "escape_link"
        try:
            link_path.symlink_to("/tmp")
            target = os.path.join(str(link_path), "something.py")
            assert is_safe_path(target, str(tmp_path)) is False
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

    def test_symlink_inside_base(self, tmp_path):
        """Symlink yang mengarah ke dalam base_dir harus diterima."""
        sub = tmp_path / "real_dir"
        sub.mkdir()
        (sub / "file.py").write_text("pass")
        link_path = tmp_path / "link_dir"
        try:
            link_path.symlink_to(sub)
            target = os.path.join(str(link_path), "file.py")
            assert is_safe_path(target, str(tmp_path)) is True
        except OSError:
            pytest.skip("Cannot create symlinks on this system")

    def test_relative_path_inside(self, tmp_path, monkeypatch):
        """Relative path yang resolve ke dalam base_dir."""
        monkeypatch.chdir(str(tmp_path))
        assert is_safe_path("./src/main.py", str(tmp_path)) is True

    def test_relative_path_outside(self, tmp_path, monkeypatch):
        """Relative path yang resolve ke luar base_dir."""
        sub = tmp_path / "project"
        sub.mkdir()
        monkeypatch.chdir(str(tmp_path))
        assert is_safe_path("../outside.py", str(sub)) is False

    def test_empty_filepath(self, tmp_path, monkeypatch):
        """Empty string resolve ke cwd — tidak crash."""
        monkeypatch.chdir(str(tmp_path))
        result = is_safe_path("", str(tmp_path))
        assert isinstance(result, bool)

    def test_empty_base_dir(self, tmp_path, monkeypatch):
        """Empty base_dir resolve ke cwd."""
        monkeypatch.chdir(str(tmp_path))
        target = os.path.join(str(tmp_path), "file.py")
        result = is_safe_path(target, "")
        assert isinstance(result, bool)


class TestIsSafePathWithDifferentBaseDirs:
    """Test bahwa base_dir parameter benar-benar digunakan."""

    def test_same_file_different_base_dirs(self, tmp_path):
        """File yang sama bisa safe atau unsafe tergantung base_dir."""
        project_a = tmp_path / "project_a"
        project_b = tmp_path / "project_b"
        project_a.mkdir()
        project_b.mkdir()

        target = os.path.join(str(project_a), "main.py")

        # Safe jika base_dir = project_a
        assert is_safe_path(target, str(project_a)) is True
        # Unsafe jika base_dir = project_b
        assert is_safe_path(target, str(project_b)) is False

    def test_nested_base_dir(self, tmp_path):
        """File di parent dir tidak safe jika base_dir adalah subdirectory."""
        parent = tmp_path / "parent"
        child = parent / "child"
        parent.mkdir()
        child.mkdir()

        parent_file = os.path.join(str(parent), "secret.py")
        # File di parent tidak safe jika base = child
        assert is_safe_path(parent_file, str(child)) is False
        # Tapi safe jika base = parent
        assert is_safe_path(parent_file, str(parent)) is True

    def test_deeply_nested_path(self, tmp_path):
        """Path yang sangat dalam tetap safe selama di dalam base."""
        deep = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        target = os.path.join(str(deep), "deep_file.py")
        assert is_safe_path(target, str(tmp_path)) is True
