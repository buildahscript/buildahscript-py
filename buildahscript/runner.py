import ast


def parse_buildargs(argdefs, argvals):
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


def run_file(filename, buildargs):
    with open(filename, 'rt') as fobj:
        tree = ast.parse(fobj.read(), filename)

    # TODO: Transform
    # TODO: Globals

    code = compile(tree, filename, 'exec')
    exec(code)
