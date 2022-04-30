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
from streamlink.utils.url import update_qsd

log = logging.getLogger(__name__)


MAX_INT32 = 2147483647
YYMMDDH_PATTERN = '%y%m%d%H'
CHARS = string.digits + string.ascii_uppercase
SUBS_ONLY = 'The {0} {1!r} is not available since it requires a subscription.'


class NoSubscriptionError(PluginError):
    def __init__(self, *args):
        error = SUBS_ONLY.format(*args)
        PluginError.__init__(self, error)


class Scene(enum.Enum):
    innerSite = 4
    embededPlayer = 11


def now_milliseconds():
    return int(time.time() * 1000)


class TrovoApolloAPI:
    CLI_ID = 4
    HOST = 'trovo.live'

    def __init__(self, client):
        self.client = client
        self.client.headers.update({
            'Origin': f'https://{self.HOST}',
            'Referer': f'https://{self.HOST}/',
            'User-Agent': useragents.CHROME
        })

    @staticmethod
    def build_gql_query(name, sha256hash, **params):
        return {
            'operationName': name,
            'extensions': {
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': sha256hash
                }
            },
            'variables': {
                'params': dict(**params)
            }
        }

    @staticmethod
    def build_stream_params():
        now = now_milliseconds()
        str_date = time.strftime(YYMMDDH_PATTERN)
        step1 = round(MAX_INT32 * (random.random() or .5))
        step2 = int(step1 * now % 1e10)
        pvid = f'{step2}{str_date}'
        scene = Scene(TrovoApolloAPI.CLI_ID).name
        return {
            '_f_': now,
            'pvid': pvid,
            'playScene': scene
        }

    @staticmethod
    def build_url_params(cli_id):
        now = now_milliseconds()
        tid = f'{now}{random.randint(1000, 9999)}'
        qid = ''.join(random.choice(CHARS) for _ in range(10))
        return {
            'chunk': 1,
            'resolution': '826*1536',
            'locale': 'en-US',
            'cli': cli_id,
            'from': '/',
            'reqms': now,
            'qid': qid,
            'client_info': {
                'device_info': {
                    'tid': tid
                }
            }
        }

    def call(self, data, schema):
        response = self.client.post(
            f'https://gql.{self.HOST}/',
            json=data,
            params=self.build_url_params(self.CLI_ID)
        )

        return self.client.json(response, schema=schema)

    def video(self, id):
        query = self.build_gql_query(
            'batchGetVodDetailInfo',
            'ceae0355d66476e21a1dd8e8af9f68de95b4019da2cda8b177c9a2255dad31d0',
            vids=[id]
        )

        schema = validate.Schema(validate.all({
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
                                'playInfos': [{
                                    'playUrl': validate.any(
                                        '',
                                        validate.all(
                                            validate.url(),
                                            validate.transform(
                                                lambda src: update_qsd(src, self.build_stream_params())
                                            )
                                        )
                                    ),
                                    'bitrate': int,
                                    'desc': str
                                }],
                                'playbackRights':
                                {
                                    'playbackRightsSetting': str
                                },
                            }
                        }
                    }
                }
            }
        }),
            validate.get(('data', 'batchGetVodDetailInfo', 'VodDetailInfos', id)),
            validate.union_get(
                ('vodInfo', 'vid'),
                ('streamerInfo', 'nickName'),
                ('vodInfo', 'categoryName'),
                ('vodInfo', 'title'),
                ('vodInfo', 'playbackRights', 'playbackRightsSetting'),
                ('vodInfo', 'playInfos'))
        )

        return self.call(query, schema=schema)

    def channel(self, channel):
        query = self.build_gql_query(
            'getLiveInfo',
            'a769a1ec0108996681ebd58a6349af72b97b8043d949929a6e2d3a11afbeed3a',
            userName=channel
        )

        schema = validate.Schema(validate.all({
            'data':
            {
                'getLiveInfo':
                {
                    'isLive': int,
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
                            'playUrl': validate.any(
                                '',
                                validate.all(
                                    validate.transform(
                                        lambda src: update_qsd(src, self.build_stream_params())
                                    ),
                                    validate.transform(
                                        lambda src: src.replace('.flv', '.m3u8')
                                    ),
                                    validate.url(
                                        scheme='http',
                                        path=validate.endswith('.m3u8')
                                    ),
                                )
                            ),
                            'vipOnly': validate.transform(bool),
                            'desc': str,
                            'bitrate': int
                        }]
                    }
                }
            }
        }),
            validate.get(('data', 'getLiveInfo')),
            validate.union_get(
                ('programInfo', 'id'),
                ('streamerInfo', 'userName'),
                ('categoryInfo', 'name'),
                ('programInfo', 'title'),
                'isLive',
                ('programInfo', 'streamInfo'))
        )

        return self.call(query, schema=schema)


@pluginmatcher(re.compile(r"""
    https?://trovo\.live/
    (?:
        (?:clip|video)/(?P<video>[^/?&]+)
        |
        (?P<channel>[^/?]+)
    )
""", re.VERBOSE))
class Trovo(Plugin):
    def __init__(self, url):
        super().__init__(url)
        groupdict = self.match.groupdict()
        self.kind = next(((str(k), str(v)) for k, v in groupdict.items() if v is not None))

        self.apollo_api = TrovoApolloAPI(client=self.session.http)

    def _video(self, id):
        try:
            data = self.apollo_api.video(id)
        except (PluginError, TypeError):
            raise NoStreamsError(self.url)

        self.id, self.author, self.category, \
            self.title, rights, videos = data

        if 'SubscriberOnly' in rights:
            raise NoSubscriptionError('vod', self.id)

        for video in videos:
            src = video.get('playUrl')
            quality = video.get('desc')
            yield quality, HLSStream(self.session, src)

    def _channel(self, channel):
        try:
            data = self.apollo_api.channel(channel)
        except (PluginError, TypeError):
            raise NoStreamsError(self.url)

        self.id, self.author, self.category, \
            self.title, online, streams = data

        if online == 0:
            raise PluginError('This stream is currently offline.')

        for stream in streams:
            src = stream.get('playUrl')
            isVIP = stream.get('vipOnly')
            quality = stream.get('desc')
            if isVIP:
                log.warning(SUBS_ONLY.format('quality', quality))
                continue
            yield quality, HLSStream(self.session, src)

    def _get_streams(self):
        key, value = self.kind
        method = getattr(self, f'_{key}')
        return method(value)


__plugin__ = Trovo
