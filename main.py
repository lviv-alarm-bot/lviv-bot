import os
import time
import requests
from flask import Flask, jsonify
from threading import Thread

# 1. Налаштування Flask-сервера, щоб Render бачив "Web Service"
app = Flask('')

@app.route('/')
def home():
    return "Бот моніторингу працює!", 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run_server():
    # Render автоматично передає порт у змінну оточення PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Логіка моніторингу тривог DiMap
TOKEN = "9257983302:AAEbmL_VjbpITwCznZzRlnMXnItn8rL1QBM"
CHANNEL_ID = "@yoy_lviv_monitor"
API_URL = "https://ubilling.net.ua/aerialalerts/?json=true" # або міняйте на https://dimap.live

TARGET_REGIONS = ["Львів", "Львівська", "Львівський"]
current_alerts = {region: False for region in TARGET_REGIONS}

def send_telegram_message(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Помилка Telegram: {e}")

def check_alerts():
    global current_alerts
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code != 200:
            return
        
        json_data = response.json()
        active_alerts = json_data.get("alerts", [])
        
        # Збираємо регіони з червоним статусом тривоги
        regions_with_red_alert = []
        for alert in active_alerts:
            if alert.get("color") == "red" and alert.get("alertType") == "air":
                regions_with_red_alert.append(alert.get("region", ""))
        
        for target in TARGET_REGIONS:
            is_active_now = any(target in active_reg for active_reg in regions_with_red_alert)
            
            if is_active_now and not current_alerts[target]:
                current_alerts[target] = True
                send_telegram_message(f"🔴 *🚨 ПОВІТРЯНА ТРИВОГА на Львівщині!* \n\n📍 Регіон: *{target}*\n⚠️ Негайно прямуйте в укриття!")
                
            elif not is_active_now and current_alerts[target]:
                current_alerts[target] = False
                send_telegram_message(f"🟢 *✅ ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ!* \n\n📍 Регіон: *{target}*\n👍 Можна залишати укриття.")
    except Exception as e:
        print(f"Помилка моніторингу: {e}")

def monitor_loop():
    print("🚀 Цикл моніторингу DiMap запущено...")
    while True:
        check_alerts()
        time.sleep(20) # Опитування кожні 20 секунд

# 3. Головний запуск
if __name__ == "__main__":
    # Запускаємо веб-сервер у фоновому потоці
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Запускаємо моніторинг у головному потоці
    monitor_loop()
