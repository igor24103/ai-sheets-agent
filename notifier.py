"""
Notification service — Telegram alerts for processed leads
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def send_telegram(message: str) -> bool:
    """Send message via Telegram Bot API"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured, skipping notification")
        return False

    payload = json.dumps({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }).encode()

    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
        return False


def notify_hot_lead(lead: Dict, result: Dict):
    """Send alert for high-score leads"""
    message = (
        f"🔥 *Hot Lead Detected!*\n\n"
        f"👤 *{lead.get('name', 'Unknown')}*\n"
        f"🏢 {lead.get('company', 'N/A')}\n"
        f"📧 {lead.get('email', 'N/A')}\n"
        f"⭐ Score: *{result.get('score', 0)}/10*\n\n"
        f"📊 _{result.get('analysis', '')}_"
    )
    send_telegram(message)


def notify_batch_complete(total: int, hot: int, warm: int, cold: int):
    """Send batch processing summary"""
    message = (
        f"✅ *Batch Processing Complete*\n\n"
        f"📊 Processed: *{total}* leads\n"
        f"🔥 Hot: *{hot}*\n"
        f"🟡 Warm: *{warm}*\n"
        f"🔵 Cold: *{cold}*"
    )
    send_telegram(message)


def notify_error(error: str):
    """Send error alert"""
    send_telegram(f"🚨 *AI Sheets Agent Error*\n\n`{error}`")
