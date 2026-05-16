from datetime import datetime
from app.config import REPORTS_DIR


def write_report(prefix: str, content: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = REPORTS_DIR / f"{prefix}_{timestamp}.md"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)