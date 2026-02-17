import os
from telethon import TelegramClient, events
import re
import requests
import time
from datetime import datetime

# --- Telegram API credentials ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE")
target_group = int(os.getenv("TARGET_GROUP"))

# --- Quotex token ---
qt_token = os.getenv("QUOTEX_TOKEN")

# --- Request headers ---
headers = {
    "Authorization": f"Bearer {qt_token}",
    "Content-Type": "application/json"
}

# --- Initialize Telegram client ---
client = TelegramClient("session", api_id, api_hash)


# ===== PARSE SIGNAL FROM TELEGRAM MESSAGE =====
def parse_signal(msg):
    msg = msg.lower()

    # Extract asset
    asset = re.search(r"asset:\s*([a-z0-9\/\-\(\) ]+)", msg)
    asset = asset.group(1).replace("(otc)", "").strip().upper() if asset else None

    # Direction
    if "buy" in msg:
        direction = "call"
    elif "sell" in msg:
        direction = "put"
    else:
        direction = None

    # Expiration
    exp = re.search(r"expiration:\s*m(\d+)", msg)
    duration = int(exp.group(1)) * 60 if exp else 60

    # Entry time
    entry = re.search(r"entry:\s*(\d{2}:\d{2})", msg)
    entry_time = entry.group(1) if entry else None

    # Gale count
    gale_count = 0
    if "1st gale" in msg:
        gale_count = 1
    if "2nd gale" in msg:
        gale_count = 2

    return {
        "asset": asset,
        "direction": direction,
        "duration": duration,
        "entry_time": entry_time,
        "gale_count": gale_count
    }


# ===== WAIT UNTIL A SPECIFIC TIME =====
def wait_until(time_str):
    target = datetime.strptime(time_str, "%H:%M").replace(
        year=datetime.now().year,
        month=datetime.now().month,
        day=datetime.now().day
    )
    while datetime.now() < target:
        time.sleep(0.4)


# ===== EXECUTE QUOTEX TRADE =====
def execute_trade(asset, direction, amount, duration):
    payload = {
        "asset": asset,
        "direction": direction,
        "amount": amount,
        "duration": duration
    }
    r = requests.post("https://api.quotex.io/v1/trade", json=payload, headers=headers)
    print("TRADE RESPONSE:", r.text)
    return r.text


# ===== LISTEN FOR NEW SIGNALS IN TARGET GROUP =====
@client.on(events.NewMessage(chats=target_group))
async def handler(event):
    text = event.message.message

    # Ignore irrelevant messages
    if "asset:" not in text.lower():
        return

    print("\n=== NEW SIGNAL DETECTED ===")
    data = parse_signal(text)
    print(data)

    if not data["asset"] or not data["direction"] or not data["entry_time"]:
        print("❌ INVALID SIGNAL — SKIPPING")
        return

    # Wait for entry time
    wait_until(data["entry_time"])
    print("✔ Executing main entry...")
    execute_trade(data["asset"], data["direction"], 1, data["duration"])

    # Gale entries
    for gale in range(1, data["gale_count"] + 1):
        gale_time = datetime.strptime(data["entry_time"], "%H:%M")
        gale_time = gale_time.replace(minute=gale_time.minute + gale)
        gale_time_str = gale_time.strftime("%H:%M")

        wait_until(gale_time_str)
        print(f"✔ Executing Gale {gale}...")
        execute_trade(data["asset"], data["direction"], 2 ** gale, data["duration"])


# ===== START BOT =====
client.start(phone=phone)
print("BOT RUNNING 24/7 ON RAILWAY...")
client.run_until_disconnected()
