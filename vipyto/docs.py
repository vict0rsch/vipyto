"""
This module contains utilities related to documenting a Python project with
Sphinx.

Its main function is :py:func:`~vipyto.docs.init_docs`, which does the following:

- Creates a ``docs/`` directory in the root of the project
- Runs ``sphinx-quickstart`` in that directory, with a selection of extensions
- Adds a selection of extensions to ``docs/conf.py``
- Adds a selection of configuration to ``docs/conf.py``
- Creates a ``docs/requirements-docs.txt`` file with the packages required to
    build the docs
- Creates a ``.readthedocs.yml`` file with the configuration required by
    readthedocs.io
- Creates a ``docs/index.rst`` file (which includes your README.md by default)
- Installs the packages required to build the docs (starting with ``sphinx``
    if it is not already installed)

Importantly, it sets up ``autoapi`` to document your code automatically from its
existing docstrings. This means that you don't need to write any additional
documentation to get started with Sphinx.

.. note::

    This function expects your package to be called the same as the folder it is in.
    This means you would have a directory ``{project}/`` which would contain
    ``{project}/{project}``, ``{project}/.git/``, ``{project}/README.md``, etc.

    If that is not the case, you should update ``docs/conf.py``, specifically
    the ``autoapi_dirs`` variable.

"""
import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from textwrap import dedent

from vipyto import log, status
from vipyto.cmd import run_command
from vipyto.path import get_git_root

PREAMBLE = """\
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
"""
"""
Imports settings.

:meta private:
"""

RTD_CONF = """
# Read the Docs configuration file for Sphinx projects
# See https://docs.readthedocs.io/en/stable/config-file/v2.html for details

# Required
version: 2

# Set the OS, Python version and other tools you might need
build:
  os: ubuntu-22.04
  tools:
    python: "3.9"
    # You can also specify other tool versions:
    # nodejs: "20"
    # rust: "1.70"
    # golang: "1.20"

# Build documentation in the "docs/" directory with Sphinx
sphinx:
  configuration: docs/conf.py
  # You can configure Sphinx to use a different builder, for instance use the
  # dirhtml builder for simpler URLs
  # builder: "dirhtml"
  # Fail on all warnings to avoid broken references
  # fail_on_warning: true
# Optionally build your docs in additional formats such as PDF and ePub
# formats:
#    - pdf
#    - epub

# Optional but recommended, declare the Python requirements required
# to build your documentation
# See https://docs.readthedocs.io/en/stable/guides/reproducible-builds.html
python:
  install:
    - requirements: docs/requirements-docs.txt
"""
"""
Contents for the ``.readthedocs.yml`` file that will be created by
:py:func:`~vipyto.docs.init_docs`.

:meta private:
"""

REQS = """\
sphinx
myst-parser
furo
sphinx-copybutton
sphinx-autodoc-typehints
sphinx-autoapi
sphinx-math-dollar
sphinx-design
sphinx-copybutton
sphinxext-opengraph
"""
"""
List of packages that will be installed in the docs environment by
:py:func:`~vipyto.docs.init_docs`.
"""

EXTS = """\
extensions = [
    "myst_parser",
    "sphinx.ext.viewcode",
    "sphinx_math_dollar",
    "sphinx.ext.mathjax",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.todo",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]
"""
"""
Overwrite of the ``extensions`` list in ``docs/conf.py`` that will be created by
:py:func:`~vipyto.docs.init_docs`.

:meta private:
"""

CONFIGS = r"""
# Configuration section from vipyto:
# ----------------------------------

# Configuratiion for sphinx.ext.autodoc & autoapi.extension
# https://autoapi.readthedocs.io/

autodoc_typehints = "description"
autoapi_type = "python"
autoapi_dirs = [str(ROOT/ "$PROJECT")]
autoapi_member_order = "groupwise"
autoapi_template_dir = "_templates/autoapi"
autoapi_python_class_content = "init"
autoapi_options = [
    "members",
    "undoc-members",
]
autoapi_keep_files = False

# Configuration for sphinx_math_dollar

# sphinx_math_dollar
# https://www.sympy.org/sphinx-math-dollar/

# Note: CHTML is the only output format that works with \mathcal{}
mathjax_path = "https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS_CHTML"
mathjax3_config = {
    "tex": {
        "inlineMath": [
            ["$", "$"],
            ["\\(", "\\)"],
        ],
        "processEscapes": True,
    },
    "jax": ["input/TeX", "output/CommonHTML", "output/HTML-CSS"],
}

# Configuration for sphinx_autodoc_typehints
# https://github.com/tox-dev/sphinx-autodoc-typehints
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True
typehints_defaults = "comma"

# Configuration for the MyST (markdown) parser
# https://myst-parser.readthedocs.io/en/latest/intro.html
myst_enable_extensions = ["colon_fence"]

# Configuration for sphinxext.opengraph
# https://sphinxext-opengraph.readthedocs.io/en/latest/

ogp_site_url = "TODO"
ogp_social_cards = {
    "enable": True,
    "image": "./_static/images/SOME_IMAGE",
}

"""
"""
Additional configuration that will be added to ``docs/conf.py`` by
:py:func:`~vipyto.docs.init_docs`.

:meta private:
"""

