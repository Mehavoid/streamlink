"""
$url trovo.live
$type live, vod
"""

import enum
import logging
import random
import re
import string
import time

from streamlink.exceptions import NoStreamsError, PluginError
from streamlink.plugin import Plugin, pluginmatcher
from streamlink.plugin.api import useragents, validate
from streamlink.stream.hls import HLSStream
from streamlink.stream.http import HTTPStream
from streamlink.utils.url import update_qsd

log = logging.getLogger(__name__)


CHARS = string.digits + string.ascii_uppercase
VIP_ONLY = 'The quality "{0}" is not available since it requires a subscription.'


class CLI(enum.Enum):
    innerSite = 4
    embededPlayer = 11


def build_stream_params():
    pass


def build_url_params(cli_id):
    now = int(time.time())
    tid = f'{now}{int(9e3 * random.random() + 1e3)}'
    qid = ''.join(random.choice(CHARS) for _ in range(10))
    return {
        'chunk': 1,
        'resolution': '826*1536',
        'locale': 'en-US',
        'cli': cli_id,
        'from': '/',
        'reqms': now,
        'qid': qid,
        'client_info':
        {
            'device_info':
            {
                'tid': tid
            }
        }
    }


def build_gql_query(name, sha256hash, **params):
    return {
        'operationName': name,
        'extensions':
        {
            'persistedQuery':
            {
                'version': 1,
                'sha256Hash': sha256hash
            }
        },
        'variables':
        {
            'params': dict(**params)
        }
    }


def update_params(src):
    return update_qsd(src, build_stream_params())


class TrovoApolloAPI:
    CLI_ID = 4

    def __init__(self, session):
        self.session = session
        self.session.http.headers.update({
            'Origin': 'https://trovo.live',
            'Referer': 'https://trovo.live/',
            'User-Agent': useragents.CHROME
        })

    def call(self, data, schema):
        response = self.session.http.post(
            'https://gql.trovo.live/',
            json=data,
            params=build_url_params(self.CLI_ID)
        )

        return self.session.http.json(response, schema=schema)

    def video(self, id):
        query = build_gql_query(
            'batchGetVodDetailInfo',
            'ceae0355d66476e21a1dd8e8af9f68de95b4019da2cda8b177c9a2255dad31d0',
            vids=list(id)
        )

        schema = validate.Schema({
            'data':
            {
                'batchGetVodDetailInfo':
                {
                    'VodDetailInfos':
                    {
                        id:
                        {
                            'streamerInfo':
                            {
                                'nickName': str
                            },
                            'vodInfo':
                            {
                                'categoryName': str,
                                'title': str,
                                'vid': str,
                                'playInfos': [validate.all({
                                    'playUrl': validate.all(validate.url(), validate.transform(update_params)),
                                    'bitrate': int,
                                    'desc': str
                                })]
                            }
                        }
                    }
                }
            }
        },
            validate.get(('data', 'batchGetVodDetailInfo', 'VodDetailInfos', id)),
            validate.union_get(
                ('vodInfo', 'vid'),
                ('streamerInfo', 'nickName'),
                ('streamerInfo', 'nickName'),
                ('vodInfo', 'categoryName'),
                ('vodInfo', 'title'),
                ('vodInfo', 'playInfos'))
        )

        return self.call(query, schema=schema)

    def channel(self, channel):
        query = build_gql_query(
            'getLiveInfo',
            'a769a1ec0108996681ebd58a6349af72b97b8043d949929a6e2d3a11afbeed3a',
            userName=channel
        )

        schema = validate.Schema({
            'data':
            {
                'getLiveInfo': validate.all({
                    'categoryInfo':
                    {
                        'name': str
                    },
                    'streamerInfo':
                    {
                        'userName': str
                    },
                    'programInfo':
                    {
                        'id': str,
                        'title': str,
                        'streamInfo': [{
                            'playUrl': validate.all(str, validate.transform(update_params)),
                            'vipOnly': validate.transform(bool),
                            'desc': str,
                            'bitrate': int
                        }],
                    }
                })
            }
        },
            validate.get(('data', 'getLiveInfo')),
            validate.union_get(
                ('programInfo', 'id'),
                ('streamerInfo', 'userName'),
                ('categoryInfo', 'name'),
                ('programInfo', 'title'),
                ('programInfo', 'streamInfo'))
        )

        return self.call(query, schema=schema)


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
        self.kind = next(((str(k), str(v)) for k, v in match.items() if v is not None))

        self.appolo_api = TrovoApolloAPI(session=self.session)

    def _video(self, id):
        try:
            data = self.apollo_api.video(id)
        except (PluginError, TypeError):
            raise NoStreamsError(self.url)

        self.id, self.author, self.category, self.title, videos = data

        for video in videos:
            src = video.get('playUrl')
            quality = video.get('desc')
            yield quality, HLSStream(self.session, src)

    def _channel(self, channel):
        try:
            data = self.apollo_api.channel(channel)
        except (PluginError, TypeError):
            raise NoStreamsError(self.url)

        self.id, self.author, self.category, self.title, streams = data

        for stream in streams:
            src = stream.get('playUrl')
            isVIP = stream.get('vipOnly')
            quality = stream.get('desc')
            if isVIP:
                log.warning(VIP_ONLY.format(quality))
                continue
            yield quality, HTTPStream(self.session, src)

    def _get_streams(self):
        key, value = self.kind
        method = getattr(self, f'_{key}')
        return method(value)


__plugin__ = Trovo
