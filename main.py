import os
import time
import requests
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

# Повністю забираємо токен із коду. Тепер він житиме лише в пам'яті Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = "@yoy_lviv_monitor" 
PS_API_URL = "https://i-scuba.com"

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active and monitoring airspace!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    server.serve_forever()

def check_airspace_details():
    last_processed_guid = None
    print("Розумний моніторинг курсу БПЛА та Ракет для Львівщини активовано...")
    keywords = ["львів", "львівщин", "стрий", "золочів", "червоноград", "самбір", "броди", "яворів", "західн", "заходу"]
    
    while True:
        try:
            if not TOKEN:
                time.sleep(30)
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
            print(f"Помилка оновлення даних ПС ЗСУ: {e}")
            
        time.sleep(20)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    if TOKEN:
        try:
            test_text = "🔄 <b>Систему моніторингу активовано!</b>\n\nБот успішно підключився до каналу. Тепер сповіщення про рух Шахедів та Ракет на підльоті до Львівщини публікуватимуться автоматично 24/7."
            send_url = f"https://telegram.org{TOKEN}/sendMessage"
            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": test_text, "parse_mode": "HTML"})
        except:
            pass
        
    check_airspace_details()

