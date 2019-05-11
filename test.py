#!/usr/bin/env python

import os
import logbook
import sys

from main import get_config
from frontpage.frontpage import HackerNewsFrontPage
from firebase import FirebaseStreamingEvents
from services.twitter import TestTwitter

DB_FILENAME = 'hnfp_storage.db'

def main():
    if os.path.isfile(DB_FILENAME):
        print("remove existing DB")
        os.remove(DB_FILENAME)

    config = get_config('secrets.json')
    twitter = TestTwitter(**config)
    hackernews_frontpage = HackerNewsFrontPage(DB_FILENAME, twitter)
    firebase = FirebaseStreamingEvents(hackernews_frontpage)

    try:
        firebase.run()
    except KeyboardInterrupt:
        print("Shutting down")

if __name__ == '__main__':
    logbook.set_datetime_format("local")
    logbook.compat.redirect_logging()
    logbook.StreamHandler(sys.stdout).push_application()
    main()
