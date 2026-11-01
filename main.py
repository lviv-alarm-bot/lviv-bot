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
# Спеціальні пошукові стрічки для Львова (Погода, Світло, Транспорт)
WEATHER_URL = "https://google.com"
OBLENERGO_URL = "https://google.com"

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active and running multiple streams!")

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

# 2. АВТОМАТИЧНА ПОГОДА ТА СВІТЛО (Прості побутові новини)
def check_daily_utility_info():
    last_weather_title = None
    last_light_title = None
    
    while True:
        try:
            if not TOKEN:
                time.sleep(10)
                continue
                
            # Перевірка погоди у Львові
            weather_res = requests.get(WEATHER_URL, timeout=15)
            if weather_res.status_code == 200:
                w_root = ET.fromstring(weather_res.content)
                w_item = w_root.find(".//item")
                if w_item is not None:
                    w_title = w_item.find("title").text
                    if last_weather_title is not None and w_title != last_weather_title:
                        w_clean = w_title.split(" - ")[0]
                        bot_text = f"🌤 <b>ПОГОДА У ЛЬВОВІ | СВІЖИЙ ПРОГНОЗ</b>\n\n📌 {w_clean}\n\n🤖 <i>Вдалих та безпечних вам справ!</i>"
                        send_url = f"https://telegram.org{TOKEN}/sendMessage"
                        requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": bot_text, "parse_mode": "HTML"})
                    last_weather_title = w_title

            # Перевірка щоденних новин про світло від Львівобленерго
            light_res = requests.get(OBLENERGO_URL, timeout=15)
            if light_res.status_code == 200:
                l_root = ET.fromstring(light_res.content)
                l_item = l_root.find(".//item")
                if l_item is not None:
                    l_title = l_item.find("title").text
                    if last_light_title is not None and l_title != last_light_title:
                        l_clean = l_title.split(" - ")[0]
                        bot_text = f"💡 <b>ЕНЕРГЕТИКА | ЛЬВІВОБЛЕНЕРГО</b>\n\n📌 {l_clean}\n\n⚡ <i>Слідкуйте за оновленнями графіків у нашому каналі.</i>"
                        send_url = f"https://telegram.org{TOKEN}/sendMessage"
                        requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": bot_text, "parse_mode": "HTML"})
                    last_light_title = l_title

        except Exception as e:
            print(f"Помилка побутових новин: {e}")
            
        time.sleep(300) # Перевірка побутової інформації раз на 5 хвилин

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Потік для тривог
    airspace_thread = threading.Thread(target=check_airspace_details)
    airspace_thread.daemon = True
    airspace_thread.start()
    
    # Потік для щоденної інфи (Погода, Світло)
    check_daily_utility_info()
