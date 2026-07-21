import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)

# Tokeningiz va Admin ID raqamingizni shu yerga yozing
TOKEN = "8938258523:AAFz7tEXBTb28bZrsFdivjl8vgD_l0iUMl4"
ADMIN_ID = (8159829976) # O'z Telegram ID raqamingizni yozing (masalan: 582910492)

bot = Bot(token=TOKEN)
router = Router()

# Global xotirada narx va balanslar (keyinchalik bazaga ulanadi)
ADMIN_SETTINGS = {
    "price_per_star": 210,
    "user_balance": 15000,  # Test balansi
}


# FSM Holatlari (Qadamlar)
class OrderState(StatesGroup):
    waiting_for_username = State()
    waiting_for_custom_amount = State()
    confirming_order = State()
    admin_change_price = State()
    admin_add_balance = State()


# ---------------------------------------------------------
# 1. /START KOMANDASI (ASOSIY MENYU VA ADMIN TUGMA)
# ---------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    # Foydalanuvchi admin ekanligini tekshirish
    is_admin = message.from_user.id == ADMIN_ID

    text = (
        f"🤖 <b>Ａ𝘀𝘀𝗮𝗹𝗼𝗺  𝗮𝗹𝗮𝘆𝗸𝘂𝗺,</b> {message.from_user.first_name}. <b>𝗯𝗼𝘁𝗴𝗮  𝘅𝘂𝘀𝗵  𝗸𝗲𝗹𝗶𝗯𝘀𝗶𝘇!</b>\n\n"
        f"🧑‍💻 <b>𝗕𝗼𝘁  𝗼𝗿𝗾𝗮𝗹𝗶  «⭐️ 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺  𝗦𝘁𝗮𝗿𝘀»  𝘃𝗮  «🌟 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺  𝗣𝗿𝗲𝗺𝗶𝘂𝗺»  𝗹𝗮𝗿𝗻𝗶  𝘅𝗮𝗿𝗶𝗱  𝗾𝗶𝗹𝗶𝘀𝗵𝗶𝗻𝗴𝗶𝘇  𝗺𝘂𝗺𝗸𝗶𝗻</b>\n\n"
        f"<b>𝗤𝘂𝘆𝗶𝗱𝗮𝗴𝗶  𝗺𝗲𝗻𝘆𝘂𝗱𝗮𝗻  𝗸𝗲𝗿𝗮𝗸𝗹𝗶𝘀𝗶𝗻𝗶  𝘁𝗮𝗻𝗹𝗮𝗻𝗴</b>\n👇"
    )

    keyboard_buttons = [
        [
            InlineKeyboardButton(
                text="⭐ 𝑆𝑇𝐴𝑅𝑆 𝑂𝐿𝐼𝑆𝐻", callback_data="menu_stars"
            ),
            InlineKeyboardButton(
                text="🌟 𝑃𝑅𝐸𝑀𝐼𝑈𝑀 𝑂𝐿𝐼𝑆𝐻", callback_data="menu_premium"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎁 𝐺𝐼𝐹𝑇 𝑂𝐿𝐼𝑆𝐻", callback_data="menu_gift"
            ),
            InlineKeyboardButton(
                text="🏆 𝑇𝑂𝑃 𝑅EY𝑇𝐼𝑁𝐺", callback_data="menu_top"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 𝑆𝑇𝐴𝑇𝐼𝑆𝑇𝐼𝐾𝐴𝑀", callback_data="menu_stats"
            ),
            InlineKeyboardButton(
                text="👤 𝑃𝑅𝑂𝐹𝐼𝐿", callback_data="menu_profile"
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"💳 𝐵𝐴𝐿𝐴Ն𝑆: {ADMIN_SETTINGS['user_balance']:,} 𝑠𝑜'𝑚",
                callback_data="menu_balance",
            )
        ],
    ]

    # Agar foydalanuvchi admin bo'lsa, maxsus admin panel tugmasini qo'shamiz
    if is_admin:
        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="⚙️ 𝐴𝐷𝑀𝐼Ն  𝑃𝐴Ն𝐸𝐿", callback_data="admin_panel"
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ---------------------------------------------------------
# 2. STARS OLISH MENYUSI (USERNAME SO'RASH) VA "O'ZIM UCHUN"
# ---------------------------------------------------------
@router.callback_query(F.data == "menu_stars")
async def stars_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderState.waiting_for_username)
    text = (
        f"⭐ <b>𝑆𝑡𝑎𝑟𝑠  𝘅𝗮𝗿𝗶𝗱  𝗾𝗶𝗹𝗶𝘀𝗵</b>\n\n"
        f"🔎 <b>𝑆𝑡𝑎𝑟𝑠  𝘆𝘂𝗯𝗼𝗿𝗶𝗹𝗶𝘀𝗵𝗶  𝗸𝗲𝗿𝗮𝗸  𝗯𝗼'𝗹𝗴𝗮𝗻  𝗳𝗼𝘆𝗱𝗮𝗹𝗮𝗻𝘂𝘃𝗰𝗵𝗶𝗻𝗶𝗻𝗴  𝘂𝘀𝗲𝗿𝗻𝗮𝗺𝗲'𝗶𝗻𝗶  𝗸𝗶𝗿𝗶𝘁𝗶𝗻𝗴:</b>\n\n"
        f"👇 <b>𝑀𝑖𝑠𝗼𝗹:</b> @xxxxxxxxxx132x"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 O'zim uchun", callback_data="for_myself"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 𝑂𝑟𝗾𝗮𝗴𝗮", callback_data="back_to_start"
                )
            ],
        ]
    )
    await callback.message.edit_text(
        text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    await callback.answer()


# "O'zim uchun" tugmasi bosilganda avtomatik o'z username'ini oladi
@router.callback_query(F.data == "for_myself")
async def for_myself_handler(callback: CallbackQuery, state: FSMContext):
    username = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else f"id:{callback.from_user.id}"
    )
    await state.update_data(username=username)

    search_msg = await callback.message.answer(
        "<b>𝐹𝑜𝑦𝑑𝑎𝑙𝑎𝑛𝑢𝑣𝑐ℎ𝑖  𝑞𝑖𝑑𝑖𝑟𝑖𝑙𝑚𝑜𝑞𝑑𝑎</b>🔍", parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(1.2)
    await search_msg.delete()

    await show_amount_selection(callback.message, username, state)
    await callback.answer()


# ---------------------------------------------------------
# 3. USERNAME QABUL QILISH VA MIQDOR TANLASHGA O'TISH
# ---------------------------------------------------------
@router.message(OrderState.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)

    search_msg = await message.answer(
        "<b>𝐹𝑜𝑦𝑑𝑎𝑙𝑎𝑛𝑢𝑣𝑐ℎ𝑖  𝑞𝑖𝑑𝑖𝑟𝑖𝑙𝑚𝑜𝑞𝑑𝑎</b>🔍", parse_mode=ParseMode.HTML
    )
    await asyncio.sleep(1.2)
    await search_msg.delete()

    await show_amount_selection(message, username, state)


async def show_amount_selection(message: Message, username: str, state: FSMContext):
    text = (
        f"⭐ <b>𝑇𝑒𝑙𝑒𝑔𝑟𝗮𝗺  𝑆𝑡𝑎𝑟𝑠  𝑏𝑢𝑦𝑢𝑟𝑡𝑚𝑎</b>\n\n"
        f"👤 <b>𝑄𝑎𝑏𝑢𝑙  𝑞𝑖𝑙𝑢𝑣𝑐ℎ𝑖:</b> {username}\n\n"
        f"🔻 <b>𝑀𝑖𝑛𝑖𝑚𝑎𝑙:</b> 50\n"
        f"🔺 <b>𝑀𝑎𝑘𝑠𝑖𝑚𝑎𝑙:</b> 480\n\n"
        f"⭐ <b>𝐾𝑒𝑟𝑎𝑘𝑙𝑖  𝑆𝑡𝑎𝑟𝑠  𝗺𝗶𝗾𝗱𝗼𝗿𝗶𝗻𝗶  𝘁𝗮𝗻𝗹𝗮𝗻𝗴  𝘆𝗼𝗸𝑖  𝗿𝗮𝗾𝗮𝗺  𝗯𝗶𝗹𝗮𝗻  𝘆𝘂𝗯𝗼𝗿𝗶𝗻𝗴:</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="50 stars ✖️", callback_data="amount_50"
                ),
                InlineKeyboardButton(
                    text="100 stars ✖️", callback_data="amount_100"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="200 stars ✖️", callback_data="amount_200"
                ),
                InlineKeyboardButton(
                    text="250 stars ✖️", callback_data="amount_250"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="500 stars ✖️", callback_data="amount_500"
                ),
                InlineKeyboardButton(
                    text="1000 stars ✖️", callback_data="amount_1000"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⚡ 𝐵𝑜𝑠𝗵𝑞𝑎  𝑞𝑖𝑦𝑚𝑎𝑡", callback_data="custom_amount"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 𝑂𝑟𝗾𝗮𝗴𝗮", callback_data="menu_stars"
                )
            ],
        ]
    )

    await state.set_state(OrderState.confirming_order)
    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


