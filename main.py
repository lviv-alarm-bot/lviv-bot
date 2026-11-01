import os
import time
import requests
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = "@yoy_lviv_monitor" 

# ДЖЕРЕЛА ДАНИХ
PS_API_URL = "https://i-scuba.com"
LVIV_NEWS_URL = "https://google.com"

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    server.serve_forever()

# 1. ПОСТІЙНИЙ МОНІТОРИНГ ТРИВОГ (Кожні 20 секунд)
def check_airspace_details():
    last_processed_guid = None
    keywords = ["львів", "львівщин", "стрий", "золочів", "червоноград", "самбір", "броди", "яворів", "західн", "заходу"]
    
    while True:
        try:
            if not TOKEN:
                time.sleep(10)
                continue
            response = requests.get(PS_API_URL, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                latest_item = root.find(".//item")
                if latest_item is not None:
                    guid = latest_item.find("guid").text
                    description = latest_item.find("description").text if latest_item.find("description") is not None else latest_item.find("title").text
                    
                    if last_processed_guid is not None and guid != last_processed_guid:
                        text_to_check = description.lower()
                        if any(word in text_to_check for word in keywords):
                            bot_text = f"⚠️ <b>ОПЕРАТИВНА ІНФОРМАЦІЯ ПРО РУХ ЦІЛЕЙ:</b>\n\n📌 {description}\n\n🚨 <i>Будьте уважні, загроза безпосередньо для нашого регіону!</i>"
                            send_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": bot_text, "parse_mode": "HTML"})
                    last_processed_guid = guid
        except Exception as e:
            print(f"Помилка ПС ЗСУ: {e}")
        time.sleep(20)

# 2. ПОСТІЙНИЙ МОНІТОРИНГ МІСЬКИХ НОВИН (Кожні 60 секунд)
def check_lviv_news():
    last_news_title = None
    news_keywords = ["світл", "вод", "відключен", "дтп", "аварі", "транспорт", "опален", "рух"]
    
    while True:
        try:
            if not TOKEN:
                time.sleep(10)
                continue
            response = requests.get(LVIV_NEWS_URL, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                latest_item = root.find(".//item")
                if latest_item is not None:
                    title = latest_item.find("title").text
                    
                    if last_news_title is not None and title != last_news_title:
                        title_lower = title.lower()
                        if any(word in title_lower for word in news_keywords):
                            clean_title = title.split(" - ")
                            news_text = f"📰 <b>НОВИНИ ЛЬВОВА | ОПЕРАТИВНО</b>\n\n📌 {clean_title[0]}\n\n📢 <i>Поділіться інформацією з близькими!</i>"
                            send_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": news_text, "parse_mode": "HTML"})
                    last_news_title = title
        except Exception as e:
            print(f"Помилка новин: {e}")
        time.sleep(60)

# 3. АВТОМАТИЧНИЙ ТАЙМЕР АКТИВНОСТІ КАНАЛУ (Кожні 2 години)
def hourly_activity_loop():
    print("Таймер регулярної активності каналу запущено...")
    while True:
        try:
            if TOKEN:
                # Бот буде стабільно нагадувати підписникам корисні посилання
                activity_text = "📢 <b>Йой | Моніторинг Львів працює 24/7</b>\n\n🔔 Наш робот безперервно стежить за повітряним простором Львівщини та міськими комунальними службами.\n\n📍 <i>Увімкніть сповіщення, щоб першими дізнаватися про загрози та ситуацію у Львові!</i>"
                send_url = f"https://telegram.org{TOKEN}/sendMessage"
                requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": activity_text, "parse_mode": "HTML"})
                print("Опубліковано плановий пост активності.")
        except Exception as e:
            print(f"Помилка таймера: {e}")
        
        time.sleep(7200) # Повторювати рівно кожні 2 години (7200 секунд)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # 100% робочий безпомилковий стартовий пост
    if TOKEN:
        try:
            welcome_text = "🚀 <b>Бот успішно активований у хмарі!</b>\n\nАвтоматичний моніторинг повітряних тривог, руху Шахедів/Ракет та головних міських новин для каналу @yoy_lviv_monitor перейшов у цілодобовий режим чергування 24/7."
            send_url = f"https://telegram.org{TOKEN}/sendMessage"
            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": welcome_text, "parse_mode": "HTML"})
        except Exception as e:
            print(f"Помилка старту: {e}")

    # Потік для тривог
    airspace_thread = threading.Thread(target=check_airspace_details)
    airspace_thread.daemon = True
    airspace_thread.start()
    
    # Потік для регулярних щогодинних постів
    activity_thread = threading.Thread(target=hourly_activity_loop)
    activity_thread.daemon = True
    activity_thread.start()
    
    # Запуск новин у головному потоці
    check_lviv_news()


