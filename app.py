from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests, re, os

TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = 1335030495
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbye79W47TuvkLQMGJM5LYXyvdWUXYWpgZsst6xFD1L2UHba6bcducgNpNDtYopXAZ-CPg/exec"

user_state = {}
user_data = {}

def start(update, context):
    chat_id = update.message.chat_id
    user_state[chat_id] = "menu"
    user_data[chat_id] = {}

    update.message.reply_text(
        "🏥 Medix Care Hospital\n\n"
        "1️⃣ Book Appointment\n"
        "2️⃣ Cancel Appointment"
    )

def handle_message(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    text = update.message.text.strip()
    state = user_state.get(chat_id, "menu")

    if state == "menu":
        if text == "1":
            user_state[chat_id] = "department"
            update.message.reply_text(
                "Select Department:\n"
                "1️⃣ General Medicine\n"
                "2️⃣ Cardiology\n"
                "3️⃣ Orthopedics"
            )

        elif text == "2":
            r = requests.get(GOOGLE_URL, params={
                "action": "cancel",
                "user_id": user.id
            })

            if r.text == "CANCELLED":
                update.message.reply_text("❌ Appointment cancelled.")
            else:
                update.message.reply_text("⚠️ No active appointment found.")

    elif state == "department":
        depts = {"1": "General Medicine", "2": "Cardiology", "3": "Orthopedics"}
        if text in depts:
            user_data[chat_id] = {
                "department": depts[text],
                "doctor": "Dr. Kumar"
            }
            user_state[chat_id] = "date"
            update.message.reply_text("📅 Enter Date (DD-MM-YYYY)")

    elif state == "date":
        if re.match(r"\d{2}-\d{2}-\d{4}", text):
            user_data[chat_id]["date"] = text
            user_state[chat_id] = "time"
            update.message.reply_text("1️⃣ 9-10\n2️⃣ 10-11\n3️⃣ 11-12")

    elif state == "time":
        slots = {"1": "9-10", "2": "10-11", "3": "11-12"}
        if text in slots:
            user_data[chat_id]["time"] = slots[text]
            d = user_data[chat_id]

            r = requests.get(GOOGLE_URL, params={
                "action": "book",
                "user_id": user.id,
                "user_name": user.first_name,
                "department": d["department"],
                "doctor": d["doctor"],
                "date": d["date"],
                "time": d["time"]
            })

            if r.text == "SLOT_ALREADY_BOOKED":
                update.message.reply_text("⛔ Slot already booked.")
                return

            if r.text == "USER_ALREADY_HAS_APPOINTMENT":
                update.message.reply_text(
                    "⚠️ You already have an active appointment.\nCancel it first."
                )
                user_state[chat_id] = "menu"
                return

            if r.text == "BOOKED":
                msg = (
                    "🆕 Appointment Booked\n\n"
                    f"🏥 {d['department']}\n"
                    f"👨‍⚕️ {d['doctor']}\n"
                    f"📅 {d['date']}\n"
                    f"🕒 {d['time']}"
                )
                update.message.reply_text(msg)
                if user.id != ADMIN_CHAT_ID:
                    context.bot.send_message(ADMIN_CHAT_ID, msg)

                user_state[chat_id] = "menu"
                user_data.pop(chat_id, None)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
