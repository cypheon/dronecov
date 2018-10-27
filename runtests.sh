#!/bin/sh

set -e
set -u

ACCESS_TOKEN=$(DRONECOV_DB_URI=sqlite:///./tests/tmp.db pipenv run ./dronecov.py token-batch testuser token-name)
export ACCESS_TOKEN

PYTHONPATH="$PWD:${PYTHONPATH:-}" \
  pipenv run pytest \
  --tavern-global-cfg tests/common.yaml \
  tests/*.tavern.yaml -v
