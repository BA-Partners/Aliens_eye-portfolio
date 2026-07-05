"""Phone number scanning for Aliens Eye."""

from __future__ import annotations

from datetime import datetime
from typing import Any


try:
    from phonenumbers import carrier, geocoder, is_possible_number, is_valid_number
    from phonenumbers import number_type as _number_type
    from phonenumbers import parse as _parse
    from phonenumbers import region_code_for_number
except ImportError:
    import phonenumbers

    _parse = phonenumbers.parse
    _number_type = phonenumbers.number_type
    carrier = phonenumbers.carrier
    geocoder = phonenumbers.geocoder
    is_possible_number = phonenumbers.is_possible_number
    is_valid_number = phonenumbers.is_valid_number
    region_code_for_number = phonenumbers.region_code_for_number


def _type_name(type_id: int) -> str:
    return {
        0: "unknown",
        1: "mobile",
        2: "fixed_line",
        3: "fixed_line_or_mobile",
        4: "toll_free",
        5: "premium_rate",
        6: "shared_cost",
        7: "voip",
        8: "personal_number",
        9: "pager",
        10: "uan",
        11: "voicemail",
    }.get(type_id, "unknown")


def _parse_number(raw: str, default_region: str) -> dict[str, Any] | None:
    text = raw.strip()
    if not text or text.lower() in {"n/a", "-", "none", "null", "nan"}:
        return None

    try:
        pn = _parse(text, default_region if not text.startswith("+") else None)
    except Exception:
        return None

    if not is_possible_number(pn) or not is_valid_number(pn):
        return None

    formatted = None
    try:
        import phonenumbers

        formatted = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        formatted = None

    return {
        "raw": raw,
        "e164": formatted or text,
        "country_code": int(pn.country_code),
        "type_id": int(_number_type(pn)),
        "type": _type_name(int(_number_type(pn))),
        "valid": int(is_valid_number(pn)),
        "possible": int(is_possible_number(pn)),
        "region": region_code_for_number(pn) or default_region,
        "carrier": "",
        "geolocation": "",
        "label": "",
        "datetime": datetime.now().isoformat(),
    }


def scan_numbers(
    candidates: list[str],
    default_region: str,
    dedupe: bool = True,
    only_valid: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in candidates:
        item = _parse_number(raw, default_region)
        if item is None:
            continue
        if only_valid and not item["valid"]:
            continue
        key = item.get("e164") or raw
        if dedupe:
            if key in seen:
                continue
            seen.add(key)
        results.append(item)

    summary = {
        "candidates": len(candidates),
        "unique_numbers": len(seen),
        "valid": sum(1 for item in results if item["valid"]),
        "possible": sum(1 for item in results if item["possible"]),
        "invalid": len(candidates) - len(results),
        "datetime": datetime.now().isoformat(),
    }
    return results, summary
