import asyncio
import os
from log import log, load_progress, save_progress
from config import (
    MAX_RETRIES, FLOOD_WAIT_BUFFER,
    IGNORE_PROGRESS, PROGRESS_FILE,
    STOP_AT_ID, BACKFILL_LIMIT, FORWARD_DELAY,
)
from telethon import events
from telethon.errors import (
    FloodWaitError,
    ChatForwardsRestrictedError,
    MessageIdInvalidError
)
from telethon.tl.patched import MessageService
from telethon.tl.types import PeerChannel, PeerChat



async def forward_with_retry(client, dest, message):
    if isinstance(message, MessageService):
        log.debug(f'msg {message.id}: Skipping service message (type {type(message).__name__})')
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await client.forward_messages(dest, message)
            return True
 
        except FloodWaitError as e:
            wait = e.seconds + FLOOD_WAIT_BUFFER
            log.warning(
                f'FloodWaitError on msg {message.id}: Telegram says wait {e.seconds}s. '
                f'Sleeping {wait}s (attempt {attempt}/{MAX_RETRIES})'
            )
            await asyncio.sleep(wait)
 
        except ChatForwardsRestrictedError:
            # Channel has forwards disabled — nothing we can do per message
            log.error(
                f'msg {message.id}: Channel has forwarding restricted. '
                f'Cannot forward this message.'
            )
            return False
 
        except MessageIdInvalidError:
            log.warning(f'msg {message.id}: Invalid message ID, skipping.')
            return False
 
        except Exception as e:
            log.error(f'msg {message.id}: Unexpected error on attempt {attempt}: {e}')
            if attempt < MAX_RETRIES:
                backoff = attempt * 5
                log.info(f'Retrying in {backoff}s...')
                await asyncio.sleep(backoff)
            else:
                log.error(f'msg {message.id}: Max retries reached, skipping.')
                return False
 
    return False
 
# ---------------------------------------------------------------------------
# BACKFILL
# Iterates through all historical messages oldest-first and forwards each.
# Resumes from last saved progress if the script was previously interrupted.
# ---------------------------------------------------------------------------
 
async def backfill(client, source, dest):
    last_id = load_progress()
    start_id = last_id + 1  # human-readable start for logging
 
    if last_id and not IGNORE_PROGRESS and os.path.exists(PROGRESS_FILE):
        log.info(f'Resuming backfill from message ID {start_id} (from progress file)')
    else:
        log.info(f'Starting backfill from message ID {start_id}')
 
    if STOP_AT_ID:
        log.info(f'Backfill will stop at message ID {STOP_AT_ID} (inclusive)')
    else:
        log.info('No stop ID set — will forward all available messages')
 
    forwarded  = 0
    skipped    = 0
    total_seen = 0
 
    async for message in client.iter_messages(
        source,
        limit=BACKFILL_LIMIT,
        reverse=True,
        min_id=last_id,
    ):
        total_seen += 1
 
        # Honor STOP_AT_ID — stop backfill once we pass it
        if STOP_AT_ID and message.id > STOP_AT_ID:
            log.info(f'[Backfill] Reached STOP_AT_ID {STOP_AT_ID}, stopping backfill.')
            break
 
        if not message.id:
            continue
 
        success = await forward_with_retry(client, dest, message)
 
        if success:
            forwarded += 1
            save_progress(message.id)
            log.info(
                f'[Backfill] Forwarded msg {message.id} '
                f'({forwarded} done, {skipped} skipped)'
            )
        else:
            skipped += 1
 
        await asyncio.sleep(FORWARD_DELAY)
 
        if total_seen % 100 == 0:
            log.info(
                f'[Backfill] Progress: {total_seen} seen, '
                f'{forwarded} forwarded, {skipped} skipped'
            )
 
    log.info(
        f'[Backfill] Complete. '
        f'{forwarded} forwarded, {skipped} skipped out of {total_seen} messages.'
    )
 
# ---------------------------------------------------------------------------
# LIVE FORWARDING
# Event handler that fires on every new message in the source channel.
# ---------------------------------------------------------------------------
 
def register_live_handler(client, source, dest):
 
    @client.on(events.NewMessage(chats=source))
    async def handler(event):
        message = event.message
 
        # If a stop ID is set, ignore anything beyond it
        if STOP_AT_ID and message.id > STOP_AT_ID:
            log.info(
                f'[Live] Message {message.id} exceeds STOP_AT_ID {STOP_AT_ID}, ignoring.'
            )
            return
 
        log.info(f'[Live] New message {message.id} detected, forwarding...')
 
        success = await forward_with_retry(client, dest, message)
 
        if success:
            save_progress(message.id)
            log.info(f'[Live] Forwarded message {message.id}')
        else:
            log.warning(f'[Live] Failed to forward message {message.id}')
 
# ---------------------------------------------------------------------------
# RESOLVE CHANNEL HELPER
# Accepts either a @username string or a numeric ID (int or string).
# ---------------------------------------------------------------------------
 
async def resolve_channel(client, identifier):
    try:
        numeric = int(identifier)
        str_id = str(identifier)
        if str_id.startswith('-100'):
            # Supergroup / broadcast channel — strip the -100 prefix
            channel_id = int(str_id[4:])
            peer = PeerChannel(channel_id)
        elif numeric < 0:
            # Legacy group chat (negative, but no -100 prefix)
            peer = PeerChat(abs(numeric))
        else:
            # Bare positive channel/supergroup ID
            peer = PeerChannel(numeric)
        return await client.get_entity(peer)
    except (ValueError, TypeError):
        pass
    # Username or invite link — pass through unchanged
    return await client.get_entity(identifier)