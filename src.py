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