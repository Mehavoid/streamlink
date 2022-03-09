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
        pass

    def _video(self):
        pass

    def _channel(self):
        pass

    def _get_streams(self):
        pass


__plugin__ = Trovo
