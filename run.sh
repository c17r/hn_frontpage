#!/usr/bin/env bash

RUN=$PWD/run
CURRENT=$RUN/current

PIDFILE=$RUN/hnfp.pid
LOGFILE=$RUN/hnfp.log
DBFILE=$RUN/hnfp_storage.db
CONFIGFILE=$RUN/secrets.json

source $CURRENT/venv/bin/activate

python $CURRENT/src/main.py $1 --pid-file $PIDFILE --log-file $LOGFILE --db-file $DBFILE --config-file $CONFIGFILE
