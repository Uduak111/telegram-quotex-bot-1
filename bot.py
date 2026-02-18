import os
import asyncio
import json
from telethon import TelegramClient, events
import websockets

# -----------------------------
# Environment Variables
# -----------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")
TARGET_GROUP = os.getenv("TARGET_GROUP")
QUOTEX_TOKEN = os.getenv("QUOTEX_TOKEN")
TRADE_AMOUNT = 1  # Default trade amount, can adjust

# -----------------------------
# Telegram Client
# -----------------------------
client = TelegramClient('session', API_ID, API_HASH)

# -----------------------------
# Parse trading signals
# -----------------------------
def parse_signal(message_text):
    """
    Example Telegram message:
    ✅ ENTRY CONFIRMED ✅
    🌎 Asset: TRX/USD (OTC)
    ⏳ Expiration: M1
    📊 Direction: 🟢 BUY
    """
    lines = message_text.split("\n")
    asset = None
    direction = None
    expiration = None

    for line in lines:
        if "Asset:" in line:
            asset = line.split("Asset:")[1].strip()
        if "Direction:" in line:
            direction = line.split("Direction:")[1].strip()
        if "Expiration:" in line:
            expiration = line.split("Expiration:")[1].strip()
    
    if asset and direction and expiration:
        return {
            "asset": asset,
            "direction": direction,
            "expiration": expiration,
            "amount": TRADE_AMOUNT
        }
    return None

# -----------------------------
# Quotex WebSocket
# -----------------------------
async def place_trade(trade_data):
    url = "wss://qxbroker.com/socket.io/?EIO=4&transport=websocket"
    async with websockets.connect(url) as ws:
        # Authenticate
        auth_payload = {
            "session": QUOTEX_TOKEN
        }
        await ws.send(json.dumps(["authorization", auth_payload]))
        
        # Example trade payload (simplified)
        trade_payload = {
            "cmd": "trade",
            "data": {
                "asset": trade_data["asset"],
                "direction": "buy" if "BUY" in trade_data["direction"].upper() else "sell",
                "expiration": trade_data["expiration"],
                "amount": trade_data["amount"]
            }
        }
        await ws.send(json.dumps(["trade", trade_payload]))
        print(f"Trade sent: {trade_payload}")

# -----------------------------
# Telegram event listener
# -----------------------------
@client.on(events.NewMessage(chats=TARGET_GROUP))
async def handler(event):
    msg = event.message.message
    trade = parse_signal(msg)
    if trade:
        print(f"Signal received: {trade}")
        await place_trade(trade)

# -----------------------------
# Run Telegram client
# -----------------------------
async def main():
    await client.start(phone=PHONE)
    print("Bot is now running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
