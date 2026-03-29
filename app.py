"""
Telegram Channel Forwarder
==========================
Forwards messages from a source channel to a destination channel
using a Telethon userbot. Handles backfill of historical messages
and live forwarding of new messages, with aggressive rate limit handling.
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError
from log import log
from src import resolve_channel, register_live_handler, backfill

load_dotenv()

# Credentials and channel identifiers — loaded from .env, never hardcoded
SESSION_NAME   = os.getenv('SESSION_NAME')
API_ID         = int(os.getenv('API_ID', 0))   # Telethon requires int
API_HASH       = os.getenv('API_HASH')
PHONE          = os.getenv('PHONE')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL', '')
DEST_CHANNEL   = os.getenv('DEST_CHANNEL',   '')
DO_BACKFILL    = os.getenv('DO_BACKFILL', 'true').lower() not in ('false', '0', 'no')


async def main():
    log.info('Starting Telegram Channel Forwarder')
 
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
 
    await client.start(phone=PHONE)
    log.info('Logged in successfully')
 
    # Resolve entities once at startup
    try:
        source = await resolve_channel(client, SOURCE_CHANNEL)
        dest   = await resolve_channel(client, DEST_CHANNEL)
    except ChannelPrivateError:
        log.error(
            'Cannot access source channel — make sure your account is a member.'
        )
        return
    except Exception as e:
        log.error(f'Failed to resolve channels: {e}')
        return
 
    log.info(f'Source : {getattr(source, "title", SOURCE_CHANNEL)}')
    log.info(f'Dest   : {getattr(dest, "title", DEST_CHANNEL)}')
 
    # Register live handler before backfill so no new messages are missed
    # during the (potentially very long) backfill process
    register_live_handler(client, source, dest)
    log.info('Live forwarding handler registered')
 
    if DO_BACKFILL:
        log.info('Starting backfill — this may take a long time for large channels')
        await backfill(client, source, dest)
 
    log.info('Entering live monitoring mode...')
    await client.run_until_disconnected()
 
 
if __name__ == '__main__':
    asyncio.run(main())