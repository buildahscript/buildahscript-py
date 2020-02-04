# buildahscript

Buildahscript is a new container definition language built to be imperative and flexible.

It allows you to do more with buildargs, create actually re-usable modules, and in general create more flexible container builders.

## Example

```python
#!/usr/bin/env buildahscript-py
#| pip: requests
#| arg: eula: bool
#| arg: version: str = "latest"
#| arg: type: str = "vanilla"

import tarfile

import requests


with TemporaryDirectory() as td:
    bin = td / 'bin'
    bin.mkdir()
    with Container('rust:buster') as build:
        build.copy_in('cmd', '/tmp/cmd')
        build.copy_in('localmc', '/tmp/localmc')
        build.run(['cargo', 'build', '--release'], pwd='/tmp/cmd')
        build.copy_out('/tmp/cmd/target/release/cmd', bin / 'cmd')

    with Container('rust:buster') as build:
        build.copy_in('status', '/tmp/status')
        build.copy_in('localmc', '/tmp/localmc')
        build.copy_in('mcproto-min-async', '/tmp/mcproto-min-async')
        build.run(['cargo', 'build', '--release'], pwd='/tmp/status')
        build.copy_out('/tmp/status/target/release/status', bin / 'status')

    # Download & extract mc-server-runner
    with requests.get('https://github.com/itzg/mc-server-runner/releases/download/1.3.3/mc-server-runner_1.3.3_linux_amd64.tar.gz') as resp:
        resp.raise_for_status()
        with tarfile.open(resp, 'r|*') as tf:
            for entry in tf:
                if entry.name == 'mc-server-runner':
                    tf.extract(entry, bin / 'mc-server-runner')

    with Container('openjdk:8-jre-slim') as cont:
        cont.copy_in(bin / 'cmd', '/usr/bin/cmd')
        cont.copy_in(bin / 'status', '/usr/bin/status')
        cont.copy_in(bin / 'mc-server-runner', '/mc-server-runner')

        cont.volumes |= {
            "/mc/world", "/mc/server.properties", "/mc/logs",
            "/mc/crash-reports", "/mc/banned-ips.json",
            "/mc/banned-players.json", "/mc/ops.json", "/mc/whitelist.json",
        }
        cont.entrypoint = ["/mc-server-runner", "-shell", "/bin/sh"]
        cont.command = ["/mc/launch"]
        cont.healthcheck_cmd = ["status"]
        cont.healthcheck_start_period = "5m"

        return cont.commit()
```


### shpipe

shpipe (`#|`) lines are used to specify metadata used by buildahscript. The basic form is `#| type: data`.

* `pip`: Gives a dependency to install from PyPI, as a [requirement specifier](https://pip.pypa.io/en/stable/reference/pip_install/#requirement-specifiers)
* `arg`: Defines a build arg, in the Python `name:type=default` form, where type
  is a dotted-form name to a type/parsing function, and default is a python literal.


## Licensing

This package is free to use for commercial purposes for a trial period under the terms of the [Prosperity Public License](./LICENSE).

Licenses for long-term commercial use are available via [licensezero.com](https://licensezero.com).

[![licensezero.com pricing](https://licensezero.com/projects/6aeb69c8-088b-41c2-b6ef-e7327ded1b7b/badge.svg)](https://licensezero.com/projects/6aeb69c8-088b-41c2-b6ef-e7327ded1b7b)