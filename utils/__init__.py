"""
utils/ — Package untuk utility functions.
Menggunakan lazy import untuk menghindari heavy loading saat startup.
"""


def scan_workspace(*args, **kwargs):
    from utils.scanner import scan_workspace as _scan
    return _scan(*args, **kwargs)


def get_file_list(*args, **kwargs):
    from utils.scanner import get_file_list as _get
    return _get(*args, **kwargs)


def build_vectorstore(*args, **kwargs):
    from utils.vectorstore import build_vectorstore as _build
    return _build(*args, **kwargs)


def get_retriever(*args, **kwargs):
    from utils.vectorstore import get_retriever as _get
    return _get(*args, **kwargs)


def load_memori_lokal(*args, **kwargs):
    from utils.memory import load_memori_lokal as _load
    return _load(*args, **kwargs)


def simpan_memori_lokal(*args, **kwargs):
    from utils.memory import simpan_memori_lokal as _simpan
    return _simpan(*args, **kwargs)


def is_safe_path(*args, **kwargs):
    from utils.security import is_safe_path as _safe
    return _safe(*args, **kwargs)


__all__ = [
    "scan_workspace",
    "get_file_list",
    "build_vectorstore",
    "get_retriever",
    "load_memori_lokal",
    "simpan_memori_lokal",
    "is_safe_path",
]
