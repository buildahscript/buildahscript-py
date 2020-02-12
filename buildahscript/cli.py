import argparse
import os
import shutil
import sys

from .metadata import Metadata
from .venv import make_tmp_venv
from .runner import parse_buildargs, run_file

parser = argparse.ArgumentParser(description='Run a script to build a container')
parser.add_argument('script', metavar='FILE',
                    help='File to run')
parser.add_argument('--build-arg', metavar="NAME=VALUE", dest='args', action='append',
                    help='Specify a build argument')
parser.add_argument('--tag', '-t', metavar="NAME", dest='tags', action='append',
                    help='tag to apply to the resulting image')


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

    if md.deps:
        with make_tmp_venv(md.deps) as venv:
            my_path = sys.path
            inner_path = venv.python_path()
            # This feels bad, but careful thought seems like it'll be fine?
            os.environ['PYTHONPATH'] = os.pathsep.join(inner_path + my_path)
            os.execvp('buildah', ['buildah', 'unshare', *sys.argv])
    else:
        os.execvp('buildah', ['buildah', 'unshare', *sys.argv])


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
    buildargs = parse_buildargs(md.args, rawargs)
    img = run_file(args.script, buildargs)

    if img is not None:
        for tag in args.tags:
            img.add_tag(tag)
        print('')
        print(img)
