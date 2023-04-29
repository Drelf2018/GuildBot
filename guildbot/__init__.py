from .GuildBot import Event, GuildBot, Intents, logger
from .util import get_permission_level, remove_mentions, search_bili_userid

__THE_ONLY_ONE_BOT = GuildBot(intents=Intents(public_guild_messages=True), bot_log=None)

def get_driver():
    return __THE_ONLY_ONE_BOT