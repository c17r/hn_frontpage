#!/usr/bin/env bash

/home/hn_frontpage/run/current/venv/bin/python \
    /home/hn_frontpage/run/current/src/main.py \
    $1 \
    --pid-file /home/hn_frontpage/run/hnfp.pid \
    --log-file /home/hn_frontpage/run/hnfp.log \
    --db-file /home/hn_frontpage/run/hnfp_storage.db \
    --config-file /home/hn_frontpage/run/secrets.json
