"""Conservative checks for the next Git snapshot. Never prints secret values.

Not a replacement for GitHub secret scanning or an exhaustive credential audit.
Run from any directory: python scripts/check_repository.py
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = [
    re.compile(rb"gsk_[A-Za-z0-9]{20,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{30,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def candidates():
    result = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    return sorted(set(path for path in result.decode("utf-8").split("\0") if path))


def main():
    issues = []
    checked = 0
    for relative in candidates():
        path = ROOT / relative
        if not path.is_file():
            continue
        parts = Path(relative).parts
        if (path.name.startswith(".env") and path.name != ".env.example") or relative == ".streamlit/secrets.toml":
            issues.append(f"Credential/config file included: {relative}")
        if ".venv" in parts or "__pycache__" in parts or relative.startswith("output/"):
            issues.append(f"Generated directory included: {relative}")
        if path.suffix.lower() == ".wav" or relative == "paper_context.json" or relative.startswith("data/practice_results/"):
            issues.append(f"Runtime/sample recording included: {relative}")
        if path.stat().st_size > 20 * 1024 * 1024:
            issues.append(f"File exceeds 20 MB: {relative}")
        content = path.read_bytes()
        if any(pattern.search(content) for pattern in PATTERNS):
            issues.append(f"Possible credential pattern (value redacted): {relative}")
        checked += 1
    if issues:
        print("Repository hygiene check failed:")
        for issue in issues:
            print("- " + issue)
        return 1
    print(f"Repository hygiene passed: {checked} files checked; no configured secret patterns or generated-data files found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
