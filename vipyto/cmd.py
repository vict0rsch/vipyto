"""
Command-line interface utilities.

Essentially, this module provides a wrapper around :py:func:`subprocess.check_output`.

.. code-block:: python

    from vipyto.cmd import run_command

    current_git_user = run_command("git config user.name")

"""

import subprocess


def run_command(command, cwd=None):
    """
    Run a shell command and return the output.

    Args:
        command (str): Command to run.
        cwd (str, optional): Directory to run the command in. Defaults to None.
    """
    return subprocess.check_output(command.split(" "), cwd=cwd).decode("utf-8").strip()
