from typing import Any

try:
    from tools import call_ollama, safe_parse_json
except ImportError:
    from . import call_ollama, safe_parse_json


def _normalize_requirement(data: dict[str, Any]) -> dict[str, Any]:
    peripheral_needs = data.get("peripheral_needs", [])
    if isinstance(peripheral_needs, str):
        peripheral_needs = [peripheral_needs]
    if not isinstance(peripheral_needs, list):
        peripheral_needs = []

    return {
        "voltage": str(data.get("voltage", "")).strip(),
        "interface": str(data.get("interface", "")).strip(),
        "sensor_type": str(data.get("sensor_type", "")).strip(),
        "peripheral_needs": [str(item).strip() for item in peripheral_needs if str(item).strip()],
    }


def _heuristic_requirement(task: str) -> dict[str, Any] | None:
    task_upper = task.upper()

    voltage = ""
    if "3.3" in task or "3V3" in task_upper:
        voltage = "3.3V"
    elif "5V" in task_upper or "5.0" in task:
        voltage = "5V"

    interface = ""
    if "I2C" in task_upper or "I²C" in task_upper:
        interface = "I2C"
    elif "SPI" in task_upper:
        interface = "SPI"
    elif "UART" in task_upper:
        interface = "UART"

    sensor_type = ""
    if "温湿度" in task or ("温度" in task and "湿度" in task):
        sensor_type = "温湿度传感器"
    elif "温度" in task:
        sensor_type = "温度传感器"
    elif "湿度" in task:
        sensor_type = "湿度传感器"

    peripheral_needs: list[str] = []
    if interface == "I2C":
        peripheral_needs.append("上拉电阻")
    if voltage or "去耦" in task or "滤波" in task or "小板" in task:
        peripheral_needs.append("去耦电容")

    if voltage and interface and sensor_type:
        return {
            "voltage": voltage,
            "interface": interface,
            "sensor_type": sensor_type,
            "peripheral_needs": peripheral_needs,
        }
    return None


def parse_requirement(task: str) -> dict[str, Any]:
    fast_result = _heuristic_requirement(task)
    if fast_result:
        return fast_result

    prompt = f"""
你是硬件需求解析助手。请从用户需求中提取结构化信息。

用户需求：
{task}

只返回 JSON，不要任何解释文字，不要 markdown 代码块。格式必须为：
{{
  "voltage": "3.3V",
  "interface": "I2C",
  "sensor_type": "温湿度传感器",
  "peripheral_needs": ["上拉电阻", "去耦电容"]
}}
"""
    text = call_ollama(prompt)
    parsed = safe_parse_json(text)
    return _normalize_requirement(parsed)
