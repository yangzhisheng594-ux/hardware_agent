import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"


def write_trace(
    step: str,
    input: Any,
    output: Any,
    success: bool,
    error: str | None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    trace_path = output_path / "trace.jsonl"
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "input": input,
        "output": output,
        "success": success,
        "error": error,
    }
    with trace_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
