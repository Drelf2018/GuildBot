from typing import TYPE_CHECKING, BinaryIO, Union

from botpy.types.message import Message

from .utils import *

if TYPE_CHECKING:
    from .guildbot import GuildBot


class Event:
    def __init__(self, bot: "GuildBot", raw: Message):
        """
        分析指令
        """
        self.bot = bot
        self.raw = raw

        content = remove_mentions(self.raw)
        self.args = content.split()
        self.cmd = self.args.pop(0)

    @property
    def length(self):
        return len(self.args)

    def __getitem__(self, index: int):
        """
        返回指定位置参数
        """
        return self.args[index]

    @property
    def is_admin(self) -> bool:
        """
        发送者是否有管理权限
        """
        return get_permission_level(self.raw) > 0

    async def reply(self, content: str = None, file_image: Union[bytes, BinaryIO, str] = None, channel_id: str = None, msg_id: str = None, *args: list, **kwargs: dict):
        """
        快速回复消息

        Args:
            channel_id: 子频道号
            content:    文字内容
            file_image: 图片内容
            msg_id:     回复消息号
        """
        if channel_id is None:
            channel_id = self.raw.channel_id
        if msg_id is None:
            msg_id = self.raw.id
        return await self.bot.reply(
            channel_id=channel_id,
            content=content,
            file_image=file_image,
            msg_id=msg_id,
            *args,
            **kwargs,
        )
