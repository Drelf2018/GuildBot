import os
import sys
from asyncio import Task
from importlib import import_module
from typing import BinaryIO, Callable, Coroutine, List, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bilibili_api.utils.AsyncEvent import AsyncEvent
from botpy import Client, Intents, logger
from botpy.types.message import Message
from fastapi import FastAPI

from .event import Event
from .utils import *


class GuildBot(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(intents=Intents(public_guild_messages=True), bot_log=True, *args, **kwargs)
        self.__app = FastAPI(openapi_url=None)
        self.__tasks = set()  # 异步任务集
        self.__scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")  # 定时任务框架
        self.__event_manager = AsyncEvent()

    def get(self, path: str, *args, **kwargs):
        """
        FastAPI GET 请求装饰器
        """
        return self.__app.get(path, *args, **kwargs)
    
    def post(self, path: str, *args, **kwargs):
        """
        FastAPI POST 请求装饰器
        """
        return self.__app.post(path, *args, **kwargs)

    def on(self, event_name: str):
        """
        事件监听绑定
        """
        return self.__event_manager.on(event_name)

    def add_job(self, fn: Callable, start: float = 0, interval: float = 5.0, name: str = None, args: list = None, kwargs: dict = None):
        """
        新增定时任务
        
        Args:
            fn:       任务函数
            start:    起始时间秒数
            interval: 执行间隔秒数
            name:     任务名
            args:     任务参数
            kwargs:   任务具名参数
        
        Returns:
            原函数
        """
        self.__scheduler.add_job(fn, "interval", next_run_time=delay(start), seconds=interval, name=name, args=args, kwargs=kwargs)
        return fn

    def job(self, start: float = 0, interval: float = 5.0, name: str = None, args: list = None, kwargs: dict = None):
        """
        定时任务装饰器

        Args:
            start:    起始时间秒数
            interval: 执行间隔秒数
            name:     任务名
            args:     任务参数
            kwargs:   任务具名参数
        
        Returns:
            原函数
        """
        def inner(fn):
            return self.add_job(fn, start=start, interval=interval, name=name, args=args, kwargs=kwargs)
        return inner

    async def on_at_message_create(self, message: Message):
        """
        实现机器人接收at消息
        """
        event = Event(bot=self, raw=message)
        self.__event_manager.dispatch(event.cmd, event)

    async def reply(self, channel_id: str, content: str = None, file_image: Union[bytes, BinaryIO, str] = None, msg_id: str = "10000", *args, **kwargs):
        """
        回复消息

        Args:
            channel_id: 子频道号
            content:    文字内容
            file_image: 图片内容
            msg_id:     回复消息号
        """
        if content is not None:
            content = str(content)
        return await self.api.post_message(
            channel_id=channel_id,
            content=content,
            file_image=file_image,
            msg_id=msg_id,
            *args,
            **kwargs,
        )
    
    def load_plugins(self, folder: str, exclude: List[str] = None):
        """
        加载插件
        """
        if exclude is None:
            exclude = []

        def load(name: str):
            if name in exclude:
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
        """
        创建强引用异步任务
        """
        def inner(task: Task):
            """
            参考 https://zhuanlan.zhihu.com/p/602955920
            """
            self.__tasks.remove(task)
            if callback is not None:
                result = task.result()
                callback(result)

        task = self.loop.create_task(coro)
        task.add_done_callback(inner)
        self.__tasks.add(task)
        return task

    def run(self, appid: str, secret: str, ret_coro: bool = False, host: str = "0.0.0.0", port: int = 5760) -> None:
        """
        机器人服务开始执行

        注意：这个函数必须是最后一个调用的函数，因为它是阻塞的。这意味着事件的注册或在此函数调用之后调用的任何内容在它返回之前不会执行。
        """
        if len(self.__scheduler.get_jobs()) != 0:
            self.__scheduler._eventloop = self.loop
            self.__scheduler.start()

        if len(self.__app.routes) != 0:
            config = uvicorn.Config(
                self.__app,
                host=host,
                port=port,
                log_level="info"
            )
            server = UvicornServer(config=config)
            with server.run_in_thread():
                super().run(appid, secret, ret_coro)
        else:
            super().run(appid, secret, ret_coro)
