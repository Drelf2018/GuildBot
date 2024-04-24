import contextlib
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from bilibili_api import search, user
from botpy.types.gateway import UserPayload
from botpy.types.message import Message
from botpy.types.user import Member


def delay(seconds: float) -> datetime:
    """
    返回延迟时间点

    Args:
        seconds: 需要延后的秒数
    
    Returns:
        datetime.datetime 对象
    """
    return datetime.now() + timedelta(seconds=seconds)


class UvicornServer(uvicorn.Server):
    """
    不阻塞启动 fastapi
    
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


async def search_bili_userid(keyword: str, default: Optional[str] = None) -> Optional[str]:
    """
    根据关键词返回用户b站uid
    
    Args:
        keyword: 关键词
        default: 缺省 uid

    Returns:
        Optional[str] uid
    """
    res = await search.search_by_type(
        keyword,
        search_type=search.SearchObjectType.USER,
        order_type=search.OrderUser.FANS,
        order_sort=0
    )
    users: List[dict] = res.get("result", [])
    if len(users) == 0:
        return default
    return str(users[0].get("mid", default))


async def get_bili_roomid(uid: int) -> Optional[str]:
    """
    获取直播间号
    """
    data = await user.User(uid).get_user_info()
    roomid = data.get("live_room", {}).get("roomid", None)
    if roomid is None:
        return None
    return str(roomid)


def remove_mentions(message: Message) -> str:
    """
    移除消息中的@信息
    """
    raw: str = message.content
    mentions: List[UserPayload] = message.mentions
    for mention in mentions:
        raw = raw.replace(f"<@!{mention.id}>", "")
    return raw.strip()


def get_permission_level(message: Message) -> int:
    """
    获取权限等级
    """
    level = 0
    member: Member = message.member
    roles: List[str] = member.roles
    for i, role in enumerate(["5", "2", "4"]):
        level += 2**i if role in roles else 0
    return level