import datetime
import logging
import time

import requests

import services.storage as db
from firebase import FireBaseStreamingProcessBase
from .formatters import Formatter


_logger = logging.getLogger(__name__)


class HackerNewsEmptyDataException(Exception):
    pass


class HackerNewsFrontPage(FireBaseStreamingProcessBase):
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json?orderBy=%22$key%22&limitToFirst=30'
    twitter = None

    def __init__(self, db_path, twitter):
        db.init(db_path)
        self.twitter = twitter

    def _get_hn_data(self, hn_id):
        times = 0
        while times < 5:
            times += 1
            title_url = 'https://hacker-news.firebaseio.com/v0/item/%s.json' % hn_id
            r = requests.get(title_url)
            r.raise_for_status()
            rv = r.json()
            if rv is not None:
                return rv
            time.sleep(1.0)
        return None

    def _post_to_twitter(self, story):
        hn_data = self._get_hn_data(story.hn_id)
        if (hn_data is None):
            raise HackerNewsEmptyDataException(story.hn_id)
        tweet = self._format_tweet(story, hn_data)
        self.twitter.post_status(tweet)
        _logger.info("Posting " + hn_data['title'])

    def _format_tweet(self, story, hn_data):
        formatter = Formatter.get_formatter(story, hn_data)
        post = formatter()
        title_length = 140 - len(formatter)
        if len(hn_data['title']) <= title_length:
            post = hn_data['title'] + post
        else:
            post = hn_data['title'][:(title_length - 1)] + chr(8230) + post

        return post

    def _today(self):
        return datetime.date.today()

    def _tomorrow(self):
        return datetime.date.today() + datetime.timedelta(days=1)

    def _is_ready_to_post(self, story):
        return story.next_post < self._today()

    def _update_story(self, story, position):
        if story.last_saw < self._today():
            story.times += 1
        story.last_saw = self._today()

        # 0 means we've never seen it
        # less than since we want to record how close they come to #1
        if story.position == 0 or position < story.position:
            story.position = position

    def _set_next_post(self, story):
        story.next_post = self._tomorrow()

    def process(self, event):

        for position, hn_id in enumerate(event['data'], start=1):

            story, _ = db.Story.get_or_create(hn_id=hn_id)
            self._update_story(story, position)
            if self._is_ready_to_post(story):
                self._post_to_twitter(story)
                self._set_next_post(story)
            story.save()
