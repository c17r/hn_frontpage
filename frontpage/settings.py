import logging
import os
import sys

from abc import ABC

import environ
import logbook
import sentry_sdk

from services import Twitter
from services.twitter import TestTwitter


_logger = logging.getLogger(__name__)


class Settings(ABC):
    def setup(self, env):
        pass

    def get_twitter(self):
        pass

    def report_exception(self, exc):
        pass


class ProdSettings(Settings):
    def setup(self, env):
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
    def setup(self, env):
        logbook.StreamHandler(sys.stdout).push_application()
        if os.path.isfile(env('HNFP_DB_FILE')) and env('HNFP_DEBUG_CLEAR_DB'):
            _logger.info('removing existing DB')
            os.remove(env('HNFP_DB_FILE'))

    def get_twitter(self):
        return TestTwitter

    def report_exception(self, exc):
        pass
