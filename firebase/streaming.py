import json
import logging

import requests


_logger = logging.getLogger(__name__)


class FirebaseStreamingEvents(object):
    request = None
    process_object = None
    RETURN_EVENTS = frozenset(['keep-alive'])
    RAISE_EVENTS = frozenset(['cancel', 'auth_revoked'])

    def __init__(self, process_object):
        self.process_object = process_object

    def _create_requests(self):
        self.request = requests.get(
            self.process_object.url,
            stream=True,
            headers={
                'Accept': 'text/event-stream',
            }
        )

    def _get_data(self):
        while True:
            try:
                for line in self.request.iter_lines():
                    yield line
            except requests.exceptions.RequestException as e:
                _logger.exception()
                self._create_requests()

    def run(self):
        if self.request is None:
            self._create_requests()

        event = {}
        for line in self._get_data():
            if not line:
                continue
            if line[:6] == 'event:':
                event['event'] = line[7:]
                continue
            if line[:5] == 'data:':
                event['data'] = line[6:]
                if self._process_event(event) is not None:
                    break
                event = {}

    def _process_event(self, event):
        if not self.process_object.raw_events:
            if event['event'] in self.RETURN_EVENTS:
                return
            if event['event'] in self.RAISE_EVENTS:
                return KeyboardInterrupt
        return self.process_object.process(json.loads(event['data']))


class FireBaseStreamingProcessBase(object):
    url = None
    raw_events = False

    def process(self, event):
        raise NotImplemented('Base Class')
