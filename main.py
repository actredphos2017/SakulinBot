from feature2048 import _2048Feature
from featuredebug import DebugFeature
from featurewebcraftapi import WebCraftAPIFeature

from tgbot import build_bot
import os
from dotenv import load_dotenv

load_dotenv()

tgbot_token = os.getenv('TGBOT_TOKEN')
web_craft_hostname = os.getenv('CRAFT_HOST_NAME')
admin_authorization = os.getenv('ADMIN_AUTHORIZATION')

if __name__ == '__main__':
    build_bot(
        features=[
            DebugFeature(),
            WebCraftAPIFeature(web_craft_hostname, admin_authorization, https=False),
            _2048Feature()
        ],
        bot_meta={
            'type': 'telegram',
            'token': tgbot_token
        }
    ).run()
