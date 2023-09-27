import re
from textwrap import dedent
from importlib.metadata import version as get_version
from importlib.metadata import PackageNotFoundError

from vipyto.cmd import run_command
from vipyto.path import get_git_root
from vipyto import print

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
  # You can configure Sphinx to use a different builder, for instance use the dirhtml builder for simpler URLs
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

REQS = """
sphinx
myst-parser
furo==2023.3.27
sphinx-copybutton
sphinx-autodoc-typehints
sphinx-autoapi==2.1.0
sphinx-math-dollar
sphinx-design
sphinx-copybutton
sphinxext-opengraph
"""

EXTS = """
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

CONFIGS = """

# Configuration section from vipyto:
# ----------------------------------

# Configuratiion for sphinx.ext.autodoc & autoapi.extension
# https://autoapi.readthedocs.io/

autodoc_typehints = "description"
autoapi_type = "python"
autoapi_dirs = ["../$PROJECT"]
autoapi_member_order = "alphabetical"
autoapi_template_dir = "_templates/autoapi"
autoapi_python_class_content = "init"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
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

INDEX = """
.. include:: ../README.md
   :parser: myst_parser.sphinx_

.. toctree::
   :hidden:
   :maxdepth: 4

   self

"""


def init_docs():
    """
    Initialize the docs for a project.
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
                if re.match("version\s?=\s?.+", line):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    break
        except FileNotFoundError:
            version = "0.1.0"

    print(f"Initializing docs for {project} version {version} and author {author}")
    (root / "docs").mkdir(exist_ok=True)
    command = " ".join(
        [
            f"sphinx-quickstart -q -p {project} -a {author} -v {version}",
            "--no-sep --ext-autodoc --ext-viewcode --ext-todo --ext-mathjax",
            "--ext-intersphinx --makefile",
            "docs/",
        ]
    )
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

    print("[bold green]Done! Run `cd docs && make html` to build the docs![bold green]")
    print(
        "[yellow]You may need to update docs/conf.py to update your package directory "
        + "(line: `autoapi_dirs = `)."
    )
