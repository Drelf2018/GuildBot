from guildbot import Event, get_driver

bot = get_driver()

@bot.on("/help")
async def help(event: Event):
    await event.reply(content=open("resource/notice.txt", "r+", encoding="utf-8").read())
