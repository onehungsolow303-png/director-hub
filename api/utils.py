# api/utils.py
"""Shared utilities for the API layer."""
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(path):
    """Resolve a path relative to the project directory. Passes data URLs and absolute paths through."""
    if not path:
        return path
    if path.startswith("data:"):
        return path
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_DIR, path)


def resolve_output_dir(output_dir, default="output"):
    """Resolve output directory, creating it if needed."""
    if not output_dir:
        output_dir = default
    path = resolve_path(output_dir)
    os.makedirs(path, exist_ok=True)
    return path
