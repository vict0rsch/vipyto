from importlib.metadata import version

import os
from pathlib import Path
import builtins
from rich import pretty
from rich.console import Console

console = Console()
print = console.print
pretty.install()

os.environ["PYTHONBREAKPOINT"] = "ipdb.set_trace"

__version__ = version("vipyto")
