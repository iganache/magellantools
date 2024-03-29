# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "magellantools"
copyright = "2023, Indujaa Ganesh"
author = "Indujaa Ganesh"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_rtd_theme",
    "autoapi.extension",
    "nbsphinx",
]

templates_path = ["_templates"]
exclude_patterns = []

autoapi_dirs = ["../../src"]
autoapi_add_toctree_entry = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Logo
html_logo = "img/logo.png"

# Set top level page
master_doc = "index"
