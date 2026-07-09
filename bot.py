import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Logging sozlash
logging.basicConfig(level=logging.INFO)

# ----------------- ASOSIY SOZLAMALAR -----------------
BOT_TOKEN = "8824099204:AAH-rHIOhXiNP8T6C37hDpE-RYHRQ-6a1-A"
ADMIN_ID = 8200259525  # Mashhurbek profili

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ----------------- OPERATIV MA'LUMOTLAR BAZASI -----------------
db_users = set()
db_premium_users = set()  # Premium sotib olganlar ID-si
db_movies = {}  # {kino_kod: {"file_id": id, "views": 0}}
db_referals = {}  # {ref_id: {"name": nomi, "count": 0, "users": []}}

# --- DINAMIK MAJBURIY OBUNA SOZLAMALARI ---
channel_config = {
    "status": False,      
    "username": "",       
    "url": ""            
}

# ----------------- FSM STATES -----------------
class MovieStates(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()

class BroadcastStates(StatesGroup):
    waiting_for_msg = State()

class RefStates(StatesGroup):
    waiting_for_name = State()

class ChannelStates(StatesGroup):
    waiting_for_username = State()

class PremiumStates(StatesGroup):
    waiting_for_receipt = State()

# ----------------- KLAVIATURALAR -----------------
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

# ----------------- OBUNA TEKSHIRISH -----------------
async def check_subscription(user_id: int) -> bool:
    if user_id in db_premium_users or user_id == ADMIN_ID or not channel_config["status"]:
        return True
    try:
        member = await bot.get_chat_member(chat_id=channel_config["username"], user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        logging.error(f"Obuna tekshirishda xatolik: {e}")
        return True 

# ----------------- START BUYRUG'I -----------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() 
    user_id = message.from_user.id
    db_users.add(user_id)
    
    args = message.text.split()
    if len(args) > 1:
        ref_code = args[1]
        if ref_code in db_referals and user_id not in db_referals[ref_code]["users"]:
            db_referals[ref_code]["count"] += 1
            db_referals[ref_code]["users"].append(user_id)

    if not await check_subscription(user_id):
        builder = InlineKeyboardBuilder()
        builder.button(text="🍿 Kanalga obuna bo'lish", url=channel_config["url"])
        builder.button(text="✅ Tekshirish", callback_data="check_sub")
        builder.adjust(1)
        await message.answer("⚠️ **Botdan foydalanish uchun homiy kanalimizga obuna bo'lishingiz shart!**", parse_mode="Markdown", reply_markup=builder.as_markup())
        return

    await message.answer(f"👋 **Assalomu alaykum {message.from_user.first_name} botimizga xush kelibsiz.**\n\n🎬 Kino kodini yuboring...", parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if await check_subscription(user_id):
        await callback.message.delete()
        await callback.message.answer("✅ Muvaffaqiyatli o'tdingiz! Kino kodini yuboring...", reply_markup=get_main_keyboard(user_id))
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

# ----------------- KINO QIDIRISH TIZIMI -----------------
@dp.message(F.text.isdigit())
async def search_movie(message: types.Message, state: FSMContext):
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
        
        caption_text = f"🎬 **Kino kodi:** {code}\n🤖 **Botimiz:** @{(await bot.get_me()).username}\n👁 **Ko'rishlar:** {movie['views']} ta"
        await message.answer_video(video=movie["file_id"], caption=caption_text, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await message.answer("❌ **Kino kodi noto'g'ri yubordingiz!**", parse_mode="Markdown")

# ----------------- PREMIUM INTERFEYS VA AVTO-CHEK -----------------
@dp.message(F.text == "💎 Premium")
@dp.callback_query(F.data == "buy_premium")
async def show_premium(event: types.Message | types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "💎 **PREMIUM OBUNA**\n\nPremium orqali kanallarga obuna bo'lmasdan reklamalarsiz kino ko'rasiz.\n\n📋 **Tariflardan birini tanlang:**"
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
async def process_tarif(callback: types.CallbackQuery, state: FSMContext):
    tarif_name = callback.data.split("_")[1]
    await state.update_data(chosen_tarif=tarif_name, user_id=callback.from_user.id)
    
    text = (
        "💳 **PREMIUM OBUNA - TO'LOV**\n\n"
        "💳 **Karta raqami:** `5614 6840 9146 5672`\n"
        "👤 **Karta egasi:** ISMATULLAYEVA NOZANIN\n\n"
        "📸 **To'lovni bajaring va shu yerga faqat to'lov chekini (rasmini) yuboring!**"
    )
    await state.set_state(PremiumStates.waiting_for_receipt)
    await callback.message.edit_text(text, parse_mode="Markdown")

@dp.message(PremiumStates.waiting_for_receipt, F.photo)
async def handle_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    
    # Adminga tasdiqlash uchun yuborish
    admin_builder = InlineKeyboardBuilder()
    admin_builder.button(text="✅ Tasdiqlash", callback_data=f"approve_{data['user_id']}")
    admin_builder.button(text="❌ Rad etish", callback_data=f"reject_{data['user_id']}")
    admin_builder.adjust(2)
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 **Yangi Premium To'lov Cheki!**\n\n👤 **Foydalanuvchi:** {message.from_user.full_name}\n🆔 **ID:** `{data['user_id']}`\n📋 **Tarif:** {data['chosen_tarif'].upper()}",
        parse_mode="Markdown",
        reply_markup=admin_builder.as_markup()
    )
    await message.answer("✅ **Chekingiz qabul qilindi! Admin tekshirganidan so'ng premium yoqiladi.**")

# --- ADMIN TASDIQLASH PROSESSI ---
@dp.callback_query(F.data.startswith("approve_"))
async def approve_premium(callback: types.CallbackQuery):
    target_user_id = int(callback.data.split("_")[1])
    db_premium_users.add(target_user_id)
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟢 **Tasdiqlandi va Premium berildi!**", reply_markup=None)
    try:
        await bot.send_message(chat_id=target_user_id, text="🎉 **Tabriklaymiz! To'lovingiz tasdiqlandi, sizga Premium obuna yoqildi!**")
    except: pass

@dp.callback_query(F.data.startswith("reject_"))
async def reject_premium(callback: types.CallbackQuery):
    target_user_id = int(callback.data.split("_")[1])
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n🔴 **To'lov rad etildi!**", reply_markup=None)
    try:
        await bot.send_message(chat_id=target_user_id, text="❌ **Siz yuborgan to'lov cheki admin tomonidan rad etildi! Iltimos, qayta tekshirib to'g'ri chekni yuboring.**")
    except: pass

# ----------------- ADMIN PANEL VA STRUKTURALAR -----------------
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
    await message.answer(f"📊 **BOT STATISTIKASI**\n\n👥 **Obunachilar:** {len(db_users)} ta\n🎬 **Kinolar:** {len(db_movies)} ta\n⚙️ **Majburiy obuna:** {'🟢 YOQILGAN' if channel_config['status'] else '❌ O\'CHIRILGAN'}", parse_mode="Markdown")

# --- MAJBURIY OBUNA RICHAGI ---
@dp.message(F.text == "⚙️ Obuna Sozlamalari", F.from_user.id == ADMIN_ID)
async def channel_settings(message: types.Message):
    builder = InlineKeyboardBuilder()
    status_text = "🔴 O'chirish" if channel_config["status"] else "🟢 Yoqish"
    builder.button(text=status_text, callback_data="toggle_channel")
    builder.button(text="✍️ Kanalni o'zgartirish", callback_data="change_channel")
    builder.adjust(1)
    await message.answer(f"⚙️ **MAJBURIY OBUNA RICHAGI**\n\n📈 **Holati:** {'🟢 YOQILGAN' if channel_config['status'] else '❌ O\'CHIRILGAN'}\n🔗 **Kanal:** `{channel_config['username'] if channel_config['username'] else 'Yo\'q'}`", parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "toggle_channel", F.from_user.id == ADMIN_ID)
async def toggle_channel(callback: types.CallbackQuery):
    if not channel_config["username"]:
        await callback.answer("⚠️ Oldin kanal qo'shing!", show_alert=True)
        return
    channel_config["status"] = not channel_config["status"]
    await callback.answer("⚙️ O'zgardi!")
    await channel_settings(callback.message)

@dp.callback_query(F.data == "change_channel", F.from_user.id == ADMIN_ID)
async def change_channel_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ChannelStates.waiting_for_username)
    await callback.message.answer("✍ **Kanal userneymini yozing (Boshida @ bo'lsin):**")
    await callback.answer()

@dp.message(ChannelStates.waiting_for_username, F.from_user.id == ADMIN_ID)
async def change_channel_finish(message: types.Message, state: FSMContext):
    username = message.text.strip()
    if not username.startswith("@"):
        await message.answer("❌ Xato! @ bo'lishi shart.")
        return
    channel_config["username"] = username
    channel_config["url"] = f"https://t.me/{username.replace('@', '')}"
    channel_config["status"] = True
    await state.clear()
    await message.answer(f"✅ Kanal saqlandi va yoqildi: {username}", reply_markup=get_admin_panel())

# --- KINO YUKLASH ---
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
        await message.answer("❌ **Iltimos, faqat raqamlardan iborat kod yuboring!**")
        return
    code = message.text
    data = await state.get_data()
    db_movies[code] = {"file_id": data["file_id"], "views": 0}
    await state.clear()
    await message.answer(f"✅ **Kino yuklandi!**\n🔑 Kod: `{code}`", parse_mode="Markdown", reply_markup=get_admin_panel())

# --- RASMDAGIDEK REFERALLAR RO'YXATI VA HAVOLA YARATISH ---
@dp.message(F.text == "🔗 Referallar", F.from_user.id == ADMIN_ID)
async def referal_panel(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Havola yaratish")
    
    # Xuddi rasmdagidek ishlayotgan har bir referalni alohida tugma qilib chiqaramiz
    if db_referals:
        for r_id, r_data in db_referals.items():
            builder.button(text=f"📌 {r_data['name']} • 👥 {r_data['count']}")
            
    builder.button(text="📊 Boshqaruv")
    builder.adjust(1) # Har bir referal rasmdagidek alohida qatorda chiqadi
    
    await message.answer("👥 **Ishlayotgan faol referal havolalaringiz ro'yxati:**", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "➕ Havola yaratish", F.from_user.id == ADMIN_ID)
async def create_ref_start(message: types.Message, state: FSMContext):
    await state.set_state(RefStates.waiting_for_name)
    await message.answer("✍️ **Havola uchun nom kiriting (Masalan: Abbosbek):**")

@dp.message(RefStates.waiting_for_name, F.from_user.id == ADMIN_ID)
async def create_ref_finish(message: types.Message, state: FSMContext):
    name = message.text.strip()
    ref_id = f"ref_{len(db_referals) + 1}"
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={ref_id}"
    
    db_referals[ref_id] = {"name": name, "count": 0, "users": []}
    await state.clear()
    
    await message.answer(f"✅ **Referal havola yaratildi!**\n\n📌 **Nomi:** {name}\n🔗 **Havola:** `{link}`", parse_mode="Markdown", reply_markup=get_admin_panel())

# --- REKLAMA ---
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
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"🚀 **Reklama {count} ta foydalanuvchiga muvaffaqiyatli yuborildi!**", reply_markup=get_admin_panel())

# --- RUN POLLING ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
