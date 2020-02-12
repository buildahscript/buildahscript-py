import ast
import os
import sys

from . import modglobals


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

    Return2Call().visit(tree)

    sys.path = [os.path.dirname(filename)] + sys.path

    glbls = {
        name: getattr(modglobals, name)
        for name in modglobals.__all__
    }
    glbls['__name__'] = '__script__'
    glbls['__args__'] = buildargs
    glbls.update(buildargs)
    sys.modules['__buildah__'] = modglobals

    code = compile(tree, filename, 'exec')
    try:
        exec(code, glbls)
    except modglobals.ReturnImage as exc:
        image = exc.args[0]
    else:
        image = None

    return image


class Return2Call(ast.NodeTransformer):
    """
    Turn top-level return statements into calls to __return__
    """
    # Input: Return(value=<RETVAL>)
    # Output: Expr(value=Call(func=Name(id='__return__', ctx=Load()), args=[<RETVAL>], keywords=[]))

    def visit_FunctionDef(self, node):
        # Don't recurse
        return node

    def visit_AsyncFunctionDef(self, node):
        # Don't recurse
        return node

    def visit_ClassDef(self, node):
        # Don't recurse
        return node

    def visit_Return(self, node):
        return ast.fix_missing_locations(ast.copy_location(
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id='__return__', ctx=ast.Load()),
                    args=[node.value],
                    keywords=[],
                ),
            ),
            node,
        ))
