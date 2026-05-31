from typing import Any


NET_NAMES = {
    "3.3v",
    "vcc",
    "gnd",
    "sda",
    "scl",
    "addr",
    "0x44",
    "0x45",
    "i2c",
}


def _stringify_connection(connection: dict[str, Any]) -> str:
    return " ".join(str(value) for value in connection.values()).lower()


def _component_names(design: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for component in design.get("components", []):
        if isinstance(component, dict) and component.get("name"):
            names.add(str(component["name"]).lower())
    return names


def _endpoint_component(endpoint: str) -> str | None:
    endpoint = endpoint.strip()
    if "." not in endpoint:
        return None
    prefix = endpoint.split(".", 1)[0].strip()
    if not prefix:
        return None
    if prefix.lower() in NET_NAMES:
        return None
    if prefix[0].isdigit():
        return None
    return prefix.lower()


def _connection_endpoints(design: dict[str, Any]) -> list[tuple[str, str]]:
    endpoints: list[tuple[str, str]] = []
    for connection in design.get("connections", []):
        if not isinstance(connection, dict):
            continue
        endpoints.append((str(connection.get("from", "")), str(connection.get("to", ""))))
    return endpoints


def validate_design(design: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    endpoints = _connection_endpoints(design)
    component_names = _component_names(design)
    connection_texts = [
        _stringify_connection(connection)
        for connection in design.get("connections", [])
        if isinstance(connection, dict)
    ]
    all_connection_text = " ".join(connection_texts)

    power_vcc_passed = any(
        ("3.3v" in source.lower() or "3.3v" in target.lower())
        and (
            (_endpoint_component(source) in component_names)
            or (_endpoint_component(target) in component_names)
        )
        for source, target in endpoints
    )
    checks.append(
        {
            "rule": "POWER_VCC",
            "passed": power_vcc_passed,
            "message": "At least one component is connected to 3.3V"
            if power_vcc_passed
            else "No component connection to 3.3V was found",
        }
    )

    gnd_passed = any("gnd" in source.lower() or "gnd" in target.lower() for source, target in endpoints)
    checks.append(
        {
            "rule": "GND_CONN",
            "passed": gnd_passed,
            "message": "GND connection exists" if gnd_passed else "No GND connection was found",
        }
    )

    pullup_passed = "pullup" in all_connection_text or "pull-up" in all_connection_text or "上拉" in all_connection_text
    checks.append(
        {
            "rule": "I2C_PULLUP",
            "passed": pullup_passed,
            "message": "I2C pull-up resistor connection exists"
            if pullup_passed
            else "No I2C pull-up resistor connection was found",
        }
    )

    power = design.get("power", {})
    decoupling_passed = isinstance(power, dict) and bool(str(power.get("decoupling_cap", "")).strip())
    checks.append(
        {
            "rule": "DECOUPLING_CAP",
            "passed": decoupling_passed,
            "message": "Decoupling capacitor is specified"
            if decoupling_passed
            else "power.decoupling_cap is empty",
        }
    )

    referenced_components: set[str] = set()
    for source, target in endpoints:
        for endpoint in (source, target):
            component = _endpoint_component(endpoint)
            if component:
                referenced_components.add(component)
    missing_components = sorted(referenced_components - component_names)
    integrity_passed = not missing_components
    checks.append(
        {
            "rule": "COMPONENT_INTEGRITY",
            "passed": integrity_passed,
            "message": "All referenced components are declared"
            if integrity_passed
            else f"Connections reference undeclared components: {', '.join(missing_components)}",
        }
    )

    citations = design.get("citations", [])
    citation_passed = isinstance(citations, list) and len(citations) > 0
    checks.append(
        {
            "rule": "CITATION_EXISTS",
            "passed": citation_passed,
            "message": "Citations exist" if citation_passed else "citations list is empty",
        }
    )

    return {"passed": all(check["passed"] for check in checks), "checks": checks}
