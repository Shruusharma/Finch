import logging
from fastapi import APIRouter, HTTPException
from agents.insight_agent import generate_weekly_insight
from memory.insight_store import get_latest_insight

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/insights/generate")
async def generate_insight():
    """
    Triggers generation of a new weekly insight report.
    Intended to be called by a scheduler (Railway cron, Phase 10),
    but can be called manually for testing.
    """
    try:
        report = generate_weekly_insight()
        return {"status": "generated", "report": report}
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(status_code=500, detail="Insight generation failed")


@router.get("/insights/latest")
async def latest_insight():
    """
    Returns the most recently generated insight report, if any.
    """
    insight = get_latest_insight()
    if insight is None:
        raise HTTPException(status_code=404, detail="No insight report generated yet")
    return insight