import os
from dotenv import load_dotenv

load_dotenv()

# Backfill settings
_bl            = os.getenv('BACKFILL_LIMIT')
BACKFILL_LIMIT = int(_bl) if _bl is not None else None
PROGRESS_FILE  = os.getenv('PROGRESS_FILE', 'forwarder_progress.json')

# Range control
START_FROM_ID   = int(os.getenv('START_FROM_ID', '1'))
_stop           = os.getenv('STOP_AT_ID')
STOP_AT_ID      = int(_stop) if _stop is not None else None
IGNORE_PROGRESS = os.getenv('IGNORE_PROGRESS', 'false').lower() in ('true', '1', 'yes')

# Rate limiting
FORWARD_DELAY     = float(os.getenv('FORWARD_DELAY',     '1.5'))
FLOOD_WAIT_BUFFER = int(os.getenv(  'FLOOD_WAIT_BUFFER', '10'))
MAX_RETRIES       = int(os.getenv(  'MAX_RETRIES',       '3'))
