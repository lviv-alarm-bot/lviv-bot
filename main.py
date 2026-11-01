import time
import requests

TOKEN = "9257983302:AAGYlPVE18uIAkwbNeOvDZ0_uQ3L-I77Yss"
CHANNEL_ID = "@yoy_lviv_monitor" 
REGION_ID = "14" # ID Львівської області

API_URL = "https://ubilling.net.ua"

def check_alarm():
    last_state = None
    print("Моніторинг запущено на сервері Render. Шукаємо загрози...")
    
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
                print("Перевірка статусу успішна. Загрози:", "ТАК" if is_active else "НІ")
        except Exception as e:
            print(f"Помилка мережі: {e}")
            
        time.sleep(10) # Перевірка кожні 10 секунд

if __name__ == "__main__":
    check_alarm()
