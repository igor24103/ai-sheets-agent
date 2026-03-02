#!/usr/bin/env python3
"""
AI Sheets Agent — Main Entry Point
Reads leads from Google Sheets, scores them with AI, writes results back.

Usage:
    python main.py              # Process once
    python main.py --watch      # Continuous polling mode
    python main.py --dry-run    # Preview without writing
"""
import argparse
import logging
import sys
import time
from datetime import datetime

from config import BATCH_SIZE, POLL_INTERVAL, LEADS_SHEET, PROCESSED_SHEET, ANALYTICS_SHEET
from sheets import SheetsManager
from agent import AIAgent
from notifier import notify_hot_lead, notify_batch_complete, notify_error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


# Expected sheet headers
HEADERS = ["Name", "Email", "Company", "Message", "Status", "Score", "Category", "Analysis", "AI_Response"]


def process_leads(sheets: SheetsManager, agent: AIAgent, dry_run: bool = False) -> dict:
    """Process unscored leads from Google Sheets"""
    
    # Ensure headers exist
    if not dry_run:
        sheets.ensure_headers(LEADS_SHEET, HEADERS)

    # Get unprocessed leads
    leads = sheets.get_unprocessed_leads(LEADS_SHEET)
    
    if not leads:
        logger.info("No new leads to process")
        return {"total": 0, "hot": 0, "warm": 0, "cold": 0}

    logger.info(f"Found {len(leads)} unprocessed leads (batch size: {BATCH_SIZE})")

    # Process in batches
    batch = leads[:BATCH_SIZE]
    stats = {"total": 0, "hot": 0, "warm": 0, "cold": 0, "scores": []}

    for lead in batch:
        name = lead.get("name", "Unknown")
        logger.info(f"Scoring lead: {name} ({lead.get('email', '')})")

        # Call AI agent
        result = agent.score_lead(lead)

        score = result["score"]
        category = result["category"]
        analysis = result["analysis"]
        response = result["response"]

        logger.info(f"  → Score: {score}/10 ({category}) — {analysis[:80]}")

        # Update counters
        stats["total"] += 1
        stats["scores"].append(score)
        stats[category] += 1

        # Write results back to sheet
        if not dry_run:
            row = lead["_row_number"]
            sheets.update_row(LEADS_SHEET, row, {
                "status": "processed",
                "score": str(score),
                "category": category,
                "analysis": analysis,
                "ai_response": response
            }, [h.lower().replace(" ", "_") for h in HEADERS])

            # Append to processed sheet for history
            sheets.append_row(PROCESSED_SHEET, [
                name, lead.get("email", ""), lead.get("company", ""),
                str(score), category, analysis,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ])

            # Notify on hot leads
            if category == "hot":
                notify_hot_lead(lead, result)

        # Rate limiting
        time.sleep(1)

    # Calculate analytics
    stats["avg_score"] = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
    stats["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write analytics
    if not dry_run and stats["total"] > 0:
        sheets.write_analytics(ANALYTICS_SHEET, stats)
        notify_batch_complete(stats["total"], stats["hot"], stats["warm"], stats["cold"])

    return stats


def main():
    parser = argparse.ArgumentParser(description="AI Sheets Agent — Lead Scoring Automation")
    parser.add_argument("--watch", action="store_true", help="Continuous polling mode")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to sheet")
    parser.add_argument("--provider", choices=["openai", "ollama"], help="Override AI provider")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("  AI Sheets Agent")
    logger.info("=" * 50)

    # Initialize components
    sheets = SheetsManager()
    agent = AIAgent(provider=args.provider)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE — no changes will be written")

    if args.watch:
        logger.info(f"👀 Watch mode — polling every {POLL_INTERVAL}s")
        while True:
            try:
                stats = process_leads(sheets, agent, dry_run=args.dry_run)
                if stats["total"] > 0:
                    logger.info(f"✅ Batch done: {stats['total']} leads (🔥{stats['hot']} 🟡{stats['warm']} 🔵{stats['cold']})")
            except KeyboardInterrupt:
                logger.info("Stopped by user")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                notify_error(str(e))
            
            time.sleep(POLL_INTERVAL)
    else:
        try:
            stats = process_leads(sheets, agent, dry_run=args.dry_run)
            logger.info(f"\n{'='*50}")
            logger.info(f"  Results: {stats['total']} processed")
            logger.info(f"  🔥 Hot: {stats['hot']}  🟡 Warm: {stats['warm']}  🔵 Cold: {stats['cold']}")
            if stats["scores"]:
                logger.info(f"  📊 Avg Score: {stats['avg_score']:.1f}/10")
            logger.info(f"{'='*50}")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            notify_error(str(e))
            sys.exit(1)


if __name__ == "__main__":
    main()
