import os
import time
from datetime import datetime
import requests
import pytz
from flask import Flask, jsonify
from threading import Thread

# 1. Налаштування веб-сервера Flask для Render
app = Flask('')

@app.route('/')
def home():
    return "Active Monitor Bot is running!", 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Основна конфігурація бота
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = "@yoy_lviv_monitor"
API_URL = "https://dimap.live"

TARGET_REGIONS = ["Львів", "Львівська", "Львівський"]
current_alerts = {region: False for region in TARGET_REGIONS}

# Змінні для відстеження надсилання звітів (щоб надсилати лише 1 раз на вказану годину)
last_morning_date = ""
last_afternoon_date = ""
last_evening_date = ""

def send_telegram_message(text):
    if not TOKEN:
        print("[Помилка] Токен TELEGRAM_TOKEN не знайдено!")
        return
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Помилка Telegram: {e}")

# --- ФУНКЦІЇ ОТРИМАННЯ ДАНИХ ---

def get_weather():
    """Отримує поточну погоду для Львова"""
    try:
        url = "https://open-meteo.com"
        res = requests.get(url, timeout=10).json()
        current = res.get("current_weather", {})
        temp = current.get("temperature", "?")
        wind = current.get("windspeed", "?")
        return f"🌡 Температура: *{temp}°C*\n💨 Вітер: *{wind} км/год*"
    except:
        return "🌡 Погода: *Тимчасово недоступна*"

def get_currency():
    """Отримує актуальний курс валют НБУ"""
    try:
        url = "https://bank.gov.ua"
        data = requests.get(url, timeout=10).json()
        usd = next(item for item in data if item["cc"] == "USD")["rate"]
        eur = next(item for item in data if item["cc"] == "EUR")["rate"]
        return f"💵 USD: *{usd:.2f} грн*\n💶 EUR: *{eur:.2f} грн*"
    except:
        return "💵 Курс валют: *Тимчасово недоступний*"

# --- ОСНОВНІ ЦИКЛИ ---

def check_alerts():
    """Моніторинг повітряних тривог"""
    global current_alerts
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code != 200:
            return
        
        json_data = response.json()
        active_alerts = json_data.get("alerts", [])
        
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
        print(f"Помилка моніторингу тривог: {e}")

def check_time_for_reports():
    """Перевіряє час для надсилання ранкових, денних та вечірніх новин"""
    global last_morning_date, last_afternoon_date, last_evening_date
    try:
        kyiv_tz = pytz.timezone("Europe/Kiev")
        now_kyiv = datetime.now(kyiv_tz)
        current_date = now_kyiv.strftime("%Y-%m-%d")
        current_hour = now_kyiv.hour

        # 🌅 РАНОК (О 8:00 або пізніше, якщо сервер перезапускався)
        if current_hour >= 8 and current_hour < 14 and last_morning_date != current_date:
            last_morning_date = current_date
            weather_info = get_weather()
            currency_info = get_currency()
            message = (
                f"🌅 *ДОБРОГО РАНКУ, ЛЬВІВ!* 🇺🇦\n"
                f"📅 Дата: *{now_kyiv.strftime('%d.%m.%Y')}*\n\n"
                f"🌤 *Погода у місті:*\n{weather_info}\n\n"
                f"📊 *Офіційний курс валют (НБУ):*\n{currency_info}\n\n"
                f"🔔 _Канал стежить за безпекою. Вдалого дня!_"
            )
            send_telegram_message(message)

        # 🏙 ОБІД (О 14:00 або пізніше)
        elif current_hour >= 14 and current_hour < 21 and last_afternoon_date != current_date:
            last_afternoon_date = current_date
            weather_info = get_weather()
            message = (
                f"🏙 *ОБІДНІЙ ІНФОБЛОК* \n"
                f"🕒 Час: *{now_kyiv.strftime('%H:%M')}*\n\n"
                f"🌤 *Актуальна погода зараз:*\n{weather_info}\n\n"
                f"ℹ️ На каналі триває автоматичний моніторинг повітряного простору. "
                f"У разі небезпеки сповіщення з'явиться тут миттєво."
            )
            send_telegram_message(message)

        # 🌌 ВЕЧІР (О 21:00 або пізніше)
        elif current_hour >= 21 and last_evening_date != current_date:
            last_evening_date = current_date
            weather_info = get_weather()
            message = (
                f"🌌 *ТИХОГО ВЕЧОРА, ЛЬВІВ!* \n"
                f"🌛 Час відпочинку та затишку.\n\n"
                f"🌤 *Погода на вечір/ніч:*\n{weather_info}\n\n"
                f"🛡 _Наш моніторинг працює 24/7 без вихідних. Навіть вночі бот надішле сигнал тривоги, якщо виникне загроза. Спокійної та тихої ночі!_ ✨"
            )
            send_telegram_message(message)

    except Exception as e:
        print(f"Помилка таймера новин: {e}")

def monitor_loop():
    print("🚀 Розширений триразовий моніторинг запущено...")
    while True:
        check_alerts()           # Перевірка тривог (кожні 20 секунд)
        check_time_for_reports()  # Перевірка розкладу публікацій
        time.sleep(20)

if __name__ == "__main__":
    server_thread = Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    monitor_loop()
