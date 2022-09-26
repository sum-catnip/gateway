#!/usr/bin/env bash

SHARE=/usr/share
BIN=/usr/bin
SYSTEMD=TODO
if [[ $EUID -ne 0 ]]; then
   SHARE=~/.local/share
   BIN=~/.local/bin
   SYSTEMD=~/.config/systemd/user
fi

mkdir -p $SYSTEMD
mkdir -p $SHARE
mkdir -p $BIN
GATEWAY=$SHARE/gateway

rm -rf $GATEWAY
cp -r . $GATEWAY
python3 -m venv $GATEWAY/venv
source $GATEWAY/venv/bin/activate
python3 -m pip install -r $GATEWAY/requirements.txt
cp scripts/run.sh $BIN/gateway

cp $GATEWAY/systemd/user.service $SYSTEMD/gateway.service