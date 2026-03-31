import sqlite3
import asyncio
import os
import yt_dlp
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8611009386:AAHsJYl7IhJQ6YrQZwI12sp4U5Mv9_Fwm-o"
CHANNEL_USERNAME = "@vexorasave017"
ADMIN_ID = 562708594

# دیتابیس
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    language TEXT DEFAULT 'fa'
)
""")
conn.commit()

# متن‌ها
TEXTS = {
    "fa": {
        "welcome": "🌐 زبان خود را انتخاب کن:",
        "join": "❌ اول عضو کانال شو:",
        "start": "🚀 خوش آمدی! لینک بفرست",
        "downloading": "⏳ در حال دانلود...",
        "error": "❌ خطا در دانلود"
    },
    "en": {
        "welcome": "🌐 Choose language:",
        "join": "❌ Join channel first:",
        "start": "🚀 Welcome! Send link",
        "downloading": "⏳ Downloading...",
        "error": "❌ Download error"
    },
    "de": {
        "welcome": "🌐 Sprache wählen:",
        "join": "❌ Kanal beitreten:",
        "start": "🚀 Willkommen! Link senden",
        "downloading": "⏳ Wird geladen...",
        "error": "❌ Fehler"
    },
    "ar": {
        "welcome": "🌐 اختر اللغة:",
        "join": "❌ انضم للقناة:",
        "start": "🚀 مرحبا! أرسل الرابط",
        "downloading": "⏳ جاري التحميل...",
        "error": "❌ خطأ"
    }
}

def language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇦🇫 فارسی", callback_data="lang_fa")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de")],
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar")]
    ])

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
        [InlineKeyboardButton("عضو شدم ✅", callback_data="check_join")]
    ])

def get_lang(user_id):
    cursor.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else "fa"

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# چک عضویت
async def is_joined(user_id, context):
    if user_id == ADMIN_ID:
        return True
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    await update.message.reply_text(TEXTS["fa"]["welcome"], reply_markup=language_keyboard())

# انتخاب زبان
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    lang = query.data.split("_")[1]

    cursor.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
    conn.commit()

    await query.answer()

    if not await is_joined(user_id, context):
        await query.message.edit_text(TEXTS[lang]["join"], reply_markup=join_keyboard())
    else:
        await query.message.edit_text(TEXTS[lang]["start"])

# تایید عضویت
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_lang(user_id)

    if await is_joined(user_id, context):
        await query.answer("✅")
        await query.message.edit_text(TEXTS[lang]["start"])
    else:
        await query.answer("❌", show_alert=True)

# دانلود
def download_sync(url):
    ydl_opts = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "format": "best",
        "quiet": True,
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return [ydl.prepare_filename(info)]

async def download(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, download_sync, url)
import yt_dlp
import os
async def handle_instagram(update, context, url):
    try:
        chat_id = update.effective_chat.id
        await update.message.reply_text("⏳ در حال دانلود...")
        ydl_opts = {
            'outtmpl': 'insta.%(ext)s',
            'format': 'best',
            'quiet': True,
            'cookiesfrombrowser': ('chrome',)
        }

        info = ydl.extract_info(url, download=True)

        if not info:
            await update.message.reply_text("❌ لینک خراب است")
            return

        if 'entries' in info:
            info = info['entries'][0]

        file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as f:
            if file_path.endswith(".mp4"):
                await context.bot.send_video(chat_id=chat_id, video=f)
            else:
                await context.bot.send_photo(chat_id=chat_id, photo=f)

        os.remove(file_path)

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ خطا در دانلود اینستاگرام")
# هندل اصلی (بدون باگ)
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(user_id)

    if not await is_joined(user_id, context):
        await update.message.reply_text(TEXTS[lang]["join"], reply_markup=join_keyboard())
        return

    url = update.message.text
    if "instagram" in url:
        await handle_instagram(update, context, url)
        return
    msg = await update.message.reply_text(TEXTS[lang]["downloading"])

    try:
        files = await download(url)

        for file in files:
            if not os.path.exists(file):
                continue

            try:
                with open(file, "rb") as f:
                    chat_id = update.effective_chat.id

                    if file.endswith(".mp4"):
                        await context.bot.send_video(chat_id=chat_id, video=f)
                    elif file.endswith((".jpg", ".png", ".jpeg")):
                        await context.bot.send_photo(chat_id=chat_id, photo=f)
                    else:
                        await context.bot.send_document(chat_id=chat_id, document=f)


                os.remove(file)

            except Exception as e:
                print("SEND ERROR:", e)

        await msg.delete()

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        await update.message.reply_text(TEXTS[lang]["error"])

# ====== ادمین ======

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("📊 کاربران", callback_data="stats")],
        [InlineKeyboardButton("📢 ارسال همگانی", callback_data="broadcast")]
    ]

    await update.message.reply_text("⚙️ پنل ادمین", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await query.message.reply_text(f"👥 کاربران: {count}")

    elif query.data == "broadcast":
        context.user_data["broadcast"] = True
        await query.message.reply_text("✉️ پیام را بفرست:")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("broadcast"):
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        for user in users:
            try:
                await context.bot.send_message(user[0], update.message.text)
            except:
                pass

        context.user_data["broadcast"] = False
        await update.message.reply_text("✅ ارسال شد")

# اجرا
def main():
    os.makedirs("downloads", exist_ok=True)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))

    app.add_handler(CallbackQueryHandler(set_language, pattern="lang_"))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="stats|broadcast"))

    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🔥 BOT RUNNING...")

    app.run_polling()

if __name__ == "__main__":
    main()