import time
from io import BytesIO
from typing import Union

import httpx
from weibo_poster import Post, get_content, parse_text

from guildbot import Event, get_driver, logger

from .d2p import create_new_img

bot = get_driver()

CONTENT = dict()

async def put(post: Post, channel_id: str = "9638022"):
    logger.info(f"用户 {post.name} 微博 {post.mid} 搬运中")
    CONTENT[post.mid] = post.text

    # 文字版
    ts, _ = parse_text(post.text)
    content = get_content(ts)
    msg = f"{post.name}\n粉丝 {post.follower} | 关注 {post.following}\n发送了微博:\n\n{content}\n\n"
    if post.repost:
        rs, _ = parse_text(post.repost.text)
        rcontent = get_content(rs)
        msg += f"回复 @{post.repost.name}:\n{rcontent}\n\n"
    msg += f"{post.date} 来自{post.source}" 

    await bot.reply(channel_id, msg)
    
    # 图片版
    try:
        image = await create_new_img(post)
        bytesio = BytesIO()
        image.save(bytesio, format="png")
        await bot.reply(channel_id, file_image=bytesio.getvalue())
    except Exception as e:
        await bot.reply(channel_id, e)
        logger.error(e)
    

async def generator(channel_id: Union[str, int]):
    tt = int(time.time()) - 86400
    res = httpx.get(f"https://api.nana7mi.link/post?beginTs={tt}")
    data = res.json()
    if data["code"] == 0:
        pdata = data["data"][-1]
        post = Post.parse(pdata)
        await put(post, channel_id=channel_id)


# @bot.job(3, 4.5)
# async def weibo():
#     logger.debug("更新微博")
#     res = httpx.get("https://api.nana7mi.link/post")
#     data = res.json()
#     if data["code"] == 0:
#         for pdata in data["data"]:
#             post = Post.parse(pdata)
#             if CONTENT.get(post.mid, "") != post.text:
#                 await put(post)
                
                
@bot.on("/weibo")
async def send(event: Event):
    await generator(event.raw.channel_id)


@bot.get("/weibo")
def send(channel: Union[str, int]):
    bot.create_task(generator(channel))
