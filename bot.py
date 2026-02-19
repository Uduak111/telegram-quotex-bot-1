# nextqx_copy_bot_railway.py

import os
import re
import asyncio
import json
import csv
from telethon import TelegramClient, events
import websockets
from datetime import datetime

# -----------------------------
# ENV VARIABLES (RAILWAY)
# -----------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
QX_PHONE = os.getenv("QX_PHONE")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

TRADE_AMOUNT = 5
DEFAULT_TIMEFRAME = "M1"
CSV_FILE = "trade_log.csv"

# Debug
print(f"[{datetime.now()}] [DEBUG] API_ID: {API_ID}")
print(f"[{datetime.now()}] [DEBUG] API_HASH exists: {bool(API_HASH)}")
print(f"[{datetime.now()}] [DEBUG] TELEGRAM PHONE exists: {bool(PHONE)}")
print(f"[{datetime.now()}] [DEBUG] QUOTEX PHONE exists: {bool(QX_PHONE)}")
print(f"[{datetime.now()}] [DEBUG] CHANNEL_ID: {CHANNEL_ID}")

# -----------------------------
# PARSE SIGNALS
# -----------------------------
def parse_signal(message):
    try:
        pair_match = re.search(r'💳\s*(\S+)', message)
        pair = pair_match.group(1).replace("-", "/") if pair_match else None

        tf_match = re.search(r'🔥\s*(M\d+)', message)
        timeframe = tf_match.group(1) if tf_match else DEFAULT_TIMEFRAME

        dir_match = re.search(r'🟥SELL|🟩BUY', message)
        direction = None
        if dir_match:
            if "SELL" in dir_match.group(0):
                direction = "PUT"
            else:
                direction = "CALL"

        return pair, direction, timeframe
    except Exception as e:
        print(f"[{datetime.now()}] Error parsing signal:", e)
        return None, None, None

# -----------------------------
# CSV LOGGING
# -----------------------------
def log_trade(pair, direction, amount, timeframe):
    header = ["timestamp", "pair", "direction", "amount", "timeframe"]
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow([datetime.now(), pair, direction, amount, timeframe])
    print(f"[{datetime.now()}] [CSV] Trade logged")

# -----------------------------
# QUOTEX CLIENT WITH AUTO-RETRY
# -----------------------------
class QuotexClient:
    def __init__(self, phone):
        self.phone = phone
        self.ws_url = "wss://trade.quotex.io/websocket"
        self.ws = None

    async def connect(self):
        attempt = 1
        while True:
            try:
                self.ws = await websockets.connect(self.ws_url)
                print(f"[{datetime.now()}] [Quotex] Connected to WebSocket")
                await self.login()
                break
            except Exception as e:
                print(f"[{datetime.now()}] [Quotex] Connection failed: {e}")
                print(f"[{datetime.now()}] Retrying in 5 seconds... (Attempt {attempt})")
                attempt += 1
                await asyncio.sleep(5)

    async def login(self):
        login_packet = json.dumps({
            "method": "auth.login",
            "params": {"phone": self.phone}
        })
        await self.ws.send(login_packet)
        print(f"[{datetime.now()}] [Quotex] Phone login sent")

    async def place_trade(self, pair, direction, amount, timeframe="M1"):
        if not self.ws:
            print(f"[{datetime.now()}] [Quotex] WebSocket not connected yet")
            return
        try:
            trade_packet = json.dumps({
                "method": "trade.create",
                "params": {
                    "pair": pair,
                    "direction": direction,
                    "amount": amount,
                    "timeframe": timeframe
                }
            })
            await self.ws.send(trade_packet)
            print(f"[{datetime.now()}] [Quotex] Trade sent: {pair} {direction} ${amount} {timeframe}")
            log_trade(pair, direction, amount, timeframe)
        except Exception as e:
            print(f"[{datetime.now()}] [Quotex] Error sending trade:", e)

# -----------------------------
# TELEGRAM CLIENT
# -----------------------------
async def main():
    # Start Quotex client with auto-retry
    qx_client = QuotexClient(QX_PHONE)
    asyncio.create_task(qx_client.connect())

    # Start Telegram client (session file included)
    client = TelegramClient("nextqx_session", API_ID, API_HASH)
    await client.start()
    print(f"[{datetime.now()}] [Telegram] Client started")

    @client.on(events.NewMessage(chats=CHANNEL_ID))
    async def handler(event):
        message = event.message.message
        pair, direction, timeframe = parse_signal(message)
        if pair and direction:
            print(f"[{datetime.now()}] [Signal] {pair} {direction} {timeframe}")
            await qx_client.place_trade(pair, direction, TRADE_AMOUNT, timeframe)
        else:
            print(f"[{datetime.now()}] [Signal] Could not parse message")

    print(f"[{datetime.now()}] [Bot] Listening for signals...")
    await client.run_until_disconnected()

# Run
asyncio.run(main())
