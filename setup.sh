#!/usr/bin/env bash

set -eE

[ -f .venv/bin/python ] || python3 -m venv --without-pip .venv/
[ -f .venv/bin/pip ] || curl https://bootstrap.pypa.io/get-pip.py | .venv/bin/python

.venv/bin/pip install -e .
