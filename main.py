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
CURRENCY_API_URL = "https://bank.gov.ua" # Офіційне API Нацбанку

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Active Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    server.serve_forever()

# 1. МОНІТОРИНГ ТРИВОГ (Кожні 20 секунд)
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
                            bot_text = f"⚠️ <b>ОПЕРАТИВНА ІНФОРМАЦІЯ ПРО РУХ ЦІЛЕЙ:</b>\n\n📌 {description}\n\n🚨 <i>Будьте уважні!</i>"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": bot_text, "parse_mode": "HTML"})
                    last_processed_guid = guid
        except:
            pass
        time.sleep(20)

# 2. МОНІТОРИНГ МІСЬКИХ НОВИН (Кожні 60 секунд)
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
                            news_text = f"📰 <b>НОВИНИ ЛЬВОВА | ОПЕРАТИВНО</b>\n\n📌 {clean_title}"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": news_text, "parse_mode": "HTML"})
                    last_news_title = title
        except:
            pass
        time.sleep(60)

# 3. АВТОМАТИЧНИЙ КУРС ВАЛЮТ (Публікація кожні 4 години)
def check_currency_loop():
    print("Потік курсу валют запущено...")
    while True:
        try:
            if TOKEN:
                res = requests.get(CURRENCY_API_URL, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    usd_rate = 0
                    eur_rate = 0
                    for item in data:
                        if item.get("cc") == "USD":
                            usd_rate = round(item.get("rate"), 2)
                        if item.get("cc") == "EUR":
                            eur_rate = round(item.get("rate"), 2)
                    
                    currency_text = (
                        f"💵 <b>ОФІЦІЙНИЙ КУРС ВАЛЮТ (НБУ):</b>\n\n"
                        f"🇺🇸 <b>Долар (USD):</b> {usd_rate} грн\n"
                        f"🇪🇺 <b>Євро (EUR):</b> {eur_rate} грн\n\n"
                        f"📊 <i>Оновлення курсу відбуваються автоматично.</i>"
                    )
                    requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": currency_text, "parse_mode": "HTML"})
        except Exception as e:
            print(f"Помилка валюти: {e}")
            
        time.sleep(14400) # Оновлювати рівно кожні 4 години

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    airspace_thread = threading.Thread(target=check_airspace_details)
    airspace_thread.daemon = True
    airspace_thread.start()
    
    currency_thread = threading.Thread(target=check_currency_loop)
    currency_thread.daemon = True
    currency_thread.start()
    
    check_lviv_news()
