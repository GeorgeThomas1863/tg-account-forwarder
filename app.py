"""
Telegram Channel Forwarder
==========================
Forwards messages from a source channel to a destination channel
using a Telethon userbot. Handles backfill of historical messages
and live forwarding of new messages, with aggressive rate limit handling.
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError
from log import log

from src import resolve_channel, register_live_handler, backfill
from dotenv import load_dotenv

load_dotenv()

SESSION_NAME = os.getenv('SESSION_NAME')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')

SOURCE_CHANNEL  = ''           # username (no @) or numeric ID e.g. -1001234567890
DEST_CHANNEL    = ''           # username (no @) or numeric ID
 
# Backfill settings
DO_BACKFILL         = True     # set False to only forward new messages going forward
BACKFILL_LIMIT      = None     # None = all messages; set e.g. 1000 to cap it
PROGRESS_FILE       = 'forwarder_progress.json'  # tracks last forwarded message ID
 
# Range control
# START_FROM_ID: first message ID to forward. Defaults to 1 (beginning of channel).
#   If a progress file exists from a previous run, it takes precedence unless
#   you set IGNORE_PROGRESS = True.
# STOP_AT_ID: last message ID to forward (inclusive). None = no stop, run forever.
#   Applies to both backfill and live forwarding.
START_FROM_ID       = 1       # e.g. 1003 to start at message 1003
STOP_AT_ID          = None    # e.g. 5000 to stop after message 5000
IGNORE_PROGRESS     = False   # set True to force START_FROM_ID even if progress file exists
 
# Rate limiting — conservative defaults, tune if you get FloodWaits
FORWARD_DELAY       = 1.5      # seconds between each forward during backfill
FLOOD_WAIT_BUFFER   = 10       # extra seconds added on top of Telegram's flood wait
MAX_RETRIES         = 5        # per-message retry attempts before skipping



SOURCE_CHANNEL
DEST_CHANNEL = os.getenv('DEST_CHANNEL')
DO_BACKFILL = os.getenv('DO_BACKFILL')
BACKFILL_LIMIT = os.getenv('BACKFILL_LIMIT')
PROGRESS_FILE = os.getenv('PROGRESS_FILE')


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