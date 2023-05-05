import asyncio
from typing import Callable, List

from botpy import logger


class Promise:
    "链式异步任务"

    def __init__(self, judge: Callable, max_times: int = 1, interval: float = 5.0, reject: Callable = None):
        self.__judge = judge
        self.__times = max_times
        self.__interval = interval
        self.__then: List[Callable] = list()
        self.__reject = reject
        self.__catch = logger.error

    def then(self, fn: Callable):
        "链式任务"

        self.__then.append(fn)
        return self
    
    def catch(self, fn: Callable):
        "错误回调"

        self.__catch = fn
        return self

    async def __call__(self, *args):
        return await self.run(*args)

    async def run(self, *args):
        try:
            for _ in range(self.__times):
                if await self.__judge():
                    break
                await asyncio.sleep(self.__interval)
            else:
                if self.__reject is not None:
                    await self.__reject()
                return
            for then in self.__then:
                args = await then(*args)
            return args
        except Exception as e:
            self.__catch(e)
