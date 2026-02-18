import os
import asyncio
from telethon import TelegramClient, events

# -----------------------------
# Environment variables from Railway
# -----------------------------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TARGET_GROUP = os.getenv("TARGET_GROUP")  # Telegram group ID like -1001234567890
QUOTEX_TOKEN = os.getenv("QUOTEX_TOKEN")  # your demo or live token
# -----------------------------

# Use the pre-saved session file (from local login)
client = TelegramClient('session', API_ID, API_HASH)

# -----------------------------
# Listen to new messages in target group
# -----------------------------
@client.on(events.NewMessage(chats=TARGET_GROUP))
async def handle_message(event):
    message = event.raw_text
    print("New message received:", message)

    # -----------------------------
    # PLACEHOLDER: parse message and send trade to Quotex
    # Example:
    # if "BUY" in message:
    #     send_trade("BUY", asset, expiry)
    # -----------------------------

# -----------------------------
# Main bot runner
# -----------------------------
async def main():
    await client.start()  # Uses session.session; no login input needed
    print("Bot is now running...")
    await client.run_until_disconnected()  # Keeps bot alive

asyncio.run(main())
