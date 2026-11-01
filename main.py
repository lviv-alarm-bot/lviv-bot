import os
import time
import requests
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = "@yoy_lviv_monitor" 

# ДЖЕРЕЛА ДАНИХ
PS_API_URL = "https://i-scuba.com" # Повітряні Сили
LVIV_NEWS_URL = "https://google.com" # Новини Львова

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

# 1. МОНІТОРИНГ РАКЕТ І ШАХЕДІВ
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

# 2. МОНІТОРИНГ МІСЬКИХ НОВИН
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
                            clean_title = title.split(" - ")[0]
                            news_text = f"📰 <b>НОВИНИ ЛЬВОВА | ОПЕРАТИВНО</b>\n\n📌 {clean_title}\n\n📢 <i>Поділіться інформацією з близькими!</i>"
                            send_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": news_text, "parse_mode": "HTML"})
                    last_news_title = title
        except Exception as e:
            print(f"Помилка новин: {e}")
        time.sleep(60)

if __name__ == "__main__":
    # Запуск веб-сервера проти сну
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # ТЕСТОВИЙ ЗАПУСК СТАРТУ (Змінні виправлені)
    if TOKEN:
        try:
            welcome_text = "🚀 <b>Бот успішно активований у хмарі!</b>\n\nАвтоматичний моніторинг повітряних тривог, руху Шахедів/Ракет та головних міських новин для каналу @yoy_lviv_monitor перейшов у цілодобовий режим чергування 24/7."
            send_url = f"https://telegram.org{TOKEN}/sendMessage"
            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": welcome_text, "parse_mode": "HTML"})
        except Exception as e:
            print(f"Помилка тесту: {e}")

    # Запуск потоку повітряних тривог
    airspace_thread = threading.Thread(target=check_airspace_details)
    airspace_thread.daemon = True
    airspace_thread.start()
    
    # Запуск новин Львова
    check_lviv_news()
