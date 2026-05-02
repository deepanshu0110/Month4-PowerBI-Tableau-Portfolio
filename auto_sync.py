"""
AUTO GITHUB SYNC — Month 4 Portfolio Watcher
=============================================
Drop any file into your Month 4 folder → auto-commits and pushes to GitHub.
Also auto-updates README.md with a table of all files.

HOW TO RUN (PowerShell):
    cd "C:\Users\Deepanshu\OneDrive\Desktop\Excel\Month4"
    python auto_sync.py

STOP: Ctrl+C
"""

import os
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ─── CONFIG ────────────────────────────────────────────────────────────────────
WATCH_FOLDER = Path(r"C:\Users\Deepanshu\OneDrive\Desktop\Excel\Month4")
REPO_NAME    = "Month4-PowerBI-Tableau-Portfolio"
GITHUB_USER  = "deepanshu0110"
README_PATH  = WATCH_FOLDER / "README.md"

# Extensions to track (ignore temp files)
TRACKED_EXTENSIONS = {".xlsx", ".ipynb", ".pbix", ".twbx", ".twb",
                      ".py", ".sql", ".csv", ".pdf", ".png"}

# Extensions to always ignore
IGNORE_PATTERNS = {"~$", ".tmp", ".lock", ".git"}

# Day-to-topic map for Month 4 (update as days are added)
DAY_TOPICS = {
    66: "Power BI Setup + Data Model Basics",
    67: "DAX Foundations — Calculated Columns vs Measures",
    68: "DAX Time Intelligence",
    69: "Power BI Relationships + Star Schema",
    70: "Week 1 Mini-Project — Sales Dashboard",
    71: "Power Query — Data Cleaning in Power BI",
    72: "Advanced DAX — CALCULATE, FILTER, ALL",
    73: "Drill-through + Bookmarks + Tooltips",
    74: "KPI Cards + Conditional Formatting",
    75: "Week 2 Mini-Project — KPI Report",
    76: "Tableau Setup + Connecting to Data",
    77: "Tableau Charts — Bar, Line, Scatter, Maps",
    78: "Tableau Calculated Fields + LOD Expressions",
    79: "Tableau Dashboards + Actions",
    80: "Week 3 Mini-Project — Tableau Sales Story",
    81: "Power BI vs Tableau — Side-by-Side Build",
    82: "Power BI Service — Publish + Share",
    83: "Tableau Public — Publish + Portfolio",
    84: "End-to-End BI Project — Client Brief",
    85: "Month 4 Capstone — Full BI Dashboard",
}
# ───────────────────────────────────────────────────────────────────────────────


