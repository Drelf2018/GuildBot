import os
import time
from io import BytesIO
from random import choice
from typing import Union

from PIL import Image

try:
    from .danmakus import ukamnads
    from .util import get_face
except:
    from danmakus import ukamnads
    from util import get_face

from vue2img import createApp, getCuttedBody, word2cloud


async def make_image(uid: Union[int, str], last: int = 0, export = None):
    export = BytesIO() if export is None else export

    uk = ukamnads()
    liveid = await uk.get_last_liveid(uid, last)
    live = await uk.get_live(liveid)

    dms = uk.get_danmakus(live)
    channel = uk.get_channel(live)
    detail = uk.get_detail(live)

    gift, guard, superchat, total_income = uk.get_income(live)

    line_width = 850
    income = Image.new('RGBA', (line_width, 50), (132, 212, 155) if guard != 0.0 else 'grey')
    if total_income:
        income.paste((255, 168, 180), (0, 0, int(line_width * gift / total_income), 50))
        income.paste((74, 194, 246), (int(line_width * (total_income - superchat) / total_income), 0, line_width, 50))

    bg = Image.new("L", (850, 300), "black")
    wc = word2cloud("/".join(dms), bg, "resource/font/HarmonyOS_Sans_SC_Regular.ttf")

    path = f"resource/Tachie/{uid}"
    nanami = None
    face = None
    for _, _, files in os.walk(path):
        nanami = getCuttedBody(Image.open(os.path.join(path, choice(files))))
        break
    else:
        face = await get_face(uid)

    t2s = lambda tt: time.strftime('%m/%d %H:%M', time.localtime(tt // 1000))

    if detail["stopDate"] == 0:
        time_str = " (在播)"
        detail["stopDate"] = 1000 * int(time.time())
    else:
        time_str = ""

    time_str = t2s(detail["startDate"]) + " - " + t2s(detail["stopDate"]) + time_str
    
    detail.update({
        "uName": channel["uName"],
        "time": time_str,
        
        "density": str(detail["danmakusCount"] * 60000 // (detail["stopDate"] - detail["startDate"])) + " / min",
        "gift": gift,
        "guard": guard,
        "superchat": superchat,
        "income": total_income,
        
        "dm": wc,
        "incomeLine": income,
        "nanami": nanami,
        "face": face
    })

    canvas = createApp(1000).mount(path="resource/Live.vue", data=detail).export().canvas
    
    if face is not None:
        w, h = canvas.size
        canvas = canvas.crop((0, 48, w, h))

    canvas.save(export, format="png")
    return export


if __name__ == "__main__":
    import asyncio
    asyncio.run(make_image(434334701, export="test.png"))
