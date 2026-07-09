import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- SOZLAMALAR ---
BOT_TOKEN = "8824099204:AAETKSI7llQgIqZWnVfQZbLSzR5A1hTGCLo"
ADMIN_ID = 8200259525
CARD_INFO = "5614 6840 9146 5672 (ISMATULLAYEVA NOZANIN)"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- XOTIRA (Baza ulamaganimiz uchun bu yerda saqlanadi) ---
db_referals = {} # {ref_id: {"name": name, "count": 0}}
db_movies = {}   # {code: file_id}

# --- HOLATLAR ---
class States(StatesGroup):
    waiting_for_name = State()
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_receipt = State()

# --- KLAVIATURALAR ---
def main_menu(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="💎 Premium")
    if user_id == ADMIN_ID:
        builder.button(text="📊 Boshqaruv")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎬 Kino yuklash")
    builder.button(text="🔗 Referallar")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 Xush kelibsiz! Kino kodini yuboring.", reply_markup=main_menu(message.from_user.id))

# --- PREMIUM (CHEK TIZIMI) ---
@dp.message(F.text == "💎 Premium")
async def premium(message: types.Message, state: FSMContext):
    await message.answer(f"💳 Karta: {CARD_INFO}\n📸 To'lov qilgach chekni rasm sifatida yuboring.")
    await state.set_state(States.waiting_for_receipt)

@dp.message(States.waiting_for_receipt, F.photo)
async def check_receipt(message: types.Message, state: FSMContext):
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, 
                         caption=f"🔔 Yangi chek! User: {message.from_user.full_name}\nID: {message.from_user.id}")
    await message.answer("✅ Chek adminga yuborildi, kuting.")
    await state.clear()

# --- ADMIN REFERALLAR (RASMDAGIDEK) ---
@dp.message(F.text == "📊 Boshqaruv", F.from_user.id == ADMIN_ID)
async def admin(message: types.Message):
    await message.answer("Admin panel:", reply_markup=admin_menu())

@dp.message(F.text == "🔗 Referallar", F.from_user.id == ADMIN_ID)
async def ref_list(message: types.Message):
    builder = ReplyKeyboardBuilder()
    for rid, data in db_referals.items():
        builder.button(text=f"📌 {data['name']} • 👥 {data['count']}")
    builder.button(text="➕ Havola yaratish")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1)
    await message.answer("Ishchi referallar:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "➕ Havola yaratish", F.from_user.id == ADMIN_ID)
async def create_ref(message: types.Message, state: FSMContext):
    await message.answer("Referal nomini yozing:")
    await state.set_state(States.waiting_for_name)

@dp.message(States.waiting_for_name)
async def save_ref(message: types.Message, state: FSMContext):
    ref_id = f"ref_{len(db_referals)+1}"
    db_referals[ref_id] = {"name": message.text, "count": 0}
    await message.answer(f"✅ Yaratildi: {message.text}", reply_markup=admin_menu())
    await state.clear()

# --- KINO YUKLASH (QOTMAYDIGAN) ---
@dp.message(F.text == "🎬 Kino yuklash", F.from_user.id == ADMIN_ID)
async def upload_video(message: types.Message, state: FSMContext):
    await message.answer("Video yuboring:")
    await state.set_state(States.waiting_for_video)

@dp.message(States.waiting_for_video, F.video)
async def get_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await message.answer("Kodini yozing:")
    await state.set_state(States.waiting_for_code)

@dp.message(States.waiting_for_code)
async def get_code(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam!")
        return
    data = await state.get_data()
    db_movies[message.text] = data['file_id']
    await message.answer("✅ Saqlandi!", reply_markup=admin_menu())
    await state.clear()

# --- /cancel (QOTISHLARNI YECHISH) ---
@dp.message(Command("cancel"))
async def cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu(message.from_user.id))

# --- QIDIRUV ---
@dp.message(F.text.isdigit())
async def search(message: types.Message):
    code = message.text
    if code in db_movies:
        await message.answer_video(db_movies[code])
    else:
        await message.answer("❌ Bunday kod yo'q!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
