"""DocDrift - Documentation-code sync drift detection engine."""
import ast, re, json, sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

SKIP = frozenset('print str int float list dict set tuple len range type isinstance '
    'open super enumerate zip map filter sorted hasattr getattr setattr format repr '
    'bool any all max min sum abs round next iter reversed input id hash ord chr '
    'hex oct bin vars dir help staticmethod classmethod property Exception ValueError '
    'TypeError KeyError IndexError RuntimeError AttributeError ImportError OSError '
    'FileNotFoundError NotImplementedError StopIteration Path datetime'.split())
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env', '.tox'}


@dataclass
class Symbol:
    name: str; kind: str; file: str; line: int


@dataclass
class DocRef:
    name: str; file: str; line: int; context: str


@dataclass
class DriftIssue:
    file: str; line: int; symbol: str; reason: str; severity: str = "error"


def extract_symbols(code: str, filepath: str) -> List[Symbol]:
    """Extract function and class symbols from Python source via AST."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(Symbol(node.name, "function", filepath, node.lineno))
        elif isinstance(node, ast.ClassDef):
            out.append(Symbol(node.name, "class", filepath, node.lineno))
    return out


def extract_doc_refs(content: str, filepath: str) -> List[DocRef]:
    """Extract code references from Markdown documentation."""
    refs = []
    for m in re.finditer(r'```(?:python3?|py)\n(.*?)```', content, re.DOTALL):
        base = content[:m.start()].count('\n') + 2
        for i, line in enumerate(m.group(1).splitlines()):
            for name in re.findall(r'from\s+\S+\s+import\s+(\w+)', line):
                refs.append(DocRef(name, filepath, base + i, line.strip()))
            for name in re.findall(r'(\w+)\s*\(', line):
                if name not in SKIP:
                    refs.append(DocRef(name, filepath, base + i, line.strip()))
    for m in re.finditer(r'`(\w+)\(\)`', content):
        ln = content[:m.start()].count('\n') + 1
        if m.group(1) not in SKIP:
            refs.append(DocRef(m.group(1), filepath, ln, m.group(0)))
    return refs


def detect_drift(symbols: List[Symbol], refs: List[DocRef]) -> List[DriftIssue]:
    """Cross-reference doc refs against code symbols to find drift."""
    known = {s.name for s in symbols}
    issues, seen = [], set()
    for r in refs:
        key = (r.file, r.line, r.name)
        if key not in seen and r.name not in known:
            seen.add(key)
            issues.append(DriftIssue(r.file, r.line, r.name,
                f"Symbol `{r.name}` referenced in docs but not found in code"))
    return issues


def scan_project(root_path: str) -> dict:
    """Scan a project directory and return drift analysis."""
    root = Path(root_path)
    symbols, refs = [], []
    def ok(p):
        return not (SKIP_DIRS & set(p.parts))
    for f in root.rglob("*.py"):
        rel = f.relative_to(root)
        if ok(rel):
            try:
                symbols.extend(extract_symbols(f.read_text(errors='ignore'), str(rel)))
            except (OSError, PermissionError):
                continue
    for ext in ("*.md", "*.mdx", "*.rst"):
        for f in root.rglob(ext):
            rel = f.relative_to(root)
            if ok(rel):
                try:
                    refs.extend(extract_doc_refs(f.read_text(errors='ignore'), str(rel)))
                except (OSError, PermissionError):
                    continue
    issues = detect_drift(symbols, refs)
    total = len({(r.file, r.name) for r in refs})
    score = max(0, round((1 - len(issues) / max(total, 1)) * 100))
    return {"symbols": len(symbols), "refs": total, "issues": issues, "score": score}


def main(argv=None):
    """CLI entry point."""
    import argparse
    p = argparse.ArgumentParser(prog="docdrift", description="Detect documentation drift")
    p.add_argument("path", nargs="?", default=".", help="Project directory to scan")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--fail-under", type=int, default=0, help="Min freshness score (0-100)")
    args = p.parse_args(argv)
    r = scan_project(args.path)
    if args.json:
        print(json.dumps({"freshness_score": r["score"], "symbols": r["symbols"],
            "doc_refs": r["refs"], "issues": [{"file": i.file, "line": i.line,
            "symbol": i.symbol, "reason": i.reason} for i in r["issues"]]}, indent=2))
    else:
        print(f"\n\U0001f4ca DocDrift Report\n{'='*50}")
        for label, val in [("Code symbols", r["symbols"]), ("Doc references", r["refs"]),
                           ("Drift issues", len(r["issues"])), ("Freshness score", f"{r['score']}%")]:
            print(f"  {label:18s} {val}")
        print()
        for i in r["issues"]:
            print(f"  \U0001f534 {i.file}:{i.line} \u2014 {i.reason}")
        if not r["issues"]:
            print("  \u2705 No drift detected!")
    sys.exit(1 if r["issues"] or r["score"] < args.fail_under else 0)


if __name__ == "__main__":
    main()
