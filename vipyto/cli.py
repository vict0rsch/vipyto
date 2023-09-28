"""
Command-line intereface for ``vipyto``.

Currently, the following commands are available:

- ``vipyto docs init``: Initialize the docs for your project using Sphinx


.. note::

    ``vipyto docs init`` will install packages if they are not already installed,
    like ``sphinx`` and Sphinx extensions. You can find the list of packages in
    :py:const:`~vipyto.docs.REQS`.
"""
import typer

from vipyto.docs import init_docs
from vipyto.path import get_git_root
from vipyto.cmd import run_command
import subprocess
from vipyto import status, log

app = typer.Typer()
docs_app = typer.Typer()
app.add_typer(
    docs_app,
    name="docs",
    help="Initialization tools for {}".format(
        ", ".join(
            [
                "docs",
            ]
        )
    ),
)


@docs_app.command(
    "init",
    help="Initialize the docs for your project using Sphinx and "
    + "a selection of extensions.",
)
def run_init_docs():
    """
    Command-line interface for initializing the docs for a project.
    """
    init_docs()


@docs_app.command(
    "build",
    help="Build the docs for your project using Sphinx.",
)
def build_docs():
    """
    Command-line interface for building your project's docs.
    """
    root = get_git_root()
    docs = root / "docs"
    with status("Running `make html` in {}".format(docs)):
        try:
            run_command("make html", cwd=docs)
        except subprocess.CalledProcessError as e:
            log(str(e))
            log("Failed to build docs", style="bold red")
            raise typer.Exit(1)
    log(
        f"Successfully built docs. Open {docs / '_build/html/index.html'} to see them",
        style="green",
    )
