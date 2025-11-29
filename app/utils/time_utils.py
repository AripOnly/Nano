# app/tools/utils/time_utils.py

from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time(timezone: str = "Asia/Makassar") -> str:
    """
    Dapatkan waktu sekarang dengan format lengkap.

    Args:
        timezone: Timezone string (default: Asia/Makassar)

    Returns:
        String waktu format: "Friday, 17-10-2025 02:33:34 WITA"
    """
    try:
        now = datetime.now(ZoneInfo(timezone))
        return now.strftime("%A, %d-%m-%Y %H:%M:%S %Z")
    except Exception:
        # Fallback ke local time
        return datetime.now().strftime("%A, %d-%m-%Y %H:%M:%S")


def get_timestamp(timezone: str = "Asia/Makassar") -> str:
    """
    Dapatkan timestamp untuk logging/file naming.

    Returns:
        String format: "2025-10-17_02-33-34"
    """
    try:
        now = datetime.now(ZoneInfo(timezone))
        return now.strftime("%Y-%m-%d_%H-%M-%S")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
