"""
utils/security.py — Shared security utilities.

Fungsi keamanan yang digunakan oleh beberapa agent (editor, rag, dll.)
untuk memastikan operasi file tetap dalam sandbox yang aman.
"""

import os


def is_safe_path(filepath: str, base_dir: str) -> bool:
    """
    Pastikan filepath berada di dalam base_dir (security sandbox).

    Menggunakan os.path.realpath() untuk resolve symlinks dan
    os.sep untuk mencegah prefix bypass attack.

    Args:
        filepath: Path yang akan dicek keamanannya.
        base_dir: Direktori dasar yang menjadi sandbox.

    Returns:
        True jika filepath berada di dalam base_dir, False jika di luar.

    Contoh:
        >>> is_safe_path("/project/src/main.py", "/project")
        True
        >>> is_safe_path("/etc/passwd", "/project")
        False
        >>> is_safe_path("/project_evil/hack.py", "/project")
        False
    """
    target_abs = os.path.realpath(os.path.abspath(filepath))
    base_abs = os.path.realpath(os.path.abspath(base_dir))
    return target_abs == base_abs or target_abs.startswith(base_abs + os.sep)
