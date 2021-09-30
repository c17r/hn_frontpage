#!/usr/bin/env python

import json
import logging
import os
import sys

from abc import ABC

import environ
import logbook
import sentry_sdk

from frontpage.frontpage import HackerNewsFrontPage
from firebase import FirebaseStreamingEvents
from services import Twitter
from services.twitter import TestTwitter


_logger = logging.getLogger(__name__)


env = environ.Env(
    HNFP_TOKEN=(str, ''),
    HNFP_TOKEN_SECRET=(str, ''),
    HNFP_CONSUMER_KEY=(str, ''),
    HNFP_CONSUMER_SECRET=(str, ''),
    HNFP_DEBUG=(bool, False),
    HNFP_DEBUG_CLEAR_DB=(bool, True),
    HNFP_DB_FILE=(str, ''),
    HNFP_SENTRYIO_URL=(str, '')
)
environ.Env.read_env()


class Settings(ABC):
    def setup(self):
        pass

    def get_twitter(self):
        pass

    def report_exception(self, exc):
        pass


class ProdSettings(Settings):
    def setup(self):
        sentry_sdk.init(env('HNFP_SENTRYIO_URL'), traces_sample_rate=0.0)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logbook.StreamHandler(
            sys.stdout,
            level='INFO',
            format_string=u"{record.time:%Y-%m-%d %H:%M:%S.%f} : {record.level_name} : {record.channel} : {record.message}"
        ).push_application()

    def get_twitter(self):
        return Twitter

    def report_exception(self, exc):
        sentry_sdk.capture_exception(exc)


class DevSettings(Settings):
    def setup(self):
        logbook.StreamHandler(sys.stdout).push_application()
        if os.path.isfile(env('HNFP_DB_FILE')) and env('HNFP_DEBUG_CLEAR_DB'):
            _logger.info('removing existing DB')
            os.remove(env('HNFP_DB_FILE'))

    def get_twitter(self):
        return TestTwitter

    def report_exception(self, exc):
        pass


def main():
    logbook.set_datetime_format("local")
    logbook.compat.redirect_logging()

    settings = ProdSettings() if not env('HNFP_DEBUG') else DevSettings()
    settings.setup()

    config = {
        'token': env('HNFP_TOKEN'),
        'token_secret': env('HNFP_TOKEN_SECRET'),
        'consumer_key': env('HNFP_CONSUMER_KEY'),
        'consumer_secret': env('HNFP_CONSUMER_SECRET'),
    }
    klass = settings.get_twitter()
    twitter = klass(**config)
    hackernews_frontpage = HackerNewsFrontPage(env('HNFP_DB_FILE'), twitter)
    firebase = FirebaseStreamingEvents(hackernews_frontpage)

    while True:
        try:
            firebase.run()
        except KeyboardInterrupt:
            _logger.info("Shutdown signal received, stopping..")
            return
        except Exception as e:
            _logger.exception("Exception: " + str(e))
            settings.report_exception(e)

if __name__ == "__main__":
    logging.getLogger("environ.environ").setLevel(logging.WARNING)
    main()
