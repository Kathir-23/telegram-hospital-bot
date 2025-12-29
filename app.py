from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import re
import os

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
print("🔑 TOKEN LOADED:", "YES" if TOKEN else "NO")

GOOGLE_URL = "https://script.google.com/macros/s/AKfycbxVCBVeH3NbHfS6Ex_PLPP4Rl45MTvS8X79CH3x_2rG03Og1_qbbRIIbn0Cb48oZEu-Pg/exec"

ADMIN_CHAT_ID = 1335030495
# ---------------------------------------

user_state = {}
user_data = {}

# ---------- START ----------
def start(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id

    print(f"🚀 /start pressed | user_id={user.id} | user_name={user.first_name}")

    user_state[chat_id] = "language"
    user_data[chat_id] = {}

    update.message.reply_text(
        "👋 Welcome to Medix Care Hospital\n\n"
        "Please select language:\n"
        "1️⃣ English\n"
        "2️⃣ தமிழ்"
    )

# ---------- MESSAGE HANDLER ----------
def handle_message(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    state = user_state.get(chat_id, "language")

    # ---------- LANGUAGE ----------
    if state == "language":
        if text == "1":
            user_state[chat_id] = "menu"
            update.message.reply_text(
                "Main Menu:\n"
                "1️⃣ Book Appointment\n"
                "2️⃣ Hospital Timings"
            )
        elif text == "2":
            user_state[chat_id] = "menu"
            update.message.reply_text(
                "முதன்மை பட்டியல்:\n"
                "1️⃣ நேரம் பதிவு\n"
                "2️⃣ மருத்துவமனை நேரம்"
            )
        else:
            update.message.reply_text("Please enter 1 or 2")

    # ---------- MENU ----------
    elif state == "menu":
        if text == "1":
            user_state[chat_id] = "department"
            update.message.reply_text(
                "Select Department:\n"
                "1️⃣ General Medicine\n"
                "2️⃣ Cardiology\n"
                "3️⃣ Orthopedics"
            )
        elif text == "2":
            update.message.reply_text("🕘 Hospital Timings: 9 AM – 6 PM")
        else:
            update.message.reply_text("Invalid option")

    # ---------- DEPARTMENT ----------
    elif state == "department":
        departments = {
            "1": "General Medicine",
            "2": "Cardiology",
            "3": "Orthopedics"
        }
        if text in departments:
            user_data[chat_id]["dept"] = departments[text]
            user_data[chat_id]["doctor"] = "Dr. Kumar"
            user_state[chat_id] = "date"
            update.message.reply_text(
                "Doctor: Dr. Kumar\n"
                "Enter date (DD-MM-YYYY)"
            )
        else:
            update.message.reply_text("Select valid department")

    # ---------- DATE ----------
    elif state == "date":
        if re.match(r"\d{2}-\d{2}-\d{4}", text):
            user_data[chat_id]["date"] = text
            print(f"📅 Date received: {text}")
            user_state[chat_id] = "time"
            update.message.reply_text(
                "Select Time:\n"
                "1️⃣ 9-10\n"
                "2️⃣ 10-11\n"
                "3️⃣ 11-12"
            )
        else:
            update.message.reply_text("❌ Invalid date format (DD-MM-YYYY)")

    # ---------- TIME ----------
    elif state == "time":
        time_slots = {
            "1": "9-10",
            "2": "10-11",
            "3": "11-12"
        }
        if text in time_slots:
            user_data[chat_id]["time"] = time_slots[text]
            d = user_data[chat_id]

            payload = {
                "date": d["date"],
                "department": d["dept"],
                "doctor": d["doctor"],
                "time": d["time"]
            }

            try:
                requests.get(GOOGLE_URL, params=payload, timeout=10)
                print("✅ Appointment successfully saved to Google Sheet")
            except Exception as e:
                print("❌ Google Sheet Error:", e)

            final_message = (
                "🆕 New Appointment Booked\n\n"
                f"👤 User: {user.first_name}\n"
                f"🆔 User ID: {user.id}\n\n"
                f"🏥 Department: {d['dept']}\n"
                f"👨‍⚕️ Doctor: {d['doctor']}\n"
                f"📅 Date: {d['date']}\n"
                f"🕒 Time: {d['time']}"
            )

          # Send to USER
update.message.reply_text(final_message)

# Send to ADMIN only if different
if user.id != ADMIN_CHAT_ID:
    context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=final_message)


            user_state[chat_id] = "language"
            user_data.pop(chat_id, None)

        else:
            update.message.reply_text("Select valid time")

# ---------- MAIN ----------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    print("🤖 Bot is running...")
    updater.idle()

if __name__ == "__main__":
    main()
