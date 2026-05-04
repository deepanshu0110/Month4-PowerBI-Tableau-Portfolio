# AUTO GITHUB SYNC - Power BI Portfolio Watcher
# Drop any file into the folder -> auto-commits and pushes to GitHub
# Also auto-updates README.md with a table of all files
#
# HOW TO RUN (PowerShell):
#   cd "C:\Users\Deepanshu\OneDrive\Desktop\Power BI"
#   python auto_sync.py
#
# STOP: Ctrl+C

import os
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CONFIG -------------------------------------------------------------------
WATCH_FOLDER = Path(r"C:\Users\Deepanshu\OneDrive\Desktop\Power BI")
REPO_NAME    = "Month4-PowerBI-Tableau-Portfolio"
GITHUB_USER  = "deepanshu0110"
README_PATH  = WATCH_FOLDER / "README.md"

TRACKED_EXTENSIONS = {".xlsx", ".ipynb", ".pbix", ".twbx", ".twb",
                      ".py", ".sql", ".csv", ".pdf", ".png"}

IGNORE_PATTERNS = {"~$", ".tmp", ".lock", ".git", "auto_sync"}

DAY_TOPICS = {
    66: "Power BI Setup + Data Model Basics",
    67: "DAX Foundations - Calculated Columns vs Measures",
    68: "DAX Time Intelligence",
    69: "Power BI Relationships + Star Schema",
    70: "Week 1 Mini-Project - Sales Dashboard",
    71: "Power Query - Data Cleaning in Power BI",
    72: "Advanced DAX - CALCULATE, FILTER, ALL",
    73: "Drill-through + Bookmarks + Tooltips",
    74: "KPI Cards + Conditional Formatting",
    75: "Week 2 Mini-Project - KPI Report",
    76: "Tableau Setup + Connecting to Data",
    77: "Tableau Charts - Bar, Line, Scatter, Maps",
    78: "Tableau Calculated Fields + LOD Expressions",
    79: "Tableau Dashboards + Actions",
    80: "Week 3 Mini-Project - Tableau Sales Story",
    81: "Power BI vs Tableau - Side-by-Side Build",
    82: "Power BI Service - Publish + Share",
    83: "Tableau Public - Publish + Portfolio",
    84: "End-to-End BI Project - Client Brief",
    85: "Month 4 Capstone - Full BI Dashboard",
}
# ------------------------------------------------------------------------------


