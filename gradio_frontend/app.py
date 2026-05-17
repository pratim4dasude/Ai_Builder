import os
import sys
import json
import asyncio
import subprocess
import threading
import httpx
from datetime import datetime
import gradio as gr


# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR   = os.path.join(FRONTEND_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_PREVIEW_CHARS = 1800

# ── Worker registry ────────────────────────────────────────────────────────────
WORKERS = {
    "Finance Worker": {
        "path":       os.path.join(BASE_DIR, "finance_intellegence_worker"),
        "port":       8001,
        "url":        "http://127.0.0.1:8001/chat",
        "session_id": "finance-gradio-session",
    },
    "Logistics Worker": {
        "path":       os.path.join(BASE_DIR, "logistics_operations_worker"),
        "port":       8002,
        "url":        "http://127.0.0.1:8002/chat",
        "session_id": "logistics-gradio-session",
    },
    "Growth Worker": {
        "path":       os.path.join(BASE_DIR, "growth_marketing_worker"),
        "port":       8003,
        "url":        "http://127.0.0.1:8003/chat",
        "session_id": "growth-gradio-session",
    },
}

_processes: list[subprocess.Popen] = []


# ── Worker lifecycle ───────────────────────────────────────────────────────────

def _start_worker(worker_name: str, config: dict) -> None:
    worker_path = config["path"]
    port        = config["port"]

    if not os.path.exists(worker_path):
        print(f"[ERROR] Folder not found for {worker_name}: {worker_path}")
        return

    # Quick sync check only at startup (before event loop is running)
    try:
        r = httpx.get(f"http://127.0.0.1:{port}/docs", timeout=1)
        if r.status_code == 200:
            print(f"[OK] {worker_name} already running on port {port}")
            return
    except Exception:
        pass

    print(f"[STARTING] {worker_name} on port {port}")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(port)],
        cwd=worker_path,
    )
    _processes.append(process)


def _poll_ready(worker_name: str, port: int, timeout: int = 30) -> None:
    """Background thread — polls until worker is reachable."""
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"http://127.0.0.1:{port}/docs", timeout=1)
            if r.status_code == 200:
                print(f"[READY] {worker_name} on port {port}")
                return
        except Exception:
            pass
        time.sleep(1)
    print(f"[WARNING] {worker_name} did not become ready within {timeout}s")


def start_all_workers() -> None:
    print("\n==============================")
    print("STARTING AI BUILDER WORKERS")
    print("==============================\n")
    for name, cfg in WORKERS.items():
        _start_worker(name, cfg)
        threading.Thread(
            target=_poll_ready,
            args=(name, cfg["port"]),
            daemon=True,
        ).start()


def shutdown_workers() -> None:
    print("\n[INFO] Shutting down workers...")
    for p in _processes:
        try:
            p.terminate()
        except Exception:
            pass


# ── Async health check (safe inside event loop) ────────────────────────────────

async def _is_worker_up(port: int) -> bool:
    """Async health check — never blocks the event loop."""
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get(f"http://127.0.0.1:{port}/docs")
            return r.status_code == 200
    except Exception:
        return False


# ── Response helpers ───────────────────────────────────────────────────────────

