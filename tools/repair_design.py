from typing import Any

try:
    from tools import call_ollama, safe_parse_json
    from tools.validate_design import validate_design
except ImportError:
    from . import call_ollama, safe_parse_json
    from .validate_design import validate_design


def _failed_rules(validation_report: dict[str, Any]) -> list[str]:
    return [
        str(check.get("rule"))
        for check in validation_report.get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]


def repair_design(design: dict[str, Any], validation_report: dict[str, Any]) -> dict[str, Any]:
    failed_rules = _failed_rules(validation_report)
    if not failed_rules:
        return {
            "repair_attempted": False,
            "repair_success": None,
            "failed_rules_before_repair": [],
            "actions": [],
            "validation_after_repair": validation_report,
        }

    prompt = f"""
你是硬件设计 JSON 修正助手。请根据失败规则修正设计。

原始 design.json：
{design}

校验报告：
{validation_report}

失败规则：
{failed_rules}

修正要求：
1. 只返回 JSON，不要任何解释文字，不要 markdown 代码块。
2. 返回对象必须包含 design 和 actions 两个字段。
3. design 必须包含 requirement_summary、components、connections、power、citations、uncertainties。
4. 如果缺少 I2C 上拉，请添加 SDA/SCL 上拉电阻及其连接。
5. 如果缺少 GND 或 3.3V 连接，请补齐连接。
6. 如果 connections 引用了未声明元件，请在 components 中补齐或修正连接名。

返回格式：
{{
  "design": {{
    "requirement_summary": "...",
    "components": [],
    "connections": [],
    "power": {{"supply_voltage": "3.3V", "decoupling_cap": "0.1uF"}},
    "citations": [],
    "uncertainties": []
  }},
  "actions": ["added pull-up resistors R1 and R2 for SDA and SCL"]
}}
"""
    try:
        response = safe_parse_json(call_ollama(prompt))
    except Exception as exc:
        return {
            "repair_attempted": True,
            "repair_success": False,
            "failed_rules_before_repair": failed_rules,
            "reason": f"修正模型输出无法解析：{exc}",
        }

    repaired_design = response.get("design", response)
    actions = response.get("actions", ["模型返回了修正版设计"])
    if isinstance(actions, str):
        actions = [actions]
    if not isinstance(actions, list):
        actions = ["模型返回了修正版设计"]

    validation_after_repair = validate_design(repaired_design)
    repair_success = bool(validation_after_repair.get("passed"))

    report: dict[str, Any] = {
        "repair_attempted": True,
        "repair_success": repair_success,
        "failed_rules_before_repair": failed_rules,
        "actions": [str(action) for action in actions],
        "validation_after_repair": validation_after_repair,
    }

    if repair_success:
        report["_repaired_design"] = repaired_design
    else:
        still_failed = _failed_rules(validation_after_repair)
        report["reason"] = (
            "Knowledge base does not contain enough information to resolve "
            + ", ".join(still_failed or failed_rules)
        )

    return report
