import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

INSIGHT_FILE = Path("./data/latest_insight.json")


def save_insight(text: str) -> None:
    """Saves the latest insight report to disk, with a timestamp."""
    INSIGHT_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report": text,
    }

    with open(INSIGHT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved insight report ({len(text)} chars)")


def get_latest_insight() -> dict | None:
    """Returns the latest insight report, or None if none exists yet."""
    if not INSIGHT_FILE.exists():
        return None

    with open(INSIGHT_FILE, "r") as f:
        return json.load(f)