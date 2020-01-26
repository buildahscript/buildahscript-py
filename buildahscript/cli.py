import os
import shutil
import sys


def main():
    if '_CONTAINERS_USERNS_CONFIGURED' in os.environ:
        return main_inner()
    else:
        return main_outer()


def main_inner():
    """
    We're running inside the buildah unshare environment, actually do the build
    """
    print("TODO: main_inner")


def main_outer():
    """
    Initial entrypoint, spin up the pip environment and then rerun under buildah
    unshare.
    """
    # Work-around https://github.com/containers/buildah/issues/2113
    # https://github.com/containers/buildah/issues/1754
    _fix_path()

    # TODO: Set up environment
    print("TODO: venv")

    os.execvp('buildah', ['buildah', 'unshare', *sys.argv])
    # XXX: This'll probably change with the pip environment


def _fix_path():
    if shutil.which('runc') is None:
        for path in ('/sbin', '/usr/sbin', '/usr/local/sbin'):
            if os.path.exists(os.path.join(path, 'runc')):
                os.environ['PATH'] += os.pathsep + path
                break
        else:
            # runc in not in PATH nor in additional directories
            # I guess fall through and let buildah fail?
            pass
