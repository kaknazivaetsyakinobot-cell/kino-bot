import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Logging sozlash (Xatoliklarni terminalda kuzatish)
logging.basicConfig(level=logging.INFO)

# ----------------- ASOSIY SOZLAMALAR -----------------
BOT_TOKEN = "8824099204:AAEs2Gf8J_j6LeHgZdy81HCQbf-b5fCo1uQ"
ADMIN_ID = 8200259525  # BU_YERGA_O'ZINGNI_TELEGRAM_ID_RAQAMINGNI_YOZ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----------------- OPERATIV MA'LUMOTLAR BAZASI -----------------
db_users = set()
db_premium_users = set()
db_movies = {}  # {kino_kod: {"file_id": id, "views": 0}}
db_referals = {}  # {ref_id: {"name": nomi, "count": 0, "users": []}}

# --- DINAMIK MAJBURIY OBUNA SOZLAMALARI ---
channel_config = {
    "status": False,      # True - yoqilgan, False - o'chirilgan
    "username": "",       # Kanal userneymi (@ bilan)
    "url": ""            # Kanal havolasi
}

# ----------------- FSM STATES (KIRISH JALAYONLARI UCHUN) -----------------
class MovieStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()

class BroadcastStates(StatesGroup):
    waiting_for_msg = State()

class RefStates(StatesGroup):
    waiting_for_name = State()

class ChannelStates(StatesGroup):
    waiting_for_username = State()

# ----------------- KLAVIATURALAR (REPLIKATLAR) -----------------
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
    builder.button(text="⚙️ Obuna Sozlamalari")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

# ----------------- MAJBURIY OBUNA TEKSHIRISH TIZIMI -----------------
async def check_subscription(user_id: int) -> bool:
    if not channel_config["status"] or user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_config["username"], user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        logging.error(f"Obuna tekshirishda xatolik: {e}")
        return True # Agar kanal topilmasa bot qotib qolmasligi uchun o'tkazib yuboradi

# ----------------- START BUYRUG'I -----------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # Har qanday chala qolgan jarayonni srazu o'chiradi
    user_id = message.from_user.id
    db_users.add(user_id)
    
    # Referal link orqali kirgandagi hisob-kitob
    args = message.text.split()
    if len(args) > 1:
        ref_code = args[1]
        if ref_code in db_referals and user_id not in db_referals[ref_code]["users"]:
            db_referals[ref_code]["count"] += 1
            db_referals[ref_code]["users"].append(user_id)

    # Majburiy obunani tekshirish
    if not await check_subscription(user_id):
        builder = InlineKeyboardBuilder()
        builder.button(text="🍿 Kanalga obuna bo'lish", url=channel_config["url"])
        builder.button(text="✅ Tekshirish", callback_data="check_sub")
        builder.adjust(1)
        
        await message.answer(
            "⚠️ **Botdan foydalanish uchun homiy kanalimizga obuna bo'lishingiz shart!**",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )
        return

    await message.answer(
        f"👋 **Assalomu alaykum {message.from_user.first_name} botimizga xush kelibsiz.**\n\n🎬 Kino kodini yuboring...",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id)
    )

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id):
        await callback.message.delete()
        await callback.message.answer(
            "✅ Muvaffaqiyatli o'tdingiz! Kino kodini yuboring...",
            reply_markup=get_main_keyboard(user_id)
        )
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# ----------------- KINO QIDIRISH TIZIMI -----------------
@dp.message(F.text.isdigit())
async def search_movie(message: types.Message, state: FSMContext):
    # Agar admin kino yuklayotgan bo'lsa, qidiruv ishlamaydi
    current_state = await state.get_state()
    if current_state in [MovieStates.waiting_for_code.state, MovieStates.waiting_for_video.state]:
        return

    user_id = message.from_user.id
    if not await check_subscription(user_id):
        return

    code = message.text
    if code in db_movies:
        movie = db_movies[code]
        movie["views"] += 1
        
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

# ----------------- PREMIUM INTEGRATSIYA -----------------
@dp.message(F.text == "💎 Premium")
@dp.callback_query(F.data == "buy_premium")
async def show_premium(event: types.Message | types.CallbackQuery):
    text = (
        "💎 **PREMIUM OBUNA**\n\n"
        "Premium orqali quyidagilarga ega bo'lasiz:\n"
        "• Kanallarga obuna bo'lmasdan kino ko'rish\n"
        "• Reklamalarsiz foydalanish\n\n"
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
    text = (
        "💳 **PREMIUM OBUNA - TO'LOV MA'LUMOTLARI**\n\n"
        "💳 **Karta raqami:** `6262 5700 0130 3561`\n"
        "👤 **Karta egasi:** Fuzuliddin Rajabov\n\n"
        "⚠️ **Diqqat:** To'lovni amalga oshirgach, chekni adminga yuboring."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="buy_premium")
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())

# ----------------- ADMIN BOSHQUV PANELI -----------------
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
        f"👥 **Obunachilar soni:** {len(db_users)} ta\n"
        f"🎬 **Kinolar soni:** {len(db_movies)} ta\n"
        f"⚙️ **Majburiy obuna:** {'🟢 YOQILGAN' if channel_config['status'] else '❌ O\'CHIRILGAN'} ({channel_config['username']})"
    )
    await message.answer(stat_text, parse_mode="Markdown")

