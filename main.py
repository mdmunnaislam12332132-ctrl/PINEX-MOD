import requests
import time
import telebot
import threading
import os
import json
from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ===========================
# ⚙️ কনফিগারেশন (আপনার তথ্য)
# ===========================

# টেলিগ্রাম বট টোকেন
BOT_TOKEN = "8332595835:AAFDZuCFQT0fM5KdWkpnOFpyBTMGH-wWspM"
CHANNEL_ID = "-1003466119460"

# ফায়ারবেস ডাটাবেস লিঙ্ক
FIREBASE_URL = "https://ck-win-36ca8-default-rtdb.firebaseio.com"

# গেম API কনফিগারেশন
API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"
# লক্ষ্য করুন: এই টোকেনটি নির্দিষ্ট সময় পর এক্সপায়ার হতে পারে, তখন নতুন টোকেন বসাতে হবে
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY4Mzk0NDY2IiwibmJmIjoiMTc2ODM5NDQ2NiIsImV4cCI6IjE3NjgzOTYyNjYiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxLzE0LzIwMjYgNzoxMTowNiBQTSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFjY2Vzc19Ub2tlbiIsIlVzZXJJZCI6IjE4OTc0NSIsIlVzZXJOYW1lIjoiODgwMTMxMDQ5NDUwNyIsIlVzZXJQaG90byI6IjEiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR1dVR0ZPIiwiQW1vdW50IjoiMC40MSIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMS8xNC8yMDI2IDY6NDE6MDYgUE0iLCJMb2dpbklQQWRkcmVzcyI6IjEwMy4xOTkuMTA4LjI3IiwiRGJOdW1iZXIiOiIwIiwiSXN2YWxpZGF0b3IiOiIwIiwiS2V5Q29kZSI6IjkiLCJUb2tlblR5cGUiOiJBY2Nlc3NfVG9rZW4iLCJQaG9uZVR5cGUiOiIxIiwiVXNlclR5cGUiOiIwIiwiVXNlck5hbWUyIjoiIiwiaXNzIjoiand0SXNzdWVyIiwiYXVkIjoibG90dGVyeVRpY2tldCJ9.F2XKZyg4PQQ9ht-g9rRdr6P1Dr-x8KbycEs5ESdohi4"

# Flask অ্যাপ (Render এর জন্য)
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

@app.route('/')
def health():
    return "✅ SYSTEM ACTIVE: Bot & Data Scraper Running..."

# ===========================
# 🛠️ হেল্পার ফাংশন
# ===========================
def get_result_info(num):
    try:
        n = int(num)
        size = "BIG" if n >= 5 else "SMALL"
        if n in [1, 3, 7, 9]: color = "GREEN"
        elif n in [2, 4, 6, 8]: color = "RED"
        elif n == 0: color = "RED+VIOLET"
        elif n == 5: color = "GREEN+VIOLET"
        else: color = "UNKNOWN"
        return size, color
    except:
        return "N/A", "N/A"

# ===========================
# 🔄 ডাটা কালেক্টর লুপ (Thread 1)
# ===========================
def data_collection_loop():
    print("🚀 Data Collection Started...")
    last_period = None

    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
        "Origin": "https://tkclub2.com",
        "Referer": "https://tkclub2.com/"
    }

    while True:
        try:
            payload = {
                "typeId": 1, "pageSize": 10, "pageNo": 1, "language": 0,
                "random": "6d89e472605c47948f21e54e4c9c104e",
                "signature": "EB9D284C2C0B46A495E4D1A02E2752D8",
                "timestamp": int(time.time())
            }

            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                res_json = response.json()
                records = res_json.get('data', {}).get('list', [])

                if records:
                    latest = records[0]
                    period = str(latest.get('issueNumber'))
                    result_num = latest.get('number')

                    if period != last_period and result_num is not None:
                        size, color = get_result_info(result_num)
                        
                        save_data = {
                            'period': period,
                            'number': result_num,
                            'size': size,
                            'color': color,
                            'timestamp': int(time.time())
                        }
                        
                        # Firebase এ সেভ করা
                        requests.put(f"{FIREBASE_URL}/wingo_records/{period}.json", json=save_data)
                        print(f"📥 New Data: {period} -> {size}")

                        # টেলিগ্রাম নোটিফিকেশন (Optional)
                        try:
                            msg = f"🎰 <b>New Result:</b> {period}\nResult: {result_num} ({size})"
                            bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
                        except: pass

                        last_period = period
            elif response.status_code == 401:
                print("⚠️ Token Expired! Update AUTH_TOKEN in code.")
                
            time.sleep(3) # ৩ সেকেন্ড পর পর চেক করবে

        except Exception as e:
            print(f"⚠️ API Error: {e}")
            time.sleep(5)

# ===========================
# 🤖 টেলিগ্রাম বট কমান্ড (Thread 2 handled by library)
# ===========================
def bot_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("📊 Status"), KeyboardButton("📥 Download Data"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 **Admin Panel Ready!**\nUse buttons below to manage data.", reply_markup=bot_keyboard())

@bot.message_handler(func=lambda message: message.text == "📊 Status")
def check_status(message):
    wait = bot.reply_to(message, "Checking Database...")
    try:
        r = requests.get(f"{FIREBASE_URL}/wingo_records.json")
        data = r.json()
        count = len(data) if data else 0
        bot.edit_message_text(f"✅ **Database Status:**\n\nTotal Records: `{count}`\nConnection: OK", message.chat.id, wait.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, wait.message_id)

@bot.message_handler(func=lambda message: message.text == "📥 Download Data")
def download_data(message):
    wait = bot.reply_to(message, "Preparing file...")
    try:
        r = requests.get(f"{FIREBASE_URL}/wingo_records.json")
        data = r.json()
        if not data:
            bot.edit_message_text("❌ Database is empty.", message.chat.id, wait.message_id)
            return
        
        # TXT ফাইল তৈরি
        fname = "Wingo_History.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("PERIOD | NUMBER | SIZE | COLOR\n")
            f.write("-" * 35 + "\n")
            for k in sorted(data.keys()):
                d = data[k]
                f.write(f"{d['period']} | {d['number']} | {d['size']} | {d['color']}\n")
        
        with open(fname, "rb") as f:
            bot.send_document(message.chat.id, f, caption="📂 Full Database History")
        os.remove(fname)
        bot.delete_message(message.chat.id, wait.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Failed: {str(e)}", message.chat.id, wait.message_id)

# ===========================
# 🔥 মেইন রানার
# ===========================
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # ১. ডাটা কালেক্টর থ্রেড
    t1 = threading.Thread(target=data_collection_loop, daemon=True)
    t1.start()
    
    # ২. ফ্লাস্ক সার্ভার থ্রেড (Render এর জন্য)
    t2 = threading.Thread(target=run_flask, daemon=True)
    t2.start()
    
    # ৩. টেলিগ্রাম বট (মেইন থ্রেড)
    print("🤖 Bot Polling Started...")
    bot.infinity_polling()