def git_run(cmd, cwd):
    result = subprocess.run(
        cmd, cwd=str(cwd),
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def extract_day_number(filename):
    match = re.search(r'[Dd]ay[_\s]?(\d+)', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def get_topic(day, filename):
    if day and day in DAY_TOPICS:
        return DAY_TOPICS[day]
    stem = Path(filename).stem
    clean = re.sub(r'^[Dd]ay[_\s]?\d+[_\s]*', '', stem).replace("_", " ").strip()
    return clean if clean else "Practice File"


def update_readme(folder):
    files = sorted(
        [f for f in folder.iterdir()
         if f.is_file()
         and f.suffix in TRACKED_EXTENSIONS
         and not any(p in f.name for p in IGNORE_PATTERNS)
         and f.name != "README.md"],
        key=lambda f: (extract_day_number(f.name) or 999, f.name)
    )

    rows = []
    for f in files:
        day = extract_day_number(f.name)
        topic = get_topic(day, f.name)
        day_str = "Day {}".format(day) if day else "--"
        size_kb = "{:.1f} KB".format(f.stat().st_size / 1024)
        rows.append("| {} | {} | {} | {} |".format(day_str, f.name, topic, size_kb))

    table = "\n".join(rows) if rows else "| -- | No files yet | -- | -- |"
    last_updated = datetime.now().strftime("%d %b %Y, %H:%M")

    readme_content = (
        "# Month 4 - Power BI & Tableau Portfolio\n\n"
        "Part of a structured 12-month data analytics self-learning program.\n\n"
        "## What This Covers\n\n"
        "**Days 66-85 - Business Intelligence Tools**\n"
        "- Power BI: Data modelling, DAX, Power Query, KPI dashboards, publishing\n"
        "- Tableau: Charts, LOD expressions, dashboards, Tableau Public\n"
        "- End-to-end BI project from client brief to final dashboard\n"
        "- Power BI vs Tableau side-by-side comparison\n\n"
        "## Tech Stack\n\n"
        "Power BI | Tableau | DAX | Power Query | Excel | Python (Pandas)\n\n"
        "## Files in This Repository\n\n"
        "| Day | File | Topic | Size |\n"
        "|-----|------|-------|------|\n"
        "{}\n\n"
        "*Last updated: {}*\n\n"
        "## Full 12-Month Program\n\n"
        "| Month | Topic | Status |\n"
        "|-------|-------|--------|\n"
        "| 1-2   | Excel + SQL | Complete |\n"
        "| 3     | Python / Pandas + Math Bridge | Complete |\n"
        "| **4** | **Power BI + Tableau (current)** | In Progress |\n"
        "| 5     | Upwork Activation + Freelance Projects | Pending |\n"
        "| 6     | Statistics + A/B Testing | Pending |\n"
        "| 7-8   | Machine Learning | Pending |\n"
        "| 9-10  | NLP + RAG + LangChain + Local AI | Pending |\n"
        "| 11-12 | Capstone + Portfolio | Pending |\n\n"
        "## Connect\n\n"
        "[GitHub](https://github.com/deepanshu0110)\n"
    ).format(table, last_updated)

    README_PATH.write_text(readme_content, encoding="utf-8")
    print("  README.md updated ({} files tracked)".format(len(files)))


def push_file(filepath, event_type="add"):
    folder = WATCH_FOLDER
    filename = filepath.name

    if filepath.suffix not in TRACKED_EXTENSIONS:
        return
    if any(p in filename for p in IGNORE_PATTERNS):
        return

    print("\n" + "-" * 50)
    print("  {}: {}".format(event_type.upper(), filename))

    update_readme(folder)

    ok, out = git_run(["git", "add", filename, "README.md"], folder)
    if not ok:
        print("  git add failed: {}".format(out))
        return

    day = extract_day_number(filename)
    topic = get_topic(day, filename)
    ext_map = {
        ".xlsx": "Excel", ".ipynb": "Notebook", ".pbix": "Power BI",
        ".twbx": "Tableau", ".twb": "Tableau", ".py": "Python",
        ".sql": "SQL", ".csv": "CSV", ".pdf": "PDF", ".png": "Image"
    }
    file_type = ext_map.get(filepath.suffix, filepath.suffix.upper().lstrip("."))

    if day:
        commit_msg = "add Day {} {} [{}]".format(day, topic, file_type)
    else:
        commit_msg = "add {} [{}]".format(filename, file_type)

    ok, out = git_run(["git", "commit", "-m", commit_msg], folder)
    if not ok:
        if "nothing to commit" in out.lower():
            print("  Nothing new to commit - file unchanged")
        else:
            print("  git commit failed: {}".format(out))
        return
    print("  Committed: {}".format(commit_msg))

    ok, out = git_run(["git", "push", "origin", "main"], folder)
    if not ok:
        ok, out = git_run(["git", "push", "origin", "master"], folder)
    if ok:
        print("  Pushed to GitHub: {}/{}".format(GITHUB_USER, REPO_NAME))
    else:
        print("  Push failed: {}".format(out))
        print("  Run manually: git push origin main")

    print("  Time: {}".format(datetime.now().strftime("%H:%M:%S")))


class PowerBIHandler(FileSystemEventHandler):
    def __init__(self):
        self._last_event = {}

    def _debounce(self, path):
        now = time.time()
        if now - self._last_event.get(path, 0) < 3:
            return False
        self._last_event[path] = now
        return True

    def on_created(self, event):
        if not event.is_directory and self._debounce(event.src_path):
            time.sleep(1.5)
            push_file(Path(event.src_path), "add")

    def on_modified(self, event):
        if not event.is_directory and self._debounce(event.src_path):
            fname = Path(event.src_path).name
            if fname == "README.md":
                return
            time.sleep(1.5)
            push_file(Path(event.src_path), "update")


def main():
    if not WATCH_FOLDER.exists():
        print("ERROR: Folder not found: {}".format(WATCH_FOLDER))
        return

    git_dir = WATCH_FOLDER / ".git"
    if not git_dir.exists():
        print("ERROR: No git repo found. Run git init in the folder first.")
        return

    print("=" * 50)
    print("  AUTO GITHUB SYNC - Power BI Portfolio")
    print("  Watching: {}".format(WATCH_FOLDER))
    print("  Repo    : {}/{}".format(GITHUB_USER, REPO_NAME))
    print("  Drop any file in -> auto-push to GitHub")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    update_readme(WATCH_FOLDER)

    observer = Observer()
    observer.schedule(PowerBIHandler(), str(WATCH_FOLDER), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n  Watcher stopped.")

    observer.join()


if __name__ == "__main__":
    main()
