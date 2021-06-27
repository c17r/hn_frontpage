import re


class Formatter(object):
    story = None
    hn_data = None
    valid_chars = re.compile(r"[^A-Za-z0-9\-\.\_\~\:\/\?\#\[\]\@\!\$\&\'\(\)\*\+\,\;\=]")

    def __init__(self, story, hn_data):
        self.story = story
        self.hn_data = hn_data

    def __call__(self, *args, **kwargs):
        return self.make_post()

    def __len__(self):
        raise NotImplemented('Base Class')

    def _clean_url(self, url):
        return ''.join(self.valid_chars.split(url))

    def make_post(self):
        raise NotImplemented('Base Class')

    @property
    def hn_url(self):
        return "https://news.ycombinator.com/item?id=" + str(self.story.hn_id)

    @property
    def story_url(self):
        return self._clean_url(self.hn_data['url'])

    @property
    def tco_length(self):
        return 23 # used to come from help/configuration but they retired the API

    @staticmethod
    def get_formatter(story, hn_data):
        if 'type' in hn_data and hn_data['type'] == 'job':
            return JobURLFormatter(story, hn_data)
        if 'url' in hn_data:
            return URLFormatter(story, hn_data)
        return NonURLFormatter(story, hn_data)


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
