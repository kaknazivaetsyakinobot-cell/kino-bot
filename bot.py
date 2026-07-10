from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Bot tokeni va adminlar ro'yxati
API_TOKEN = '8824099204:AAGO_NnBzeybeQKog-i9bh0GrfG9mQ4AXsw'
ADMIN_IDS = [ 7873870779,8994639797 ,8200259525] # 3 ta admin ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Tugmalar tartibi
main_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
    KeyboardButton("📊 Statistika"), KeyboardButton("✉️ Xabar yuborish"),
    KeyboardButton("🎬 Kontent boshqaruvi"), KeyboardButton("🔑 Kanallar"),
    KeyboardButton("⚙️ Tizim sozlamalari"), KeyboardButton("📥 So'rovlar"),
    KeyboardButton("🔙 Orqaga"), KeyboardButton("👥 Foydalanuvchilar")
)

content_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
    KeyboardButton("🎬 Kinolar"), KeyboardButton("📮 Postlar"),
    KeyboardButton("🔗 Referal"), KeyboardButton("🔙 Asosiy panel")
)

movies_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
    KeyboardButton("📥 Kino yuklash"), KeyboardButton("📝 Kino tahrirlash"),
    KeyboardButton("🗑 Kino o'chirish"), KeyboardButton("📋 Kinolar ro'yxati"),
    KeyboardButton("🔙 Orqaga")
)

# Admin tekshiruvi funksiyasi
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Bot komandalari va handlerlar
@dp.message_handler(commands=['start', 'admin'])
async def start_handler(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Admin paneliga xush kelibsiz!", reply_markup=main_kb)
    else:
        await message.answer("Botga xush kelibsiz!")

@dp.message_handler(text="🎬 Kontent boshqaruvi")
async def content_handler(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Kontent bo'limiga xush kelibsiz:", reply_markup=content_kb)

@dp.message_handler(text="🎬 Kinolar")
async def movies_handler(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Kinolar bo'limidasiz:", reply_markup=movies_kb)

@dp.message_handler(text="🔑 Kanallar")
async def channels_handler(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("🔑 Kanallar bo'limi (Majburiy obuna sozlamalari).")

@dp.message_handler(text="🔙 Asosiy panel")
@dp.message_handler(text="🔙 Orqaga")
async def back_handler(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Admin paneliga xush kelibsiz!", reply_markup=main_kb)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
