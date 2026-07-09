import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Logging sozlash (Xatoliklarni terminalda ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# ----------------- ASOSIY SOZLAMALAR -----------------
BOT_TOKEN = "8824099204:AAFGjNB9-853psiXet3rWLNRjb678lyP80M"
ADMIN_ID =  8200259525 # BU_YERGA_O'ZINGNI_TELEGRAM_ID_RAQAMINGNI_YOZ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----------------- DATA BAZA CHIZMASI -----------------
db_users = set()
db_movies = {}
db_referals = {}

# --- DINAMIK MAJBURIY OBUNA RICHAGI ---
channel_config = {
    "status": False,      # True bo'lsa yoqiladi, False bo'lsa majburiy obuna o'chadi
    "username": "",       # Kanal nomi (masalan: @Xabarlar_Uz)
    "url": ""            # Linki
}

# ----------------- FSM STATES (XATOSIZ STRUKTURA) -----------------
class MovieStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()

class ChannelStates(StatesGroup):
    waiting_for_username = State()

# ----------------- REPLIKATLAR (KLAVIATURALAR) -----------------
def get_main_keyboard(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="💎 Premium")
    if user_id == ADMIN_ID:
        builder.button(text="📊 Boshqaruv")
    builder.adjust(2 if user_id == ADMIN_ID else 1)
    return builder.as_markup(resize_keyboard=True)

def get_admin_panel():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📈 Statistika")
    builder.button(text="🎬 Kontent boshqaruvi")
    builder.button(text="⚙️ Obuna Sozlamalari") # Siz so'ragan richag
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

# ----------------- OBUNA TEKSHIRISH -----------------
async def check_subscription(user_id: int) -> bool:
    if not channel_config["status"] or user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_config["username"], user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        logging.error(f"Kanal tekshirishda xatolik: {e}")
        return True # Server qotib qolmasligi uchun xato bo'lsa o'tkazib yuboradi

# ----------------- START BUYRUG'I -----------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # Har qanday chala qolgan eski holatlarni tozalaydi!
    user_id = message.from_user.id
    db_users.add(user_id)

    if not await check_subscription(user_id):
        builder = InlineKeyboardBuilder()
        builder.button(text="🍿 Kanalga obuna bo'lish", url=channel_config["url"])
        builder.button(text="✅ Tekshirish", callback_data="check_sub")
        builder.adjust(1)
        await message.answer("⚠️ **Botdan foydalanish uchun kanalimizga obuna bo'ling!**", parse_mode="Markdown", reply_markup=builder.as_markup())
        return

    await message.answer(
        f"👋 **Salom {message.from_user.first_name}! Kino kodini yuboring...**",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id):
        await callback.message.delete()
        await callback.message.answer("✅ Muvaffaqiyatli o'tdingiz! Kino kodini yuboring...", reply_markup=get_main_keyboard(user_id))
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# ----------------- KINO QIDIRISH (ENG TO'G'RI VARIANT) -----------------
@dp.message(F.text.isdigit())
async def search_movie(message: types.Message, state: FSMContext):
    # Agar admin hozir kino yuklash jarayonida bo'lsa, qidiruv funksiyasi ishlamaydi!
    current_state = await state.get_state()
    if current_state == MovieStates.waiting_for_code.state:
        return

    user_id = message.from_user.id
    if not await check_subscription(user_id):
        return

    code = message.text
    if code in db_movies:
        movie = db_movies[code]
        movie["views"] += 1
        
        builder = InlineKeyboardBuilder()
        builder.button(text="↗️ Ulashish", switch_inline_query=f"Kino kodi: {code}")
        
        caption_text = f"🎬 **Kino kodi:** {code}\n👁 **Ko'rishlar:** {movie['views']} ta"
        await message.answer_video(video=movie["file_id"], caption=caption_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await message.answer("❌ **Kino kodi topilmadi yoki xato kiritildi!**", parse_mode="Markdown")

# ----------------- ADMIN PANEL (BOSHQRUV) -----------------
@dp.message(F.text == "📊 Boshqaruv", F.from_user.id == ADMIN_ID)
async def admin_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("💼 **Admin paneliga xush kelibsiz!**", reply_markup=get_admin_panel())

@dp.message(F.text == "⬅️ Orqaga")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(F.text == "📈 Statistika", F.from_user.id == ADMIN_ID)
async def admin_stat(message: types.Message):
    stat_text = (
        "📊 **BOT STATISTIKASI**\n\n"
        f"👥 **Obunachilar:** {len(db_users)} ta\n"
        f"🎬 **Kinolar soni:** {len(db_movies)} ta\n"
        f"⚙️ **Majburiy obuna:** {'🟢 YOQILGAN' if channel_config['status'] else '❌ O\'CHIRILGAN'}"
    )
    await message.answer(stat_text, parse_mode="Markdown")

# --- MAJBURIY OBUNA RICHAGI (SIZ SO'RAGANDEK) ---
@dp.message(F.text == "⚙️ Obuna Sozlamalari", F.from_user.id == ADMIN_ID)
async def channel_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    status_text = "🔴 O'chirish" if channel_config["status"] else "🟢 Yoqish"
    builder.button(text=status_text, callback_data="toggle_channel")
    builder.button(text="✍️ Kanalni o'zgartirish", callback_data="change_channel")
    builder.adjust(1)
    
    text = (
        "⚙️ **MAJBURIY OBUNA RICHAGI**\n\n"
        f"📈 **Holati:** {'🟢 YOQILGAN' if channel_config['status'] else '❌ O\'CHIRILGAN'}\n"
        f"🔗 **Kanal:** `{channel_config['username'] if channel_config['username'] else 'Kanal kiritilmagan'}`"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "toggle_channel", F.from_user.id == ADMIN_ID)
async def toggle_channel(callback: types.CallbackQuery):
    if not channel_config["username"]:
        await callback.answer("⚠️ Oldin kanal kiritishingiz kerak!", show_alert=True)
        return
    channel_config["status"] = not channel_config["status"]
    await callback.answer("⚙️ Holat o'zgardi!")
    await channel_settings(callback.message)

@dp.callback_query(F.data == "change_channel", F.from_user.id == ADMIN_ID)
async def change_channel_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ChannelStates.waiting_for_username)
    await callback.message.answer("✍️ **Kanal userneymini yozing (Boshida @ bo'lsin, masalan: @Xabarlar_Uz):**")
    await callback.answer()

@dp.message(ChannelStates.waiting_for_username, F.from_user.id == ADMIN_ID)
async def change_channel_finish(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@"):
        await message.answer("❌ Xato! Kanal nomi `@` belgisi bilan boshlanishi kerak.")
        return
    
    channel_config["username"] = username
    channel_config["url"] = f"https://t.me/{username.replace('@', '')}"
    channel_config["status"] = True
    await state.clear()
    await message.answer(f"✅ **Majburiy obuna kanali kiritildi va yoqildi!**\n🔗 Kanal: {username}", reply_markup=get_admin_panel())

# --- KINO YUKLASH (MUTLAQO XATOSIZ YANGI STRUKTURA) ---
@dp.message(F.text == "🎬 Kontent boshqaruvi", F.from_user.id == ADMIN_ID)
async def content_manage(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📥 Kino yuklash")
    builder.button(text="📊 Boshqaruv")
    await message.answer("🎬 Kinolar bo'limi:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📥 Kino yuklash", F.from_user.id == ADMIN_ID)
async def start_upload(message: types.Message, state: FSMContext):
    await state.set_state(MovieStates.waiting_for_video)
    await message.answer("🎥 **Menga kinoni video formatida yuboring...**\n*(Eski zagruzkalar va xatoliklar butunlay o'chirildi)*")

@dp.message(MovieStates.waiting_for_video, F.video)
async def process_video_upload(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(MovieStates.waiting_for_code)
    await message.answer("🔢 **Endi ushbu kino uchun faqat raqamli kod kiriting:**\n*(Iltimos, boshqa matn aralashtirmang)*")

@dp.message(MovieStates.waiting_for_code)
async def process_code_upload(message: types.Message, state: FSMContext):
    # Agar adminga adashib kod o'rniga matn yuborib qo'ysa ham xato bermaydi, tekshiradi:
    if not message.text or not message.text.isdigit():
        await message.answer("❌ **Iltimos, faqat raqamlardan iborat kod yuboring!** (Masalan: 555)")
        return

    code = message.text
    data = await state.get_data()
    db_movies[code] = {"file_id": data["file_id"], "views": 0}
    await state.clear() # Holatni tozalaydi, bot endi "zagruzka" holatida qolib ketmaydi!
    
    await message.answer(f"✅ **Kino muvaffaqiyatli yuklandi!**\n🎬 Kino kodi: `{code}`", parse_mode="Markdown", reply_markup=get_admin_panel())

# --- POLLING ISHGA TUSHIRISH ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
