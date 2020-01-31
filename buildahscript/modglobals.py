"""
Global functions for the module
"""
import subprocess

# This is mandatory
__all__ = ('__return__', 'Container')


def _buildah(*cmd, **opts):
    return subprocess.run(
        ['buildah', *cmd],
        stdout=subprocess.PIPE,
        check=True,
        **opts
    )

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

    def commit(self):
        # TODO: Update config
        proc = _buildah('commit', self._id)
        return Image._from_id_only(proc.stdout.strip())

    # add                    Add content to the container
    # commit                 Create an image from a working container
    # config                 Update image configuration settings
    # copy                   Copy content into the container
    # rename                 Rename a container
    # run                    Run a command inside of the container
    # inspect                Inspect the configuration of a container or image

    # LATER:
    # mount                  Mount a working container's root filesystem
    # umount                 Unmount the root file system of the specified working containers
    # unshare                Run a command in a modified user namespace


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
