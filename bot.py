import logging
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- LOGGING VA SOZLAMALAR ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8824099204:AAHbiBZxuiR6OFmQyzBcS9-BEeNSfbbHY_0"
ADMIN_ID = 8200259525
DB_NAME = "movie_bot_pro.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- DATABASE MANAGEMENT MODULE ---
async def create_database_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT, title TEXT)")
        await db.execute("CREATE TABLE IF NOT EXISTS referals (ref_code TEXT PRIMARY KEY, name TEXT, count INTEGER DEFAULT 0)")
        await db.commit()

# --- FSM STATE CLASSES ---
class FullBotStates(StatesGroup):
    # Referral states
    waiting_for_referral_name = State()
    # Movie upload states
    waiting_for_video_file = State()
    waiting_for_video_code = State()
    waiting_for_video_title = State()

# --- KEYBOARD BUILDER MODULE ---
def get_main_keyboard(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Kino qidirish")
    builder.button(text="👤 Profil")
    builder.button(text="💎 Premium")
    if user_id == ADMIN_ID:
        builder.button(text="⚙️ Admin Panel")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_admin_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎬 Kino yuklash")
    builder.button(text="🔗 Referallar ro'yxati")
    builder.button(text="➕ Havola yaratish")
    builder.button(text="📊 Statistika")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# --- START COMMAND HANDLER ---
@dp.message(CommandStart())
async def handle_start(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    args = command.args

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        if args and args.startswith("ref_"):
            await db.execute("UPDATE referals SET count = count + 1 WHERE ref_code = ?", (args,))
        await db.commit()

    await message.answer("Assalomu alaykum! Kino kodini yuboring.", reply_markup=get_main_keyboard(user_id))

# --- ADMIN PANEL LOGIC ---
@dp.message(F.text == "⚙️ Admin Panel", F.from_user.id == ADMIN_ID)
async def admin_main(message: types.Message):
    await message.answer("Admin boshqaruv tizimi:", reply_markup=get_admin_keyboard())

# --- REFERRAL LOGIC (DETAILED) ---
@dp.message(F.text == "➕ Havola yaratish", F.from_user.id == ADMIN_ID)
async def start_create_ref(message: types.Message, state: FSMContext):
    await message.answer("Referal uchun ism yozing:")
    await state.set_state(FullBotStates.waiting_for_referral_name)

@dp.message(FullBotStates.waiting_for_referral_name, F.from_user.id == ADMIN_ID)
async def process_create_ref(message: types.Message, state: FSMContext):
    name = message.text
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM referals")
        res = await cursor.fetchone()
        new_code = f"ref_{res[0] + 1}"
        await db.execute("INSERT INTO referals (ref_code, name, count) VALUES (?, ?, 0)", (new_code, name))
        await db.commit()
    
    bot_info = await bot.get_me()
    await message.answer(f"Havola yaratildi: https://t.me/{bot_info.username}?start={new_code}")
    await state.clear()

# --- MOVIE UPLOAD LOGIC (DETAILED) ---
@dp.message(F.text == "🎬 Kino yuklash", F.from_user.id == ADMIN_ID)
async def start_upload(message: types.Message, state: FSMContext):
    await message.answer("Kino faylini yuboring:")
    await state.set_state(FullBotStates.waiting_for_video_file)

@dp.message(FullBotStates.waiting_for_video_file, F.video)
async def process_upload_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await message.answer("Kino uchun kodni yozing:")
    await state.set_state(FullBotStates.waiting_for_video_code)

@dp.message(FullBotStates.waiting_for_video_code)
async def process_upload_code(message: types.Message, state: FSMContext):
    code = message.text
    if not code.isdigit():
        await message.answer("Faqat raqam yozing!")
        return
    data = await state.get_data()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (code, data['file_id']))
        await db.commit()
    await message.answer("Saqlandi!", reply_markup=get_admin_keyboard())
    await state.clear()

# --- SEARCH LOGIC ---
@dp.message(F.text.isdigit())
async def handle_search(message: types.Message, state: FSMContext):
    await state.clear()
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT file_id FROM movies WHERE code = ?", (message.text,))
        res = await cur.fetchone()
    
    if res:
        await message.answer_video(res[0], caption=f"Topildi: {message.text}")
    else:
        await message.answer("Bunday kod yo'q!")

# --- MISC HANDLERS ---
@dp.message(Command("cancel"))
async def cancel_process(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=get_main_keyboard(message.from_user.id))

async def main():
    await create_database_tables()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
