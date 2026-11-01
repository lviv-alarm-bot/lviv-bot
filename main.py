import os
import time
import requests
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = "@yoy_lviv_monitor" 

PS_API_URL = "https://i-scuba.com"
LVIV_NEWS_URL = "https://google.com"
CURRENCY_API_URL = "https://bank.gov.ua"

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

# 1. МОНІТОРИНГ ТРИВОГ
def check_airspace_details():
    last_processed_guid = None
    keywords = ["львів", "львівщин", "стрий", "золочів", "червоноград", "самбір", "броди", "яворів", "західн", "заходу"]
    while True:
        try:
            if not TOKEN:
                time.sleep(5)
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
                            bot_text = f"⚠️ <b>ОПЕРАТИВНА ІНФОРМАЦІЯ ПРО РУХ ЦІЛЕЙ:</b>\n\n📌 {description}"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": bot_text, "parse_mode": "HTML"})
                    last_processed_guid = guid
        except:
            pass
        time.sleep(20)

# 2. МОНІТОРИНГ МІСЬКИХ НОВИН
def check_lviv_news_loop():
    last_news_title = None
    news_keywords = ["світл", "вод", "відключен", "дтп", "аварі", "транспорт", "опален", "рух"]
    while True:
        try:
            if not TOKEN:
                time.sleep(5)
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
                            news_text = f"📰 <b>НОВИНИ ЛЬВОВА | ОПЕРАТИВНО</b>\n\n📌 {clean_title}"
                            requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": news_text, "parse_mode": "HTML"})
                    last_news_title = title
        except:
            pass
        time.sleep(60)

# 3. АВТОМАТИЧНИЙ КУРС ВАЛЮТ
def check_currency_loop():
    while True:
        try:
            if TOKEN:
                res = requests.get(CURRENCY_API_URL, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    usd_rate, eur_rate = 0, 0
                    for item in data:
                        if item.get("cc") == "USD":
                            usd_rate = round(float(item.get("rate")), 2)
                        if item.get("cc") == "EUR":
                            eur_rate = round(float(item.get("rate")), 2)
                    
                    currency_text = (
                        f"💵 <b>ОФІЦІЙНИЙ КУРС ВАЛЮТ (НБУ):</b>\n\n"
                        f"🇺🇸 <b>Долар (USD):</b> {usd_rate} грн\n"
                        f"🇪🇺 <b>Євро (EUR):</b> {eur_rate} грн\n\n"
                        f"📊 <i>Оновлення курсу працює в автоматичному режимі.</i>"
                    )
                    # МИТТЄВА ВІДПРАВКА БЕЗ ЗАТРИМОК:
                    requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": currency_text, "parse_mode": "HTML"})
        except:
            pass
            
        time.sleep(14400) # Заснути на 4 години ПІСЛЯ відправки

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    airspace_thread = threading.Thread(target=check_airspace_details)
    airspace_thread.daemon = True
    airspace_thread.start()
    
    news_thread = threading.Thread(target=check_lviv_news_loop)
    news_thread.daemon = True
    news_thread.start()
    
    # Запускаємо валюту
    check_currency_loop()

