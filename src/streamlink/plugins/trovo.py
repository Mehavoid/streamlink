"""
$url trovo.live
$type live, vod
"""

import logging
import re

from streamlink.plugin import Plugin, pluginmatcher

log = logging.getLogger(__name__)


@pluginmatcher(re.compile(r"""
    https?://trovo\.live/
    (?:
        (?:clip|video)/(?P<video>[-_ltvc0-9]+)
        |
        (?P<channel>[^/?]+)
    )
""", re.VERBOSE))
class Trovo(Plugin):
    def __init(self, url):
        pass


__plugin__ = Trovo
