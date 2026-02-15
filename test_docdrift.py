"""Tests for DocDrift - documentation drift detection engine."""
import tempfile, pytest
from pathlib import Path
from docdrift import extract_symbols, extract_doc_refs, detect_drift, scan_project
from docdrift import Symbol, DocRef


def test_extract_symbols_finds_all_kinds():
    code = (
        "def process_payment(amount, currency):\n"
        "    return amount * 1.1\n\n"
        "class PaymentGateway:\n"
        "    def charge(self, amt):\n"
        "        return amt\n\n"
        "async def fetch_data(url):\n"
        "    return {}\n"
    )
    symbols = extract_symbols(code, "payments.py")
    names = {s.name for s in symbols}
    assert "process_payment" in names
    assert "PaymentGateway" in names
    assert "fetch_data" in names
    assert "charge" in names
    assert len(symbols) == 4
    assert all(s.file == "payments.py" for s in symbols)


def test_extract_symbols_handles_syntax_error():
    bad_code = "def broken(:\n  pass"
    symbols = extract_symbols(bad_code, "bad.py")
    assert symbols == []


def test_extract_doc_refs_from_code_blocks():
    md = (
        "# API Guide\n\n"
        "Use the payment function:\n\n"
        "```python\n"
        "from payments import process_payment\n"
        "result = process_payment(100, 'USD')\n"
        "validate_response(result)\n"
        "```\n\n"
        "Call `old_function()` for legacy support.\n"
    )
    refs = extract_doc_refs(md, "README.md")
    names = {r.name for r in refs}
    assert "process_payment" in names
    assert "validate_response" in names
    assert "old_function" in names
    assert all(r.file == "README.md" for r in refs)


def test_extract_doc_refs_skips_builtins():
    md = "```python\nprint(len(items))\nresult = str(42)\n```\n"
    refs = extract_doc_refs(md, "doc.md")
    names = {r.name for r in refs}
    assert "print" not in names
    assert "len" not in names
    assert "str" not in names


def test_detect_drift_finds_missing_symbols():
    symbols = [
        Symbol("process_payment", "function", "pay.py", 1),
        Symbol("PaymentGateway", "class", "pay.py", 5),
    ]
    refs = [
        DocRef("process_payment", "README.md", 10, "process_payment(100)"),
        DocRef("old_function", "README.md", 15, "old_function()"),
        DocRef("deleted_handler", "docs/api.md", 22, "deleted_handler(req)"),
    ]
    issues = detect_drift(symbols, refs)
    drifted = {i.symbol for i in issues}
    assert "old_function" in drifted
    assert "deleted_handler" in drifted
    assert "process_payment" not in drifted
    assert len(issues) == 2


def test_detect_drift_no_false_positives():
    symbols = [
        Symbol("connect", "function", "db.py", 1),
        Symbol("query", "function", "db.py", 10),
    ]
    refs = [
        DocRef("connect", "README.md", 5, "connect()"),
        DocRef("query", "README.md", 8, "query(sql)"),
    ]
    issues = detect_drift(symbols, refs)
    assert len(issues) == 0


def test_scan_project_detects_drift():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "app.py").write_text(
            "def hello():\n    return 'hi'\n\ndef greet(name):\n    return name\n")
        Path(tmp, "README.md").write_text(
            "# App\n```python\nresult = hello()\ndata = removed_func()\n```\n")
        result = scan_project(tmp)
        assert result["symbols"] >= 2
        assert result["refs"] >= 2
        drifted_names = {i.symbol for i in result["issues"]}
        assert "removed_func" in drifted_names
        assert "hello" not in drifted_names
        assert result["score"] < 100


def test_scan_project_perfect_score():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "lib.py").write_text(
            "def alpha():\n    return 1\n\ndef beta():\n    return 2\n")
        Path(tmp, "docs.md").write_text(
            "# Lib\n```python\nalpha()\nbeta()\n```\n")
        result = scan_project(tmp)
        assert result["score"] == 100
        assert len(result["issues"]) == 0


def test_scan_project_empty():
    with tempfile.TemporaryDirectory() as tmp:
        result = scan_project(tmp)
        assert result["score"] == 100
        assert result["symbols"] == 0
        assert result["refs"] == 0
        assert result["issues"] == []