INDEX = """\
.. include:: ../README.md
   :parser: myst_parser.sphinx_

.. toctree::
   :hidden:
   :maxdepth: 4

   self

"""
"""
Default contents for ``docs/index.rst`` that will be created by
:py:func:`~vipyto.docs.init_docs`. It includes the README.md file.

:meta private:
"""


def init_docs():
    """
    Initialize the Sphinx docs for a project with a selection of extensions.

    This will attempt to create a docs/ folder, run ``sphinx-quickstart``,
    customize the resulting ``conf.py``, and install the packages required to
    build the docs. It will also create a ``.readthedocs.yml`` file in your
    repo's root folder, which is required by readthedocs.io.

    .. note::

        Run ``vipyto docs init`` from the root of your project to call this function
        directly.

    """
    root = get_git_root()
    project = root.name
    author = run_command("git config user.name")
    try:
        version = get_version(project)
    except PackageNotFoundError:
        try:
            pyproject = root / "pyproject.toml"
            lines = pyproject.read_text().split("\n")
            for line in lines:
                if re.match(r"version\s?=\s?.+", line):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    break
        except FileNotFoundError:
            version = "0.1.0"

    if (root / "docs").exists():
        log(f"You already have a docs/ directory in {root}.", style="yellow")
        if "y" not in input("Do you want to overwrite its contents? [y/N] ").lower():
            return
        shutil.rmtree(root / "docs")

    log(f"Initializing docs for {project} version {version} and author {author}")
    (root / "docs").mkdir(exist_ok=True)
    command = " ".join(
        [
            f"sphinx-quickstart -q -p {project} -a {author} -v {version}",
            "--no-sep --ext-autodoc --ext-viewcode --ext-todo --ext-mathjax",
            "--ext-intersphinx --makefile",
            "docs/",
        ]
    )
    try:
        import sphinx  # noqa: F401
    except ImportError:
        with status("Sphinx is not installed. Installing it now..."):
            run_command(f"{sys.executable} -m pip install --upgrade pip")
            run_command(f"{sys.executable} -m pip install sphinx")
    with status("Running sphinx-quickstart..."):
        run_command(command)

    conf = root / "docs" / "conf.py"
    lines = conf.read_text().split("\n")
    new_lines = []
    is_exts = False
    for line in lines:
        if line == "extensions = [":
            is_exts = True

        if line.startswith("html_theme ="):
            line = 'html_theme = "furo"'

        if line == "html_static_path = ['_static']":
            line += "\n" + 'html_css_files = ["css/custom.css"]'

        if "# -- General configuration" in line:
            line = PREAMBLE + "\n" + line

        # store
        if not is_exts:
            new_lines.append(line)

        if is_exts and line == "]":
            is_exts = False
            new_lines.append(EXTS)
    new_lines.append(CONFIGS.replace("$PROJECT", project))
    conf.write_text("\n".join(new_lines))
    (root / "docs" / "requirements-docs.txt").write_text(REQS)
    (root / ".readthedocs.yml").write_text(RTD_CONF)
    (root / "docs" / "_static" / "css").mkdir(exist_ok=True)
    (root / "docs" / "_static" / "images").mkdir(exist_ok=True)
    (root / "docs" / "_static" / "css" / "custom.css").touch()
    (root / "docs" / "index.rst").write_text(INDEX)

    with status("Installing docs dependencies..."):
        run_command(f"{sys.executable} -m pip install --upgrade pip")
        run_command(f"{sys.executable} -m pip install -r docs/requirements-docs.txt")

    with status("Running `cd docs && make html` to build the docs"):
        try:
            run_command("make html", cwd=str(root / "docs"))
            log("Your docs were built successfully!", style="green")
            log("See them by openning `docs/_build/html/index.html` in your browser.")
        except subprocess.CalledProcessError:
            log(
                dedent(
                    f"""\
                Docs building error.
                The docs were built assuming your project is called `{project}`.
                If your code is in an other folder, this may be why the build failed.
                In that case, update docs/conf.py (line: `autoapi_dirs = `).
                """
                ),
                style="orange_red1",
            )
    log("Run `make html` in the `docs/` folder to build the docs yourself.")
