"""
Global functions for the module
"""

__all__ = ()

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
    ...
    # __enter__
    # from                   Create a working container based on an image
    # __exit__
    # rm                     Remove one or more working containers

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
    ...
    # from                   Create a working container based on an image
    # tag                    Add an additional name to a local image
    # inspect                Inspect the configuration of a container or image
    # rmi                    Remove one or more images from local storage
