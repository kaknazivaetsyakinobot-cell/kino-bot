import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Logging sozlash (Xatoliklarni kuzatish uchun)
logging.basicConfig(level=logging.INFO)

# ----------------- SOZLAMALAR -----------------
BOT_TOKEN = "8824099204:AAFF3VkCeaD8qqS4vTNTZuIgwIpTYCOFq_o"
ADMIN_ID =  8200259525 # BU_YERGA_O'ZINGNI_TELEGRAM_ID_RAQAMINGNI_YOZ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----------------- MA'LUMOTLAR BAZASI (VAQTINCHALIK) -----------------
# Haqiqiy bazani Render o'chirib yubormasligi uchun operativ xotirada saqlaymiz
db_users = set()
db_premium_users = set()
db_movies = {}  # {kino_kod: {"file_id": id, "caption": matn, "views": 0}}
db_referals = {}  # {ref_id: {"name": nomi, "count": 0, "users": []}}

# ----------------- FSM STATES (INPUTLAR UCHUN) -----------------
class MovieStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()

class BroadcastStates(StatesGroup):
    waiting_for_msg = State()

class RefStates(StatesGroup):
    waiting_for_name = State()

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
    builder.button(text="📣 Xabar yuborish")
    builder.button(text="🎬 Kontent boshqaruvi")
    builder.button(text="🔗 Referallar")
    builder.button(text="⚙️ So'rovlar")
    builder.button(text="👥 Foydalanuvchilar")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# ----------------- START BUYRUG'I -----------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db_users.add(user_id)
    
    # Referal tizimini tekshirish
    args = message.text.split()
    if len(args) > 1:
        ref_code = args[1]
        if ref_code in db_referals and user_id not in db_referals[ref_code]["users"]:
            db_referals[ref_code]["count"] += 1
            db_referals[ref_code]["users"].append(user_id)

    await message.answer(
        f"👋 **Assalomu alaykum {message.from_user.first_name} botimizga xush kelibsiz.**\n\n"
        "🎬 Kino kodini yuboring...",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )

# ----------------- KINO QIDIRISH -----------------
@dp.message(F.text.isdigit())
async def search_movie(message: types.Message):
    code = message.text
    if code in db_movies:
        movie = db_movies[code]
        movie["views"] += 1
        
        # Inline tugmalar
        builder = InlineKeyboardBuilder()
        builder.button(text="💎 Premium", callback_data="buy_premium")
        builder.button(text="↗️ Ulashish", switch_inline_query=f"Kino kodi: {code}")
        builder.adjust(1, 1)
        
        caption_text = (
            f"🎬 **Kino kodi:** {code}\n"
            f"🤖 **Botimiz:** @{(await bot.get_me()).username}\n"
            f"👁 **Ko'rishlar:** {movie['views']} ta"
        )
        
        await message.answer_video(
            video=movie["file_id"],
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer("❌ **Kino kodi noto'g'ri yubordingiz!**", parse_mode="Markdown")

# ----------------- PREMIUM BO'LIMI -----------------
@dp.message(F.text == "💎 Premium")
@dp.callback_query(F.data == "buy_premium")
async def show_premium(event: types.Message | types.CallbackQuery):
    text = (
        "💎 **PREMIUM OBUNA**\n\n"
        "Premium orqali quyidagilarga ega bo'lasiz:\n"
        "• Kanallarga obuna bo'lmasdan kino ko'rish\n"
        "• Reklamalarsiz foydalanish\n"
        "• Yuqori sifatda tomosha qilish\n\n"
        "📋 **Quyidagi tariflardan birini tanlang:**"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="1 Kunlik Obuna - 5 000 so'm", callback_data="tarif_1")
    builder.button(text="10 Kunlik Premium - 10 000 so'm", callback_data="tarif_10")
    builder.button(text="VIP tarif - 15 000 so'm", callback_data="tarif_vip")
    builder.adjust(1)
    
    if isinstance(event, types.Message):
        await event.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("tarif_"))
async def process_tarif(callback: types.CallbackQuery):
    tarif_name = "1 Kunlik Obuna" if "1" in callback.data else "10 Kunlik Premium" if "10" in callback.data else "VIP tarif"
    narx = "5 000 so'm" if "1" in callback.data else "10 000 so'm" if "10" in callback.data else "15 000 so'm"
    
    text = (
        "💳 **PREMIUM OBUNA - TO'LOV MA'LUMOTLARI**\n\n"
        f"📊 **Tarif:** {tarif_name}\n"
        f"💰 **Narx:** {narx}\n"
        "💳 **Karta raqami:** `5614 6840 9146 5672`\n"
        "👤 **Karta egasi:** NOZANIN ISMATULLAYEVA\n\n"
        "⚠️ **Diqqat:** To'lovni amalga oshirgach, chekni adminga yuboring."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="buy_premium")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())

