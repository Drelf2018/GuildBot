"""
基于 danmakus.com 的爬虫工具
"""

from typing import List, Optional

from weibo_poster import Request


class ukamnads(Request):
    "基于 api.ukamnads.icu 的弹幕爬虫"

    def __init__(self, base_url: str = "https://api.ukamnads.icu/api/v2"):
        super().__init__()
        self.session.base_url = base_url

    async def get_last_liveid(self, uid: int | str, last: int = 0) -> Optional[str]:
        "获取最近直播序号"

        data: dict = await self.request("GET", "/channel", params={"uId": uid})
        lives: List[dict] = data.get("data", {}).get("lives", [])
        if len(lives) > last:
            return lives[last].get("liveId", None)
        
    async def get_live(self, liveid: str) -> dict:
        "获取直播数据"

        assert liveid is not None, "liveid can't be None"
        return await self.request("GET", "/live", params={"liveId": liveid})

    def get_channel(self, live: dict) -> dict:
        "直播生涯数据"

        return live.get("data", {}).get("data", {}).get("channel", {})

    def get_detail(self, live: dict) -> dict:
        "该场直播数据"

        return live.get("data", {}).get("data", {}).get("live", {})

    def get_danmakus(self, live: dict) -> List[str]:
        "该场直播弹幕文本"

        messages = list()
        danmakus: List[dict] = live.get("data", {}).get("data", {}).get("danmakus", [])
        for dm in danmakus:
            mes: str = dm.get("message", "")
            if mes.strip() != "":
                messages.append(mes)
        return messages

    def get_income(self, live: dict):
        "营收"

        danmakus: List[dict] = live.get("data", {}).get("data", {}).get("danmakus", [])
        gift = guard = superchat = 0.0
        for dm in danmakus:
            if dm["type"] == 1:
                gift += dm["price"]
            elif dm["type"] == 2:
                guard += dm["price"]
            elif dm["type"] == 3:
                superchat += dm["price"]
        gift = int(gift)
        guard = int(guard)
        superchat = int(superchat)
        return gift, guard, superchat, gift + guard + superchat
