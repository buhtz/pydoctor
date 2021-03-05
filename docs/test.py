#
# Run tests after the documentation is executed.
#
# These tests are designed to be executed inside tox, after sphinx-build.
#
import os
import pathlib

from sphinx.ext.intersphinx import inspect_main

from pydoctor import __version__


BASE_DIR = pathlib.Path(os.environ.get('TOX_INI_DIR', os.getcwd())) / 'build' / 'docs'


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
    with open(BASE_DIR / 'api' / 'index.html', 'r') as stream:
        page = stream.read()
        assert 'moduleIndex.html' in page, page


def test_rtd_pydoctor_multiple_call():
    """
    With the pydoctor Sphinx extension can call pydoctor for more than one
    API doc source.
    """
    with open(BASE_DIR / 'docformat' / 'epytext' / 'index.html', 'r') as stream:
        page = stream.read()
        assert '<a href="../epytext.html">pydoctor-epytext-demo</a>' in page, page


def test_rtd_extension_inventory():
    """
    The Sphinx inventory is available during normal sphinx-build.
    """
    with open(BASE_DIR / 'usage.html', 'r') as stream:
        page = stream.read()
        assert 'href="/en/latest/api/pydoctor.sphinx_ext.build_apidocs.html"' in page, page


def test_sphinx_object_inventory_version(capsys):
    """
    The Sphinx inventory is generated with the project version in the header.
    """
    # The pydoctor own inventory.
    apidocs_inv = BASE_DIR / 'api' / 'objects.inv'
    with open(apidocs_inv, 'rb') as stream:
        page = stream.read()
        assert page.startswith(
            b'# Sphinx inventory version 2\n'
            b'# Project: pydoctor\n'
            b'# Version: ' + __version__.encode() + b'\n'
            ), page

    # Check that inventory can be parsed by Sphinx own extension.
    inspect_main([str(apidocs_inv)])
    out, err = capsys.readouterr()

    assert '' == err
    assert 'pydoctor.driver.main' in out, out


def test_sphinx_object_inventory_version_epytext_demo():
    """
    The Sphinx inventory for demo/showcase code has a fixed version and name,
    passed via docs/source/conf.py.
    """
    with open(BASE_DIR / 'docformat' / 'epytext' / 'objects.inv', 'rb') as stream:
        page = stream.read()
        assert page.startswith(
            b'# Sphinx inventory version 2\n'
            b'# Project: pydoctor-epytext-demo\n'
            b'# Version: 1.3.0\n'
            ), page
