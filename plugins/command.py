from guildbot import Event, get_driver, logger
from plugins.live2img import make_image

bot = get_driver()

@bot.on("/help")
async def help(event: Event):
    await event.reply(content=open("resource/notice.txt", "r+", encoding="utf-8").read())


@bot.on("/live")
async def live(event: Event):
    uid = await event.get_uid()
    if uid is None:
        await event.reply(content="未找到该用户")
        return
    try:
        last = 0
        if event.length > 1 and event[1].isdigit():
            last = int(event[1])
        bytesio = await make_image(uid, last)
        await event.reply(file_image=bytesio.getvalue())
    except Exception as e:
        logger.error(f"{e} ({e.__traceback__.tb_lineno})")
        await event.reply(content=f"生成场报时错误")
