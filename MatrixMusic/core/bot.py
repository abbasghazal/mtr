from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus, ParseMode
import config
from ..logging import LOGGER

class Zelzaly(Client):
    def __init__(self):
        LOGGER("ميــوزك بحر").info(f"جارِ بدء تشغيل البوت . . .")
        super().__init__(
            name="YousefMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
        )
    
    async def start(self):
        await super().start()
        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention
        
        LOGGER("ميــوزك بحر").info(f" تم بدء تشغيل البوت {self.name} ...✓")
    
    async def stop(self):
        await super().stop()