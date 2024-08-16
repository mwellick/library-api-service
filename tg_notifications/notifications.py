import os
from dotenv import load_dotenv
import requests

load_dotenv()

TG_TOKEN = os.environ.get("TG_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


def send_message(message: str):
    tg_api_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    tg_response = requests.get(tg_api_url)

    if tg_response.status_code == 200:
        print("INFO: The message has been sent")
    else:
        raise Exception(f"Error sending message: {message} ")