# --- MAJBURIY OBUNA RICHAGI (DINAMIK) ---
@dp.message(F.text == "⚙️ Obuna Sozlamalari", F.from_user.id == ADMIN_ID)
async def channel_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    status_text = "🔴 O'chirish" if channel_config["status"] else "🟢 Yoqish"
    builder.button(text=status_text, callback_data="toggle_channel")
    builder.button(text="✍️ Kanalni o'zgartirish", callback_data="change_channel")
    builder.adjust(1)
    
    text = (
        "⚙️ **MAJBURIY OBUNA RICHAGI**\n\n"
        f"📈 **Hozirgi holat:** {'🟢 YOQILGAN' if channel_config['status'] else '❌ O\'CHIRILGAN'}\n"
        f"🔗 **Hozirgi kanal:** `{channel_config['username'] if channel_config['username'] else 'Kanal qo\'shilmagan'}`"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "toggle_channel", F.from_user.id == ADMIN_ID)
async def toggle_channel(callback: types.CallbackQuery):
    if not channel_config["username"]:
        await callback.answer("⚠️ Oldin kanal qo'shishingiz kerak!", show_alert=True)
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

# --- KINO YUKLASH BO'LIMI ---
@dp.message(F.text == "🎬 Kontent boshqaruvi", F.from_user.id == ADMIN_ID)
async def content_manage(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="📥 Kino yuklash")
    builder.button(text="📊 Boshqaruv")
    await message.answer("🎬 Kinolar bo'limi:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "📥 Kino yuklash", F.from_user.id == ADMIN_ID)
async def start_upload(message: types.Message, state: FSMContext):
    await state.set_state(MovieStates.waiting_for_video)
    await message.answer("🎥 **Menga kinoni video formatida yuboring...**")

@dp.message(MovieStates.waiting_for_video, F.video)
async def process_video_upload(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(MovieStates.waiting_for_code)
    await message.answer("🔢 **Endi ushbu kino uchun faqat raqamli kod kiriting:**")

@dp.message(MovieStates.waiting_for_code)
async def process_code_upload(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("❌ **Iltimos, faqat raqamlardan iborat kod yuboring!** (Masalan: 555)")
        return

    code = message.text
    data = await state.get_data()
    db_movies[code] = {"file_id": data["file_id"], "views": 0}
    await state.clear()
    await message.answer(f"✅ **Kino yuklandi!**\n🔑 Kod: `{code}`", parse_mode="Markdown", reply_markup=get_admin_panel())

# --- REFERAL TIZIMI BO'LIMI ---
@dp.message(F.text == "🔗 Referallar", F.from_user.id == ADMIN_ID)
async def referal_panel(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Havola yaratish")
    builder.button(text="📊 Boshqaruv")
    
    ref_text = "🔗 **REFERAL LINKLAR RO'YXATI**\n\n"
    if db_referals:
        for r_id, r_data in db_referals.items():
            ref_text += f"📌 **Nomi:** {r_data['name']}\n👥 **Kelganlar:** {r_data['count']} ta\n\n"
    else:
        ref_text += "Hali hech qanday referal havola yaratilmagan."
        
    await message.answer(ref_text, parse_mode="Markdown", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "➕ Havola yaratish", F.from_user.id == ADMIN_ID)
async def create_ref_start(message: types.Message, state: FSMContext):
    await state.set_state(RefStates.waiting_for_name)
    await message.answer("✍️ **Havola uchun nom kiriting (Masalan: TikTok_Kino):**")

@dp.message(RefStates.waiting_for_name, F.from_user.id == ADMIN_ID)
async def create_ref_finish(message: types.Message, state: FSMContext):
    name = message.text
    ref_id = f"ref_{len(db_referals) + 1}"
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={ref_id}"
    
    db_referals[ref_id] = {"name": name, "count": 0, "users": []}
    await state.clear()
    
    await message.answer(
        f"✅ **Referal havola yaratildi!**\n\n📌 **Nomi:** {name}\n🔗 **Havola:** `{link}`",
        parse_mode="Markdown",
        reply_markup=get_admin_panel()
    )

# --- REKLAMA TARQATISH TIZIMI ---
@dp.message(F.text == "📣 Xabar yuborish", F.from_user.id == ADMIN_ID)
async def start_broadcast(message: types.Message, state: FSMContext):
    await state.set_state(BroadcastStates.waiting_for_msg)
    await message.answer("📝 **Foydalanuvchilarga yuboriladigan reklama xabarini kiriting:**")

@dp.message(BroadcastStates.waiting_for_msg, F.from_user.id == ADMIN_ID)
async def do_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    count = 0
    for user_id in db_users:
        try:
            await message.copy_to(chat_id=user_id)
            count += 1
            await asyncio.sleep(0.05)  # Telegram spam cheklovidan o'tish uchun
        except:
            continue
    await message.answer(f"🚀 **Reklama {count} ta foydalanuvchiga muvaffaqiyatli yuborildi!**", reply_markup=get_admin_panel())

# --- POLLING REJIMINI ISHGA TUSHIRISH ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
