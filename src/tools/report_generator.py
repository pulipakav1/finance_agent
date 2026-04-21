"""
Tool: generate_report
Writes a structured markdown investment report to disk.
"""

import os
from pathlib import Path
from datetime import datetime
from loguru import logger

from config.settings import settings


def generate_report(
    ticker: str,
    title: str,
    content: str,
    recommendation: str = "NEUTRAL",
) -> dict:
    """
    Save a structured investment report as a markdown file.

    Args:
        ticker: Stock ticker symbol
        title: Report title
        content: Full markdown report content
        recommendation: BUY / HOLD / SELL / NEUTRAL

    Returns:
        Dict with file path and report metadata
    """
    try:
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename   = f"{ticker.upper()}_{timestamp}.md"
        file_path  = reports_dir / filename

        # Build full report with header
        header = f"""# {title}

**Ticker:** {ticker.upper()}
**Generated:** {datetime.now().strftime("%B %d, %Y %H:%M")}
**Recommendation:** {recommendation.upper()}

---

"""
        full_report = header + content

        file_path.write_text(full_report, encoding="utf-8")

        logger.info(f"Report saved: {file_path}")
        return {
            "success":        True,
            "file_path":      str(file_path),
            "filename":       filename,
            "ticker":         ticker.upper(),
            "recommendation": recommendation.upper(),
            "chars":          len(full_report),
            "message":        f"Report saved to {filename}",
        }

    except Exception as e:
        logger.error(f"generate_report failed: {e}")
        return {"success": False, "error": str(e)}


def list_reports() -> dict:
    """List all saved reports."""
    try:
        reports_dir = Path(settings.reports_dir)
        if not reports_dir.exists():
            return {"reports": [], "count": 0}

        reports = []
        for f in sorted(reports_dir.glob("*.md"), reverse=True):
            reports.append({
                "filename": f.name,
                "size":     f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })

        return {"reports": reports, "count": len(reports)}
    except Exception as e:
        return {"error": str(e), "reports": []}


def read_report(filename: str) -> dict:
    """Read a saved report by filename."""
    try:
        path = Path(settings.reports_dir) / filename
        if not path.exists():
            return {"error": f"Report not found: {filename}"}
        return {"filename": filename, "content": path.read_text(encoding="utf-8")}
    except Exception as e:
        return {"error": str(e)}