def git_run(cmd: list, cwd: Path) -> tuple[bool, str]:
    """Run a git command and return (success, output)."""
    result = subprocess.run(
        cmd, cwd=str(cwd),
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def extract_day_number(filename: str) -> int | None:
    """Pull day number from filename like Day66_..., day_66_..., D66_..."""
    match = re.search(r'[Dd]ay[_\s]?(\d+)', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def get_topic(day: int | None, filename: str) -> str:
    """Return topic string for a given day number."""
    if day and day in DAY_TOPICS:
        return DAY_TOPICS[day]
    # Try to infer from filename
    stem = Path(filename).stem
    # Remove day prefix if present
    clean = re.sub(r'^[Dd]ay[_\s]?\d+[_\s]*', '', stem).replace("_", " ").strip()
    return clean if clean else "Practice File"


def update_readme(folder: Path) -> None:
    """Regenerate README.md with an auto-built file table."""
    files = sorted(
        [f for f in folder.iterdir()
         if f.is_file()
         and f.suffix in TRACKED_EXTENSIONS
         and not any(p in f.name for p in IGNORE_PATTERNS)
         and f.name != "README.md"],
        key=lambda f: (extract_day_number(f.name) or 999, f.name)
    )

    # Build the files table
    rows = []
    for f in files:
        day = extract_day_number(f.name)
        topic = get_topic(day, f.name)
        day_str = f"Day {day}" if day else "—"
        size_kb = f"{f.stat().st_size / 1024:.1f} KB"
        rows.append(f"| {day_str} | {f.name} | {topic} | {size_kb} |")

    table = "\n".join(rows) if rows else "| — | No files yet | — | — |"
    last_updated = datetime.now().strftime("%d %b %Y, %H:%M")

    readme_content = f"""# Month 4 — Power BI & Tableau Portfolio

Part of a structured 12-month data analytics self-learning program.

## What This Covers

**Days 66–85 — Business Intelligence Tools**
- Power BI: Data modelling, DAX, Power Query, KPI dashboards, publishing
- Tableau: Charts, LOD expressions, dashboards, Tableau Public
- End-to-end BI project from client brief to final dashboard
- Power BI vs Tableau side-by-side comparison

## Tech Stack

Power BI · Tableau · DAX · Power Query · Excel · Python (Pandas)

## Files in This Repository

| Day | File | Topic | Size |
|-----|------|-------|------|
{table}

*Last updated: {last_updated}*

## Scoring Tracker

| Day | Topic | Score |
|-----|-------|-------|
| — | (updated after each submission) | — |

## Structure

Each day contains:
- Raw Data (unmodified source)
- Practice Guide (step-by-step tasks)
- Concept Notes (what it is, why it matters)
- Answer Key / Expected Output
- Scoring Rubric (points per task)

## Full 12-Month Program

| Month | Topic | Status |
|-------|-------|--------|
| 1–2   | Excel + SQL | ✅ Complete |
| 3     | Python / Pandas + Math Bridge | ✅ Complete |
| **4** | **Power BI + Tableau ← current** | 🔵 In Progress |
| 5     | Upwork Activation + Freelance Projects | ⏳ |
| 6     | Statistics + A/B Testing | ⏳ |
| 7–8   | Machine Learning | ⏳ |
| 9–10  | NLP + RAG + LangChain + Local AI | ⏳ |
| 11–12 | Capstone + Portfolio | ⏳ |

## Connect

[GitHub](https://github.com/deepanshu0110) · [Fiverr](https://fiverr.com) · [Upwork](https://upwork.com)

---
*Auto-synced via auto_sync.py — {REPO_NAME}*
"""
    README_PATH.write_text(readme_content, encoding="utf-8")
    print(f"  📄 README.md updated ({len(files)} files tracked)")


def push_file(filepath: Path, event_type: str = "add") -> None:
    """Stage, commit, and push a changed file + updated README."""
    folder = WATCH_FOLDER
    filename = filepath.name

    # Skip non-tracked or temp files
    if filepath.suffix not in TRACKED_EXTENSIONS:
        return
    if any(p in filename for p in IGNORE_PATTERNS):
        return

    print(f"\n{'─'*55}")
    print(f"  🔔 {event_type.upper()}: {filename}")

    # 1. Update README first
    update_readme(folder)

    # 2. Stage the file + README
    ok, out = git_run(["git", "add", filename, "README.md"], folder)
    if not ok:
        print(f"  ❌ git add failed: {out}")
        return

    # 3. Build commit message
    day = extract_day_number(filename)
    topic = get_topic(day, filename)
    ext_map = {".xlsx": "Excel", ".ipynb": "Notebook", ".pbix": "Power BI",
               ".twbx": "Tableau", ".twb": "Tableau", ".py": "Python",
               ".sql": "SQL", ".csv": "CSV", ".pdf": "PDF", ".png": "Image"}
    file_type = ext_map.get(filepath.suffix, filepath.suffix.upper().lstrip("."))

    if day:
        commit_msg = f"add: Day {day} — {topic} [{file_type}]"
    else:
        commit_msg = f"add: {filename} [{file_type}]"

    # 4. Commit
    ok, out = git_run(["git", "commit", "-m", commit_msg], folder)
    if not ok:
        if "nothing to commit" in out.lower():
            print(f"  ℹ️  Nothing new to commit — file unchanged")
        else:
            print(f"  ❌ git commit failed: {out}")
        return
    print(f"  ✅ Committed: {commit_msg}")

    # 5. Push
    ok, out = git_run(["git", "push", "origin", "main"], folder)
    if not ok:
        # Try master fallback
        ok, out = git_run(["git", "push", "origin", "master"], folder)
    if ok:
        print(f"  🚀 Pushed to GitHub: {GITHUB_USER}/{REPO_NAME}")
    else:
        print(f"  ❌ Push failed: {out}")
        print(f"  💡 Run manually: git push origin main")

    print(f"  🕐 {datetime.now().strftime('%H:%M:%S')}")


# ─── WATCHDOG EVENT HANDLER ────────────────────────────────────────────────────
class Month4Handler(FileSystemEventHandler):
    def __init__(self):
        self._last_event = {}   # debounce: filepath → last event time

    def _debounce(self, path: str) -> bool:
        """Return True if we should process this event (debounce 3s)."""
        now = time.time()
        if now - self._last_event.get(path, 0) < 3:
            return False
        self._last_event[path] = now
        return True

    def on_created(self, event):
        if not event.is_directory and self._debounce(event.src_path):
            # Small delay so file write completes before we read it
            time.sleep(1.5)
            push_file(Path(event.src_path), "add")

    def on_modified(self, event):
        if not event.is_directory and self._debounce(event.src_path):
            fname = Path(event.src_path).name
            if fname == "README.md":   # Skip auto-generated updates
                return
            time.sleep(1.5)
            push_file(Path(event.src_path), "update")


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    if not WATCH_FOLDER.exists():
        print(f"❌ Folder not found: {WATCH_FOLDER}")
        print(f"   Create it first, then run this script again.")
        return

    # Check git is initialised
    git_dir = WATCH_FOLDER / ".git"
    if not git_dir.exists():
        print(f"❌ No git repo found at: {WATCH_FOLDER}")
        print(f"   Run setup_month4_repo.ps1 first (see instructions).")
        return

    print("=" * 55)
    print("  📂 AUTO GITHUB SYNC — Month 4")
    print(f"  Watching: {WATCH_FOLDER}")
    print(f"  Repo    : {GITHUB_USER}/{REPO_NAME}")
    print("  Drop any file in → auto-push to GitHub")
    print("  Press Ctrl+C to stop")
    print("=" * 55)

    # Initial README sync on start
    update_readme(WATCH_FOLDER)

    observer = Observer()
    observer.schedule(Month4Handler(), str(WATCH_FOLDER), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n  ⏹  Watcher stopped.")

    observer.join()


if __name__ == "__main__":
    main()
