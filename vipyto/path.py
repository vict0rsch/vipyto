"""
A few utilities to manipulate paths.

.. code-block:: python

    from vipyo.path import resolve

    # Resolves environment variables and user home directory
    path = resolve("~/path/to/$ENV_VAR/file")

.. code-block:: python

    from vipyo.path import add_git_root_to_path

    add_git_root_to_path()

    # Now you can import modules from the git root

    from mypackage import mymodule

    # This is particularly useful when you want to use a module
    # from a script that is not in the root of your project

.. code-block:: python

    from vipyo.path import get_git_root

    # without adding it to the path, you may want to get the absolute
    # path to your project to manipulate paths in your code with
    # respect to the project root.

    root = get_git_root()

.. note::

    Functions refer to ``[...]_git_[...]`` because this is how the root path
    is determined: it is the **first** folder that contains a ``.git`` folder
    when going up the directory tree from the current working directory.

"""

import os
import sys
from pathlib import Path


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
