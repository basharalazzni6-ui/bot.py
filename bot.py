import sqlite3
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

# ===== قاعدة البيانات =====
conn = sqlite3.connect("files.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT,
    file_id TEXT
)
""")
conn.commit()

# ===== Web Server =====
app_web = Flask('')

@app_web.route('/')
def home():
    return "Bot is running!"

def run():
    app_web.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ===== أوامر البوت =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 مكتبة الجامعة\n\n"
        "📤 أرسل ملف\n"
        "🔍 /search اسم_المادة"
    )

async def save_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        context.user_data["file_id"] = update.message.document.file_id
        context.user_data["file_name"] = update.message.document.file_name
        context.user_data["waiting"] = True
        await update.message.reply_text("📚 اكتب اسم المادة:")

async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting"):
        cursor.execute(
            "INSERT INTO files (name, category, file_id) VALUES (?, ?, ?)",
            (context.user_data["file_name"], update.message.text, context.user_data["file_id"])
        )
        conn.commit()
        context.user_data["waiting"] = False
        await update.message.reply_text("✅ تم حفظ الملف")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    cursor.execute("SELECT name, file_id FROM files WHERE category LIKE ?", ('%' + keyword + '%',))
    results = cursor.fetchall()

    if results:
        for name, file_id in results:
            await update.message.reply_document(file_id, caption=name)
    else:
        await update.message.reply_text("❌ لا توجد نتائج")

# ===== التشغيل =====
def main():
    keep_alive()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(MessageHandler(filters.Document.ALL, save_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_category))

    app.run_polling()

main()
