import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменных окружения

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Файл для хранения задач
TASKS_FILE = "tasks.json"

def load_tasks():
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

tasks = load_tasks()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍅 Запустить таймер", callback_data="timer")],
        [InlineKeyboardButton(text="📝 Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="list_tasks")],
        [InlineKeyboardButton(text="✅ Выполнить задачу", callback_data="complete_task")],
        [InlineKeyboardButton(text="❌ Удалить все задачи", callback_data="clear_tasks")]
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in tasks:
        tasks[user_id] = []
        save_tasks(tasks)
    
    await message.answer(
        "🤖 Привет! Я *MyBrot* — твой помощник по продуктивности!\n\n"
        "👇 *Выбери действие:*",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "timer")
async def start_timer(callback: types.CallbackQuery):
    await callback.message.answer(
        "🍅 *Таймер запущен!*\n⏱ 25 минут работы",
        parse_mode="Markdown"
    )
    await asyncio.sleep(1500)
    await callback.message.answer(
        "🔔 *Время вышло!*\n☕️ Сделай перерыв 5-10 минут",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "add_task")
async def ask_task(callback: types.CallbackQuery):
    await callback.message.answer(
        "📝 *Напиши задачу текстом:*",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message()
async def save_user_task(message: types.Message):
    user_id = str(message.from_user.id)
    if message.text.startswith("/"):
        return
    
    if user_id not in tasks:
        tasks[user_id] = []
    
    tasks[user_id].append({"text": message.text, "completed": False})
    save_tasks(tasks)
    await message.answer(f"✅ *Задача сохранена!*\n📌 {message.text}", parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "list_tasks")
async def show_tasks(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    user_tasks = tasks.get(user_id, [])
    active_tasks = [t for t in user_tasks if not t["completed"]]
    
    if not active_tasks:
        await callback.message.answer("📭 *У тебя пока нет задач*", parse_mode="Markdown")
    else:
        task_list = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(active_tasks)])
        await callback.message.answer(f"📋 *Твои задачи:*\n\n{task_list}", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "complete_task")
async def complete_task_menu(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    user_tasks = tasks.get(user_id, [])
    active_tasks = [t for t in user_tasks if not t["completed"]]
    
    if not active_tasks:
        await callback.message.answer("🎉 *Нет активных задач!*", parse_mode="Markdown")
        await callback.answer()
        return
    
    buttons = [[InlineKeyboardButton(text=f"✅ {t['text'][:30]}", callback_data=f"complete_{i}")] 
               for i, t in enumerate(active_tasks[:10])]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")])
    
    await callback.message.answer(
        "✅ *Отметь выполненную задачу:*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("complete_"))
async def complete_task(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    user_tasks = tasks.get(user_id, [])
    active_tasks = [t for t in user_tasks if not t["completed"]]
    
    task_index = int(callback.data.split("_")[1])
    if task_index < len(active_tasks):
        completed_task = active_tasks[task_index]
        for task in user_tasks:
            if task["text"] == completed_task["text"] and not task["completed"]:
                task["completed"] = True
                break
        save_tasks(tasks)
        await callback.message.answer(f"🎉 *Молодец!* ✅ {completed_task['text']}", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "clear_tasks")
async def clear_tasks(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    tasks[user_id] = []
    save_tasks(tasks)
    await callback.message.answer("🗑 *Все задачи удалены*", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.answer("🔙 *Главное меню*", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

async def main():
    print("🤖 Бот MyBrot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
