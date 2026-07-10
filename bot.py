import logging
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- KONFIGURATSIYA ---
BOT_TOKEN = "8824099204:AAGQlrk_Dig_4bFM1abs-ZwnxLbzj_CnWQc"
ADMIN_ID = 8200259525
DB_NAME = "kino_bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# --- FSM STATES ---
class States(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_channel = State()

# --- BAZA INIT ---
async def db_init():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, file_id TEXT, views INTEGER DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        await db.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
        # Boshlang'ich config
        await db.execute("INSERT OR IGNORE INTO config VALUES ('channel_username', '@KinoStarBot')")
        await db.execute("INSERT OR IGNORE INTO config VALUES ('is_sub_enabled', '0')")
        await db.commit()

# --- FUNKSIYALAR ---
async def get_config():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM config")
        return dict(await cursor.fetchall())

async def check_sub(user_id):
    cfg = await get_config()
    if cfg['is_sub_enabled'] == '0' or user_id == ADMIN_ID: return True
    try:
        member = await bot.get_chat_member(chat_id=cfg['channel_username'], user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- MENYULAR ---
def main_kb(user_id):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎬 Kino qidirish")
    if user_id == ADMIN_ID: kb.button(text="📊 Admin panel")
    return kb.as_markup(resize_keyboard=True)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        await db.commit()
    
    if not await check_sub(message.from_user.id):
        cfg = await get_config()
        kb = InlineKeyboardBuilder()
        kb.button(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{cfg['channel_username'].replace('@', '')}")
        kb.button(text="✅ Tekshirish", callback_data="check_sub")
        await message.answer("❌ Botdan foydalanish uchun kanalga obuna bo'ling!", reply_markup=kb.as_markup())
    else:
        await message.answer("👋 Xush kelibsiz! Kino kodini yuboring.", reply_markup=main_kb(message.from_user.id))

@dp.callback_query(F.data == "check_sub")
async def check_sub_cb(cb: types.CallbackQuery):
    if await check_sub(cb.from_user.id):
        await cb.message.edit_text("✅ Rahmat! Endi kod yuborishingiz mumkin.")
    else:
        await cb.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)

# --- ADMIN PANEL ---
@dp.message(F.text == "📊 Admin panel", F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.button(text="📥 Kino yuklash")
    kb.button(text="⚙️ Sozlamalar")
    await message.answer("Admin boshqaruv:", reply_markup=kb.as_markup(resize_keyboard=True))

@dp.message(F.text == "📥 Kino yuklash", F.from_user.id == ADMIN_ID)
async def load_video(message: types.Message, state: FSMContext):
    await message.answer("Video yuboring:")
    await state.set_state(States.waiting_for_video)

@dp.message(States.waiting_for_video, F.video)
async def get_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await message.answer("Kodini yozing:")
    await state.set_state(States.waiting_for_code)

@dp.message(States.waiting_for_code)
async def get_code(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO movies (code, file_id) VALUES (?, ?)", (message.text, data['file_id']))
        await db.commit()
    await message.answer("✅ Saqlandi!")
    await state.clear()

# --- QIDIRUV ---
@dp.message(F.text.isdigit())
async def search(message: types.Message):
    if not await check_sub(message.from_user.id):
        await message.answer("❌ Avval obuna bo'ling!")
        return
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT file_id FROM movies WHERE code = ?", (message.text,)) as cur:
            res = await cur.fetchone()
            if res: await message.answer_video(res[0])
            else: await message.answer("❌ Kod topilmadi!")

async def main():
    await db_init()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
