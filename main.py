#!/usr/bin/env python
import logging

import environ
import logbook
import sentry_sdk

from frontpage import HackerNewsFrontPage, HackerNewsEmptyDataException, DevSettings, ProdSettings
from firebase import FirebaseStreamingEvents


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


def main():
    logbook.set_datetime_format("local")
    logbook.compat.redirect_logging()

    settings = ProdSettings() if not env('HNFP_DEBUG') else DevSettings()
    settings.setup(env)

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
