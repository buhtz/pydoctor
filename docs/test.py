#
# Run tests after the documentation is executed.
#
# These tests are designed to be executed inside tox, after sphinx-build.
#

import os
import pathlib

BASE_DIR = pathlib.Path(os.environ.get('TOX_INI_DIR', os.getcwd())) / 'build' / 'docs'
API_DIR = BASE_DIR / 'api'


def test_help_output_extension():
    """
    The help output extension will include the CLI help on the Sphinx page.
    """
    with open(BASE_DIR / 'help.html', 'r') as stream:
        page = stream.read()
        assert '--project-url=PROJECTURL' in page, page


def test_rtd_pydoctor_call():
    """
    With the pydoctor Sphinx extension, the pydoctor API HTML files are
    generated.
    """
    # The pydoctor index is generated and overwrites the Sphinx files.
    with open(API_DIR / 'index.html', 'r') as stream:
        page = stream.read()
        assert 'moduleIndex.html' in page, page


def test_rtd_pydoctor_multiple_call():
    """
    With the pydoctor Sphinx extension can call pydoctor for more than one
    API doc source.
    """
    with open(BASE_DIR / 'docformat' / 'epytext' / 'demo' / 'index.html', 'r') as stream:
        page = stream.read()
        assert 'pydoctor-epytext-demo API Documentation' in page, page


def test_rtd_extension_inventory():
    """
    The Sphinx inventory is available during normalsphinx-build.
    """
    with open(BASE_DIR / 'usage.html', 'r') as stream:
        page = stream.read()
        assert 'href="/en/latest/api/pydoctor.sphinx_ext.build_apidocs.html"' in page, page
