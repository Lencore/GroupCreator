import logging
from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted, UserAlreadyParticipant, PeerIdInvalid
import config
import os
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Отключаем лишние сообщения от Pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("pyrogram.session.auth").disabled = True

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

CHANNEL_LINK = "https://t.me/+Odc4YrC33v82Njli"

async def join_channel():
    try:
        chat = await app.join_chat(CHANNEL_LINK)
        logger.info(f"Бот присоединился к каналу: {chat.id}")
        return chat.id
    except UserAlreadyParticipant:
        chat = await app.get_chat(CHANNEL_LINK)
        logger.info(f"Бот уже является участником канала: {chat.id}")
        return chat.id
    except Exception as e:
        logger.error(f"Не удалось присоединиться к каналу: {e}")
        return None

async def get_chat(chat_id):
    try:
        chat = await app.get_chat(chat_id)
        logger.info(f"Получена информация о чате: {chat.id} - {chat.title}")
        return chat
    except Exception as e:
        logger.error(f"Не удалось получить информацию о чате {chat_id}: {e}")
        return None

async def get_peer_id():
    try:
        async for dialog in app.get_dialogs():
            chat_type = dialog.chat.type
            chat_id = dialog.chat.id
            chat_title = dialog.chat.title or dialog.chat.first_name or "Unnamed"
            logger.info(f"Найден диалог: {chat_type} - {chat_id} - {chat_title}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при получении списка диалогов: {e}")
        return False

async def create_chat(client, message):
    if message.text.startswith(('true', 'false')):
        return  # Пропускаем сообщения с отчетами

    logger.info(f"Получена новая команда в канале {message.chat.id}")
    try:
        lines = message.text.split("\n")
        if len(lines) != 6:
            error_message = "Команда должна содержать 6 строк: title, type, avatar, members, admins, sender"
            report = f"false\n{lines[-1]}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(message.chat.id, report)
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
            report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(message.chat.id, report)
            return

        chat_id = chat.id
        logger.info(f"Создан новый чат типа {chat_type} с ID {chat_id}")

        await asyncio.sleep(3)

        # Подгрузка и установка аватарки
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.png")
        if os.path.isfile(avatar_path):
            try:
                await client.set_chat_photo(chat_id=chat_id, photo=avatar_path)
            except Exception as e:
                error_message = f"Failed to set chat photo: {str(e)}"
                report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {error_message}"
                await client.send_message(message.chat.id, report)
                return
        else:
            error_message = f"Avatar file {chat_avatar_name}.png not found"
            report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(message.chat.id, report)
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
            logger.error(f"Failed to set protected content for chat {chat_id}: {str(e)}")

        # Добавление участников
        members_added = True
        for user_id in members:
            await asyncio.sleep(3)
            try:
                await client.add_chat_members(chat_id, user_id)
            except (FloodWait, PeerFlood, UserPrivacyRestricted) as e:
                logger.error(f"Failed to add user {user_id} to chat {chat_id}: {str(e)}")
                members_added = False
            except Exception as e:
                logger.error(f"Unexpected error adding user {user_id} to chat {chat_id}: {str(e)}")
                members_added = False

        # Назначение админов
        admins_promoted = True
        for admin_id in admins:
            if admin_id not in members:
                logger.warning(f"Admin {admin_id} not in members list for chat {chat_id}, skipping")
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
                logger.error(f"Failed to promote admin {admin_id} in chat {chat_id}: {str(e)}")
                admins_promoted = False

        await asyncio.sleep(3)

        # Получение ссылки приглашения
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception as e:
            invite_link = "false"
            error_message = f"Failed to get invite link for chat {chat_id}: {str(e)}"
            await client.send_message(config.OWNER_ID, error_message)

        # Отправка отчета
        report = f"true\n{sender}\n{chat_id}\n{invite_link}\n{str(members_added).lower()}\n{str(admins_promoted).lower()}"
        await client.send_message(message.chat.id, report)
        logger.info(f"Отправлен отчет о создании чата {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        error_message = f"Ошибка: {str(e)}"
        report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\n{error_message}"
        await client.send_message(message.chat.id, report)
        await client.send_message(config.OWNER_ID, error_message)

async def main():
    async with app:
        channel_id = await join_channel()
        if not channel_id:
            logger.error("Не удалось получить ID канала. Завершение работы.")
            return

        logger.info(f"Бот запущен и готов к работе в канале {channel_id}")
        
        # Получаем список всех диалогов
        await get_peer_id()
        
        while True:
            try:
                async for message in app.get_chat_history(channel_id, limit=1):
                    if message.text:
                        await create_chat(app, message)
                    break
            except PeerIdInvalid:
                logger.error(f"Неверный ID канала: {channel_id}. Попытка переподключения.")
                channel_id = await join_channel()
                if not channel_id:
                    logger.error("Не удалось переподключиться к каналу. Завершение работы.")
                    return
            except Exception as e:
                logger.error(f"Ошибка при получении обновлений: {e}")
            
            await asyncio.sleep(5)  # Проверяем новые сообщения каждые 5 секунд

if __name__ == "__main__":
    app.run(main())