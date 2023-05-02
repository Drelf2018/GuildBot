import httpx
from typing import Tuple
from io import BytesIO
from PIL import Image, ImageDraw
from bilibili_api import user


async def get_face(uid: int = 434334701) -> Image.Image:
    # 爬取装扮及头像
    js = await user.User(uid).get_user_info()
    # 头像
    if face := js.get('face'):
        response = httpx.get(face)  # 请求图片
        face = Image.open(BytesIO(response.read()))  # 读取图片
        w, h = face.size
        a = Image.new('L', face.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色圆形

    # 装扮
    if pendant := js.get('pendant', {}).get('image'):
        response = httpx.get(pendant)  # 请求图片
        pendant = Image.open(BytesIO(response.read()))  # 读取图片
        pendant = pendant.convert('RGBA')

        bg = Image.new('RGBA', (int(1.75*w), int(1.75*h)), (0, 0, 0, 0))
        bg.paste(face, (int(0.375*w), int(0.375*h)), mask=a)  # 粘贴至背景
        pendant = pendant.resize((int(1.75*w), int(1.75*h)), Image.LANCZOS)  # 装扮应当是头像的1.75倍
        try:
            bg.paste(pendant, (0, 0), mask=pendant.getchannel('A'))  # 粘贴至背景
        except Exception:
            pendant = None
    # 粉圈
    if not pendant:
        image = Image.new('RGBA', (int(1.16*w), int(1.16*h)), (0, 0, 0, 0))
        image.paste(face, (int(0.08*w), int(0.08*h)), mask=a)  # 粘贴至背景
        ps = Image.new("RGB", (int(1.16*w), int(1.16*h)), (242, 93, 142))
        a = Image.new('L', ps.size, 0)  # 创建一个黑色背景的画布
        ImageDraw.Draw(a).ellipse((0, 0, a.width, a.height), fill=255)  # 画白色外圆
        ImageDraw.Draw(a).ellipse((int(0.06*w), int(0.06*h), int(1.1*w), int(1.1*h)), fill=0)  # 画黑色内圆
        image.paste(ps, (0, 0), mask=a)  # 粘贴至背景
        w, h = image.size
        bg = Image.new('RGBA', (int(1.25*w), int(1.25*h)), (0, 0, 0, 0))
        bg.paste(image, (int((1.25-1)/2*w), int((1.25-1)/2*h)))

    return bg


if __name__ == "__main__":
    import asyncio
    asyncio.run(get_face(188888131)).show()