# ---------------------------------------------------------
# 4. TAYYOR TUGMALARDAN BIRINI BOSGANDA (50, 100 va hokazo)
# ---------------------------------------------------------
@router.callback_query(F.data.startswith("amount_"))
async def process_preset_amount(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    price_per_star = ADMIN_SETTINGS["price_per_star"]
    total_price = amount * price_per_star
    user_balance = ADMIN_SETTINGS["user_balance"]

    data = await state.get_data()
    username = data.get("username", "@user")

    if user_balance < total_price:
        diff = total_price - user_balance
        text = (
            f"⚠️ <b>𝐵𝗮𝗹𝗮𝗻𝘀  𝘆𝗲𝘁𝗮𝗿𝗹𝗶  𝗲𝗺𝗮𝘀.</b> "
            f"<b>{diff:,}  𝘀𝗼'𝗺  𝗾𝗼'𝘀𝗵𝗶𝗯  𝘁𝘂𝗿𝗶𝘀𝗵𝗶𝗻𝗴𝗶𝘇  𝗸𝗲𝗿𝗮𝗸.</b>"
        )
        await callback.message.answer(text, parse_mode=ParseMode.HTML)
    else:
        text = (
            f"⭐ <b>𝐵𝑢𝑦𝑢𝑟𝑡𝑚𝑎𝑛𝑖  𝘁𝗮𝘀𝗱𝗶𝗾𝗹𝗮𝗻𝗴</b>\n\n"
            f"👤 <b>𝑄𝑎𝑏𝑢𝑙  𝑞𝑖𝑙𝑢𝑣𝑐ℎ𝑖:</b> {username}\n"
            f"⭐ <b>𝑆𝑡𝑎𝑟𝑠:</b> {amount}\n"
            f"💰 <b>𝑁𝑎𝑟𝑥:</b> {total_price:,} 𝑠𝑜'𝑚\n"
            f"👛 <b>𝐵𝑎𝗹𝗮𝗻𝘀𝑖𝑛𝗴𝑖𝘇:</b> Eтарли (Аноним аккаунтдан ечилиди)"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ 𝑇𝑎𝑠𝑑𝑖𝑞𝑙𝑎𝑠𝗵", callback_data="confirm_buy"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ 𝐵𝑒𝑘𝑜𝑟  𝑞𝑖𝑙𝑖𝑠𝗵", callback_data="back_to_start"
                    )
                ],
            ]
        )
        await callback.message.answer(
            text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )
    await callback.answer()


