from bilibili_api.utils.AsyncEvent import AsyncEvent

from .guildbot import Event, GuildBot, logger

__all__ = [
    "Event",
    "GuildBot",
    "logger",
    "ipcEvent",
]

ipcEvent = AsyncEvent()  # InterPlugins Communication 插件间通信
__THE_ONLY_ONE_BOT = None

def get_driver():
    return __THE_ONLY_ONE_BOT

def set_driver(*args, **kwargs):
    global __THE_ONLY_ONE_BOT
    __THE_ONLY_ONE_BOT = GuildBot(*args, **kwargs)
    return __THE_ONLY_ONE_BOT
