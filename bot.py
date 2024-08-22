from pyrogram import Client, filters
from pyrogram.types import ChatPermissions, InputMediaPhoto
import config
import os
import asyncio

app = Client("my_bot", api_id=config.API_ID, api_hash=config.API_HASH, phone_number=config.PHONE_NUMBER)

@app.on_message(filters.chat(config.CHANNEL_ID))
async def create_chat(client, message):
    try:
        lines = message.text.split("\n")
        if len(lines) < 4:
            error_message = "Команда должна содержать 4 строки: title, type, avatar, admin"
            report = f"false\nnull\nnull\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_title = lines[0]
        chat_type = lines[1]
        chat_avatar_name = lines[2]
        chat_admin = int(lines[3])

        # Задержка перед выполнением команд
        await asyncio.sleep(1)

        # Создание чата
        if chat_type == "supergroup":
            chat = await client.create_supergroup(chat_title)
        elif chat_type == "channel":
            chat = await client.create_channel(chat_title)
        else:
            error_message = "Wrong chat type, use supergroup or channel"
            report = f"false\nnull\nnull\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        chat_id = chat.id

        # Подгрузка и установка аватарки
        avatar_path = os.path.join(os.getcwd(), f"{chat_avatar_name}.jpg")
        if os.path.isfile(avatar_path):
            try:
                await client.set_chat_photo(chat_id, InputMediaPhoto(avatar_path))
            except Exception as e:
                error_message = f"Failed to set chat photo: {str(e)}"
                report = f"false\n{chat_id}\nnull\nfalse\nError: {error_message}"
                await client.send_message(config.CHANNEL_ID, report)
                return
        else:
            error_message = f"Avatar file {chat_avatar_name}.jpg not found"
            report = f"false\n{chat_id}\nnull\nfalse\nError: {error_message}"
            await client.send_message(config.CHANNEL_ID, report)
            return

        # Настройка прав и добавление участников
        await asyncio.sleep(1)  # Задержка
        if chat_type == "supergroup":
            await client.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=True))
            await client.set_chat_permissions(chat_id, ChatPermissions(can_invite_users=False))

        # Запрет на копирование контента
        await asyncio.sleep(1)  # Задержка
        await client.set_chat_permissions(chat_id, ChatPermissions(can_save_content=False))

        # Добавление участников
        user_ids = [1747279, 1045827, 142283509, 1873028973]
        for user_id in user_ids:
            await asyncio.sleep(1)  # Задержка
            await client.add_chat_members(chat_id, user_id)

        # Назначение админов
        await asyncio.sleep(1)  # Задержка
        await client.promote_chat_member(chat_id, 1873028973, can_manage_chat=True, can_post_messages=True, can_edit_messages=True, can_delete_messages=True, can_invite_users=True, can_restrict_members=True, can_pin_messages=True, can_promote_members=True)
        
        admin_added = False
        try:
            await asyncio.sleep(1)  # Задержка
            await client.promote_chat_member(chat_id, chat_admin, can_manage_chat=True, can_post_messages=True, can_edit_messages=True, can_delete_messages=True, can_invite_users=True, can_restrict_members=True, can_pin_messages=True, can_promote_members=True)
            admin_added = True
        except Exception:
            admin_added = False

        # Получение ссылки приглашения
        try:
            await asyncio.sleep(1)  # Задержка
            invite_link = await client.export_chat_invite_link(chat_id)
        except Exception as e:
            invite_link = "null"
            error_message = f"Failed to get invite link: {str(e)}"
            await client.send_message(config.OWNER_ID, error_message)

        # Отправка отчета
        report = f"true\n{chat_id}\n{invite_link}\n{admin_added}"
        await client.send_message(config.CHANNEL_ID, report)

    except Exception as e:
        error_message = f"Ошибка: {str(e)}"
        report = f"false\nnull\nnull\nfalse\n{error_message}"
        await client.send_message(config.CHANNEL_ID, report)
        await client.send_message(config.OWNER_ID, error_message)

app.run()