# ---------------------------------------------------------
# 5. BOSHQA QIYMAT BOSILGANDA
# ---------------------------------------------------------
@router.callback_query(F.data == "custom_amount")
async def custom_amount_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = data.get("username", "@user")
    price = ADMIN_SETTINGS["price_per_star"]

    await state.set_state(OrderState.waiting_for_custom_amount)
    text = (
        f"⭐ <b>𝑇𝑒𝑙𝑒𝑔𝗿𝗮𝗺  𝑆𝑡𝑎𝑟𝑠  𝘅𝗮𝗿𝗶𝗱  𝗾𝗶𝗹𝗶𝘀ℎ</b>\n\n"
        f"👤 <b>𝑄𝑎𝑏𝑢𝑙  𝑞𝑖𝑙𝑢𝑣𝑐ℎ𝑖:</b> {username}\n"
        f"💰 <b>1 𝑆𝑡𝑎𝑟𝑠 = {price} 𝑠𝑜'𝑚</b>\n\n"
        f"<b>𝑁𝑒𝗰𝗵𝗮  𝑆𝑡𝑎𝑟𝑠  𝘅𝗮𝗿𝗶𝗱  𝗾𝗶𝗹𝗺𝗼𝗾𝗰𝗵𝗶𝘀𝗶𝘇?</b>\n"
        f"𝑀𝑖𝑛𝑖𝑚𝑎𝑙: 50, 𝑀𝑎𝑘𝑠𝑖𝑚𝑎𝑙: 483\n"
        f"<b>𝑀𝑖𝑞𝑑𝑜𝑟𝑛𝑖  𝑘𝑖𝑟𝑖𝑡𝑖𝑛𝑔:</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 𝑂𝑟𝗾𝗮𝗴𝗮", callback_data="menu_stars"
                )
            ]
        ]
    )
    await callback.message.edit_text(
        text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    await callback.answer()


# ---------------------------------------------------------
# 6. QO'LDA KIRITILGAN MIQDORNI QABUL QILISH VA TEKSHIRISH
# ---------------------------------------------------------
@router.message(OrderState.waiting_for_custom_amount)
async def process_custom_amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer(
            "⚠️ <b>𝐼𝑙𝑡𝑖𝑚𝑜𝑠, 𝑓𝑎𝑞𝑎𝑡 𝑟𝑎𝑞𝑎𝗺 𝑘𝑖𝑟𝑖𝑡𝑖𝑛𝑔!</b>", parse_mode=ParseMode.HTML
        )
        return

    amount = int(message.text)
    price_per_star = ADMIN_SETTINGS["price_per_star"]
    total_price = amount * price_per_star
    user_balance = ADMIN_SETTINGS["user_balance"]

    data = await state.get_data()
    username = data.get("username", "@user")

    if user_balance < total_price:
        diff = total_price - user_balance
        text = (
            f"⚠️ <b>𝐵𝗮𝗹𝗮𝗻𝘀  𝘆𝗲𝘁𝗮𝗿𝗹𝗶  𝗲𝗺𝗮𝘀.</b> "
            f"<b>{diff:,}  𝘀𝗼'𝗺  𝗾𝗼'𝘀𝗵𝗶𝗯  𝘁𝘂𝗿𝗶𝘀𝗵𝗶𝗻𝗴𝗶𝘇  𝗸𝗲𝗿𝗮𝗸.</b>"
        )
        await message.answer(text, parse_mode=ParseMode.HTML)
    else:
        text = (
            f"⭐ <b>𝐵𝑢𝑦𝑢𝑟𝑡𝑚𝑎𝑛𝑖  𝘁𝗮𝘀𝗱𝑖𝑞𝗹𝑎𝗻𝗴</b>\n\n"
            f"👤 <b>𝑄𝑎𝑏𝑢𝑙  𝑞𝑖𝑙𝑢𝑣𝑐ℎ𝑖:</b> {username}\n"
            f"⭐ <b>𝑆𝑡𝑎𝑟𝑠:</b> {amount}\n"
            f"💰 <b>𝑁𝑎𝑟𝑥:</b> {total_price:,} 𝑠𝑜'𝑚\n"
            f"👛 <b>𝐵𝗮𝗹𝗮𝗻𝘀𝑖𝑛𝗴𝑖𝘇:</b> Eтарли (Аноним аккаунтдан ечилиди)"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ 𝑇𝑎𝑠𝑑𝑖𝑞𝑙𝑎𝑠𝗵", callback_data="confirm_buy"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ 𝐵𝑒𝑘𝑜𝑟  𝑞𝑖𝑙𝑖𝑠𝗵", callback_data="back_to_start"
                    )
                ],
            ]
        )
        await message.answer(
            text, parse_mode=ParseMode.HTML, reply_markup=keyboard
        )


