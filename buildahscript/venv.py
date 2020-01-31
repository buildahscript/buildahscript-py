"""
Tools to build & populate venvs
"""
import contextlib
import json
import os
import subprocess
import tempfile
import venv


@contextlib.contextmanager
def make_tmp_venv(reqs):
    # TODO: Caching?
    with tempfile.TemporaryDirectory() as td:
        venv.create(td, with_pip=True)
        pip = os.path.join(td, 'bin', 'pip')
        subprocess.run([pip, 'install', 'wheel'], check=True)
        if reqs:
            subprocess.run([pip, 'install', *reqs], check=True)

        yield Venv(td)


class Venv:
    def __init__(self, root):
        self.root = root

    def bin(self, program):
        return os.path.join(self.root, 'bin', program)

    def python_path(self):
        proc = subprocess.run(
            [self.bin('python'), '-c', "print(__import__('json').dumps(__import__('sys').path))"],
            stdout=subprocess.PIPE, check=True
        )
        return json.loads(proc.stdout)
