#!/usr/bin/env bash

TARGET=/usr/share
if [[ $EUID -ne 0 ]]; then
   TARGET=~/.local/share
fi

TARGET=$TARGET/gateway

source $TARGET/venv/bin/activate
PYTHONPATH=$TARGET python3 -m app