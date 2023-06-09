import asyncio
from typing import List

import httpx
from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont, truetype

from .emoji import Emoji, getEmojiImg

ICON = {
    '开学季': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/72/2021_kaixueji_org.png',
    '融化': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/53/2022_melt_org.png',
    '哇': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/3d/2022_wow_org.png',
    '苦涩': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/7e/2021_bitter_org.png',
    '开学季': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/72/2021_kaixueji_org.png',
    '单身青蛙': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/6c/2022_SingleFrog_org.png',
    '收到': 'https://face.t.sinajs.cn/t4/appstyle/expression/ext/normal/8b/2022_get_org.png'
}

class Font:
    msyh = 'C:/Windows/Fonts/msyh.ttc'
    homo = 'resource/font/HarmonyOS_Sans_SC_Regular.ttf'

    FontManager = {
        msyh: {16: truetype(msyh, 16)},
        homo: {16: truetype(homo, 16)}
    }

    @classmethod
    def getSizedFont(cls, font, size):
        if isinstance(font, FreeTypeFont):
            return font
        if not cls.FontManager.get(font):
            return None
        sizedFont = cls.FontManager[font].get(size)
        if sizedFont:
            return sizedFont
        else:
            newFont = truetype(font, size)
            cls.FontManager[font][size] = newFont
            return newFont


class TextManager:
    class Text:
        def __init__(self, text: str, color: str = '#FFFFFF', size: int = 16, font: Font = Font.homo) -> None:
            self.text = text
            self.color = color
            self.size = size
            self.font = Font.getSizedFont(font, size)
            self.width, self.height = self.sumSize()

        def __repr__(self) -> str:
            return f'[{self.text}]({self.color},{self.size},{self.font})'

        def __len__(self) -> int:
            return len(self.text)

        def getSize(self, pos: int = -1):
            return self.width[pos], self.height[pos]

        def getMaxPos(self, width: int, start: int = 0):
            start = self.width[start]
            for pos, w in enumerate(self.width):
                if w-start > width:
                    return pos - 1
            else:
                return pos

        def sumSize(self) -> List[int]:
            width, height = [0] * (len(self.text)+1), [0] * (len(self.text)+1)
            for i in range(len(self.text)+1):
                width[i], height[i] = self.font.getsize(self.text[:i])
            return width, height

    async def setContent(self, content) -> 'TextManager':
        self.Content = []
        for c in content:
            if isinstance(c, tuple):
                text, *args = c
                last = 0
                now = 0
                while now < len(text):
                    if text[now] == '\n':
                        if last != now:
                            self.Content.append(self.Text(text[last:now], *args))
                        self.Content.append('#')
                        last = now + 1
                    elif Emoji.get(text[now]):
                        if last != now:
                            self.Content.append(self.Text(text[last:now], *args))
                        self.Content.append(await getEmojiImg(text[now]))
                        last = now + 1
                    elif text[now] == '[':
                        if last != now:
                            self.Content.append(self.Text(text[last:now], *args))
                        last = now + 1
                    elif text[now] == ']':
                        if last != now:
                            if (url := text[last:now]) in ICON:
                                url = ICON[url]
                            if url.startswith('http') and url.endswith('.png'):
                                response = httpx.get(url)  # 请求图片
                                im = Image.open(response).convert('RGBA')  # 读取图片
                                self.Content.append(im)
                            else:
                                self.Content.append(self.Text(text[last-1:now+1], *args))
                        last = now + 1
                    now += 1
                else:
                    if last != now:
                        self.Content.append(self.Text(text[last:now], *args))
            else:
                self.Content.append(c)
        return self

    def print(self):
        for c in self.Content:
            print(c)

    def prePaste(self, limit: int, im: Image.Image):
        x, y, line_height = 0, 0, 3
        draw = ImageDraw.Draw(im)
        for c in self.Content:
            if c == '#':
                x = 0
                y += line_height
                line_height = 3
            elif isinstance(c, Image.Image):
                flag = False
                if c.height in [16, 64, 72]:
                    flag = True
                    if line_height == 3:
                        line_height = 39.6
                    c = c.resize((int(line_height/1.1), int(line_height/1.1)), Image.ANTIALIAS)
                w, h = c.size
                if limit - x < w:
                    x = 0
                    y += line_height
                    line_height = h * (1.1 if flag else 1)
                else:
                    line_height = max(line_height, h * (1.1 if flag else 1))
                im.paste(c, (int(x), int(y-(0.14*line_height if flag else 0))), mask=c.getchannel('A'))
                x += w
            elif isinstance(c, self.Text):
                pos = c.getMaxPos(limit-x)
                w, h = c.getSize(pos)
                if y == 0:
                    y = 0.333 * h
                draw.text((x, y), c.text[:pos], c.color, c.font)
                x += w
                line_height = max(line_height, 1.333 * h)
                while pos != len(c):
                    x = 0
                    y += line_height
                    line_height = 3
                    rpos = c.getMaxPos(limit, pos)

                    draw.text((x, y), c.text[pos:rpos], c.color, c.font)
                    w, h = c.getSize(rpos)
                    x += w - c.getSize(pos)[0]
                    line_height = max(line_height, 1.333 * h)
                    pos = rpos
        if (fy := y + (line_height if x else 0)) > im.height:
            return int(fy)
        return im.crop((0, 0, limit, y + (line_height if x else 0)))

    def paste(self, limit: int):
        im = Image.new('RGBA', (int(limit), 3000), '#00000000')
        res = self.prePaste(limit, im)
        if isinstance(res, int):
            im = Image.new('RGBA', (int(limit), res + 1), '#00000000')
            return self.prePaste(limit, im)
        else:
            return res

async def main():
    im = (await TextManager().setContent([
        ('醒了 明天要去上舞蹈课！今天也还是歇了 晚点可能用手机播一会儿但我最近🧠空空有点不知道说什么☹️', '#0000FF', 45, Font.homo)
    ])).paste(960)

    bg = Image.new('RGB', im.size, '#F5F5F7')
    bg.paste(im, mask=im.getchannel('A'))
    bg.show()


if __name__ == '__main__':
    asyncio.run(main())
