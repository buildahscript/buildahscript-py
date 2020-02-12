"""
Global functions for the module
"""
import contextlib
import copy
import json
import pathlib
import shutil
import subprocess
import typing

# This is mandatory
__all__ = ('__return__', 'Container')


def _buildah(*cmd, **opts):
    opts.setdefault('stdout', subprocess.PIPE)
    opts.setdefault('check', True)
    return subprocess.run(['buildah', *cmd], encoding='utf-8', **opts)

# build-using-dockerfile Build an image using instructions in a Dockerfile

# info                   Display Buildah system information
# version                Display the Buildah version information

# images                 List images in local storage
# containers             List working containers and their base images
# rename                 Rename a container
# pull                   Pull an image from the specified location
# push                   Push an image to a specified destination
# login                  Login to a container registry
# logout                 Logout of a container registry


def _dict_diff(old, new):
    """
    Compares two dicts, returning two iterables: the keys that have been added
    or changed, and the keys that have been deleted.
    """
    oldkeys = set(old.keys())
    newkeys = set(new.keys())
    changed = newkeys - oldkeys
    deleted = oldkeys - newkeys
    for key in newkeys & oldkeys:
        if new[key] != old[key]:
            changed.add(key)

    assert len(changed & deleted) == 0
    return changed, deleted


def _join_shellwords(seq):
    """
    Joins a sequence together, parsable https://github.com/mattn/go-shellwords

    This exists because buildah config --cmd uses it
    """
    # FIXME: Handle ' in items
    return " ".join(f"'{s}'" for s in seq)


class Container:
    _id: str

    environ: typing.Dict[str, str]
    command: typing.List[str]
    entrypoint: typing.List[str]
    labels: typing.Dict[str, str]
    volumes: typing.Set[str]

    def __str__(self):
        return self._id

    def __repr__(self):
        return f'<{type(self).__name__} {self._id}>'

    def __init__(self, image):
        proc = _buildah('from', str(image))
        self._id = proc.stdout.strip()
        self._init_config()

    @classmethod
    def _from_id_only(cls, id):
        # Do magic to avoid creating a container
        self = cls.__new__(cls)
        self._id = id
        self._init_config()
        return self

    def _init_config(self):
        """
        Initialize the config attrs
        """
        info = self.inspect()
        kinda_config = json.loads(info['Config'])
        config = kinda_config['config']  # Might be 'container_config'??
        self.environ = dict(
            item.split('=', 1)
            for item in config['Env'] or {}
        )
        self.command = config['Cmd'] or []
        self.entrypoint = config['Entrypoint'] or []
        self.labels = config['Labels'] or {}
        self.volumes = set(config['Volumes'].keys()) if config['Volumes'] else set()
        self.workdir = config['WorkingDir']
        # TODO: ExposedPorts
        # TODO: StopSignal
        # TODO: Author, comment, created by, domainname, shell, user, workingdir
        self._snapshot_config()

    def _snapshot_config(self):
        """
        Snapshot config for future comparison
        """
        self._snapshot = copy.deepcopy(vars(self))

    def _produce_config_args(self):
        """
        Compares the config attrs to the snapshot and generates args
        """
        args = []

        # Simple stuff: command, entrypoint, workdir
        if self.command != self._snapshot['command']:
            args += ['--cmd', _join_shellwords(self.command)]
        if self.entrypoint != self._snapshot['entrypoint']:
            args += ['--entrypoint', json.dumps(self.entrypoint)]
        if self.workdir != self._snapshot['workdir']:
            args += ['--workingdir', self.workdir]

        # Environment
        env_add, env_del = _dict_diff(self._snapshot['environ'], self.environ)
        for key in env_add:
            args += ['--env', f"{key}={self.environ[key]}"]
        for key in env_del:
            args += ['--env', f"{key}-"]

        # Volumes
        vol_add = self.volumes - self._snapshot['volumes']
        vol_del = self._snapshot['volumes'] - self.volumes
        for v in vol_add:
            args += ['--volume', v]
        for v in vol_del:
            args += ['--volume', f"{v}-"]

        return args

    def _commit_config(self):
        """
        Commit any config changes to buildah
        """
        if not hasattr(self, '_snapshot'):
            return
        _buildah('config', *self._produce_config_args(), self._id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buildah('rm', self._id, stdout=subprocess.DEVNULL)

    def inspect(self):
        """
        Return some metadata about the container
        """
        self._commit_config()
        proc = _buildah('inspect', '--type', 'container', self._id)
        return json.loads(proc.stdout)

    def commit(self):
        self._commit_config()
        proc = _buildah('commit', self._id)
        return Image._from_id_only(proc.stdout.strip())

    @contextlib.contextmanager
    def mount(self):
        """
        Mounts the container's filesystem onto the host. Context manager.

        The context manager returns a pathlib.Path, which points to the mount
        point.
        """
        proc = _buildah('mount', self._id)
        path = proc.stdout.strip()
        yield pathlib.Path(path)
        _buildah('umount', self._id)

    def copy_in(self, src, dst):
        """
        Copies a file or directory from the host into the container.

        dst must include the name that will be taken, not just the parent
        directory.

        This is wrong: copy_in("myfile", "/usr/bin")
        This is right: copy_in("myfile", "/usr/bin/foobar")
        """
        _buildah('copy', self._id, str(src), str(dst))

    def copy_out(self, src, dst):
        """
        Copies a file or directory out of the container to the host.

        dst must include the name that will be taken, not just the parent
        directory.
        """
        dst = pathlib.Path(dst)
        # Cleanup what already exists
        if dst.is_dir():
            shutil.rmtree(dst)
        elif dst.exists():
            dst.unlink()

        with self.mount() as root:
            fullsrc = root / src.lstrip('/')
            if fullsrc.is_dir():
                shutil.copytree(fullsrc, dst)
            else:
                shutil.copy2(fullsrc, dst)

    def run(
        self, cmd, *,
        # buildah flags
        shell=False, user=None, volumes=None, mounts=None,
        # TODO: cap add/drop, hostname, ipc, isolation, network, pid, uts
        # Subprocess flags
        stdin=None, input=None, stdout=None, stderr=None,
        # TODO: timeout, cwd, env
    ):
        self._commit_config()
        args = []
        opts = {
            'stdin': stdin,
            'input': input,
            'stdout': stdout,
            'stderr': stderr,
        }

        if user is not None:
            args += ['--user', str(user)]

        if volumes is not None:
            for vol in volumes:
                if isinstance(vol, str):
                    args += ['--volume', vol]
                else:
                    args += ['--volume', ':'.join(vol)]

        if mounts is not None:
            for mnt in mounts:
                args += [
                    '--mount', ','.join(f"{k}={v}" for k, v in mnt.items())
                ]

        if shell:
            raise NotImplementedError("shell not implemented yet")

        return _buildah('run', *args, '--', self._id, *cmd, **opts)

    # rename                 Rename a container
    # run                    Run a command inside of the container


class Image:
    _id: str

    def __str__(self):
        return self._id

    def __repr__(self):
        return f'<{type(self).__name__} {self._id}>'

    @classmethod
    def _from_id_only(cls, id):
        self = cls()
        self._id = id
        return self

    def add_tag(self, tag):
        _buildah('tag', self._id, tag)

    # from                   Create a working container based on an image
    # inspect                Inspect the configuration of a container or image
    # rmi                    Remove one or more images from local storage


class ReturnImage(BaseException):
    pass


def __return__(img):
    if isinstance(img, Container):
        raise TypeError("Returned a container, not an image (Did you forget .commit()?)")
    else:
        raise ReturnImage(img)
