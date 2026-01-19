import requests
import time
import json
import os
import threading
import telebot
from flask import Flask

# ===========================
# ⚙️ কনফিগারেশন
# ===========================
# আপনার দেওয়া ফায়ারবেস লিঙ্ক
FIREBASE_URL = "https://ck-win-36ca8-default-rtdb.firebaseio.com"
# গেমের API লিঙ্ক
API_URL = "https://api880.inpay88.net/api/webapi/GetNoaverageEmerdList"

# আপনার দেওয়া নতুন টোকেন (eyJhbGci...)
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY4NzQ1MDkxIiwibmJmIjoiMTc2ODc0NTA5MSIsImV4cCI6IjE3Njg3NDY4OTEiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxLzE4LzIwMjYgODozNDo1MSBQTSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFjY2Vzc19Ub2tlbiIsIlVzZXJJZCI6IjE4OTc0NSIsIlVzZXJOYW1lIjoiODgwMTMxMDQ5NDUwNyIsIlVzZXJQaG90byI6IjEiLCJOaWNrTmFtZSI6Ik1lbWJlck5OR1dVR0ZPIiwiQW1vdW50IjoiMC4zOCIsIkludGVncmFsIjoiMCIsIkxvZ2luTWFyayI6Ikg1IiwiTG9naW5UaW1lIjoiMS8xOC8yMDI2IDg6MDQ6NTEgUE0iLCJMb2dpbklQQWRkcmVzcyI6IjEwMy4xOTkuMTA4LjI3IiwiRGJOdW1iZXIiOiIwIiwiSXN2YWxpZGF0b3IiOiIwIiwiS2V5Q29kZSI6IjU3IiwiVG9rZW5UeXBlIjoiQWNjZXNzX1Rva2VuIiwiUGhvbmVUeXBlIjoiMSIsIlVzZXJUeXBlIjoiMCIsIlVzZXJOYW1lMiI6IiIsImlzcyI6Imp3dElzc3VlciIsImF1ZCI6ImxvdHRlcnlUaWNrZXQifQ.eMtZvqooxpKA-XcxlvGowekIqD1JpfOh3-MzBfWv0wM"

# টেলিগ্রাম বট টোকেন
BOT_TOKEN = "8332595835:AAFDZuCFQT0fM5KdWkpnOFpyBTMGH-wWspM"
bot = telebot.TeleBot(BOT_TOKEN)

# Render-এর জন্য Flask অ্যাপ
app = Flask(__name__)

@app.route('/')
def health_check():
    return "<h1>PINEX DATA COLLECTOR IS ONLINE ✅</h1>"

# ===========================
# 🛠️ রেজাল্ট ক্যালকুলেশন ফাংশন
# ===========================
def get_info(num):
    try:
        n = int(num)
        size = "BIG" if n >= 5 else "SMALL"
        color = "GREEN" if n in [1,3,7,9] else "RED"
        if n == 0 or n == 5: color = "VIOLET"
        return size, color
    except:
        return "N/A", "N/A"

# ===========================
# 🚀 ডাটা কালেক্টর (ব্যাকগ্রাউন্ডে চলবে)
# ===========================
def run_loop():
    print("🚀 Monitoring Started... Data will be saved to Firebase.")
    last_period = None
    
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"
    }

    while True:
        try:
            # গেমের ডাটা চেক (1 Minute - TypeId 1)
            payload = {"typeId": 1, "pageSize": 10, "pageNo": 1}
            response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('data', {}).get('list', [])
                
                if records:
                    latest = records[0]
                    period = str(latest['issueNumber'])
                    num = latest['number']

                    if period != last_period:
                        size, color = get_info(num)
                        
                        # ডাটাবেসে সেভ করার জন্য ফরম্যাট
                        save_data = {
                            "period": period,
                            "number": num,
                            "size": size,
                            "color": color,
                            "timestamp": int(time.time())
                        }
                        
                        # Firebase এ PUT মেথড দিয়ে সেভ করা
                        firebase_res = requests.put(f"{FIREBASE_URL}/wingo_records/{period}.json", json=save_data)
                        
                        if firebase_res.status_code == 200:
                            print(f"✅ Saved: {period} -> {size} ({num})")
                        else:
                            print(f"❌ Firebase Error: {firebase_res.status_code}")
                            
                        last_period = period
            
            elif response.status_code == 401:
                print("⚠️ Token Expired! Please update AUTH_TOKEN.")
            
            time.sleep(2) # ২ সেকেন্ড পর পর চেক করবে

        except Exception as e:
            print(f"⚠️ Error occurred: {e}")
            time.sleep(5)

# ===========================
# 🤖 টেলিগ্রাম বট কমান্ড (স্ট্যাটাস চেক)
# ===========================
@bot.message_handler(commands=['start', 'status'])
def send_status(message):
    try:
        # ডাটাবেস থেকে বর্তমান সংখ্যা চেক
        res = requests.get(f"{FIREBASE_URL}/wingo_records.json?shallow=true")
        count = len(res.json()) if res.json() else 0
        bot.reply_to(message, f"📊 **PINEX Collector Status**\n\n✅ Server: Online\n📁 Total Records: {count}\n🚀 Mode: 24/7 Scanning")
    except:
        bot.reply_to(message, "⚠️ Database Connection Failed!")

# ===========================
# 🏁 রানার
# ===========================
if __name__ == "__main__":
    # ১. ডাটা কালেক্টর থ্রেড শুরু করা
    threading.Thread(target=run_loop, daemon=True).start()
    
    # ২. টেলিগ্রাম বট থ্রেড শুরু করা
    threading.Thread(target=bot.infinity_polling, daemon=True).start()
    
    # ৩. Flask সার্ভার রান করা (Render Port অনুযায়ী)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
