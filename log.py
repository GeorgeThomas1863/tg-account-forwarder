import logging
import os
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('forwarder.log'),
    ]
)

log = logging.getLogger(__name__)

def load_progress():
    if not IGNORE_PROGRESS and os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            saved = data.get('last_forwarded_id', 0)
            if saved:
                return saved
    # Fall back to START_FROM_ID (subtract 1 since min_id is exclusive)
    return max(0, START_FROM_ID - 1)
 
def save_progress(message_id):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({
            'last_forwarded_id': message_id,
            'updated_at': datetime.utcnow().isoformat()
        }, f)