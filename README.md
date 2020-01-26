Argument Features:
* build args
* tags

Language features:
* Front matter
  * Required pip packages
  * Build arg conversions
* build args
* return an image
* Container.open(): "Opens" a file inside the container (lots of buffering
  happening), object has additional methods for chown, chmod, stat, etc
* Container.copy_out(): Copies a file/directory from container to host (mount, copy, unmount)
* Container.run(): Accepts all arguments of subprocess.run() (requires a lot of magic)

Additional
* Makes sure script is run inside `buildah unshare`, so a bunch of stuff (most
  everyting) works correctly. (See: `$_CONTAINERS_USERNS_CONFIGURED`)

```python
#!/usr/bin/env buildahscript
#| pip: requests
#| arg: eula: bool
#| arg: version: str = "latest"
#| arg: type: str = "vanilla"

with TemporaryDirectory() as td:
    bin = td / 'bin'
    bin.mkdir()
    with workspace('rust:buster') as build:
        build.copy_in('cmd', '/tmp/cmd')
        build.copy_in('localmc', '/tmp/localmc')
        build.run(['cargo', 'build', '--release'], pwd='/tmp/cmd')
        build.copy_out('/tmp/cmd/target/release/cmd', bin / 'cmd')

    with workspace('rust:buster') as build:
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

    with workspace('openjdk:8-jre-slim') as cont:
        cont.copy_in(bin / 'cmd', '/usr/bin/cmd')
        cont.copy_in(bin / 'status', '/usr/bin/status')
        cont.copy_in(bin / 'mc-server-runner', '/mc-server-runner')

        # Build /mc

        cont.config(
            volumes=[
                "/mc/world", "/mc/server.properties", "/mc/logs",
                "/mc/crash-reports", "/mc/banned-ips.json",
                "/mc/banned-players.json", "/mc/ops.json", "/mc/whitelist.json",
            ],
            entrypoint=["/mc-server-runner", "-shell", "/bin/sh"],
            cmd=["/mc/launch"],
            healthcheck=["status"],
            healthcheck_start_period="5m",
        )
        return cont.commit()
```
