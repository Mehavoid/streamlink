"""
$url trovo.live
$type live, vod
"""

import logging
import re

from streamlink.plugin import Plugin, pluginmatcher

log = logging.getLogger(__name__)


def build_stream_params():
    pass


def build_url_params():
    pass


def build_gql_params():
    pass


class TrovoApolloAPI:
    def __init__(self):
        pass

    def call(self):
        pass

    def video(self):
        pass

    def channel(self):
        pass


@pluginmatcher(re.compile(r"""
    https?://trovo\.live/
    (?:
        (?:clip|video)/(?P<video>[-_ltvc0-9]+)
        |
        (?P<channel>[^/?]+)
    )
""", re.VERBOSE))
class Trovo(Plugin):
    def __init__(self, url):
        super().__init__(url)
        match = self.match.groupdict()
        self.kind = ((str(k), str(v)) for k, v in match.items() if v is not None)

        self.appolo_api = TrovoApolloAPI(session=self.session)

    def _video(self, id):
        pass

    def _channel(self, channel):
        pass

    def _get_streams(self):
        key, value = next(self.kind)
        method = getattr(self, f'_{key}')
        return method(value)


__plugin__ = Trovo
