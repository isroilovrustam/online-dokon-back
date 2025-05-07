# app_name/utils.py
import requests
from config.settings import BOT_B_TOKEN
bot_token = BOT_B_TOKEN

def send_telegram_message(chat_id, text, bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    response = requests.post(url, data=payload)
    return response.json()
