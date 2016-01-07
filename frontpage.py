import datetime
import logging

import requests

import services.storage as db
from firebase import FireBaseStreamingProcessBase


_logger = logging.getLogger(__name__)


class Formatter(object):
    story = None
    hn_data = None
    twitter_config = None

    def __init__(self, story, hn_data, twitter_config):
        self.story = story
        self.hn_data = hn_data
        self.twitter_config = twitter_config

    def __call__(self, *args, **kwargs):
        return self.make_post()

    def __len__(self):
        raise NotImplemented('Base Class')

    def make_post(self):
        raise NotImplemented('Base Class')

    @property
    def hn_url(self):
        return "https://news.ycombinator.com/item?id=" + str(self.story.hn_id)

    @property
    def story_url(self):
        return self.hn_data['url']

    @property
    def tco_length(self):
        rtn = self.twitter_config['short_url_length']
        if self.twitter_config['short_url_length_https'] > rtn:
            rtn = self.twitter_config['short_url_length_https']
        return rtn

    @staticmethod
    def get_formatter(story, hn_data, twitter_config):
        if 'type' in hn_data and hn_data['type'] == 'job':
            return JobURLFormatter(story, hn_data, twitter_config)
        if 'url' in hn_data:
            return URLFormatter(story, hn_data, twitter_config)
        return NonURLFormatter(story, hn_data, twitter_config)


class URLFormatter(Formatter):
    def make_post(self):
        return "\nL: %s\nC: %s" % (self.story_url, self.hn_url)

    @property
    def tco_length(self):
        orig = super(URLFormatter, self).tco_length
        return orig * 2

    def __len__(self):
        post_length = len(self.make_post())
        urls_length = len(self.story_url) + len(self.hn_url)
        return post_length - urls_length + self.tco_length


class NonURLFormatter(Formatter):
    def make_post(self):
        return "\nC: %s" % self.hn_url

    def __len__(self):
        post_length = len(self.make_post())
        urls_length = len(self.hn_url)
        return post_length - urls_length + self.tco_length


class JobURLFormatter(Formatter):
    def make_post(self):
        return "L: %s" % self.story_url

    def __len__(self):
        post_length = len(self.make_post())
        urls_length = len(self.story_url)
        return post_length - urls_length + self.tco_length


class HackerNewsFrontPage(FireBaseStreamingProcessBase):
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json?orderBy=%22$key%22&limitToFirst=30'
    twitter = None

    def __init__(self, db_path, twitter):
        db.init(db_path)
        self.twitter = twitter

    def _get_hn_data(self, hn_id):
        title_url = 'https://hacker-news.firebaseio.com/v0/item/%s.json' % hn_id
        r = requests.get(title_url)
        r.raise_for_status()
        return r.json()

    def _post_to_twitter(self, story):
        hn_data = self._get_hn_data(story.hn_id)
        tweet = self._format_tweet(story, hn_data)
        self.twitter.post_status(tweet)
        _logger.info("Posting " + hn_data['title'])

    def _format_tweet(self, story, hn_data):
        config = self.twitter.twitter_config
        formatter = Formatter.get_formatter(story, hn_data, config)
        post = formatter()
        title_length = 140 - len(formatter)
        if len(hn_data['title']) <= title_length:
            post = hn_data['title'] + post
        else:
            post = hn_data['title'][:(title_length - 1)] + unichr(8230) + post

        return post

    def _today(self):
        return datetime.date.today()

    def _tomorrow(self):
        return datetime.date.today() + datetime.timedelta(days=1)

    def _is_ready_to_post(self, story):
        return story.next_post < self._today()

    def _update_story(self, story):
        if story.last_saw < self._today():
            story.times += 1
        story.last_saw = self._today()

    def _set_next_post(self, story):
        story.next_post = self._tomorrow()

    def process(self, event):

        for hn_id in event['data'].itervalues():

            story, _ = db.Story.get_or_create(hn_id=hn_id)
            self._update_story(story)
            if self._is_ready_to_post(story):
                self._post_to_twitter(story)
                self._set_next_post(story)
            story.save()
