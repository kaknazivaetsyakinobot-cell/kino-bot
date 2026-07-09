import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# BotFather'dan olgan tokeningizni quyidagi qo'shtirnoq ichiga yozing
API_TOKEN = '8824099204:AAFF3VkCeaD8qqS4vTNTZuIgwIpTYCOFq_o'
CHANNEL_ID = '@kino_topish' # Majburiy a'zolik kanali niki

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Baza bilan ishlash
conn = sqlite3.connect('kinobot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referrer_id INTEGER,
        balance INTEGER DEFAULT 0
    )
''')
conn.commit()

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None
    
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not user:
        if referrer_id and referrer_id != user_id:
            cursor.execute('INSERT INTO users (user_id, referrer_id) VALUES (?, ?)', (user_id, referrer_id))
            cursor.execute('UPDATE users SET balance = balance + 1 WHERE user_id = ?', (referrer_id,))
            try:
                await bot.send_message(referrer_id, "🎉 Do'stingiz taklifingizni qabul qildi!")
            except:
                pass
        else:
            cursor.execute('INSERT INTO users (user_id) VALUES (?)', (user_id,))
        conn.commit()

    is_joined = await check_sub(user_id)
    if not is_joined:
        kb = InlineKeyboardBuilder()
        kb.button(text="Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}")
        kb.button(text="Tekshirish ✅", callback_data="check_subscription")
        kb.adjust(1)
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=kb.as_markup())
    else:
        ref_link = f"https://t.me/{(await bot.get_me()).username}?start={user_id}"
        await message.answer(f"Xush kelibsiz!\nSizning referral havolangiz:\n{ref_link}")

if __name__ == '__main__':
    dp.run_polling(bot)
