import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = "9257983302:AAGYlPVE18uIAkwbNeOvDZ0_uQ3L-I77Yss"
CHANNEL_ID = "@yoy_lviv_monitor" 
REGION_ID = "14" 

# Використовуємо стабільне API мапи тривог
API_URL = "https://ubilling.net.ua/aerialalerts/?json=true"

# --- СТВОРЕННЯ МІНІ-САЙТУ ДЛЯ ОБХОДУ СНУ ---
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is alive and working!")

def run_web_server():
    # Render автоматично дає порт у змінній оточення PORT, або використовуємо 8080
    import os
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    print(f"Веб-сервер для утримання активності запущено на порту {port}")
    server.serve_forever()

# --- ОСНОВНА ЛОГІКА БОТА ---
def check_alarm():
    last_state = None
    print("Моніторинг загроз активовано...")
    
    while True:
        try:
            response = requests.get(API_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                is_active = REGION_ID in data
                
                if last_state is not None and is_active != last_state:
                    if is_active:
                        text = "🚨 **ПОВІТРЯНА TРИВОГА У ЛЬВІВСЬКІЙ ОБЛАСТІ!**\n\n⚠️ Зафіксовано загрозу! Перейдіть в укриття. Можливий рух ракет або ворожих БПЛА (дронів)."
                    else:
                        text = "🟢 **ВІДБІЙ ПОВІТРЯНОЇ TРИВОГИ у Львівській області.**\n\nНебезпека минула. Дякуємо Силам ППО!"
                    
                    send_url = f"https://telegram.org{TOKEN}/sendMessage"
                    requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"})
                
                last_state = is_active
                print("Статус успішно перевірено, загрози:", "ТАК" if is_active else "НІ")
        except Exception as e:
            print(f"Помилка мережі: {e}")
            
        time.sleep(15) # Перевірка кожні 15 секунд

if __name__ == "__main__":
    # Запускаємо веб-сайт в окремому потоці, щоб він не заважав боту перевіряти тривоги
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    # Запускаємо самого бота
    check_alarm()
