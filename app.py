from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import re
import os

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = 1335030495  # YOUR TELEGRAM ID
GOOGLE_URL = "https://script.google.com/macros/s/AKfycbxmwZHpnV6Nu5Y14Eit815iFbjkD_5b2TRWgK7i52nGrDrTUVWX9DTNhQ3TX7Xo6uVRdg/exec"
# =========================================

print("🔑 TOKEN LOADED:", "YES" if TOKEN else "NO")

user_state = {}
user_data = {}

# ================= START =================
def start(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id

    print(f"🚀 /start pressed | user_id={user.id} | user_name={user.first_name}")

    user_state[chat_id] = "menu"
    user_data[chat_id] = {}

    update.message.reply_text(
        "🏥 Medix Care Hospital\n\n"
        "1️⃣ Book Appointment\n"
        "2️⃣ Cancel Appointment"
    )

# ================= MESSAGE HANDLER =================
def handle_message(update, context):
    user = update.message.from_user
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    state = user_state.get(chat_id, "menu")

    # ---------- MENU ----------
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
            payload = {
                "action": "cancel",
                "user_id": user.id
            }

            r = requests.get(GOOGLE_URL, params=payload)
            print("❌ Cancel response:", r.text)

            if r.text == "CANCELLED":
                msg = "❌ Your appointment has been cancelled."
                update.message.reply_text(msg)

                if user.id != ADMIN_CHAT_ID:
                    context.bot.send_message(ADMIN_CHAT_ID, msg)

            else:
                update.message.reply_text("⚠️ No active appointment found")

        else:
            update.message.reply_text("Please select 1 or 2")

    # ---------- DEPARTMENT ----------
    elif state == "department":
        departments = {
            "1": "General Medicine",
            "2": "Cardiology",
            "3": "Orthopedics"
        }

        if text in departments:
            user_data[chat_id]["department"] = departments[text]
            user_data[chat_id]["doctor"] = "Dr. Kumar"
            user_state[chat_id] = "date"

            update.message.reply_text(
                "Doctor: Dr. Kumar\n"
                "Enter Date (DD-MM-YYYY)"
            )
        else:
            update.message.reply_text("Invalid department")

    # ---------- DATE ----------
    elif state == "date":
        if re.match(r"\d{2}-\d{2}-\d{4}", text):
            user_data[chat_id]["date"] = text
            user_state[chat_id] = "time"

            update.message.reply_text(
                "Select Time:\n"
                "1️⃣ 9-10\n"
                "2️⃣ 10-11\n"
                "3️⃣ 11-12"
            )
        else:
            update.message.reply_text("❌ Invalid date format")

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
                "action": "book",
                "user_id": user.id,
                "user_name": user.first_name,
                "department": d["department"],
                "doctor": d["doctor"],
                "date": d["date"],
                "time": d["time"]
            }

            r = requests.get(GOOGLE_URL, params=payload)
            print("📡 Booking response:", r.text)

            # ===== SLOT ALREADY BOOKED =====
            if r.text == "SLOT_TAKEN":
                update.message.reply_text(
                    "⛔ This time slot is already booked.\n\n"
                    "Please choose another time."
                )
                user_state[chat_id] = "time"
                return

            # ===== BOOKED SUCCESSFULLY =====
            if r.text == "BOOKED":
                confirmation_msg = (
                    "🆕 Appointment Booked\n\n"
                    f"👤 User: {user.first_name}\n"
                    f"🆔 User ID: {user.id}\n\n"
                    f"🏥 Department: {d['department']}\n"
                    f"👨‍⚕️ Doctor: {d['doctor']}\n"
                    f"📅 Date: {d['date']}\n"
                    f"🕒 Time: {d['time']}"
                )

                update.message.reply_text(confirmation_msg)

                if user.id != ADMIN_CHAT_ID:
                    context.bot.send_message(ADMIN_CHAT_ID, confirmation_msg)

                user_state[chat_id] = "menu"
                user_data.pop(chat_id, None)
                return

            # ===== UNKNOWN ERROR =====
            update.message.reply_text("⚠️ Something went wrong. Try again later.")

        else:
            update.message.reply_text("Invalid time selection")

# ================= MAIN =================
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
