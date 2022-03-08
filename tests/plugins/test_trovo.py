from streamlink.plugins.trovo import Trovo
from tests.plugins import PluginCanHandleUrl


class TestPluginCanHandleUrlTrovo(PluginCanHandleUrl):
    __plugin__ = Trovo

    should_match_groups = [
        ('https://trovo.live/Maddyson',
            {'channel': 'Maddyson'}),
        ('https://trovo.live/Maddyson?adtag=user.EXAMPLE.clip',
            {'channel': 'Maddyson'}),
        ('https://trovo.live/clip/lc-387743296843423010',
            {'video': 'lc-387743296843423010'}),
        ('https://trovo.live/clip/lc-387702296843423010?ltab=videos',
            {'video': 'lc-387702296843423010'}),
        ('https://trovo.live/video/ltv-108024053_108024053_387702296935586449',
            {'video': 'ltv-108024053_108024053_387702296935586449'}),
        ('https://trovo.live/video/ltv-108024053_108024053_387702296935586449?ltab=videos&adtag=user.EXAMPLE.clip',
            {'video': 'ltv-108024053_108024053_387702296935586449'}),
    ]

    should_not_match = [
        'https://trovo.live'
        'https://trovo.live/'
    ]
