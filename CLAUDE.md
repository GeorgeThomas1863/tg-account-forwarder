# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Important: You are the orchestrator. Your subagents execute. You should NOT build, verify, or code inline (if possible). Your job is to plan, prioritize & coordinate the acitons of your subagents!

Keep your replies extremely concise and focus on providing necessary information.

Put all pictures / screenshots you take with the mcp plugin in the "pics" subfolder, under the .claude folder in THIS project.

Do NOT commit anything to GitHub. The user will control all commits to GitHub. Do NOT edit or in any way change the user's Git history or interact with GitHub.

## Project Overview

A Telegram userbot that forwards messages from a source channel to a destination channel. Supports historical backfill and live real-time forwarding with rate-limit resilience and progress persistence.

## Architecture

Three files, each with a single responsibility:

- **`app.py`** — Orchestration: loads config, initializes Telethon client, resolves channels, registers live handler, runs backfill, then runs the client loop indefinitely.
- **`src.py`** — Core forwarding logic: `forward_with_retry()` wraps Telethon's `forward_messages()` with exponential backoff, FloodWait handling, and skip logic for restricted/invalid messages.
- **`log.py`** — Progress persistence: reads/writes a JSON file storing the last successfully forwarded message ID, enabling resumption after interruption.

### Key Behavioral Detail

The live event handler is registered **before** backfill begins. This ensures no messages are missed during long backfill operations — live messages queue up and are forwarded after backfill completes.

### Error Handling Hierarchy

1. `FloodWaitError` → sleep the required duration + buffer, then retry
2. `ChatForwardsRestrictedError` → skip silently
3. `MessageIdInvalidError` → skip silently
4. General errors → exponential backoff (`5s × attempt`), up to `MAX_RETRIES`
