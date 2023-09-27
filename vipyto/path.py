import os
from pathlib import Path
import sys


def get_git_root():
    """
    Recursively finds the root directory of a git repository.

    Returns:
        Path|None: Path to the root directory of the git repository or None.
    """
    path = Path.cwd()
    while path != path.parent:
        if (path / ".git").is_dir():
            return path
        path = path.parent
    return None


def add_git_root_to_path(verbose=False):
    """
    Recursively finds the root directory of a git repository
    and adds it to the path.

    Args:
        verbose (bool): Print the path that is added to the path.
    """
    root = get_git_root()
    if not root:
        if verbose:
            print("No git root found")

    if verbose:
        print("Adding {} to path".format(root))

    sys.path.append(str(root))


def resolve(path):
    """
    Resolves a path to an absolute path, taking into account environment variables.

    Args:
        path (str): Path to resolve.

    Returns:
        str: Absolute path.
    """
    return Path(os.path.expandvars(os.path.expanduser(str(path)))).resolve()
