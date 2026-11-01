import time
import requests
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "9257983302:AAGYlPVE18uIAkwbNeOvDZ0_uQ3L-I77Yss"
CHANNEL_ID = "@yoy_lviv_monitor" 

# Джерело оперативної інформації Повітряних Сил ЗСУ (дзеркало у форматі RSS)
PS_API_URL = "https://i-scuba.com"

# --- ВЕБ-СЕРВЕР ДЛЯ ОБХОДУ СНУ НА RENDER ---
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active and monitoring airspace!")

def run_web_server():
    import os
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    server.serve_forever()

# --- ЛОГІКА МОНІТОРУ НАПРЯМКУ ДРОНІВ ТА РАКЕТ ---
def check_airspace_details():
    last_processed_guid = None
    print("Розумний моніторинг курсу БПЛА та Ракет для Львівщини активовано...")
    
    # Ключові слова для фільтрації новин саме по нашому регіону
    keywords = ["львів", "львівщин", "стрий", "золочів", "червоноград", "самбір", "броди", "яворів", "західн", "заходу"]
    
    while True:
        try:
            response = requests.get(PS_API_URL, timeout=15)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                latest_item = root.find(".//item")
                
                if latest_item is not None:
                    guid = latest_item.find("guid").text
                    title = latest_item.find("title").text
                    # Отримуємо повний текст повідомлення
                    description = latest_item.find("description").text if latest_item.find("description") is not None else title
                    
                    if last_processed_guid is not None and guid != last_processed_guid:
                        text_to_check = description.lower()
                        
                        # Перевіряємо, чи стосується свіжа оперативка Львівської області
                        if any(word in text_to_check for word in keywords):
                            # Формуємо красивий пост із напрямком руху цілей
                            bot_text = f"⚠️ **ОПЕРАТИВНА ІНФОРМАЦІЯ ПРО РУХ ЦІЛЕЙ:**\n\n📌 {description}\n\n🚨 *Будьте уважні, загроза безпосередньо для нашого регіону!*"
                            
                            send_url = f"https://telegram.org{TOKEN}/sendMessage"
                            requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": bot_text, "parse_mode": "HTML"})
                            print(f"Опубліковано оперативну інформацію: {title}")
                    
                    last_processed_guid = guid
        except Exception as e:
            print(f"Помилка оновлення даних ПС ЗСУ: {e}")
            
        time.sleep(20) # Перевірка кожні 20 секунд (оперативно для БПЛА)

if __name__ == "__main__":
    # Запуск веб-сайту-будильника
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Тестове повідомлення в канал про успішне оновлення системи
    try:
        requests.post(f"https://telegram.org{TOKEN}/sendMessage", json={"chat_id": CHANNEL_ID, "text": "🔄 **Систему моніторингу оновлено!**\n\nТепер бот автоматично відстежуватиме напрямок руху Шахедів/Ракет та публікуватиме деталі, як тільки вони з'являться на підльоті до Львівщини.", "parse_mode": "Markdown"})
    except:
        pass
        
    # Запуск розумного моніторингу
    check_airspace_details()