def _to_text(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


def _extract_response(data) -> str:
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return _to_text(data)
    keys = ["answer", "response", "final_response", "formatted_response",
            "message", "result", "summary", "output", "memo", "recommendation"]
    for k in keys:
        if data.get(k):
            return _to_text(data[k])
    nested = data.get("data")
    if isinstance(nested, dict):
        for k in keys:
            if nested.get(k):
                return _to_text(nested[k])
    return _to_text(data)


def _save_output(worker_name: str, query: str, text: str) -> str:
    safe  = worker_name.lower().replace(" ", "_")
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    fpath = os.path.join(OUTPUT_DIR, f"{safe}_{ts}.txt")
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(f"Worker: {worker_name}\nQuery: {query}\nTime: {ts}\n\n{text}")
    return fpath


def _make_preview(full_text: str, file_path: str) -> str:
    preview = full_text[:MAX_PREVIEW_CHARS]
    if len(full_text) > MAX_PREVIEW_CHARS:
        preview += (
            "\n\n--- Preview trimmed ---\n"
            f"Full response saved at:\n{file_path}"
        )
    preview += (
        f"\n\n------------------------------\n"
        f"Characters: {len(full_text)} | File: {file_path}"
    )
    return preview


# ── Core async handler ─────────────────────────────────────────────────────────

async def call_worker_async(worker_name: str, message: str) -> str:
    if not message or not message.strip():
        return "Please enter a question."

    cfg = WORKERS[worker_name]

    # Async health check — will NOT block the event loop
    if not await _is_worker_up(cfg["port"]):
        return (
            f"[WARNING] {worker_name} is not reachable on port {cfg['port']}.\n"
            "Please check the worker process and try again."
        )

    payload = {"query": message, "session_id": cfg["session_id"]}
    print(f"\n[REQUEST] {worker_name} -> {cfg['url']}\nQUERY: {message}")

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(cfg["url"], json=payload)

        print(f"[{worker_name}] status={response.status_code} "
              f"size={len(response.text)} chars")

        if response.status_code != 200:
            err = (f"Error from {worker_name}\n\n"
                   f"Status: {response.status_code}\n\n{response.text}")
            fp = _save_output(worker_name, message, err)
            return _make_preview(err, fp)

        try:
            data        = response.json()
            full_output = _extract_response(data)
        except Exception as e:
            print(f"[{worker_name}] JSON parse error: {e}")
            full_output = response.text

        fp      = _save_output(worker_name, message, full_output)
        preview = _make_preview(full_output, fp)
        print(f"[{worker_name}] Done. Saved -> {fp}")
        return preview

    except httpx.ConnectError:
        return (f"Could not connect to {worker_name}. "
                f"Is it running on port {cfg['port']}?")
    except httpx.TimeoutException:
        return f"{worker_name} timed out (180 s). The request may still be processing."
    except Exception as e:
        return f"Unexpected error from {worker_name}: {e}"


# ── UI builder ─────────────────────────────────────────────────────────────────

def create_worker_tab(worker_name: str, description: str, examples: list) -> None:
    gr.Markdown(f"### {worker_name}")
    gr.Markdown(description)

    input_box = gr.Textbox(
        label="Ask your question",
        placeholder=f"Ask something to {worker_name}...",
        lines=2,
    )

    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary")
        clear_btn  = gr.Button("Clear")

    output_box = gr.Textbox(
        label="Response Preview",
        lines=18,
        max_lines=20,
        interactive=False,
    )

    # THE KEY FIX: cache_examples=False stops Gradio from running your handler
    # for every example the moment the tab is opened/switched to.
    gr.Examples(
        examples=examples,
        inputs=input_box,
        label="Example questions",
        cache_examples=False,
    )

    handler = lambda msg: call_worker_async(worker_name, msg)

    submit_btn.click(fn=handler, inputs=input_box, outputs=output_box)
    input_box.submit(fn=handler, inputs=input_box, outputs=output_box)
    clear_btn.click(
        fn=lambda: ("", ""),
        inputs=None,
        outputs=[input_box, output_box],
    )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    start_all_workers()

    with gr.Blocks(title="AI Builder") as demo:
        gr.Markdown("# AI Builder")
        gr.Markdown(
            "One lightweight frontend for Finance, Logistics, and Growth AI workers."
        )

        with gr.Tab("Finance"):
            create_worker_tab(
                "Finance Worker",
                "Revenue analysis, forecasting, invoice matching, deductions, leakage, and financial insights.",
                examples=[
                    "Analyze revenue performance for this month",
                    "Forecast revenue for the next 3 months",
                    "Find possible revenue leakage and deduction risks",
                    "Create a finance action memo for the leadership team",
                ],
            )

        with gr.Tab("Logistics"):
            create_worker_tab(
                "Logistics Worker",
                "Dispatch planning, warehouse assignment, route planning, clustering, delivery risk, and operations memo.",
                examples=[
                    "Create a dispatch plan for pending orders in Bangalore today",
                    "Assign pending orders to the best warehouse",
                    "Create optimal delivery routes for today's shipments",
                    "Find high risk COD or RTO orders",
                ],
            )

        with gr.Tab("Growth"):
            create_worker_tab(
                "Growth Worker",
                "Sales trends, campaign performance, product promotion, content planning, captions, and growth action memo.",
                examples=[
                    "Analyze product sales trends",
                    "Analyze campaign performance and tell which campaigns worked best",
                    "Recommend the best products to promote this week",
                    "Create a marketing action plan for this week",
                ],
            )

    try:
        demo.queue(max_size=20).launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            show_error=True,
        )
    finally:
        shutdown_workers()