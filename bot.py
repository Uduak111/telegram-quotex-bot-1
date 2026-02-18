import os
import asyncio
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==========================
# CONFIG
# ==========================

API_ID = 123456  # your api_id
API_HASH = "your_api_hash"
STRING_SESSION = "PASTE_YOUR_STRING_SESSION"

# Channel username or ID to copy trades from
SOURCE_CHANNEL = "sourcechannelusername"  # without @

# ==========================
# CLIENT
# ==========================

client = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

# ==========================
# SIMPLE TRADE PARSER
# ==========================

def parse_trade(message):
    """
    Example expected format:
    BUY BTCUSDT 65000
    SELL ETHUSDT 3200
    """

    pattern = r"(BUY|SELL)\s+([A-Z]+)\s+(\d+\.?\d*)"
    match = re.search(pattern, message)

    if match:
        side = match.group(1)
        symbol = match.group(2)
        price = float(match.group(3))

        return {
            "side": side,
            "symbol": symbol,
            "price": price
        }

    return None

# ==========================
# EVENT LISTENER
# ==========================

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    message = event.raw_text
    print("New signal received:")
    print(message)

    trade = parse_trade(message)

    if trade:
        print("Parsed trade:", trade)

        # 🔥 PLACE EXCHANGE ORDER HERE
        # execute_trade(trade)

    else:
        print("Message not recognized as trade signal.")

# ==========================
# MAIN
# ==========================

async def main():
    await client.start()
    print("Copy Trading Bot is running 🚀")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
