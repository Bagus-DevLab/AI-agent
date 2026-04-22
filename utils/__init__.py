"""
utils/ — Package untuk utility functions.

Lazy imports untuk menghindari heavy loading saat startup.
"""


def scan_workspace(*args, **kwargs):
    from utils.scanner import scan_workspace as _fn
    return _fn(*args, **kwargs)


def get_file_list(*args, **kwargs):
    from utils.scanner import get_file_list as _fn
    return _fn(*args, **kwargs)


def build_vectorstore(*args, **kwargs):
    from utils.vectorstore import build_vectorstore as _fn
    return _fn(*args, **kwargs)


def get_retriever(*args, **kwargs):
    from utils.vectorstore import get_retriever as _fn
    return _fn(*args, **kwargs)


def load_memori_lokal(*args, **kwargs):
    from utils.memory import load_memori_lokal as _fn
    return _fn(*args, **kwargs)


def simpan_memori_lokal(*args, **kwargs):
    from utils.memory import simpan_memori_lokal as _fn
    return _fn(*args, **kwargs)


def is_safe_path(*args, **kwargs):
    from utils.security import is_safe_path as _fn
    return _fn(*args, **kwargs)


__all__ = [
    "scan_workspace",
    "get_file_list",
    "build_vectorstore",
    "get_retriever",
    "load_memori_lokal",
    "simpan_memori_lokal",
    "is_safe_path",
]
