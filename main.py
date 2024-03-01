from featurewebcraftapi import WebCraftAPIFeature
from feature2048 import _2048Feature
from featurecoderunner import CodeRunnerFeature
from playground import TestFeature

from tgbot import build_bot

tgBotToken = '7135037009:AAFtf3nwFrXcOGbchNBpTfVF4UO7dbcRidI'
webCraftHostname = 'mc6.ytonidc.com:14132'

if __name__ == '__main__':
    build_bot(
        features=[
            # _2048Feature(),
            # CodeRunnerFeature(),
            WebCraftAPIFeature(webCraftHostname, False)
            # TestFeature()
        ],
        bot_meta={
            'type': 'telegram',
            'token': tgBotToken
        }
    ).run()
