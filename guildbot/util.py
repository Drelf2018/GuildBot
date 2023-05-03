import contextlib
import threading
import time
from typing import List, Optional

import uvicorn
from bilibili_api import search, user
from botpy.types.message import Message
from botpy.types.user import Member


class UvicornServer(uvicorn.Server):
    """不阻塞启动 fastapi
    
    参考：https://www.cnblogs.com/selfcs/p/17240902.html
    """

    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()


async def search_bili_userid(keyword: str):
    "根据关键词返回用户b站uid"

    res = await search.search_by_type(
        keyword,
        search_type=search.SearchObjectType.USER,
        order_type=search.OrderUser.FANS,
        order_sort=0
    )
    users: List[dict] = res.get("result", [])
    if len(users) > 0:
        return str(users[0].get("mid", 434334701))
    return None


async def get_bili_roomid(uid: int) -> Optional[str]:
    "获取直播间号"

    data = await user.User(uid).get_user_info()
    roomid = data.get("live_room", {}).get("roomid", None)
    return str(roomid) if roomid is not None else None


def remove_mentions(message: Message) -> str:
    "移除消息中的@信息"

    raw: str = message.content
    for mention in message.mentions:
        raw = raw.replace(f"<@!{mention.id}>", "")
    return raw.strip()


def get_permission_level(message: Message) -> int:
    "获取权限等级"

    level = 0
    member: Member = message.member
    roles: List[str] = member.roles
    for i, role in enumerate(["5", "2", "4"]):
        level += 2**i if role in roles else 0
    return level