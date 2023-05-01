from guildbot import get_driver, logger, Event
from weibo_poster import Request


class Online(Request):
    url = "https://m.weibo.cn/api/container/getIndex?from=page_100808&mod[]=TAB%3Ffrom%3Dpage_100808&mod[]=TAB&containerid=1008081a127e1db26d4483eadf1d1dbe1a80c2_-_live"
    last_online_status = None
    
    async def online(self):
        js = await self.request("GET", self.url)
        for key1 in js["data"]["cards"]:
            for key2 in key1["card_group"]:
                if key2["card_type"] == "30":
                    return key2["desc1"]
    
    async def check(self):
        try:
            msg = await self.online()
        except Exception as e:
            logger.error(f"状态轮询错误：{e}")
            return
        if msg and msg != self.last_online_status:
            self.last_online_status = msg
            if msg == "微博在线了":
                await bot.reply(9638022, "上线了")
            elif msg == "刚刚在线了":
                await bot.reply(9638022, "离线了")
        logger.debug(msg)


nana7mi_online = Online() # 七海Nana7mi 微博上线监控

bot = get_driver()
bot.add_job(nana7mi_online.check, 0, 10)

@bot.on("/online")
async def online(event: Event):
    await event.reply(nana7mi_online.last_online_status)
