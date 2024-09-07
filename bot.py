from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted
import config
import os
import asyncio
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='bot_log.txt',
                    filemode='a')
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

@app.on_message(filters.chat(config.CHANNEL_ID))
async def create_chat(client, message):
    logger.info(f"Received new message in channel {config.CHANNEL_ID}")
    try:
        lines = message.text.split("\n")
        if len(lines) != 6:
            error_message = "Команда должна содержать 6 строк: title, type, avatar, members, admins, sender"
            logger.error(f"Invalid command format: {error_message}")
            report = f"false\n{lines[-1]}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_title, chat_type, chat_avatar_name, members, admins, sender = lines
        members = [int(m.strip()) for m in members.split(',') if m.strip()]
        admins = [int(a.strip()) for a in admins.split(',') if a.strip()]
        
        logger.info(f"Processing command: Create {chat_type} '{chat_title}' with {len(members)} members and {len(admins)} admins")

        await asyncio.sleep(3)

        # Создание чата
        if chat_type == "supergroup":
            chat = await client.create_supergroup(chat_title)
        elif chat_type == "channel":
            chat = await client.create_channel(chat_title)
        else:
            error_message = "Wrong chat type, use supergroup or channel"
            logger.error(f"Invalid chat type: {error_message}")
            report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_id = chat.id
        logger.info(f"Successfully created {chat_type} with ID: {chat_id}")

        # ... (остальной код остается без изменений)

    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        logger.error(f"Unhandled exception: {error_message}")
        report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\n{error_message}"
        await client.send_message(config.CHANNEL_ID, report)
        await client.send_message(config.OWNER_ID, error_message)

async def check_channel():
    while True:
        try:
            chat = await app.get_chat(config.CHANNEL_ID)
            logger.info(f"Successfully checked channel {config.CHANNEL_ID}")
            async for message in app.get_chat_history(config.CHANNEL_ID, limit=1):
                logger.info(f"Last message in channel: {message.text[:50]}...")
        except Exception as e:
            logger.error(f"Failed to check channel: {str(e)}")
        await asyncio.sleep(300)  # Проверка каждые 5 минут

async def main():
    try:
        await app.start()
        logger.info("Bot started successfully")
        me = await app.get_me()
        logger.info(f"Bot info: id={me.id}, name={me.first_name}, username={me.username}")
        
        asyncio.create_task(check_channel())
        
        await app.idle()
    except Exception as e:
        logger.critical(f"Failed to start bot: {str(e)}")
    finally:
        await app.stop()
        logger.info("Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())