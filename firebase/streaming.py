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

    def run(self):
        if self.request is None:
            self.request = requests.get(
                self.process_object.url,
                stream=True,
                headers={
                    'Accept': 'text/event-stream',
                }
            )

        event = {}
        for line in self.request.iter_lines():
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
