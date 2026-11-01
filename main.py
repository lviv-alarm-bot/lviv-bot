import time
import requests

# Дані вашого бота та каналу прописані автоматично:
TOKEN = "9257983302:AAGYlPVE18uIAkwbNeOvDZ0_uQ3L-I77Yss"
CHANNEL_ID = "@yoy_lviv_monitor" 
REGION_ID = "14" # ID Львівської області у базі загроз

API_URL = "https://ubilling.net.ua/aerialalerts/?json=true"

def check_alarm():
    last_state = None
    print("Моніторинг каналу @yoy_lviv_monitor запущено. Шукаємо загрози для Львівщини...")
    
    while True:
        try:
            response = requests.get(API_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                is_active = REGION_ID in data
                
                if last_state is not None and is_active != last_state:
                    if is_active:
                        text = "🚨 **ПОВІТРЯНА ТРИВОГА У ЛЬВІВСЬКІЙ ОБЛАСТІ!**\n\n⚠️ Зафіксовано загрозу! Перейдіть в укриття. Можливий рух ракет або ворожих БПЛА (дронів)."
                    else:
                        text = "🟢 **ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ у Львівській області.**\n\nНебезпека минула. Дякуємо Силам ППО!"
                    
                    send_url = f"https://telegram.org{TOKEN}/sendMessage"
                    requests.post(send_url, json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "Markdown"})
                
                last_state = is_active
        except Exception as e:
            print(f"Тимчасова помилка мережі: {e}")
            
        time.sleep(10) # Перевірка кожні 10 секунд

if __name__ == "__main__":
    check_alarm()
