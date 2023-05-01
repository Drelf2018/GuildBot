import asyncio
import time
from io import BytesIO
from typing import BinaryIO, Union, List

import httpx
from aiowebsocket.converses import AioWebSocket
from weibo_poster import BiliGo as plainBot
from weibo_poster.biligo import DanmakuPost, Receive, RoomInfo

from guildbot import get_driver, logger, ipcRenderer
from plugins.live2img import make_image

from .query import QUERY


async def download(url: str):
    "下载图片"

    res = httpx.get(url)
    data = BytesIO(res.content)
    return data.getvalue()


class BiliGo(plainBot):
    async def run(self):
        """
        阻塞异步连接
        """

        @ipcRenderer.on("room")
        async def update(rooms: List[int]):
            self.update(rooms)

        async with AioWebSocket(self.url + f"/ws?id={self.aid}") as aws:
            logger.info("Adapter 连接成功")
            async for evt in Receive(aws.manipulator.receive):
                cmd = evt["command"]
                roomInfo = RoomInfo(**evt["live_info"])
                if cmd == "DANMU_MSG":
                    self.dispatch(cmd, roomInfo, DanmakuPost.parse(evt))
                elif cmd in ["LIVE", "PREPARING"]:
                    self.dispatch(cmd, roomInfo)
                elif cmd in ["SEND_GIFT", "USER_TOAST_MSG", "SUPER_CHAT_MESSAGE", "INTERACT_WORD"]:
                    self.dispatch(cmd, roomInfo, evt["content"]["data"])


SUPER_CHAT = []  # SC的唯一id避免重复记录
ROOM_STATUS = {}  # 直播间开播状态
bot = get_driver()
bili = BiliGo("guild", "http://localhost:8080", *QUERY.rooms())


def userFilter(_: RoomInfo, danmaku: Union[DanmakuPost, dict]):
    "用户过滤"

    if isinstance(danmaku, DanmakuPost):
        return int(danmaku.uid) in QUERY.users()
    else:
        return int(danmaku.get("uid")) in QUERY.users()


async def send(room: Union[str, int], uid: Union[str, int], content: str = None, file_image: Union[bytes, BinaryIO, str] = None):
    for channel_id in QUERY.broadcast(room, uid):
        asyncio.create_task(bot.reply(channel_id=channel_id, content=content, file_image=file_image))


@bili.on("LIVE")
async def live(roomInfo: RoomInfo):
    "开播"

    tt = int(time.time())
    roomid = roomInfo.room_id
    if tt - ROOM_STATUS.get(roomid, 0) > 10800:
        ROOM_STATUS[roomid] = tt
        file_image = await download(roomInfo.cover)
        await send(roomid, roomInfo.uid, "{name}开播了！\n{title}".format_map(roomInfo.__dict__), file_image)


@bili.on("INTERACT_WORD", userFilter)
async def interact(roomInfo: RoomInfo, data: dict):
    "进入直播间"

    await send(roomInfo.room_id, int(data["uid"]), f"{data['uname']} 进入了 {roomInfo.name} 的直播间")


@bili.on("DANMU_MSG", userFilter)
async def danmu(roomInfo: RoomInfo, danmaku: DanmakuPost):
    "接受到弹幕"

    msg = f'{danmaku.name} 在 {roomInfo.name} 的直播间说：{danmaku.text}'

    file_image = None
    if len(danmaku.picUrls) > 0:
        image = danmaku.picUrls[0]
        file_image = await download(image)

    await send(roomInfo.room_id, danmaku.uid, msg, file_image=file_image)


@bili.on("SEND_GIFT", userFilter)
async def gift(roomInfo: RoomInfo, data: dict):
    "接受到礼物"

    msg = f"{data['uname']} 在 {roomInfo.name} 的直播间" + "{action} {giftName}".format_map(data) + f'￥{data["price"]/1000}'
    await send(roomInfo.room_id, data["uid"], msg)


@bili.on("USER_TOAST_MSG", userFilter)
async def guard(roomInfo: RoomInfo, data: dict):
    "接受到大航海"

    msg = f'{data["username"]} 在 {roomInfo.name} 的直播间赠送 {data["role_name"]}￥{data["price"]//1000}'
    await send(roomInfo.room_id, data["uid"], msg)


@bili.on("SUPER_CHAT_MESSAGE", userFilter)
async def super(roomInfo: RoomInfo, data: dict):
    "接受到醒目留言"

    super_id = int(data.get("id", 0))
    if super_id not in SUPER_CHAT:
        SUPER_CHAT.append(super_id)
        u1 = data['user_info']['uname']
        msg = f"{u1} 在 {roomInfo.name} 的直播间发送" + " ￥{price} SuperChat 说：{message}".format_map(data)
        await send(roomInfo.room_id, data["uid"], msg)


@bili.on("PREPARING")
async def preparing(roomInfo: RoomInfo):
    "下播"

    roomid = roomInfo.room_id
    uid = roomInfo.uid

    try:
        bytesio = await make_image(uid)
        await send(roomid, uid, file_image=bytesio.getvalue())
    except Exception as e:
        logger.error(f"{e} ({e.__traceback__.tb_lineno})")
        await send(roomid, uid, content=f"生成 {roomInfo.name} 场报时错误")
