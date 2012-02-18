"""Fabfile for release management."""

import codecs
import glob
import os
import re

from fabric.api import local, abort, lcd

HERE = os.path.dirname(__file__)
ROOT = HERE

# =============================================================================
# internal helpers
# =============================================================================

def _readfile(fname, strip="\n"):
    """Shortcut for reading a text file."""

    with codecs.open(fname, 'r', 'UTF8') as fp:
        content = fp.read()
    return content.strip(strip) if strip else content

def _contains(fname, rx, reflags=0):
    """Check if content of `fname` matches (contains) `rx`."""

    content = _readfile(fname)
    return re.search(rx, content, reflags)

def _needcleanworkingcopy():
    """Aborts if working copy is dirty."""

    if local("hg status -n", capture=True):
        abort("dirty working copy")

# =============================================================================
# release tools
# =============================================================================

def push():
    """Push master branch."""

    _needcleanworkingcopy()

    hgignore = _readfile(".hgignore").split("\n")[2:]
    gitignore = _readfile(".gitignore").split("\n")
    if hgignore != gitignore:
        abort("hg and git ignore files differ")

    local("hg push -r master bitbucket")
    local("hg push -r master github")

def release_check(version):
    """Various checks to be done prior a release."""

    # --- check README --------------------------------------------------------

    from docutils.core import publish_cmdline
    readme = os.path.join(ROOT, "README.rst")
    publish_cmdline(argv=["--halt", "2", readme, os.devnull])

    # --- version numbers -----------------------------------------------------

    rx = r'\n--+\nChanges\n--+\n\nVersion %s\n~~+\n\n' % version
    if not _contains(readme, rx):
        abort("bad version in README.rst")

    setup = os.path.join(ROOT, "setup.py")
    rx = r'''\nversion *= *['"]%s['"]\n''' % version
    if not _contains(setup, rx):
        abort("bad version in setup.py")

    # --- run tests -----------------------------------------------------------

    local("python tests.py")

    # --- check working copy --------------------------------------------

    _needcleanworkingcopy()

    out = local("hg bookmarks", capture=True)
    if not re.match(r'\s*\* master\s', out):
        abort("working copy is not at master bookmark")

def release(version):
    """Make a release."""

    release_check(version)

    local("rm -rf %s" % os.path.join(ROOT, "build"))
    local("rm -rf %s" % os.path.join(ROOT, "dist"))

    local("python setup.py clean build sdist") # test build

    local("hg tag %s" % version)

    local("python setup.py register sdist upload")

    push()
