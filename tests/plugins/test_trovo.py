from streamlink.plugins.trovo import Trovo
from tests.plugins import PluginCanHandleUrl


class TestPluginCanHandleUrlTrovo(PluginCanHandleUrl):
    __plugin__ = Trovo

    should_match_groups = [
        ('https://trovo.live/s/Maddyson/215661616',
            {'channel': 'Maddyson'}),
        ('https://trovo.live/s/Maddyson/215661616?adtag=user.EXAMPLE.clip',
            {'channel': 'Maddyson'}),
        ('https://trovo.live/s/ChilledCatRadio/549755919717?vid=lc-387702300526225353&adtag=user.BAN.clip',
            {'channel': 'ChilledCatRadio', 'video': 'lc-387702300526225353'}),
        ('https://trovo.live/s/ChilledCatRadio/549755919717?vid=ltv-100025538_100025538_387702302348073784&adtag=user.BAN.clip',
            {'channel': 'ChilledCatRadio', 'video': 'ltv-100025538_100025538_387702302348073784'}),
    ]

    should_not_match = [
        'https://trovo.live',
        'https://trovo.live/',
        'https://trovo.live/Maddyson',
        'https://trovo.live/clip/lc-387743296843423010',
        'https://trovo.live/video/ltv-108024053_108024053_387702296935586449?ltab=videos&adtag=user.EXAMPLE.clip',
    ]
