import os
import sys
from asyncio import Task
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, BinaryIO, Callable, Coroutine, List, Optional, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bilibili_api.utils.AsyncEvent import AsyncEvent
from botpy import Client, Intents, logger
from botpy.types.message import Message
from fastapi import FastAPI

from .util import *


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
        "回复消息"
        
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
    __app = FastAPI()
    __tasks = set()  # 异步任务集
    __jobs = dict()  # 定时任务集
    __scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")  # 定时任务框架
    __event_manager = AsyncEvent()

    def get(self, path: str, *args, **kwarge):
        "接收 web GET 请求"

        return self.__app.get(path, *args, **kwarge)
    
    def post(self, path: str, *args, **kwarge):
        "接收 web POST 请求"

        return self.__app.post(path, *args, **kwarge)

    def on(self, event_name: str):
        "绑定事件监听"

        return self.__event_manager.on(event_name)

    @staticmethod
    def delay(seconds: float):
        "以当前时间为基准延后"

        return datetime.now() + timedelta(seconds=seconds)

    def add_job(self, fn: Callable, start: int = 0, interval: float = 5.0, name: str = None,  args: list = None, kwargs: dict = None):
        "新增任务"

        job = self.__scheduler.add_job(fn, "interval", next_run_time=self.delay(start), seconds=interval, name=name, args=args, kwargs=kwargs)
        if name is not None:
            self.__jobs[name] = job.id
        return fn

    def job(self, start: int = 0, interval: float = 5.0, name: str = None, args: list = None, kwargs: dict = None):
        "轮询装饰器"

        def inner(fn):
            return self.add_job(fn, start=start, interval=interval, name=name, args=args, kwargs=kwargs)
        return inner

    def cancel(self, name: str):
        "取消定时任务"

        job_id = self.__jobs.get(name, None)
        if job_id is not None:
            self.__scheduler.remove_job(job_id)

    async def on_at_message_create(self, message: Message):
        "派发消息"

        event = Event(bot=self, raw=message)
        self.__event_manager.dispatch(event.cmd, event)

    async def reply(self, channel_id: str, content: str = None, file_image: Union[bytes, BinaryIO, str] = None, msg_id: str = "10000"):
        "回复消息"
        
        return await self.api.post_message(
            channel_id=channel_id,
            content=str(content) if content is not None else None,
            file_image=file_image,
            msg_id=msg_id
        )
    
    def load_plugins(self, folder: str, exclude: List[str] = None):
        "加载插件"

        def load(name: str):
            if exclude is not None and name in exclude:
                return
            try:
                import_module(name)
                logger.info(f"{name} 加载成功")
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
    
    def create_task(self, coro: Coroutine, callback: Callable = None):
        "创建异步任务"

        # 参考 https://zhuanlan.zhihu.com/p/602955920
        def inner(task: Task):
            self.__tasks.remove(task)
            if callback is not None:
                result = task.result()
                callback(result)

        task = self.loop.create_task(coro)
        task.add_done_callback(inner)
        self.__tasks.add(task)
        return task

    def run(self, *args: Any, **kwargs: Any) -> None:
        """
        机器人服务开始执行

        注意:
          这个函数必须是最后一个调用的函数，因为它是阻塞的。这意味着事件的注册或在此函数调用之后调用的任何内容在它返回之前不会执行。
          如果想获取协程对象，可以使用`start`方法执行服务, 如:
        ```
        async with Client as c:
            c.start()
        ```
        """

        self.__scheduler._eventloop = self.loop
        self.__scheduler.start()

        config = uvicorn.Config(
            self.__app,
            host=kwargs.get("host", "0.0.0.0"),
            port=kwargs.get("port", 5760),
            log_level="info"
        )
        server = UvicornServer(config=config)

        with server.run_in_thread():
            super().run(*args, **kwargs)
