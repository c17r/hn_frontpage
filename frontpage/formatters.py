
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

    @property
    def story_url(self):
        # Job posts can be either to an external job site..OR..a special HN
        # item that has no comments.  Handle both cases.
        try:
            return super(JobURLFormatter, self).story_url
        except:
            return self.hn_url

    def make_post(self):
        return "\nJ: %s" % self.story_url

    def __len__(self):
        post_length = len(self.make_post())
        urls_length = len(self.story_url)
        return post_length - urls_length + self.tco_length
