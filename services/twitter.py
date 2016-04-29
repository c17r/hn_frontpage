from __future__ import absolute_import
import datetime
import logging

import twitter as api


_logger = logging.getLogger(__name__)


class TwitterServiceAuthenticationException(Exception):
    pass


class TwitterServiceNotConfigured(Exception):
    pass


class TwitterNetworkException(Exception):
    pass


class TwitterBase(object):

    def __init__(self, token, token_secret, consumer_key, consumer_secret):
        self.token = token
        self.token_secret = token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.auth = None
        self.screen_name = None
        self.twitter = None
        self.config = None
        self.config_expires = None

    @property
    def twitter_config(self):
        raise NotImplemented('Base Class')

    def user_stream(self, see_nontweet_messages=False):
        raise NotImplemented('Base Class')

    def post_status(self, status):
        raise NotImplemented('Base Class')

    def post_reply(self, message, status):
        raise NotImplemented('Base Class')

    def post_reply(self, tweet_id, reply_to, status):
        raise NotImplemented('Base Class')


class TestTwitter(TwitterBase):

    @property
    def twitter_config(self):
        return {
            'short_url_length': 24,
            'short_url_length_https': 24
        }

    def post_status(self, status):
        print "Posting to Twitter:"
        print status
        print "---"


class Twitter(TwitterBase):

    def __init__(self, token, token_secret, consumer_key, consumer_secret):
        super(Twitter, self).__init__(token,
                                      token_secret,
                                      consumer_key,
                                      consumer_secret)
        self._verify_credentials()

    def _verify_credentials(self):
        auth = api.OAuth(
            token=self.token,
            token_secret=self.token_secret,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
        )
        twitter = api.Twitter(auth=auth)
        try:
            profile = twitter.account.verify_credentials()
        except api.TwitterHTTPError as e:
            for err in e.response_data['errors']:
                if err['code'] == 89:  # invalid token or credentials
                    raise TwitterServiceAuthenticationException(
                        "Invalid Token"
                    )
            raise

        self.auth = auth
        self.twitter = twitter
        self.screen_name = profile['screen_name']

    def _verify_configured(self):
        if self.auth is None:
            raise TwitterServiceNotConfigured

    @property
    def twitter_config(self):
        self._verify_configured()
        if not self.config or self.config_expires < datetime.date.today():
            self.config = self.twitter.help.configuration()
            self.config_expires = datetime.date.today()
        return self.config

    def user_stream(self, see_nontweet_messages=False):
        self._verify_configured()
        breaks = 0

        stream = api.TwitterStream(
            auth=self.auth,
            domain='userstream.twitter.com'
        )
        for msg in stream.user():
            if see_nontweet_messages:
                yield msg
            else:
                if 'hangup' in msg and msg['hangup'] is True:
                    breaks += 1
                    if breaks > 5:
                        raise TwitterNetworkException(
                            "Repeated Network Failures"
                        )
                elif 'event' in msg and msg['event'] == 'access_revoked':
                    raise TwitterServiceAuthenticationException(
                        "Access to Stream Revoked"
                    )
                else:
                    breaks = 0
                    yield msg

    def post_status(self, status):
        self._verify_configured()

        try:
            self.twitter.statuses.update(status=status)
        except Exception as e:
            _logger.exception(str(e) + '>' + status + '<')
            raise

    def post_reply(self, message, status):
        return self.post_reply(
            message['id_str'],
            message['user']['screen_name'],
            status
        )

    def post_reply(self, tweet_id, reply_to, status):
        self._verify_configured()

        reply = '@' + reply_to
        if reply not in status:
            status = reply + ' ' + status

        self.twitter.statuses.update(
            in_reply_to_status_id=tweet_id,
            status=status
        )


