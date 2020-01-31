FROM quay.io/buildah/stable
RUN dnf install python3

COPY . /
RUN bork build && pip3 install dist/*.whl
