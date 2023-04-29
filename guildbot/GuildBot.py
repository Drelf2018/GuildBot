import os
import sys
from dataclasses import dataclass, field
from importlib import import_module
from typing import BinaryIO, List, Optional, Union, Coroutine

from bilibili_api.utils.AsyncEvent import AsyncEvent
from botpy import Client, Intents, logger
from botpy.types.message import Message

from .util import remove_mentions, search_bili_userid, get_permission_level, get_bili_roomid


@dataclass
class Event:
    bot: "GuildBot"
    raw: Message
    cmd: str = "/help"
    args: List[str] = field(default_factory=list)
    length: int = 0
    
    def __post_init__(self):
        "分析指令"

        content = remove_mentions(self.raw)
        if content != "":
            self.args = content.split()
            self.cmd = self.args.pop(0)
            self.length = len(self.args)

    def __getitem__(self, index: int):
        return self.args[index]

    @property
    def isAdmin(self) -> bool:
        "是否有管理权限"

        return get_permission_level(self.raw) > 0

    async def reply(self, content: str = None, file_image: Union[bytes, BinaryIO, str] = None, channel_id: str = None, msg_id: str = None):
        return await self.bot.reply(
            channel_id=channel_id if channel_id else self.raw.channel_id,
            content=content,
            file_image=file_image,
            msg_id=msg_id if msg_id else self.raw.id
        )

    async def get_uid(self, position: int = 0, default: Union[int, str] = "434334701") -> Optional[str]:
        "根据参数解析b站uid"

        uid = default
        if self.length > position:
            try:
                uid = int(self[position])
            except:
                try:
                    uid = await search_bili_userid(self[position])
                except:
                    return None
        return str(uid)

    async def get_roomid(self, position: int = 0, default: Union[int, str] = "21452505") -> Optional[str]:
        "根据参数解析b站直播间号"

        roomid = default
        if self.length > position:
            try:
                roomid = int(self[position])
            except:
                try:
                    uid = await search_bili_userid(self[position])
                    if uid is not None:
                        return await get_bili_roomid(uid)
                    return None
                except:
                    return None
        return str(roomid)


class GuildBot(Client):
    __tasks = set()  # 异步任务集
    __event_manager = AsyncEvent()

    def on(self, event_name: str):
        return self.__event_manager.on(event_name)

    async def on_at_message_create(self, message: Message):
        event = Event(bot=self, raw=message)
        self.__event_manager.dispatch(event.cmd, event)

    async def reply(self, channel_id: str, content: str = None, file_image: Union[bytes, BinaryIO, str] = None, msg_id: str = "10000"):
        return await self.api.post_message(
            channel_id=channel_id,
            content=content,
            file_image=file_image,
            msg_id=msg_id
        )
    
    def load_plugins(self, folder: str):
        "加载插件"

        def load(name: str):
            try:
                import_module(name)
            except Exception as e:
                logger.error(f"{name} 加载错误：{e}")

        sys.path.append(folder)
        for _, dirs, files in os.walk(folder):
            for file in files:
                if not file.startswith("_") and file.endswith(".py"):
                    load(file.replace(".py", ""))
            for dir in dirs:
                if not dir.startswith("_"):
                    load(dir)
            break
        return self
    
    def create_task(self, coro: Coroutine):
        "创建异步任务"

        # 参考 https://zhuanlan.zhihu.com/p/602955920

        task = self.loop.create_task(coro)
        self.__tasks.add(task)
        task.add_done_callback(lambda t: self.__tasks.remove(t))
