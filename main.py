import requests
import time
import json
import os
import threading
import telebot
from flask import Flask
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ===========================
# ⚙️ কনফিগারেশন
# ===========================
FIREBASE_URL = "https://ck-win-36ca8-default-rtdb.firebaseio.com"
API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"

# নতুন টোকেন (তোমার দেওয়াটি)
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY4NzQ1MDkxIiwibmJmIjoiMTc2ODc0NTA5MSIsImV4cCI6IjE3Njg3NDY4OTEiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxLzE4LzIwMjYgODozNDo1MSBQTSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFjY2Vzc19Ub2tlbiIsIlVzZXJJZCI6IjE4OTc0NSIsIlVzZXJOYW1lIjoiODgwMTMxMDQ5NDUwNyIsIlVzZXJQaG90byI6IjEiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR1dVR0ZPIiwiQW1vdW50IjoiMC4zOCIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMS8xOC8yMDI2IDg6MDQ6NTEgUE0iLCJMb2dpbklQQWRkcmVzcyI6IjEwMy4xOTkuMTA4LjI3IiwiRGJOdW1iZXIiOiIwIiwiSXN2YWxpZGF0b3IiOiIwIiwiS2V5Q29kZSI6IjU3IiwiVG9rZW5UeXBlIjoiQWNjZXNzX1Rva2VuIiwiUGhvbmVUeXBlIjoiMSIsIlVzZXJUeXBlIjoiMCIsIlVzZXJOYW1lMiI6IiIsImlzcyI6Imp3dElzc3VlciIsImF1ZCI6ImxvdHRlcnlUaWNrZXQifQ.eMtZvqooxpKA-XcxlvGowekIqD1JpfOh3-MzBfWv0wM"

# টেলিগ্রাম বট কনফিগারেশন (তোমার আগেরটি)
BOT_TOKEN = "8332595835:AAFDZuCFQT0fM5KdWkpnOFpyBTMGH-wWspM"
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# ===========================
# 🛠️ হেল্পার ফাংশন
# ===========================
def get_result_info(num):
    try:
        n = int(num)
        size = "BIG" if n >= 5 else "SMALL"
        color = "GREEN" if n in [1,3,7,9] else "RED"
        if n in [0, 5]: 
            color = "VIOLET+" + ("RED" if n==0 else "GREEN")
        return size, color
    except:
        return "N/A", "N/A"

# ===========================
# 🚀 ডাটা কালেক্টর (লুপ)
# ===========================
def run_data_collector():
    print("🚀 Data Collector Started...")
    last_period = None
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"
    }
    
    while True:
        try:
            payload = {"typeId": 1, "pageSize": 10, "pageNo": 1}
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                res_json = response.json()
                data_list = res_json.get('data', {}).get('list', [])
                
                if data_list:
                    latest = data_list[0]
                    period = str(latest['issueNumber'])
                    num = latest['number']
                    
                    if period != last_period:
                        size, color = get_result_info(num)
                        timestamp = int(time.time())
                        
                        save_data = {
                            "period": period,
                            "number": num,
                            "size": size,
                            "color": color,
                            "timestamp": timestamp
                        }
                        
                        # Firebase এ সেভ করা
                        requests.put(f"{FIREBASE_URL}/wingo_records/{period}.json", json=save_data)
                        print(f"✅ Saved: {period} | {size} | {color}")
                        last_period = period
            
            time.sleep(2) # ২ সেকেন্ড পর পর চেক করবে
        except Exception as e:
            print(f"⚠️ Connection Error: {e}")
            time.sleep(5)

# ===========================
# 🤖 টেলিগ্রাম বট লজিক (শুধু চেক ও ডাউনলোডের জন্য)
# ===========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📊 Check Status"), KeyboardButton("📥 Download Data"))
    bot.reply_to(message, "🔥 PINEX ADMIN BOT ACTIVE!\nডাটাবেস চেক বা ডাউনলোড করতে নিচের বাটন চাপুন।", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Check Status")
def check_status(message):
    try:
        r = requests.get(f"{FIREBASE_URL}/wingo_records.json?shallow=true")
        if r.status_code == 200 and r.json():
            count = len(r.json())
            bot.reply_to(message, f"✅ Server Running Perfectly!\nTotal Records Found: {count}")
        else:
            bot.reply_to(message, "⚠️ Database Empty or Error!")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@bot.message_handler(func=lambda m: m.text == "📥 Download Data")
def download_data(message):
    wait_msg = bot.reply_to(message, "📥 ডাটাবেস ডাউনলোড হচ্ছে... দয়া করে অপেক্ষা করুন।")
    try:
        response = requests.get(f"{FIREBASE_URL}/wingo_records.json")
        data = response.json()
        
        if not data:
            bot.reply_to(message, "⚠️ ডাটাবেস খালি!")
            return

        # টেক্সট ফাইল তৈরি
        filename = "PINEX_Database_Full.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("PERIOD | NUM | SIZE | COLOR | TIME\n")
            f.write("="*50 + "\n")
            # পিরিয়ড অনুযায়ী সর্ট করা
            for k in sorted(data.keys()):
                d = data[k]
                f.write(f"{d.get('period')} | {d.get('number')} | {d.get('size')} | {d.get('color')} | {d.get('timestamp')}\n")
        
        # ফাইল সেন্ড করা
        with open(filename, "rb") as doc:
            bot.send_document(message.chat.id, doc, caption="📂 Full Database Backup")
        
        os.remove(filename) # টেম্প ফাইল ডিলিট
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# ===========================
# 🌐 ফ্লাস্ক সার্ভার (Render এর জন্য)
# ===========================
@app.route('/')
def index():
    return "<h1>PINEX SYSTEM IS RUNNING 24/7</h1>"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ===========================
# 🔥 মেইন রানার
# ===========================
if __name__ == "__main__":
    # ১. ডাটা কালেক্টর থ্রেড
    threading.Thread(target=run_data_collector, daemon=True).start()
    
    # ২. টেলিগ্রাম বট থ্রেড
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    
    # ৩. ওয়েব সার্ভার রান
    run_flask()
