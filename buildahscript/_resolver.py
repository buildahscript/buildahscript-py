from importlib import import_module
import builtins


# Based on https://github.com/python/cpython/pull/18310
def resolve_dotted_path(fullname):
    """
    Given a full dotted name (starting with the module name), return the
    referred object.

    Colon-separated module/obj names are also accepted.

    If the name does not start with a module, it is assumed to be a builtin.
    """

    if ':' in fullname:
        modname, objname = fullname.split(':', 1)
        mod = import_module(modname)
        remainder = objname.split('.')
    else:
        nameparts = fullname.split('.')
        partsiter = iter(nameparts)

        # Resolve the module part, by importing modules one at a time until one
        # fails
        mod = None
        modname = next(partsiter)
        lastpart = None
        while True:
            try:
                mod = import_module(modname)
            except ImportError:
                if mod is None:
                    # The first part isn't a valid module/package, assume the
                    # name refers to a builtin
                    mod = builtins
                    remainder = nameparts
                    break
                else:
                    # We found the end of the module name
                    remainder = [lastpart] + list(partsiter)
                    break
            try:
                lastpart = next(partsiter)
            except StopIteration:
                # We consumed the entire name searching for the not-module part,
                # so the whole name is a module name
                return mod
            modname += f".{lastpart}"

    obj = mod
    for name in remainder:
        obj = getattr(obj, name)
    return obj


if __name__ == '__main__':
    # A quick test suite
    print(resolve_dotted_path("os.path.exists"))
    print(resolve_dotted_path("pathlib.Path.cwd"))
    print(resolve_dotted_path("urllib.request"))
    print(resolve_dotted_path("str"))
    print(resolve_dotted_path("dict.fromkeys"))

    print(resolve_dotted_path("os.path:exists"))
    print(resolve_dotted_path("pathlib:Path.cwd"))
