import time

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from MatrixMusic import app
from MatrixMusic.misc import _boot_
from MatrixMusic.utils.database import add_served_chat, add_served_user
from MatrixMusic.utils.decorators.language import LanguageStart
from MatrixMusic.utils.formatters import get_readable_time
from MatrixMusic.utils.inline import start_panel
from config import BANNED_USERS
from strings import get_string


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    await message.reply_photo(
        photo='MatrixMusic/plugins/bot/matrix.png',
        caption=_["start_1"].format(app.mention),
        reply_markup=InlineKeyboardMarkup(start_panel(_)),
        reply_to_message_id=message.id
    )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    await message.reply_photo(
        photo='MatrixMusic/plugins/bot/matrix.png',
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out),
        reply_to_message_id=message.id
    )
    await add_served_chat(message.chat.id)
