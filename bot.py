from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted
import pyrogram.raw.types
import pyrogram.raw.functions
import config
import os
import asyncio
import logging
from datetime import datetime
import signal

# Настройка логирования
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("bot_log.txt"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

async def log_and_report(client, sender, success, chat_id, invite_link, members_added, admins_promoted, message):
    log_message = f"Operation: {'Success' if success else 'Failure'}\n"
    log_message += f"Sender: {sender}\n"
    log_message += f"Chat ID: {chat_id}\n"
    log_message += f"Invite Link: {invite_link}\n"
    log_message += f"Members Added: {members_added}\n"
    log_message += f"Admins Promoted: {admins_promoted}\n"
    log_message += f"Message: {message}"
    
    logger.info(log_message)
    
    report = f"{'true' if success else 'false'}\n{sender}\n{chat_id}\n{invite_link}\n{str(members_added).lower()}\n{str(admins_promoted).lower()}\n{message}"
    await client.send_message(config.CHANNEL_ID, report)
    if not success:
        await client.send_message(config.OWNER_ID, log_message)

@app.on_message(filters.chat(config.CHANNEL_ID))
async def create_chat(client, message):
    sender = "Unknown"
    chat_id = "false"
    invite_link = "false"
    members_added = False
    admins_promoted = False
    
    try:
        lines = message.text.split("\n")
        if len(lines) != 6:
            error_message = "Команда должна содержать 6 строк: title, type, avatar, members, admins, sender"
            await log_and_report(client, lines[-1], False, chat_id, invite_link, members_added, admins_promoted, f"Error: {error_message}")
            return

        chat_title, chat_type, chat_avatar_name, members, admins, sender = lines
        members = [int(m.strip()) for m in members.split(',') if m.strip()]
        admins = [int(a.strip()) for a in admins.split(',') if a.strip()]
        
        logger.info(f"Creating chat: {chat_title} ({chat_type})")
        await asyncio.sleep(3)

        # Создание чата
        if chat_type == "supergroup":
            chat = await client.create_supergroup(chat_title)
        elif chat_type == "channel":
            chat = await client.create_channel(chat_title)
        else:
            error_message = "Wrong chat type, use supergroup or channel"
            await log_and_report(client, sender, False, chat_id, invite_link, members_added, admins_promoted, f"Error: {error_message}")
            return

        chat_id = chat.id
        logger.info(f"Chat created successfully. Chat ID: {chat_id}")

        await asyncio.sleep(3)

        # Подгрузка и установка аватарки
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.png")
        if os.path.isfile(avatar_path):
            try:
                await client.set_chat_photo(chat_id=chat_id, photo=avatar_path)
                logger.info(f"Chat photo set successfully for chat {chat_id}")
            except Exception as e:
                error_message = f"Failed to set chat photo: {str(e)}"
                logger.error(error_message)
                await log_and_report(client, sender, False, chat_id, invite_link, members_added, admins_promoted, f"Error: {error_message}")
                return
        else:
            error_message = f"Avatar file {chat_avatar_name}.png not found"
            logger.error(error_message)
            await log_and_report(client, sender, False, chat_id, invite_link, members_added, admins_promoted, f"Error: {error_message}")
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
            logger.info(f"Chat permissions set for supergroup {chat_id}")

        await asyncio.sleep(3)

        # Запрет на копирование контента
        try:
            await client.set_chat_protected_content(chat_id, enabled=True)
            logger.info(f"Protected content enabled for chat {chat_id}")
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
            logger.info(f"Invite link generated for chat {chat_id}: {invite_link}")
        except Exception as e:
            invite_link = "false"
            error_message = f"Failed to get invite link: {str(e)}"
            logger.error(error_message)
            await client.send_message(config.OWNER_ID, error_message)

        # Отправка отчета
        await log_and_report(client, sender, True, chat_id, invite_link, members_added, admins_promoted, "Chat created successfully")

    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        await log_and_report(client, sender, False, chat_id, invite_link, members_added, admins_promoted, error_message)

@app.on_raw_update()
async def raw_update_handler(client, update, users, chats):
    if isinstance(update, pyrogram.raw.types.UpdatesTooLong):
        logger.info("Received UpdatesTooLong. Syncing updates...")
        await client.invoke(pyrogram.raw.functions.updates.GetState())
        logger.info("Updates synced successfully")

async def health_check():
    while True:
        await asyncio.sleep(300)  # Проверка каждые 5 минут
        try:
            me = await app.get_me()
            logger.info(f"Bot is alive. Username: @{me.username}")
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}. Shutting down...")
    app.stop()
    logger.info("Bot stopped")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    await app.start()
    logger.info("Bot started successfully")
    asyncio.create_task(health_check())
    await pyrogram.idle()

if __name__ == "__main__":
    app.run(main())