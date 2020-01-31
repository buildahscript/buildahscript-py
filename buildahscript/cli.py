import argparse
import os
import shutil
import sys

from .parser import Metadata
from .venv import make_tmp_venv

parser = argparse.ArgumentParser(description='Run a script to build a container')
parser.add_argument('script', metavar='FILE',
                    help='File to run')
parser.add_argument('--build-arg', metavar="NAME=VALUE", dest='args', action='append',
                    help='Specify a build argument')
parser.add_argument('--tag', '-t', metavar="NAME", dest='tags', action='append',
                    help='tag to apply to the resulting container')


def main():
    args = parser.parse_args()
    if '_CONTAINERS_USERNS_CONFIGURED' in os.environ:
        return main_inner(args)
    else:
        return main_outer(args)


def main_outer(args):
    """
    Initial entrypoint, spin up the pip environment and then rerun under buildah
    unshare.
    """
    # Work-around https://github.com/containers/buildah/issues/2113
    # https://github.com/containers/buildah/issues/1754
    _fix_path()

    with open(args.script, 'rt') as script:
        md = Metadata.from_line_iter(script)

    with make_tmp_venv(md.deps) as venv:
        print(venv.python_path())
        os.execvp('buildah', ['buildah', 'unshare', *sys.argv])

    # FIXME: Cleanup venv


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


def main_inner(args):
    """
    We're running inside the buildah unshare environment, actually do the build.
    """
    # Parse buildargs
    with open(args.script, 'rt') as script:
        md = Metadata.from_line_iter(script)

    if args.args:
        rawargs = dict(
            kv.split('=', 1)
            for kv in args.args
        )
    else:
        rawargs = {}
    buildargs = apply_buildargs(md.args, rawargs)
    print("TODO: Run script")
    print(f"\t{buildargs!r}")


def apply_buildargs(argdefs, argvals):
    buildargs = {
        name: default
        for name, (_, default) in argdefs.items()
    }
    for k, v in argvals.items():
        if k not in argdefs:
            buildargs[k] = v
        else:
            cast, _ = argdefs[k]
            buildargs[k] = cast(v)

    return buildargs
