from bilibili_api.utils.AsyncEvent import AsyncEvent

from .GuildBot import Event, GuildBot, Intents, logger
from .promise import Promise
from .util import *

ipcRenderer = AsyncEvent()  # InterPlugins Communication 插件内通信
__THE_ONLY_ONE_BOT = GuildBot(intents=Intents(public_guild_messages=True), bot_log=None)

def get_driver():
    return __THE_ONLY_ONE_BOT
