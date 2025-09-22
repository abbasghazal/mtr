# MatRix
import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from MatrixMusic import LOGGER, app, userbot
from MatrixMusic.core.call import Zelzaly
from MatrixMusic.misc import sudo
from MatrixMusic.plugins import ALL_MODULES
from MatrixMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("MatrixMusic.plugins" + all_module.replace("\\", "."))
    LOGGER("MatrixMusic.plugins").info("Successfully Imported Modules...")
    await userbot.start()
    await Zelzaly.start()
    try:
        await Zelzaly.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("MatrixMusic").error(
            "Please turn on the videochat of your log group\channel.\n\nStopping Bot..."
        )
        exit()
    except:
        pass
    await Zelzaly.decorators()
    LOGGER("MatrixMusic").info("تم تنصيب سورس ماتركـس ينجاح اذهب الى بوتك واستمتع باستخدام الاوامر")
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("MatrixMusic").info("Stopping Matrix Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())