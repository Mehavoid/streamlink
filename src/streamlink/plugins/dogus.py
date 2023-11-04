"""
$description Turkish live TV channels from Dogus Group, including Euro Star, Star and NTV.
$url eurostartv.com.tr
$url kralmuzik.com.tr
$url ntv.com.tr
$url startv.com.tr
$type live
"""

import re

from streamlink.plugin import Plugin, pluginmatcher
from streamlink.plugin.api import validate
from streamlink.stream.hls import HLSStream


@pluginmatcher(re.compile(r"https?://(?:www\.)?eurostartv\.com\.tr/canli-izle"))
@pluginmatcher(re.compile(r"https?://(?:www\.)?kralmuzik\.com\.tr/tv/.+"))
@pluginmatcher(re.compile(r"https?://(?:www\.)?ntv\.com\.tr/canli-yayin/ntv"))
@pluginmatcher(re.compile(r"https?://(?:www\.)?startv\.com\.tr/canli-yayin"))
class Dogus(Plugin):
    _re_live_hls = re.compile(r"'(https?://[^']+/live/hls/[^']+)'")
    _re_yt_script = re.compile(r"youtube\.init\('([\w-]{11})'")

    def _get_streams(self):
        root = self.session.http.get(self.url, schema=validate.Schema(validate.parse_html()))

        # https://www.ntv.com.tr/canli-yayin/ntv?youtube=true
        yt_iframe = root.xpath("string(.//iframe[contains(@src,'youtube.com')][1]/@src)")
        # https://www.startv.com.tr/canli-yayin
        dm_iframe = root.xpath("string(.//iframe[contains(@src,'dailymotion.com')][1]/@src)")
        if yt_script := root.xpath(
            "string(.//script[contains(text(), 'youtube.init')][1]/text())"
        ):
            if m := self._re_yt_script.search(yt_script):
                yt_iframe = f"https://www.youtube.com/watch?v={m.group(1)}"

        if iframe := yt_iframe or dm_iframe:
            return self.session.streams(iframe)

        if dd_script := root.xpath(
            "string(.//script[contains(text(), '/live/hls/')][1]/text())"
        ):
            if m := self._re_live_hls.search(dd_script):
                return HLSStream.parse_variant_playlist(self.session, m.group(1))


__plugin__ = Dogus
