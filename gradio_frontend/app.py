import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime
import gradio as gr


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(FRONTEND_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_PREVIEW_CHARS = 1800

WORKERS = {
    "Finance Worker": {
        "path": os.path.join(BASE_DIR, "finance_intellegence_worker"),
        "port": 8001,
        "url": "http://127.0.0.1:8001/chat",
        "session_id": "finance-gradio-session",
    },
    "Logistics Worker": {
        "path": os.path.join(BASE_DIR, "logistics_operations_worker"),
        "port": 8002,
        "url": "http://127.0.0.1:8002/chat",
        "session_id": "logistics-gradio-session",
    },
    "Growth Worker": {
        "path": os.path.join(BASE_DIR, "growth_marketing_worker"),
        "port": 8003,
        "url": "http://127.0.0.1:8003/chat",
        "session_id": "growth-gradio-session",
    },
}

processes = []


def is_server_running(port):
    try:
        response = requests.get(
            f"http://127.0.0.1:{port}/docs",
            timeout=2,
        )
        return response.status_code == 200
    except Exception:
        return False


def start_worker(worker_name, config):
    worker_path = config["path"]
    port = config["port"]

    if not os.path.exists(worker_path):
        print(f"[ERROR] Folder not found for {worker_name}: {worker_path}")
        return None

    if is_server_running(port):
        print(f"[OK] {worker_name} already running on port {port}")
        return None

    print(f"[STARTING] {worker_name} on port {port}")

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=worker_path,
    )

    processes.append(process)
    return process


def start_all_workers():
    print("\n==============================")
    print("STARTING AI BUILDER WORKERS")
    print("==============================\n")

    for worker_name, config in WORKERS.items():
        start_worker(worker_name, config)

    print("\n[INFO] Waiting for workers to start...")
    time.sleep(8)

    for worker_name, config in WORKERS.items():
        if is_server_running(config["port"]):
            print(f"[READY] {worker_name} running at http://127.0.0.1:{config['port']}")
        else:
            print(f"[WARNING] {worker_name} may still be starting on port {config['port']}")

    print("\n==============================")
    print("WORKER STARTUP CHECK COMPLETE")
    print("==============================\n")


def to_text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


def extract_response(data):
    if isinstance(data, str):
        return data

    if not isinstance(data, dict):
        return to_text(data)

    possible_keys = [
        "answer",
        "response",
        "final_response",
        "formatted_response",
        "message",
        "result",
        "summary",
        "output",
        "memo",
        "recommendation",
    ]

    for key in possible_keys:
        if key in data and data[key]:
            return to_text(data[key])

    if "data" in data and isinstance(data["data"], dict):
        nested_data = data["data"]

        for key in possible_keys:
            if key in nested_data and nested_data[key]:
                return to_text(nested_data[key])

    return to_text(data)


def save_full_output(worker_name, query, full_text):
    safe_worker = worker_name.lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    file_path = os.path.join(
        OUTPUT_DIR,
        f"{safe_worker}_{timestamp}.txt",
    )

    content = (
        f"Worker: {worker_name}\n"
        f"Query: {query}\n"
        f"Time: {timestamp}\n\n"
        f"{full_text}"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path


def make_preview(worker_name, query, full_text, file_path):
    full_len = len(full_text)

    preview = full_text[:MAX_PREVIEW_CHARS]

    if full_len > MAX_PREVIEW_CHARS:
        preview += (
            "\n\n--- Preview trimmed to keep browser fast ---\n"
            f"Full response saved at:\n{file_path}"
        )

    preview += (
        "\n\n------------------------------\n"
        f"Full response characters: {full_len}\n"
        f"Saved file: {file_path}"
    )

    return preview


def call_worker(worker_name, message):
    if not message or not message.strip():
        return "Please enter a question."

    config = WORKERS[worker_name]

    payload = {
        "query": message,
        "session_id": config["session_id"],
    }

    print("\n==============================")
    print(f"REQUEST TO: {worker_name}")
    print(f"URL: {config['url']}")
    print(f"QUERY: {message}")
    print("==============================\n")

    try:
        response = requests.post(
            config["url"],
            json=payload,
            timeout=180,
        )

        print(f"[{worker_name}] Status Code: {response.status_code}")
        print(f"[{worker_name}] Raw response size: {len(response.text)} chars")

        if response.status_code != 200:
            error_text = (
                f"Error from {worker_name}\n\n"
                f"Status Code: {response.status_code}\n\n"
                f"{response.text}"
            )

            file_path = save_full_output(worker_name, message, error_text)
            return make_preview(worker_name, message, error_text, file_path)

        try:
            data = response.json()

            if isinstance(data, dict):
                print(f"[{worker_name}] JSON keys: {list(data.keys())}")
            else:
                print(f"[{worker_name}] JSON type: {type(data)}")

            full_output = extract_response(data)

        except Exception as e:
            print(f"[{worker_name}] JSON parse error: {str(e)}")
            full_output = response.text

        print(f"[{worker_name}] Extracted output size: {len(full_output)} chars")

        file_path = save_full_output(worker_name, message, full_output)
        preview = make_preview(worker_name, message, full_output, file_path)

        print(f"[{worker_name}] Full output saved at: {file_path}")
        print(f"[{worker_name}] Response completed.")
        print("==============================\n")

        return preview

    except requests.exceptions.ConnectionError as e:
        print(f"[{worker_name}] CONNECTION ERROR")
        print(str(e))
        return f"Could not connect to {worker_name}. Check port {config['port']}."

    except requests.exceptions.Timeout:
        print(f"[{worker_name}] TIMEOUT ERROR")
        return f"{worker_name} took too long to respond."

    except Exception as e:
        print(f"[{worker_name}] UNEXPECTED ERROR")
        print(str(e))
        return f"Unexpected error from {worker_name}: {str(e)}"


def create_worker_tab(worker_name, description, examples):
    gr.Markdown(f"### {worker_name}")
    gr.Markdown(description)

    input_box = gr.Textbox(
        label="Ask your question",
        placeholder=f"Ask something to {worker_name}...",
        lines=2,
    )

    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear")

    output_box = gr.Textbox(
        label="Response Preview",
        lines=18,
        max_lines=20,
        interactive=False,
    )

    # Show examples as plain text — no gr.Examples component at all.
    # gr.Examples was the cause of the tab-switch freeze.
    examples_text = "**Try these:**  \n" + "  \n".join(f"• {ex}" for ex in examples)
    gr.Markdown(examples_text)

    submit_btn.click(
        fn=lambda msg: call_worker(worker_name, msg),
        inputs=input_box,
        outputs=output_box,
    )

    input_box.submit(
        fn=lambda msg: call_worker(worker_name, msg),
        inputs=input_box,
        outputs=output_box,
    )

    clear_btn.click(
        fn=lambda: ("", ""),
        inputs=None,
        outputs=[input_box, output_box],
    )


def shutdown_workers():
    print("\n[INFO] Shutting down workers...")

    for process in processes:
        try:
            process.terminate()
        except Exception:
            pass


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