import json
import logging
import re
from abc import ABC

import requests


_logger = logging.getLogger(__name__)


class FirebaseStreamingEvents(object):
    request = None
    process_object = None
    RETURN_EVENTS = frozenset(['keep-alive'])
    RAISE_EVENTS = frozenset(['cancel', 'auth_revoked'])
    SSE = re.compile(r'event: (.+)\ndata: (.+)')

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
                for line in self.request.iter_lines(chunk_size=1, delimiter=b'\n\n'):
                    yield line
            except requests.exceptions.RequestException as e:
                _logger.exception("Exception: " + str(e))
                self._create_requests()

    def run(self):
        if self.request is None:
            self._create_requests()

        event = {}
        for line in self._get_data():
            line = line.decode('utf-8')
            _logger.debug('Data from server: ' + str(line))
            if not line:
                continue
            event = self._process_data(line)
            if self._process_event(event) is not None:
                break

    def _process_data(self, raw):
        values = self.SSE.match(raw)
        return {
            'event': values.group(1),
            'data': values.group(2),
        }

    def _process_event(self, event):
        if not self.process_object.raw_events:
            if event['event'] in self.RETURN_EVENTS:
                return
            if event['event'] in self.RAISE_EVENTS:
                return KeyboardInterrupt
        return self.process_object.process(json.loads(event['data']))


class FireBaseStreamingProcessBase(ABC):
    url = None
    raw_events = False

    def process(self, event):
        raise NotImplemented('Base Class')