# ----------------- ADMIN PANEL LOGIKASI -----------------
@dp.message(F.text == "📊 Boshqaruv", F.from_user.id == ADMIN_ID)
async def admin_menu(message: types.Message):
    await message.answer("💼 **Admin paneliga xush kelibsiz!**", reply_markup=get_admin_panel())

@dp.message(F.text == "⬅️ Orqaga")
async def back_to_main(message: types.Message):
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(F.text == "增 Statistika", F.from_user.id == ADMIN_ID)
async def admin_stat(message: types.Message):
    stat_text = (
        "📊 **BOT STATISTIKASI**\n\n"
        f"👥 **Obunachilar soni:** {len(db_users)} ta\n"
        f"🔥 **Faol obunachilar:** {len(db_users)} ta\n"
        f"💎 **Premium a'zolar:** {len(db_premium_users)} ta\n"
        f"🎬 **Kinolar soni:** {len(db_movies)} ta"
    )
    await message.answer(stat_text, parse_mode="Markdown")

# --- KINO YUKLASH ---
@dp.message(F.text == "🎬 Kontent boshqaruvi", F.from_user.id == ADMIN_ID)
async def content_manage(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📥 Kino yuklash")
    builder.button(text="⬅️ Orqaga")
    await message.answer("🎬 Kinolar bo'limidasiz:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📥 Kino yuklash", F.from_user.id == ADMIN_ID)
async def start_upload(message: types.Message, state: FSMContext):
    await state.set_state(MovieStates.waiting_for_video)
    await message.answer("🎥 **Menga kinoni (video formatida) yuboring...**", parse_mode="Markdown")

@dp.message(MovieStates.waiting_for_video, F.video)
async def process_video_upload(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(MovieStates.waiting_for_code)
    await message.answer("🔢 **Endi ushbu kino uchun kod kiriting:**", parse_mode="Markdown")

@dp.message(MovieStates.waiting_for_code, F.text.isdigit())
async def process_code_upload(message: types.Message, state: FSMContext):
    code = message.text
    data = await state.get_data()
    
    db_movies[code] = {"file_id": data["file_id"], "views": 0}
    await state.clear()
    
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔄 Yana Kino Yuklash")
    builder.button(text="📊 Boshqaruv")
    
    await message.answer(f"✅ **Kino muvaffaqiyatli yuklandi!**\n🔑 **Kino kodi:** {code}", parse_mode="Markdown", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "🔄 Yana Kino Yuklash", F.from_user.id == ADMIN_ID)
async def upload_more(message: types.Message, state: FSMContext):
    await start_upload(message, state)

# --- REFERAL PANELI ---
@dp.message(F.text == "🔗 Referallar", F.from_user.id == ADMIN_ID)
async def referal_panel(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Havola yaratish")
    builder.button(text="⬅️ Orqaga")
    
    ref_text = "🔗 **Referal bo'limi**\n\n"
    if db_referals:
        for r_id, r_data in db_referals.items():
            ref_text += f"📌 **Nomi:** {r_data['name']}\n👥 **Kelganlar:** {r_data['count']} ta\n"
    else:
        ref_text += "Hali hech qanday referal havola yaratilmagan."
        
    await message.answer(ref_text, parse_mode="Markdown", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "➕ Havola yaratish", F.from_user.id == ADMIN_ID)
async def create_ref_start(message: types.Message, state: FSMContext):
    await state.set_state(RefStates.waiting_for_name)
    await message.answer("✍️ **Havola uchun nom kiriting (Masalan: Instagram, TikTok):**", parse_mode="Markdown")

@dp.message(RefStates.waiting_for_name)
async def create_ref_finish(message: types.Message, state: FSMContext):
    name = message.text
    ref_id = f"ref_{len(db_referals) + 1}"
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={ref_id}"
    
    db_referals[ref_id] = {"name": name, "count": 0, "users": []}
    await state.clear()
    
    await message.answer(
        f"✅ **Referal havola yaratildi!**\n\n"
        f"📌 **Nomi:** {name}\n"
        f"🔗 **Havola:** {link}",
        reply_markup=get_admin_panel()
    )

# --- REKLAMA TARQATISH ---
@dp.message(F.text == "📣 Xabar yuborish", F.from_user.id == ADMIN_ID)
async def start_broadcast(message: types.Message, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_for_msg)
    await message.answer("📝 **Foydalanuvchilarga yuboriladigan xabarni (matn, rasm yoki video) kiriting:**")

@dp.message(BroadcastStates.waiting_for_msg)
async def do_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    count = 0
    for user_id in db_users:
        try:
            await message.copy_to(chat_id=user_id)
            count += 1
            await asyncio.sleep(0.05)  # Telegram spam blokiga tushmaslik uchun
        except Exception:
            continue
    await message.answer(f"🚀 **Xabar {count} ta foydalanuvchiga muvaffaqiyatli yuborildi!**", parse_mode="Markdown", reply_markup=get_admin_panel())

# ----------------- SERVER ISHGA TUSHIRISH -----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
