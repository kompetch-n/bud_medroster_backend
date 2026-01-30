import os
import requests

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def send_line_message(to: str, message: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }

    payload = {
        "to": to,
        "messages": [
            {"type": "text", "text": message}
        ]
    }

    requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)
