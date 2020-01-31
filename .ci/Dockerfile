FROM quay.io/buildah/stable
RUN dnf install python3

COPY . /
RUN pip3 install bork && bork build && pip3 install dist/*.whl