# ---------------------------------------------------------
# 7. ADMIN PANEL BOSHQARUVI
# ---------------------------------------------------------
@router.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Siz admin emassiz! ❌", show_alert=True)
        return

    text = (
        f"⚙️ <b>𝐴𝐷𝑀𝐼Ն  𝑃𝐴Ն𝐸𝐿</b>\n\n"
        f"💰 1 Stars narxi: <b>{ADMIN_SETTINGS['price_per_star']} so'm</b>\n"
        f"👛 Test balans: <b>{ADMIN_SETTINGS['user_balance']:,} so'm</b>\n\n"
        f"Kerakli amalni tanlang:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Stars narxini o'zgartirish",
                    callback_data="admin_set_price",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Balansni o'zgartirish",
                    callback_data="admin_set_balance",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Asosiy menyu", callback_data="back_to_start"
                )
            ],
        ]
    )
    await callback.message.edit_text(
        text, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "admin_set_price")
async def admin_set_price(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(OrderState.admin_change_price)
    await callback.message.edit_text(
        "💰 <b>Yangi 1 ta Stars narxini kiriting (so'mda):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Orqaga", callback_data="admin_panel"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@router.message(OrderState.admin_change_price)
async def save_new_price(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.text.isdigit():
        await message.answer("⚠️ Faqat raqam kiriting!")
        return

    ADMIN_SETTINGS["price_per_star"] = int(message.text)
    await state.clear()
    await message.answer(
        f"✅ <b>Stars narxi muvaffaqiyatli {ADMIN_SETTINGS['price_per_star']} so'mga o'zgartirildi!</b>",
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "admin_set_balance")
async def admin_set_balance(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await state.set_state(OrderState.admin_add_balance)
    await callback.message.edit_text(
        "💳 <b>Yangi balans miqdorini kiriting (so'mda):</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Orqaga", callback_data="admin_panel"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@router.message(OrderState.admin_add_balance)
async def save_new_balance(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.text.isdigit():
        await message.answer("⚠️ Faqat raqam kiriting!")
        return

    ADMIN_SETTINGS["user_balance"] = int(message.text)
    await state.clear()
    await message.answer(
        f"✅ <b>Balans muvaffaqiyatli {ADMIN_SETTINGS['user_balance']:,} so'mga o'zgartirildi!</b>",
        parse_mode=ParseMode.HTML,
    )


# ---------------------------------------------------------
# 8. ORQAGA VA QOLGAN TUGMALARNI BOSHQARISH
# ---------------------------------------------------------
@router.callback_query(
    F.data.in_(
        {
            "back_to_start",
            "menu_premium",
            "menu_gift",
            "menu_top",
            "menu_stats",
            "menu_profile",
            "menu_balance",
            "confirm_buy",
        }
    )
)
async def sub_menus(callback: CallbackQuery, state: FSMContext):
    if callback.data == "back_to_start":
        await state.clear()
        await cmd_start(callback.message, state)
    elif callback.data == "confirm_buy":
        await callback.answer(
            "Buyurtma muvaffaqiyatli qabul qilindi! ✅", show_alert=True
        )
        await state.clear()
        await cmd_start(callback.message, state)
    else:
        await callback.answer(
            "Tez kunda ishga tushadi! 🚀", show_alert=True
        )


# ---------------------------------------------------------
# BOTNI ISHGA TUSHIRISH
# ---------------------------------------------------------
async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi! 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
