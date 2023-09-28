"""
Victor's Python Toolbox

A collection of tools for Python development because I was tired of writing the same
code again and again.

You may or may not like it, but I do. I hope you do too.

Modules:

- :py:mod:`vipyto.cmd`: Command-line interface utilities.
- :py:mod:`vipyto.docs`: Documentation utilities.
- :py:mod:`vipyto.path`: Path utilities.
- :py:mod:`vipyto.train`: Training utilities for PyTorch deep learning code.
- :py:mod:`vipyto.cli`: Command-line intereface for ``vipyto``.

Command-line interface summary:

.. code-block:: bash

    vipyto docs init # Initialize the docs for your project using Sphinx
    vipyto docs build # Build the docs for your project using Sphinx

Also you can use `rich <https://rich.readthedocs.io/en/stable/introduction.html>`_
to print rich text to the console:

.. code-block:: python

    from vipyto import print, log, status
    from time import sleep

    print("[bold red]Hello[/bold red] [bold blue]World[/bold blue]!")
    log("This is a log message")
    with status("This is a status message"):
        sleep(5)
    log("This is another log message")

.. image:: /_static/images/prints.png
  :alt: Demo prints

"""

import os
from importlib.metadata import version

from rich import pretty
from rich.console import Console

console = Console()
print = console.print
log = console.log
status = console.status
pretty.install()

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"

__version__ = version("vipyto")
