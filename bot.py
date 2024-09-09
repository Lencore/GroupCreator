import logging
from pyrogram import Client, filters, idle
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted, UserAlreadyParticipant
from pyrogram.handlers import MessageHandler
import config
import os
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

CHANNEL_ID = -1002208357552
CHANNEL_LINK = "https://t.me/+Odc4YrC33v82Njli"

async def join_channel():
    try:
        await app.join_chat(CHANNEL_LINK)
        logger.info(f"Успешно присоединился к каналу {CHANNEL_ID}")
    except UserAlreadyParticipant:
        logger.info(f"Бот уже является участником канала {CHANNEL_ID}")
    except Exception as e:
        logger.error(f"Не удалось присоединиться к каналу: {e}")

async def create_chat(client, message):
    logger.info(f"Получено новое сообщение в канале {message.chat.id}")
    try:
        lines = message.text.split("\n")
        if len(lines) != 6:
            error_message = "Команда должна содержать 6 строк: title, type, avatar, members, admins, sender"
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
            report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_id = chat.id
        logger.info(f"Создан новый чат типа {chat_type} с ID {chat_id}")

        await asyncio.sleep(3)

        # Подгрузка и установка аватарки
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.png")
        if os.path.isfile(avatar_path):
            try:
                await client.set_chat_photo(chat_id=chat_id, photo=avatar_path)
                logger.info(f"Установлена аватарка для чата {chat_id}")
            except Exception as e:
                error_message = f"Failed to set chat photo: {str(e)}"
                report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {error_message}"
                await client.send_message(config.CHANNEL_ID, report)
                logger.error(error_message)
                return
        else:
            error_message = f"Avatar file {chat_avatar_name}.png not found"
            report = f"false\n{sender}\n{chat_id}\nfalse\nfalse\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            logger.error(error_message)
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
            logger.info(f"Установлены права для супергруппы {chat_id}")

        await asyncio.sleep(3)

        # Запрет на копирование контента
        try:
            await client.set_chat_protected_content(chat_id, enabled=True)
            logger.info(f"Установлен запрет на копирование контента для чата {chat_id}")
        except Exception as e:
            logger.error(f"Failed to set protected content for chat {chat_id}: {str(e)}")

        # Добавление участников
        members_added = True
        for user_id in members:
            await asyncio.sleep(3)
            try:
                await client.add_chat_members(chat_id, user_id)
                logger.info(f"Добавлен участник {user_id} в чат {chat_id}")
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
                logger.info(f"Пользователь {admin_id} назначен администратором в чате {chat_id}")
            except Exception as e:
                logger.error(f"Failed to promote admin {admin_id} in chat {chat_id}: {str(e)}")
                admins_promoted = False

        await asyncio.sleep(3)

        # Получение ссылки приглашения
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
            logger.info(f"Создана ссылка приглашения для чата {chat_id}")
        except Exception as e:
            invite_link = "false"
            error_message = f"Failed to get invite link for chat {chat_id}: {str(e)}"
            await client.send_message(config.OWNER_ID, error_message)
            logger.error(error_message)

        # Отправка отчета
        report = f"true\n{sender}\n{chat_id}\n{invite_link}\n{str(members_added).lower()}\n{str(admins_promoted).lower()}"
        await client.send_message(config.CHANNEL_ID, report)
        logger.info(f"Отправлен отчет о создании чата {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        error_message = f"Ошибка: {str(e)}"
        report = f"false\n{sender}\nfalse\nfalse\nfalse\nfalse\n{error_message}"
        await client.send_message(config.CHANNEL_ID, report)
        await client.send_message(config.OWNER_ID, error_message)

async def main():
    await app.start()
    logger.info("Бот запущен")
    await join_channel()
    
    # Регистрация обработчика сообщений
    app.add_handler(MessageHandler(create_chat, filters.chat(config.CHANNEL_ID)))
    
    logger.info("Ожидание новых сообщений...")
    await idle()

if __name__ == "__main__":
    app.run(main())