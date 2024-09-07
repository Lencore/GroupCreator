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

        await asyncio.sleep(3)

        # Подгрузка и установка аватарки
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.png")
        if os.path.isfile(avatar_path):
            try:
                await client.set_chat_photo(chat_id=chat_id, photo=avatar_path)
                logger.info(f"Successfully set chat photo for {chat_id}")
            except Exception as e:
                error_message = f"Failed to set chat photo: {str(e)}"
                logger.error(error_message)
                report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {error_message}"
                await client.send_message(config.CHANNEL_ID, report)
                return
        else:
            error_message = f"Avatar file {chat_avatar_name}.png not found"
            logger.error(error_message)
            report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        await asyncio.sleep(3)

        # Настройка прав
        if chat_type == "supergroup":
            await client.set_chat_permissions(chat_id, ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=False
            ))
            logger.info(f"Set chat permissions for supergroup {chat_id}")

        await asyncio.sleep(3)

        # Запрет на копирование контента
        try:
            await client.set_chat_protected_content(chat_id, enabled=True)
            logger.info(f"Enabled protected content for {chat_id}")
        except Exception as e:
            logger.error(f"Failed to set protected content: {str(e)}")

        # Добавление участников
        members_added = True
        for user_id in members:
            await asyncio.sleep(3)
            try:
                await client.add_chat_members(chat_id, user_id)
                logger.info(f"Added user {user_id} to chat {chat_id}")
            except (FloodWait, PeerFlood, UserPrivacyRestricted) as e:
                logger.error(f"Failed to add user {user_id}: {str(e)}")
                members_added = False
            except Exception as e:
                logger.error(f"Unexpected error adding user {user_id}: {str(e)}")
                members_added = False

        # Назначение админов
        admins_promoted = True
        for admin_id in admins:
            if admin_id not in members:
                logger.warning(f"Admin {admin_id} not in members list, skipping")
                admins_promoted = False
                continue
            
            await asyncio.sleep(3)
            try:
                await client.promote_chat_member(chat_id, admin_id, ChatPrivileges(
                    can_manage_chat=True,
                    can_post_messages=True,
                    can_edit_messages=True,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_restrict_members=True,
                    can_pin_messages=True,
                    can_promote_members=True
                ))
                logger.info(f"Promoted user {admin_id} to admin in chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to promote admin {admin_id}: {str(e)}")
                admins_promoted = False

        await asyncio.sleep(3)

        # Получение ссылки приглашения
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
            logger.info(f"Generated invite link for chat {chat_id}")
        except Exception as e:
            invite_link = "false"
            error_message = f"Failed to get invite link: {str(e)}"
            logger.error(error_message)
            await client.send_message(config.OWNER_ID, error_message)

        # Отправка отчета
        report = f"true\n{sender}\n{chat_id}\n{invite_link}\n{str(members_added).lower()}\n{str(admins_promoted).lower()}"
        await client.send_message(config.CHANNEL_ID, report)
        logger.info(f"Sent report for chat {chat_id}")

    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        logger.error(f"Unhandled exception: {error_message}")
        report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\n{error_message}"
        await client.send_message(config.CHANNEL_ID, report)
        await client.send_message(config.OWNER_ID, error_message)

@app.on_start()
async def on_start():
    logger.info("Bot started successfully")
    try:
        me = await app.get_me()
        logger.info(f"Bot info: id={me.id}, name={me.first_name}, username={me.username}")
    except Exception as e:
        logger.error(f"Failed to get bot info: {str(e)}")

@app.on_stop()
async def on_stop():
    logger.info("Bot stopped")

async def check_channel():
    while True:
        try:
            chat = await app.get_chat(config.CHANNEL_ID)
            logger.info(f"Successfully checked channel {config.CHANNEL_ID}")
            last_message = await app.get_history(config.CHANNEL_ID, limit=1)
            if last_message:
                logger.info(f"Last message in channel: {last_message[0].text[:50]}...")
            else:
                logger.warning("No messages found in channel")
        except Exception as e:
            logger.error(f"Failed to check channel: {str(e)}")
        await asyncio.sleep(300)  # Проверка каждые 5 минут

if __name__ == "__main__":
    try:
        app.start()
        logger.info("Bot started")
        asyncio.get_event_loop().create_task(check_channel())
        app.run()
    except Exception as e:
        logger.critical(f"Failed to start bot: {str(e)}")