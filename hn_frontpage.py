#!/usr/bin/env python
import sys
import json
import logging
import argparse

import daemonocle

from frontpage import HackerNewsFrontPage
from firebase import FirebaseStreamingEvents
from services import Twitter


_logger = logging.getLogger(__name__)


def get_config(path):
    with open(path, "r") as f:
        raw = f.read()
    return json.loads(raw)


def cb_shutdown(message, code):
    _logger.info("Shutdown signal triggered: %s - %s", code, message)


def main():
    args = parser.parse_args()
    config = get_config(args.config_file)
    twitter = Twitter(**config)
    hackernews_frontpage = HackerNewsFrontPage(args.db_file, twitter)
    firebase = FirebaseStreamingEvents(hackernews_frontpage)

    while True:
        try:
            firebase.run()
        except KeyboardInterrupt:
            _logger.info("Shutdown signal received, stopping..")
            return
        except Exception as e:
            _logger.error("Exception: " + str(e))


parser = argparse.ArgumentParser()
parser.add_argument(
    'action',
    type=str,
    choices=['start', 'stop', 'restart', 'status', 'cli'],
)
parser.add_argument(
    '--pid-file',
    type=str,
    default='./hnfp.pid',
)
parser.add_argument(
    '--log-file',
    type=str,
    default='./hnfp.log',
)
parser.add_argument(
    '--db-file',
    type=str,
    default='./hnfp_storage.db'
)
parser.add_argument(
    '--config-file',
    type=str,
    default='./secrets.json'
)

if __name__ == "__main__":
    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s : %(levelname)s : %(name)s : %(message)s"
    )

    if args.action != 'cli':
        daemon = daemonocle.Daemon(
            worker=main,
            shutdown_callback=cb_shutdown,
            pidfile=args.pid_file,
            workdir="."
        )
        daemon.do_action(args.action)
    else:
        main()
