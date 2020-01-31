docker build -t tester .ci/Dockerfile

for script in g`demos/*`
    docker run --init --privileged tester @(script)
