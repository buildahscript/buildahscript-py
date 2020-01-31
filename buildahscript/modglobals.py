"""
Global functions for the module
"""
import contextlib
import json
import pathlib
import subprocess

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


class Container:
    _id: str

    def __str__(self):
        return self._id

    def __repr__(self):
        return f'<{type(self).__name__} {self._id}>'

    def __init__(self, image):
        proc = _buildah('from', str(image))
        self._id = proc.stdout.strip()

    @classmethod
    def _from_id_only(cls, id):
        # Do magic to avoid creating a container
        self = cls.__new__(cls)
        self._id = id
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buildah('rm', self._id, stdout=subprocess.DEVNULL)

    def inspect(self):
        """
        Return some metadata about the container
        """
        proc = _buildah('inspect', '--type', 'container', self._id)
        return json.loads(proc.stdout)

    def commit(self):
        # TODO: Update config
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
        raise NotImplementedError

    # config                 Update image configuration settings
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
        # Do magic to avoid creating a container
        self = cls.__new__(cls)
        self._id = id
        return self

    # from                   Create a working container based on an image
    # tag                    Add an additional name to a local image
    # inspect                Inspect the configuration of a container or image
    # rmi                    Remove one or more images from local storage


class ReturnImage(BaseException):
    pass


def __return__(img):
    if isinstance(img, Container):
        raise TypeError("Returned a container, not an image (Did you forget .commit()?)")
    else:
        raise ReturnImage(img)
