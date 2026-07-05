import importlib.util
from pathlib import Path


def load_phone_scanner():
    pkg_path = Path(__file__).resolve().parent.parent / "src" / "aliens_eye"
    spec = importlib.util.spec_from_file_location("phone_scanner", pkg_path / "phone_scanner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scan_numbers_valid_and_deduped():
    module = load_phone_scanner()
    results, summary = module.scan_numbers(
        ["13800138000", "+8613800138000", "n/a", "-", "13800138000"],
        default_region="CN",
    )
    assert summary["candidates"] == 5
    assert summary["valid"] == 1
    assert summary["unique_numbers"] == 1
    assert results[0]["e164"] == "+8613800138000"
    assert results[0]["valid"] == 1
    assert results[0]["type"] == "mobile"
    print("results=", results)
    print("summary=", summary)
    print("time=", __import__("datetime").datetime.now().isoformat())


def test_scan_numbers_invalid_inputs():
    module = load_phone_scanner()
    results, summary = module.scan_numbers(
        ["n/a", "-", "none", "  13800"],
        default_region="CN",
    )
    assert summary["valid"] == 0
    assert summary["invalid"] == 4
    assert results == []


def test_scan_numbers_only_valid_flag():
    module = load_phone_scanner()
    results, _ = module.scan_numbers(
        ["13800138000", "12345"],
        default_region="CN",
        only_valid=True,
    )
    assert all(item["valid"] for item in results)
    assert results[0]["e164"] == "+8613800138000"
