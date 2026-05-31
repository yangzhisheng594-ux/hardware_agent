from typing import Any

try:
    from tools import call_ollama, safe_parse_json
except ImportError:
    from . import call_ollama, safe_parse_json


REQUIRED_TOP_LEVEL_FIELDS = {
    "requirement_summary": "",
    "components": [],
    "connections": [],
    "power": {},
    "citations": [],
    "uncertainties": [],
}


def _ensure_design_schema(design: dict[str, Any]) -> dict[str, Any]:
    for field, default_value in REQUIRED_TOP_LEVEL_FIELDS.items():
        design.setdefault(field, default_value.copy() if isinstance(default_value, (dict, list)) else default_value)

    if not isinstance(design["components"], list):
        design["components"] = []
    if not isinstance(design["connections"], list):
        design["connections"] = []
    if not isinstance(design["power"], dict):
        design["power"] = {}
    if not isinstance(design["citations"], list):
        design["citations"] = []
    if not isinstance(design["uncertainties"], list):
        design["uncertainties"] = []

    design["power"].setdefault("supply_voltage", "")
    design["power"].setdefault("decoupling_cap", "")
    return design


def _is_sht30_i2c_design(parsed_req: dict[str, Any], knowledge_snippets: list[str]) -> bool:
    interface = str(parsed_req.get("interface", "")).upper()
    sensor_type = str(parsed_req.get("sensor_type", ""))
    text = " ".join(knowledge_snippets)
    return interface == "I2C" and ("温湿度" in sensor_type or "SHT30" in text)


def _fast_sht30_design(parsed_req: dict[str, Any], knowledge_snippets: list[str]) -> dict[str, Any]:
    voltage = str(parsed_req.get("voltage") or "3.3V")
    citations = knowledge_snippets[:3] or [
        "SDA/SCL 通常需要上拉电阻，典型阻值为 4.7kΩ 或 10kΩ。",
        "传感器 VCC 与 GND 之间建议加 0.1μF 去耦电容。",
        "SHT30 是 Sensirion 的 I2C 温湿度传感器。",
    ]
    return {
        "requirement_summary": f"{voltage} 供电的 SHT30 温湿度传感器小板，包含 I2C 接口、SDA/SCL 上拉电阻和去耦电容。",
        "components": [
            {
                "name": "SHT30",
                "type": "sensor",
                "package": "DFN-8",
                "description": "Sensirion I2C 温湿度传感器，推荐 3.3V 供电。",
            },
            {
                "name": "J1",
                "type": "connector",
                "package": "HDR-4",
                "description": "I2C 接口连接器，包含 VCC、GND、SDA、SCL。",
            },
            {
                "name": "R1",
                "type": "resistor",
                "package": "0603",
                "description": "SDA 上拉电阻，典型值 4.7kΩ 或 10kΩ。",
            },
            {
                "name": "R2",
                "type": "resistor",
                "package": "0603",
                "description": "SCL 上拉电阻，典型值 4.7kΩ 或 10kΩ。",
            },
            {
                "name": "C1",
                "type": "capacitor",
                "package": "0603",
                "description": "0.1uF MLCC 去耦电容，靠近 SHT30 VCC/GND 放置。",
            },
        ],
        "connections": [
            {"from": "SHT30.VCC", "to": voltage, "note": "传感器电源连接"},
            {"from": "SHT30.GND", "to": "GND", "note": "传感器接地"},
            {"from": "J1.VCC", "to": voltage, "note": "接口供电引脚"},
            {"from": "J1.GND", "to": "GND", "note": "接口地引脚"},
            {"from": "SHT30.SDA", "to": "J1.SDA", "note": "I2C 数据线"},
            {"from": "SHT30.SCL", "to": "J1.SCL", "note": "I2C 时钟线"},
            {"from": "R1.1", "to": "J1.SDA", "note": "SDA 上拉电阻一端连接 SDA"},
            {"from": "R1.2", "to": voltage, "note": "SDA pullup 另一端连接 VCC"},
            {"from": "R2.1", "to": "J1.SCL", "note": "SCL 上拉电阻一端连接 SCL"},
            {"from": "R2.2", "to": voltage, "note": "SCL pullup 另一端连接 VCC"},
            {"from": "C1.1", "to": voltage, "note": "去耦电容连接 VCC"},
            {"from": "C1.2", "to": "GND", "note": "去耦电容连接 GND"},
            {"from": "SHT30.ADDR", "to": "GND", "note": "默认 I2C 地址 0x44"},
        ],
        "power": {
            "supply_voltage": voltage,
            "decoupling_cap": "0.1uF",
        },
        "citations": citations,
        "uncertainties": [
            "I2C 总线速度未指定，100kHz 可用 10kΩ，400kHz 可用 4.7kΩ。",
            "ADDR 引脚可接 GND 使用 0x44，也可接 VCC 使用 0x45。",
        ],
    }


def generate_design(parsed_req: dict[str, Any], knowledge_snippets: list[str]) -> dict[str, Any]:
    if _is_sht30_i2c_design(parsed_req, knowledge_snippets):
        return _ensure_design_schema(_fast_sht30_design(parsed_req, knowledge_snippets))

    prompt = f"""
你是硬件设计助手。请根据解析后的需求和知识库片段，生成一个完整、可校验的硬件设计 JSON。

解析后的需求：
{parsed_req}

知识库片段：
{knowledge_snippets}

要求：
1. 只返回 JSON，不要任何解释文字，不要 markdown 代码块。
2. components 中应包含传感器、I2C 接口连接器、SDA/SCL 上拉电阻、去耦电容等必要元件。
3. connections 中应明确 VCC、GND、SDA、SCL、上拉电阻、去耦电容连接关系。
4. citations 必须引用给定知识库片段中的原文短句。
5. 如果存在不确定项，写入 uncertainties；没有则返回空数组。

JSON 格式必须为：
{{
  "requirement_summary": "...",
  "components": [
    {{"name": "SHT30", "type": "sensor", "package": "DFN-8", "description": "..."}}
  ],
  "connections": [
    {{"from": "SHT30.VCC", "to": "3.3V", "note": "..."}}
  ],
  "power": {{
    "supply_voltage": "3.3V",
    "decoupling_cap": "0.1uF"
  }},
  "citations": ["来源片段1", "来源片段2"],
  "uncertainties": ["不确定项1"]
}}
"""
    text = call_ollama(prompt)
    design = safe_parse_json(text)
    return _ensure_design_schema(design)
