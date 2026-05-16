from pathlib import Path
from datetime import datetime


def save_final_memo_as_markdown(state, output_dir: str = "reports") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    safe_city = (state.city or "city").lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_name = f"{safe_city}_dispatch_memo_{timestamp}.md"
    file_path = Path(output_dir) / file_name

    memo = state.final_memo or "No final memo generated."

    content = f"""# Dispatch Memo Report

**Run ID:** {state.runtime_logs[0]["run_id"] if state.runtime_logs else "N/A"}  
**Session ID:** {state.session_id}  
**City:** {state.city}  
**Date:** {state.date}  

---

{memo}
"""

    file_path.write_text(content, encoding="utf-8")

    return str(file_path)