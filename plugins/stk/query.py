import os
from copy import deepcopy
from itertools import product
from sys import getsizeof
from typing import Dict, List, Tuple, Union

from yaml import FullLoader, dump, load

from guildbot import logger


class Query:
    def __init__(self, config: Dict[str, Dict[int, List[int]]]):
        self.__rooms = set()
        self.__users = set()
        self.__channels: Dict[str, List[str]] = dict()
        self.__config = deepcopy(config)

        for _, value in config.items():
            rooms = value.pop("roomid")
            self.__rooms.symmetric_difference_update(rooms)

            for channel_id, users in value.items():
                list(map(self.add_event_listener, product(rooms, users, [channel_id])))
                self.__users.symmetric_difference_update(users)

        logger.info(f"channels 占用了 {getsizeof(self.__channels) // 1024} KB 内存")

    def rooms(self, guild_id: int = None):
        if guild_id is None:
            return list(self.__rooms)
        else:
            guild_id = int(guild_id)
            return self.__config.get(guild_id, {}).get("roomid", [])

    def users(self, guild_id: int = None, channel_id: int = None):
        if guild_id is None:
            return list(self.__users)
        else:
            guild_id = int(guild_id)
            channel_id = int(channel_id)
            return self.__config.get(guild_id, {}).get(channel_id, [])

    def add_event_listener(self, data: Tuple[Union[str, int], ...]):
        "注册事件监听器"

        room, uid, channel = data
        name = f"{room}_{uid}"
        if name not in self.__channels:
            self.__channels[name] = []
        self.__channels[name].append(str(channel))

    def broadcast(self, room: Union[str, int], uid: Union[str, int]):
        "查找需要广播的子频道"
        
        return self.__channels.get(f"{room}_{uid}", [])

    def update_config(self, guild_id: int, channel_id: int, rooms: List[int] = None, users: List[int] = None):
        "更新配置"

        assert rooms is not None or users is not None, "不能同时为空！"

        def update(ori: List[int], new: List[int]):
            a, b, c, d = [], [], [], []
            for item in new:
                item = int(item)
                if item > 0:
                    if item not in ori:
                        ori.append(item)
                        a.append(str(item))
                    else:
                        b.append(str(item))
                if item < 0:
                    item *= -1
                    if item in ori:
                        ori.remove(item)
                        c.append(str(item))
                    else:
                        d.append(str(item))
            self.save()
            return a, b, c, d

        guild_id = int(guild_id)
        if guild_id not in self.__config:
            self.__config[guild_id] = {"roomid": []}
        channel_id = int(channel_id)
        if channel_id not in self.__config[guild_id]:
            self.__config[guild_id][channel_id] = []

        config = self.__config[guild_id]
        if rooms is not None:
            roomids = config["roomid"]
            return update(roomids, rooms)
        if users is not None:
            userids = config[channel_id]
            return update(userids, users)

    def save(self):
        "保存配置文件"

        with open(CONFIGPATH, "w", encoding="utf-8") as fp:
            dump(self.__config, fp, allow_unicode=True)


CONFIGPATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "config.yml"
    )
)

with open(CONFIGPATH, "r", encoding="utf-8") as fp:
    config = load(fp, Loader=FullLoader)
QUERY = Query(config)
