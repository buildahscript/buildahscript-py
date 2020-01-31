"""
Code for parsing scripts
"""
import ast
import dataclasses
import re
import typing


def scan_metadata_lines(lines):
    """
    Low-level parsing of #| lines

    Generates (prefix, text) tuples.
    """
    for line in lines:
        if line.startswith('#|') and ':' in line:
            before, after = line[2:].split(':', 1)
            yield before.strip(), after.strip()
        # Ignore #| lines without a colon


# Roughly parses python typed arguments: `name : type = default`
ARG = re.compile(r"(?P<name>\w+)\s*(?::\s*(?P<cast>[\w.]+))?\s*(?:=\s*(?P<default>.+))?")


def parse_arg(text):
    """
    Parses out `name:cast=default`-styled stuff
    """
    match = ARG.match(text)
    if match:
        name = match.group('name')
        raw_cast = match.group('cast')
        raw_default = match.group('default')

        if raw_cast is None:
            cast = str
        else:
            # TODO
            raise NotImplementedError("Caster resolution not yet implemented")

        if raw_default is not None:
            default = ast.literal_eval(raw_default)
        else:
            default = None

        return name, cast, default
    else:
        raise ValueError(f"Unable to parse {text!r}")


@dataclasses.dataclass(init=False)
class Metadata:
    """
    Holds data from #| lines in a buildahscript
    """
    deps: typing.List[str]
    args: typing.Dict[str, typing.Tuple[
        typing.Callable[[str], typing.Any],
        typing.Any,
    ]]

    def __init__(self):
        self.deps = []
        self.args = {}

    @classmethod
    def from_line_iter(cls, lines):
        """
        Parses out metadata from an iterable of lines (including file objects
        opened in readable text mode).
        """
        self = cls()
        for type, data in scan_metadata_lines(lines):
            if type == 'pip':
                self.deps.append(data)
            elif type == 'arg':
                name, caster, default = parse_arg(data)
                self.args[name] = (caster, default)
            else:
                # Ignore it
                pass

        return self
