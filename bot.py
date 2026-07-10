import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- KONFIGURATSIYA ---
API_TOKEN = '8824099204:AAGO_NnBzeybeQKog-i9bh0GrfG9mQ4AXsw'
OWNER_ID = 8200259525 # O'z ID raqamingni shu yerga yoz

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- RUXSATLARNI TEKSHIRISH ---
def is_owner(user_id):
    return user_id == OWNER_ID

# --- KEYBOARDS ---
def admin_menu():
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📩 Xabar yuborish")],
        [KeyboardButton(text="🎬 Kontent boshqaruvi"), KeyboardButton(text="🔑 Kanallar")],
        [KeyboardButton(text="⚙️ Tizim sozlamalari"), KeyboardButton(text="📥 So'rovlar")],
        [KeyboardButton(text="👥 Foydalanuvchilar")]
    ], resize_keyboard=True)
    return kb

# --- HANDLERS ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Admin paneliga xush kelibsiz!", reply_markup=admin_menu())

@dp.message(F.text == "🔑 Kanallar")
async def channels_handler(message: types.Message):
    if not is_owner(message.from_user.id):
        await message.answer("❌ Sizda ushbu bo'limga kirish uchun ruxsat yo'q!")
        return
    await message.answer("🔐 Kanallar sozlamalari (Faqat siz uchun ochiq).")

@dp.message(F.text == "📥 So'rovlar")
async def requests_handler(message: types.Message):
    if not is_owner(message.from_user.id):
        await message.answer("❌ Sizda ushbu bo'limga kirish uchun ruxsat yo'q!")
        return
    await message.answer("📥 So'rovlar bo'limi (Avto tasdiqlash holati: O'chiq).")

@dp.message(F.text == "🎬 Kontent boshqaruvi")
async def content_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi post yaratish", callback_data="add_post")],
        [InlineKeyboardButton(text="🎬 Kinolar ro'yxati", callback_data="list_movies")]
    ])
    await message.answer("🎬 Kontent bo'limiga xush kelibsiz:", reply_markup=kb)

# --- BOTNI ISHGA TUSHIRISH ---
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
