from typing import List

from guildbot import Event, get_driver

from .query import QUERY
from .ws import bili

bot = get_driver()
bot.create_task(bili.run())

def parse_text(data: List[int]):
    if len(data) > 3:
        return ", ".join(data[:3]) + ", ..."
    else:
        return ", ".join(data)


@bot.on("/room")
async def modifyRoom(event: Event):
    guild_id = event.raw.guild_id
    channel_id = event.raw.channel_id
    rooms = QUERY.rooms(guild_id)

    if event.length == 0:
        if len(rooms) == 0:
            await event.reply("未在本频道监控直播间")
        else:
            await event.reply("本频道监控的直播间有：" + ", ".join([str(room) for room in rooms]))
        return

    params = []
    e = []
    for i in range(event.length):
        p = await event.get_roomid(i)
        if p is None:
            e.append(event[i])
        else:
            params.append(p)

    a, b, c, d = QUERY.update_config(guild_id, channel_id, rooms=params)
    msg = list()
    if len(a):
        msg.append("新增监控直播间：" + parse_text(a))
    if len(b):
        msg.append("已经监控直播间：" + parse_text(b))
    if len(c):
        msg.append("移除监控直播间：" + parse_text(c))
    if len(d):
        msg.append("未监控直播间：" + parse_text(d))
    if len(e):
        msg.append("未找到直播间：" + parse_text(e))

    await event.reply("\n".join(msg))


@bot.on("/user")
async def modifyUser(event: Event):
    guild_id = event.raw.guild_id
    channel_id = event.raw.channel_id
    users = QUERY.users(guild_id, channel_id)

    if event.length == 0:
        if len(users) == 0:
            await event.reply("未在本频道监控用户")
        else:
            await event.reply("本频道监控的用户有：" + ", ".join([str(user) for user in users]))
        return

    params = []
    e = []
    for i in range(event.length):
        p = await event.get_uid(i)
        if p is None:
            e.append(event[i])
        else:
            params.append(p)

    a, b, c, d = QUERY.update_config(guild_id, channel_id, users=params)
    msg = list()
    if len(a):
        msg.append("新增监控用户：" + parse_text(a))
    if len(b):
        msg.append("已经监控用户：" + parse_text(b))
    if len(c):
        msg.append("移除监控用户：" + parse_text(c))
    if len(d):
        msg.append("未监控用户：" + parse_text(d))
    if len(e):
        msg.append("未找到用户：" + parse_text(e))

    await event.reply("\n".join(msg))
