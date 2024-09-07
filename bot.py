from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, ChatPrivileges
from pyrogram.errors import FloodWait, PeerFlood, UserPrivacyRestricted
import config
import os
import asyncio
import logging

# Настройка минимального логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

async def log_and_report(client, sender, success, chat_id, invite_link, members_added, admins_promoted, message):
    report = f"{'Успешно' if success else 'Ошибка'}: {message}"
    logger.info(report)
    await client.send_message(config.CHANNEL_ID, report)

@app.on_message(filters.chat(config.CHANNEL_ID))
async def create_chat(client, message):
    logger.info(f"Получена команда: {message.text.split()[0]}")
    
    try:
        lines = message.text.split("\n")
        if len(lines) != 6:
            await log_and_report(client, "Unknown", False, "N/A", "N/A", False, False, "Неверный формат команды")
            return

        chat_title, chat_type, chat_avatar_name, members, admins, sender = lines
        members = [int(m.strip()) for m in members.split(',') if m.strip()]
        admins = [int(a.strip()) for a in admins.split(',') if a.strip()]

        # Создание чата
        if chat_type == "supergroup":
            chat = await client.create_supergroup(chat_title)
        elif chat_type == "channel":
            chat = await client.create_channel(chat_title)
        else:
            await log_and_report(client, sender, False, "N/A", "N/A", False, False, "Неверный тип чата")
            return

        chat_id = chat.id

        # Установка аватара
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.png")
        if os.path.isfile(avatar_path):
            await client.set_chat_photo(chat_id=chat_id, photo=avatar_path)

        # Настройка прав для супергруппы
        if chat_type == "supergroup":
            await client.set_chat_permissions(chat_id, ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=False
            ))

        # Запрет на копирование контента
        await client.set_chat_protected_content(chat_id, enabled=True)

        # Добавление участников
        members_added = True
        for user_id in members:
            try:
                await client.add_chat_members(chat_id, user_id)
            except (FloodWait, PeerFlood, UserPrivacyRestricted, Exception):
                members_added = False

        # Назначение админов
        admins_promoted = True
        for admin_id in admins:
            if admin_id in members:
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
                except Exception:
                    admins_promoted = False

        # Получение ссылки приглашения
        try:
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception:
            invite_link = "Не удалось создать"

        # Отправка отчета
        await log_and_report(client, sender, True, chat_id, invite_link, members_added, admins_promoted, 
                             f"Чат создан: {chat_id}\nСсылка: {invite_link}\nУчастники добавлены: {'Да' if members_added else 'Нет'}\nАдмины назначены: {'Да' if admins_promoted else 'Нет'}")

    except Exception as e:
        await log_and_report(client, "Unknown", False, "N/A", "N/A", False, False, f"Ошибка при создании чата: {str(e)}")

async def main():
    await app.start()
    logger.info("Бот запущен и ожидает команды")
    await pyrogram.idle()

if __name__ == "__main__":
    app.run(main())