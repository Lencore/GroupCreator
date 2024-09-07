from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted
import config
import os
import asyncio
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

@app.on_message(filters.chat(config.CHANNEL_ID))
async def create_chat(client, message):
    try:
        lines = message.text.split("\n")
        if len(lines) != 6:
            error_message = "Команда должна содержать 6 строк: title, type, avatar, members, admins, sender"
            logger.error(error_message)
            report = f"false\n{lines[-1]}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_title, chat_type, chat_avatar_name, members, admins, sender = lines
        members = [int(m.strip()) for m in members.split(',') if m.strip()]
        admins = [int(a.strip()) for a in admins.split(',') if a.strip()]

        await asyncio.sleep(3)

        # Создание чата
        if chat_type == "supergroup":
            chat = await client.create_supergroup(chat_title)
        elif chat_type == "channel":
            chat = await client.create_channel(chat_title)
        else:
            error_message = "Wrong chat type, use supergroup or channel"
            logger.error(error_message)
            report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_id = chat.id

        await asyncio.sleep(3)

        # Подгрузка и установка аватарки
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.png")
        if os.path.isfile(avatar_path):
            try:
                await client.set_chat_photo(chat_id=chat_id, photo=avatar_path)
            except Exception as e:
                logger.error(f"Failed to set chat photo: {str(e)}")
                report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {str(e)}"
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

        await asyncio.sleep(3)

        # Запрет на копирование контента
        try:
            await client.set_chat_protected_content(chat_id, enabled=True)
        except Exception as e:
            logger.error(f"Failed to set protected content: {str(e)}")

        # Добавление участников
        members_added = True
        for user_id in members:
            await asyncio.sleep(3)
            try:
                await client.add_chat_members(chat_id, user_id)
            except Exception as e:
                logger.error(f"Failed to add user {user_id}: {str(e)}")
                members_added = False

        # Назначение админов
        admins_promoted = True
        for admin_id in admins:
            if admin_id not in members:
                logger.error(f"Admin {admin_id} not in members list, skipping")
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
            except Exception as e:
                logger.error(f"Failed to promote admin {admin_id}: {str(e)}")
                admins_promoted = False

        await asyncio.sleep(3)

        # Получение ссылки приглашения
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception as e:
            invite_link = "false"
            logger.error(f"Failed to get invite link: {str(e)}")
            await client.send_message(config.OWNER_ID, f"Failed to get invite link: {str(e)}")

        # Отправка отчета
        report = f"true\n{sender}\n{chat_id}\n{invite_link}\n{str(members_added).lower()}\n{str(admins_promoted).lower()}"
        await client.send_message(config.CHANNEL_ID, report)

    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\nError: {str(e)}"
        await client.send_message(config.CHANNEL_ID, report)
        await client.send_message(config.OWNER_ID, f"Unhandled exception: {str(e)}")

async def check_channel():
    while True:
        try:
            await app.get_chat(config.CHANNEL_ID)
            print(f"Successfully checked channel {config.CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Failed to check channel: {str(e)}")
        await asyncio.sleep(300)  # Проверка каждые 5 минут

async def main():
    try:
        await app.start()
        print("Bot started successfully")
        print(f"Using channel ID: {config.CHANNEL_ID}")
        
        check_channel_task = asyncio.create_task(check_channel())
        
        print("Bot is now listening for updates...")
        await app.idle()
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
    finally:
        if 'check_channel_task' in locals():
            await check_channel_task
        await app.stop()
        print("Bot stopped")

if __name__ == "__main__":
    app.run(main())