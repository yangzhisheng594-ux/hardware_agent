import json
import os
from pathlib import Path
from typing import Any, Callable

try:
    from tools.generate_design import generate_design
    from tools.parse_requirement import parse_requirement
    from tools.repair_design import repair_design
    from tools.search_knowledge import search_knowledge
    from tools.validate_design import validate_design
    from tools.write_trace import write_trace
except ImportError:
    from .tools.generate_design import generate_design
    from .tools.parse_requirement import parse_requirement
    from .tools.repair_design import repair_design
    from .tools.search_knowledge import search_knowledge
    from .tools.validate_design import validate_design
    from .tools.write_trace import write_trace


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _keywords_from_requirement(task: str, parsed_req: dict[str, Any]) -> list[str]:
    keywords: list[str] = []

    for key in ("voltage", "interface", "sensor_type"):
        value = parsed_req.get(key)
        if isinstance(value, str) and value.strip():
            keywords.append(value.strip())

    peripheral_needs = parsed_req.get("peripheral_needs", [])
    if isinstance(peripheral_needs, list):
        keywords.extend(str(item).strip() for item in peripheral_needs if str(item).strip())

    if "温湿度" in task and "SHT30" not in keywords:
        keywords.append("SHT30")
    if "I2C" in task.upper() and "I2C" not in keywords:
        keywords.append("I2C")
    if any("上拉" in item or "pull" in item.lower() for item in keywords):
        keywords.extend(["SDA", "SCL"])
    if any("去耦" in item or "滤波" in item for item in keywords):
        keywords.append("0.1μF")

    seen: set[str] = set()
    deduped: list[str] = []
    for keyword in keywords:
        normalized = keyword.lower()
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(keyword)
    return deduped


def _trace_step(
    step: str,
    step_input: Any,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    try:
        output = func(*args, **kwargs)
    except Exception as exc:
        write_trace(step, step_input, None, False, str(exc), output_dir=OUTPUT_DIR)
        raise
    write_trace(step, step_input, output, True, None, output_dir=OUTPUT_DIR)
    return output


def _generate_final_report(
    task: str,
    design: dict[str, Any],
    validation_report: dict[str, Any],
    repair_report: dict[str, Any],
) -> str:
    components = design.get("components", [])
    connections = design.get("connections", [])
    power = design.get("power", {})
    citations = design.get("citations", [])
    uncertainties = design.get("uncertainties", [])

    component_lines = [
        f"- {item.get('name', '未知元件')} ({item.get('type', 'unknown')}): {item.get('description', '')}"
        for item in components
        if isinstance(item, dict)
    ]
    connection_lines = [
        f"- {item.get('from', '?')} -> {item.get('to', '?')}: {item.get('note', '')}"
        for item in connections
        if isinstance(item, dict)
    ]
    failed_checks = [
        check
        for check in validation_report.get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]

    repair_status = "未触发"
    if repair_report.get("repair_attempted"):
        repair_status = "成功" if repair_report.get("repair_success") else "失败"

    lines = [
        "# 硬件设计最终报告",
        "",
        "## 用户需求",
        task,
        "",
        "## 需求摘要",
        str(design.get("requirement_summary", "未生成")),
        "",
        "## 电源设计",
        f"- 供电电压：{power.get('supply_voltage', '未指定') if isinstance(power, dict) else '未指定'}",
        f"- 去耦电容：{power.get('decoupling_cap', '未指定') if isinstance(power, dict) else '未指定'}",
        "",
        "## 元件清单",
        *(component_lines or ["- 未生成元件清单"]),
        "",
        "## 关键连接",
        *(connection_lines or ["- 未生成连接关系"]),
        "",
        "## 规则校验",
        f"- 总体结果：{'通过' if validation_report.get('passed') else '未通过'}",
        f"- 修正状态：{repair_status}",
    ]

    if failed_checks:
        lines.append("- 未通过规则：")
        lines.extend(
            f"  - {check.get('rule', 'UNKNOWN')}: {check.get('message', '')}"
            for check in failed_checks
        )

    lines.extend(["", "## 知识库引用"])
    lines.extend([f"- {item}" for item in citations] if citations else ["- 无"])

    lines.extend(["", "## 不确定项"])
    lines.extend([f"- {item}" for item in uncertainties] if uncertainties else ["- 无"])

    if repair_report.get("repair_attempted"):
        lines.extend(["", "## 修正记录"])
        actions = repair_report.get("actions", [])
        if repair_report.get("repair_success"):
            lines.extend([f"- {action}" for action in actions] if actions else ["- 模型返回了修正版设计"])
        else:
            lines.append(f"- 修正失败原因：{repair_report.get('reason', '未提供')}")

    return "\n".join(lines) + "\n"


def run(task: str) -> Path:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    parsed_req = _trace_step("parse_requirement", {"task": task}, parse_requirement, task)

    keywords = _keywords_from_requirement(task, parsed_req)
    knowledge_snippets = _trace_step(
        "search_knowledge",
        {"keywords": keywords},
        search_knowledge,
        keywords,
    )

    design = _trace_step(
        "generate_design",
        {"parsed_req": parsed_req, "knowledge_snippets": knowledge_snippets},
        generate_design,
        parsed_req,
        knowledge_snippets,
    )
    _write_json(OUTPUT_DIR / "design.json", design)

    validation_report = _trace_step("validate_design", {"design": design}, validate_design, design)
    _write_json(OUTPUT_DIR / "validation_report.json", validation_report)

    if validation_report.get("passed"):
        repair_report: dict[str, Any] = {
            "repair_attempted": False,
            "repair_success": None,
            "failed_rules_before_repair": [],
            "actions": [],
            "validation_after_repair": validation_report,
        }
        write_trace(
            "repair_design",
            {"design": design, "validation_report": validation_report},
            repair_report,
            True,
            None,
            output_dir=OUTPUT_DIR,
        )
    else:
        repair_report = _trace_step(
            "repair_design",
            {"design": design, "validation_report": validation_report},
            repair_design,
            design,
            validation_report,
        )
        repaired_design = repair_report.pop("_repaired_design", None)
        if repaired_design and repair_report.get("repair_success"):
            design = repaired_design
            validation_report = repair_report.get("validation_after_repair", validation_report)
            _write_json(OUTPUT_DIR / "design.json", design)
            _write_json(OUTPUT_DIR / "validation_report.json", validation_report)

    _write_json(OUTPUT_DIR / "repair_report.json", repair_report)

    final_report = _generate_final_report(task, design, validation_report, repair_report)
    final_report_path = OUTPUT_DIR / "final_report.md"
    final_report_path.write_text(final_report, encoding="utf-8")
    write_trace(
        "final_report",
        {"task": task, "design": design, "validation_report": validation_report, "repair_report": repair_report},
        {"path": str(final_report_path)},
        True,
        None,
        output_dir=OUTPUT_DIR,
    )

    return final_report_path
